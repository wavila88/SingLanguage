"""Continuous recognition window (v2): no Grabar or Detener buttons.

Each sign is cut out of the video on its own:
- When the wrists move, frames are collected. Once the hands stay still for END_STILL_SECONDS (or leave the
  frame), the collected stretch goes to the motion model, the same way Detener did in the first version.
- When one hand stays still for STATIC_HOLD_SECONDS, the average of that pause goes to the static (vowel)
  model. A pause gives at most one letter; the hand has to move again before the next one.
- If a movement gave a word, the stillness after it is not read as a letter (every gesture ends still).
  If it gave nothing, it was a transition (e.g. from A to E) and the stillness is read as a letter.

What is recognized builds a message on a strip at the bottom of the window: letters in a row are
separated by ", " and words by a space. The message clears after CLEAR_AFTER_SECONDS without new signs.
"""
import math
import pickle
import sys
import time
from collections import deque
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from camera import open_camera, run_camera
from dataset import MIDDLE_MCP, WRIST, hand_record, motion_features, normalize_landmarks
from hands import HandDetector
from recognize_message import MIN_FRAMES, MODEL_PATH, NOTHING, load_motion_model
from textdraw import draw_text, text_width
from widgets import STRIP_HEIGHT, TEXT, TEXT_SECONDARY, draw_strip, scale_for

MOVE_SPEED = 2.5  # hand sizes per second; a wrist faster than this is moving (hand tremor stays under it)
SPEED_WINDOW_SECONDS = 0.15  # speed is measured against the frame this long ago, so jitter does not count
MIN_TRAVEL = 0.05  # a movement must take a wrist this far (image fraction); recorded gestures start at 0.07, tremor stays ~0.02
END_STILL_SECONDS = 0.4  # still this long after moving: the movement is over
STATIC_HOLD_SECONDS = 0.7  # one hand holding a sign this long: it is read as a static sign
STATIC_AGREEMENT = 0.7  # share of the frames in that time that must show the same sign
CLEAR_AFTER_SECONDS = 4.0  # the message clears after this long without new signs
MIN_MOTION_PROBABILITY = 0.4  # same as the first version's Grabar/Detener
MIN_STATIC_PROBABILITY = 0.6
PLACEHOLDER = "Haz un signo frente a la cámara"


def best_label(model, features, min_probability):
    """The model's best label, or None when it is not sure enough or says `nada`."""
    probabilities = model.predict_proba([features])[0]
    best = max(range(len(probabilities)), key=lambda i: probabilities[i])
    label = str(model.classes_[best])
    if probabilities[best] < min_probability or label == NOTHING:
        return None
    return label


def motion_label(model, frames):
    if model is None or len(frames) < MIN_FRAMES:
        return None
    return best_label(model, motion_features(frames), MIN_MOTION_PROBABILITY)


def average_landmarks(hands):
    """Point-by-point average of several detections of the same hand."""
    return [tuple(sum(hand[i][axis] for hand in hands) / len(hands) for axis in range(3))
            for i in range(len(hands[0]))]


def static_label(model, landmarks):
    features = [value for point in normalize_landmarks(landmarks) for value in point]
    return best_label(model, features, MIN_STATIC_PROBABILITY)


def hand_speed(previous, current, seconds):
    """Fastest wrist among the hands seen in both frames, in hand sizes per second."""
    if not previous or not current or seconds <= 0:
        return 0.0
    before = dict(previous)
    speeds = []
    for side, landmarks in current:
        if side in before:
            size = math.dist(landmarks[WRIST][:2], landmarks[MIDDLE_MCP][:2]) or 1e-6
            speeds.append(math.dist(landmarks[WRIST][:2], before[side][WRIST][:2]) / size / seconds)
    return max(speeds, default=0.0)


class SignSegmenter:
    """Turns the hands of each frame into ("word", label) or ("letter", label) events."""

    def __init__(self, static_model, motion_model):
        self.static_model = static_model
        self.motion_model = motion_model
        self._reset()

    def _reset(self):
        self.history = deque()
        self.moving = False
        self.segment = []
        self.still_since = None
        self.votes = deque()  # (time, static label or None) of the last STATIC_HOLD_SECONDS
        self.armed = True  # a letter can be emitted; false after one until the hand moves, changes or leaves
        self.static_allowed = True

    def feed(self, now, hands):
        """`hands` is a list of (side, landmarks); returns the event this frame produced, or None."""
        if not hands:
            event = self._close_segment() if self.moving else None
            self._reset()
            return event
        while self.history and now - self.history[0][0] > SPEED_WINDOW_SECONDS:
            self.history.popleft()
        speed = hand_speed(self.history[0][1], hands, now - self.history[0][0]) if self.history else 0.0
        self.history.append((now, hands))
        fast = speed > MOVE_SPEED
        if fast:
            self.moving = True
            self.static_allowed = self.armed = True
            self.still_since = None
            self._append(now, hands)
        else:
            if self.still_since is None:
                self.still_since = now
            if self.moving:
                self._append(now, hands)
        event = self._vote(now, hands)
        if self.moving and not fast and now - self.still_since >= END_STILL_SECONDS:
            event = self._close_segment() or event
        return event

    def _vote(self, now, hands):
        """Static signs: the model looks at every frame and a letter needs most of the last 0.7 s to agree.

        It does not depend on the hand being perfectly still: a trembling hand shows the same sign each frame.
        """
        label = None
        if len(hands) == 1:
            label = static_label(self.static_model, hands[0][1])
        self.votes.append((now, label))
        while now - self.votes[0][0] > STATIC_HOLD_SECONDS:
            self.votes.popleft()
        labels = [vote for _, vote in self.votes]
        top = max(set(labels), key=labels.count)
        agreed = top is not None and labels.count(top) >= STATIC_AGREEMENT * len(labels)
        if not agreed:
            self.armed = True  # the sign changed or the hand is in transit: the next steady sign counts
            return None
        if now - self.votes[0][0] < STATIC_HOLD_SECONDS * 0.9 or self.moving:
            return None
        if self.armed and self.static_allowed:
            self.armed = False
            return ("letter", top)
        return None

    def _append(self, now, hands):
        self.segment.append({"index": len(self.segment), "ms": round(now * 1000),
                             "hands": [hand_record(side, landmarks) for side, landmarks in hands]})

    def _travel(self):
        """How far any wrist got from where it started, in image fractions."""
        first, farthest = {}, 0.0
        for frame in self.segment:
            for hand in frame["hands"]:
                start = first.setdefault(hand["side"], hand["wrist"][:2])
                farthest = max(farthest, math.dist(start, hand["wrist"][:2]))
        return farthest

    def _close_segment(self):
        label = motion_label(self.motion_model, self.segment) if self._travel() >= MIN_TRAVEL else None
        self.moving, self.segment = False, []
        if label:
            self.static_allowed = False
            return ("word", label)
        return None


class MessageLine:
    """The message being built: letters in a row joined by ", ", words by a space."""

    def __init__(self):
        self.items = []
        self.last_added = None

    def add(self, kind, label, now):
        self.items.append((kind, label.upper()))
        self.last_added = now

    def update(self, now):
        if self.items and now - self.last_added >= CLEAR_AFTER_SECONDS:
            self.items = []

    def text(self):
        parts = []
        for i, (kind, label) in enumerate(self.items):
            if i:
                parts.append(", " if kind == "letter" and self.items[i - 1][0] == "letter" else " ")
            parts.append(label)
        return "".join(parts)


class ContinuousRecognizer:
    def __init__(self, static_model, motion_model):
        self.segmenter = SignSegmenter(static_model, motion_model)
        self.message = MessageLine()

    def step(self, now, hands):
        """Feed one frame and return the message to show."""
        event = self.segmenter.feed(now, hands)
        if event:
            self.message.add(*event, now)
        self.message.update(now)
        return self.message.text()


def draw_message(frame, text):
    """The message on the bottom strip; when it is too long, its end is kept."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    draw_strip(frame)
    size = max(1, round(28 * scale))
    margin = round(24 * scale)
    while text and text_width(text, size) > width - 2 * margin:
        text = text[1:]
    center_y = height - round(STRIP_HEIGHT * scale) // 2
    if text:
        draw_text(frame, text, (margin, center_y), TEXT[::-1], size=size, anchor="lm", bold=True)
    else:
        draw_text(frame, PLACEHOLDER, (margin, center_y), TEXT_SECONDARY[::-1], size=max(1, round(18 * scale)),
                  anchor="lm")
    return frame


def run_recognition_v2(cap, detector, static_model, motion_model, clock=time.monotonic):
    recognizer = ContinuousRecognizer(static_model, motion_model)

    def overlay(frame, detector, now):
        hands = list(zip(detector.handedness(), detector.landmarks())) if detector else []
        draw_message(frame, recognizer.step(now, hands))

    run_camera(cap, detector, clock=clock, overlay=overlay)


def main():
    with MODEL_PATH.open("rb") as file:
        static_model = pickle.load(file)
    cap = open_camera()
    run_recognition_v2(cap, HandDetector(max_num_hands=2), static_model, load_motion_model())


if __name__ == "__main__":
    main()
