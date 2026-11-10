import cv2
import numpy as np

from recognize_message import run_recognition


class FakeCapture:
    def __init__(self, frames):
        self._frames = list(frames)
        self.released = False

    def read(self):
        if not self._frames:
            return False, None
        return True, self._frames.pop(0)

    def release(self):
        self.released = True


class FakeDetector:
    def __init__(self, hands):
        self._hands = hands
        self.closed = False

    def process(self, frame):
        return len(self._hands)

    def landmarks(self):
        return self._hands

    def draw(self, frame):
        return frame

    def close(self):
        self.closed = True


class FakeModel:
    classes_ = np.array(list("aeiou"))

    def __init__(self):
        self.rows = []

    def predict_proba(self, rows):
        self.rows.append(rows)
        return np.array([[0.87, 0.05, 0.03, 0.03, 0.02]])


def _hand():
    return [(float(i), float(i) * 0.5, 0.1 * i) for i in range(21)]


def _any_frame():
    return np.zeros((4, 6, 3), dtype=np.uint8)


def _run(cap, detector, model, keys, monkeypatch):
    texts = []
    monkeypatch.setattr(cv2, "imshow", lambda name, img: None)
    monkeypatch.setattr(cv2, "putText", lambda img, text, *args, **kwargs: texts.append(text))
    monkeypatch.setattr(cv2, "waitKey", lambda delay: next(keys))
    run_recognition(cap, detector, model)
    return texts


def test_one_hand_shows_predicted_vowel_and_confidence(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame()])
    detector = FakeDetector([_hand()])
    model = FakeModel()

    texts = _run(cap, detector, model, iter([ord("x"), ord("q")]), monkeypatch)

    assert "A 87%" in texts
    assert len(model.rows[0][0]) == 63


def test_q_releases_camera_and_detector(monkeypatch):
    cap = FakeCapture([_any_frame()])
    detector = FakeDetector([_hand()])

    _run(cap, detector, FakeModel(), iter([ord("q")]), monkeypatch)

    assert cap.released is True
    assert detector.closed is True
