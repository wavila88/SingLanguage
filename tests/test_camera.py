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


def test_run_camera_mirrors_and_exits_on_q(monkeypatch):
    frame = np.zeros((4, 6, 3), dtype=np.uint8)
    frame[:, :3] = 255
    cap = FakeCapture([frame, frame])

    shown = []
    texts = []
    destroyed = []

    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append((name, img.copy())))
    monkeypatch.setattr(camera.cv2, "putText", lambda img, text, *args, **kwargs: texts.append(text))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: destroyed.append(True))
    keys = iter([ord("a"), ord("q")])
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
    shown = []

    monkeypatch.setattr(camera.cv2, "imshow", lambda name, img: shown.append(name))
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(camera.cv2, "waitKey", lambda delay: ord("x"))
    monkeypatch.setattr(camera.cv2, "getWindowProperty", lambda name, prop: 0 if shown else 1)

    camera.run_camera(cap)

    assert len(shown) == 1
    assert cap.released is True


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
