import numpy as np
import pytest

from src import camera, hands
from capture import capture_words as main


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
        self.closed = False

    def process(self, frame):
        return self.hands_count

    def draw(self, frame):
        self.drawn += 1
        return frame

    def close(self):
        self.closed = True


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


class ClosableDetector:
    def __init__(self):
        self.closed = False

    def process(self, frame):
        return 1

    def draw(self, frame):
        return frame

    def close(self):
        self.closed = True


def test_q_releases_both_detector_and_camera(monkeypatch):
    cap = FakeCapture([_any_frame()])
    detector = ClosableDetector()

    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: None)
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: ord("q"))
    camera.run_camera(cap, detector)

    assert cap.released is True
    assert detector.closed is True


def test_detector_init_failure_prints_error_exits_1_and_releases_camera(monkeypatch, capsys):
    cap = FakeCapture([])
    cap.isOpened = lambda: True

    def broken_detector(max_num_hands=2):
        raise RuntimeError("modelo no encontrado")

    monkeypatch.setattr(main.cv2, "VideoCapture", lambda index: cap)
    monkeypatch.setattr(main, "HandDetector", broken_detector)

    with pytest.raises(SystemExit) as exc:
        main.main()

    assert exc.value.code == 1
    assert cap.released is True
    assert "error" in capsys.readouterr().err.lower()
