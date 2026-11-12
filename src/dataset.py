import math
from typing import Protocol

VOWELS = "aeiou"

WRIST = 0
MIDDLE_MCP = 9

HAND_SIDES = ("left", "right")
HAND_VALUES = 63 + 3  # normalized points plus the raw wrist
MOTION_STEPS = 16  # frames every recorded sequence is resampled to


class SampleRepository(Protocol):
    def save_sample(self, label, points): ...

    def open_expression(self, label, kind): ...

    def save_static_sample(self, label, hands): ...

    def save_motion_sample(self, label, frames): ...


def hand_record(side, landmarks):
    """What is stored for one visible hand: its side, normalized points and raw wrist position."""
    return {
        "side": side,
        "points": [value for point in normalize_landmarks(landmarks) for value in point],
        "wrist": list(landmarks[WRIST]),
    }


def normalize_phrase(label):
    """Phrases typed as `Hola` or `hola ` are the same phrase."""
    return label.strip().lower()


def _hand_slot(hand):
    if hand is None:
        return [0.0] * (HAND_VALUES + 1)
    return list(hand["points"]) + list(hand["wrist"]) + [1.0]  # the last value says the hand is there


def _slots(hands):
    """The hand in each side's slot (None when missing); two hands with the same label still fit."""
    slots = {side: None for side in HAND_SIDES}
    extra = []
    for hand in hands:
        if hand["side"] in slots and slots[hand["side"]] is None:
            slots[hand["side"]] = hand
        else:
            extra.append(hand)
    for hand in extra:
        for side in HAND_SIDES:
            if slots[side] is None:
                slots[side] = hand
                break
    return slots


def hand_features(hands):
    """Fixed-length features for one or two stored hands: left slot, then right slot, missing hand as zeros."""
    slots = _slots(hands)
    return [value for side in HAND_SIDES for value in _hand_slot(slots[side])]


def _wrist_features(hands):
    """Where each wrist is in the image (x, y) and whether the hand is there, left slot then right slot."""
    slots = _slots(hands)
    return [value for side in HAND_SIDES
            for value in (list(slots[side]["wrist"][:2]) + [1.0] if slots[side] else [0.0, 0.0, 0.0])]


def motion_features(frames, steps=MOTION_STEPS):
    """Fixed-length features for a recorded sequence of frames, whatever its duration or frame count.

    The sequence is resampled to `steps` frames over its own duration, counted from its first saved frame
    (frames with no hand were left out when saving). The features are the path of each wrist over those frames
    (what defines a motion), the duration in seconds, and the average hand shape over the sequence.
    """
    first = frames[0]["ms"]
    duration = frames[-1]["ms"] - first
    path, shape = [], [0.0] * (len(HAND_SIDES) * (HAND_VALUES + 1))
    for step in range(steps):
        target = duration * step / (steps - 1)
        nearest = min(frames, key=lambda frame: abs(frame["ms"] - first - target))
        path += _wrist_features(nearest["hands"])
        shape = [total + value for total, value in zip(shape, hand_features(nearest["hands"]))]
    return path + [duration / 1000] + [total / steps for total in shape]


def normalize_landmarks(landmarks):
    """Coordinates relative to the wrist, divided by the wrist-to-middle-knuckle distance."""
    wrist = landmarks[WRIST]
    scale = math.dist(wrist, landmarks[MIDDLE_MCP])
    return [
        ((x - wrist[0]) / scale, (y - wrist[1]) / scale, (z - wrist[2]) / scale)
        for x, y, z in landmarks
    ]
