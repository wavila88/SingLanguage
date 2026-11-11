import numpy as np

import camera
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


def _run(cap, detector, model, keys, monkeypatch, close_after_first_frame=False):
    shown = []
    texts = []
    monkeypatch.setattr(camera, "setup_window", lambda aspect_ratio: (60, 40))
    monkeypatch.setattr(camera, "window_closed", lambda: close_after_first_frame and bool(shown))
    monkeypatch.setattr(camera, "get_window_size", lambda default: default)
    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append(img))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(camera, "draw_text", lambda img, text, *args, **kwargs: texts.append(text))
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: next(keys, -1))
    run_recognition(cap, detector, model)
    return shown, texts


def test_one_hand_shows_predicted_vowel_and_confidence_without_the_mode_menu(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame()])
    detector = FakeDetector([_hand()])
    model = FakeModel()

    _, texts = _run(cap, detector, model, iter([ord("x"), ord("y")]), monkeypatch)

    assert "A 87%" in texts
    assert len(model.rows[0][0]) == 63
    assert "Expresión estática" not in texts


def test_q_does_not_close_the_recognition_window(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame(), _any_frame()])

    shown, _ = _run(cap, FakeDetector([_hand()]), FakeModel(), iter([ord("q"), ord("q"), ord("q")]), monkeypatch)

    assert len(shown) == 3


def test_closing_with_x_releases_camera_and_detector(monkeypatch):
    cap = FakeCapture([_any_frame(), _any_frame(), _any_frame()])
    detector = FakeDetector([_hand()])

    shown, _ = _run(cap, detector, FakeModel(), iter([]), monkeypatch, close_after_first_frame=True)

    assert len(shown) == 1
    assert cap.released is True
    assert detector.closed is True
