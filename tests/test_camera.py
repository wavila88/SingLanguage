import numpy as np
import pytest

from src import camera
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
    def __init__(self, hands=()):
        self._hands = list(hands)
        self.closed = False

    def process(self, frame):
        return len(self._hands)

    def landmarks(self):
        return self._hands

    def draw(self, frame):
        return frame

    def close(self):
        self.closed = True


class FakeRepository:
    def __init__(self):
        self.saved = []

    def save_sample(self, label, points):
        self.saved.append((label, points))


def _hand():
    return [(float(i), float(i) * 0.5, 0.1 * i) for i in range(21)]


def _frames(count):
    return [np.zeros((4, 6, 3), dtype=np.uint8) for _ in range(count)]


def _drive(monkeypatch, cap, detector=None, repository=None, keys=()):
    shown = []
    texts = []
    key_iter = iter(keys)
    monkeypatch.setattr(camera, "setup_window", lambda aspect_ratio: (60, 40))
    monkeypatch.setattr(camera, "window_closed", lambda: False)
    monkeypatch.setattr(camera, "get_window_size", lambda default: default)
    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append(img))
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: next(key_iter, -1))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(camera, "draw_text", lambda img, text, *args, **kwargs: texts.append(text))
    camera.run_camera(cap, detector, repository)
    return shown, texts


def test_capture_window_shows_the_two_mode_buttons(monkeypatch):
    cap = FakeCapture(_frames(1))

    _, texts = _drive(monkeypatch, cap, FakeDetector(), FakeRepository())

    assert "Expresión estática" in texts
    assert "Expresión en movimiento" in texts


def test_keys_do_not_close_the_window_or_save_samples(monkeypatch):
    cap = FakeCapture(_frames(4))
    repository = FakeRepository()

    shown, _ = _drive(
        monkeypatch, cap, FakeDetector([_hand()]), repository,
        keys=[ord("q"), ord("a"), ord("e"), 27],
    )

    assert len(shown) == 4
    assert repository.saved == []
    assert cap.released is True


def test_run_camera_mirrors_each_frame(monkeypatch):
    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    frame[:, :3] = 255
    cap = FakeCapture([frame, frame])

    shown = []
    texts = []
    destroyed = []

    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append((name, img.copy())))
    monkeypatch.setattr(camera, "draw_text", lambda img, text, *args, **kwargs: texts.append(text))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: destroyed.append(True))
    keys = iter([ord("a"), ord("b")])
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: next(keys))

    camera.run_camera(cap)

    assert len(shown) == 2
    name, last_image = shown[-1]
    assert name == camera.WINDOW_NAME
    assert last_image[0, 0, 0] == 0
    assert last_image[0, -1, 0] == 255
    assert texts == []
    assert cap.released is True
    assert destroyed == [True]


def test_run_camera_stops_and_releases_when_window_is_closed_with_x(monkeypatch):
    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    cap = FakeCapture([frame, frame, frame])
    detector = FakeDetector()
    shown = []

    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append(name))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: ord("x"))
    monkeypatch.setattr(camera.cv2, "getWindowProperty", lambda name, prop: 0 if shown else 1)

    camera.run_camera(cap, detector)

    assert len(shown) == 1
    assert cap.released is True
    assert detector.closed is True


def test_main_reports_error_and_exits_when_camera_cannot_open(monkeypatch, capsys):
    class ClosedCapture(FakeCapture):
        def isOpened(self):
            return False

    cap = ClosedCapture([])
    started = []

    monkeypatch.setattr(main.cv2, "VideoCapture", lambda index: cap)
    monkeypatch.setattr(main, "run_camera", lambda c: started.append(c))

    with pytest.raises(SystemExit) as exc:
        main.main()

    assert exc.value.code == 1
    assert started == []
    assert "cámara" in capsys.readouterr().err.lower()


def test_ctrl_c_releases_camera_without_closing_detector(monkeypatch):
    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    cap = FakeCapture([frame])

    class InterruptedDetector:
        closed = False

        def process(self, image):
            raise KeyboardInterrupt

        def close(self):
            self.closed = True

    detector = InterruptedDetector()
    monkeypatch.setattr(camera, "setup_window", lambda aspect_ratio: (100, 100))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: None)

    camera.run_camera(cap, detector)

    assert cap.released is True
    assert detector.closed is False


def test_menu_buttons_are_side_by_side_at_the_bottom_so_the_face_stays_visible():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    camera.draw_menu(frame)

    painted = frame.any(axis=2)
    assert not painted[: int(480 * 0.75)].any()
    button_color = frame[480 - 16 - 24, 40]    # inside the left button, away from its text
    assert (button_color[::-1] == (143, 228, 206)).all()
    assert (frame[480 - 16 - 24, 320] != button_color).any()  # gap between buttons shows the strip
    assert (frame[480 - 16 - 24, 335] == button_color).all()  # right button
