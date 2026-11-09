import numpy as np

from src import camera, hands


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
    def __init__(self, hands_count):
        self.hands_count = hands_count
        self.drawn = 0

    def process(self, frame):
        return self.hands_count

    def draw(self, frame):
        self.drawn += 1
        return frame


def _run(cap, detector, keys, monkeypatch):
    shown = []
    texts = []
    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append((name, img)))
    monkeypatch.setattr(camera.cv2, "putText", lambda img, text, *args, **kwargs: texts.append(text))
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: next(keys))
    camera.run_camera(cap, detector)
    return shown, texts


def _any_frame():
    return np.zeros((4, 6, 3), dtype=np.uint8)


def test_one_hand_is_drawn_without_warning(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame()])
    detector = FakeDetector(1)

    shown, texts = _run(cap, detector, iter([ord("x"), ord("q")]), monkeypatch)

    assert len(shown) == 2
    assert detector.drawn == 2
    assert all(t != hands.NO_HAND_TEXT for t in texts)


def test_two_hands_are_both_drawn(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame()])
    detector = FakeDetector(2)

    shown, texts = _run(cap, detector, iter([ord("x"), ord("q")]), monkeypatch)

    assert len(shown) == 2
    assert detector.drawn == 2
    assert all(t != hands.NO_HAND_TEXT for t in texts)


def test_no_hand_shows_no_hand_detected_warning(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame()])
    detector = FakeDetector(0)

    shown, texts = _run(cap, detector, iter([ord("x"), ord("q")]), monkeypatch)

    assert len(shown) == 2
    assert detector.drawn == 0
    assert texts.count(hands.NO_HAND_TEXT) == 2
