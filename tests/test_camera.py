import numpy as np
import pytest

import capture_ui
import dataset
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

    def handedness(self):
        return ["left", "right"][:len(self._hands)]

    def draw(self, frame):
        return frame

    def close(self):
        self.closed = True


class FakeRepository:
    def __init__(self, counts=None):
        self.saved = []
        self.static_saved = []
        self.opened = []
        self._counts = counts or {}

    def save_sample(self, label, points):
        self.saved.append((label, points))

    def save_static_sample(self, label, hands):
        self.static_saved.append((label, hands))

    def open_expression(self, label, kind):
        self.opened.append((label, kind))
        return self._counts.get((label, kind), 0)


def _hand(dx=0.0):
    return [(dx + float(i), float(i) * 0.5, 0.1 * i) for i in range(21)]


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
    monkeypatch.setattr(camera.cv2, "setMouseCallback", lambda *args: None)
    monkeypatch.setattr(camera, "draw_text", lambda img, text, *args, **kwargs: texts.append(text))
    camera.run_camera(cap, detector, repository)
    return shown, texts


def _play(monkeypatch, steps, repository=None, window=(640, 480), detector=None, images=None):
    """Run the capture window on 640x480 frames, performing one scripted step per frame.

    A step is ("click", x, y) in video coordinates (translated to where the click lands in a
    window of the given size), ("key", code) or ("text", "abc"). Returns the texts drawn on each frame.
    """
    window_w, window_h = window
    scale = min(window_w / 640, window_h / 480)
    offset_x, offset_y = (window_w - 640 * scale) / 2, (window_h - 480 * scale) / 2
    queue = []
    for step in steps:
        if step[0] == "text":
            queue.extend(("key", ord(char)) for char in step[1])
        else:
            queue.append(step)
    handler = {}
    per_frame, current = [], []

    clock_state = {"now": 0.0}  # half a second per frame, so recordings have predictable timing

    def wait_key(delay):
        result = next_key(delay)
        clock_state["now"] += 0.5
        return result

    def next_key(delay):
        step = queue.pop(0) if queue else None
        if step is None:
            return -1
        if step[0] == "click":
            handler["callback"](camera.cv2.EVENT_LBUTTONDOWN, int(offset_x + step[1] * scale),
                                int(offset_y + step[2] * scale), 0, None)
            return -1
        return step[1]

    def imshow(name, img):
        per_frame.append(list(current))
        current.clear()
        if images is not None:
            images.append(img.copy())

    monkeypatch.setattr(camera, "setup_window", lambda aspect_ratio: window)
    monkeypatch.setattr(camera, "window_closed", lambda: False)
    monkeypatch.setattr(camera, "get_window_size", lambda default: window)
    monkeypatch.setattr(camera.cv2, "imshow", imshow)
    monkeypatch.setattr(camera.cv2, "waitKey", wait_key)
    monkeypatch.setattr(camera.cv2, "destroyAllWindows", lambda: None)
    monkeypatch.setattr(camera.cv2, "setMouseCallback",
                        lambda name, callback, *args: handler.__setitem__("callback", callback))
    monkeypatch.setattr(camera, "draw_text", lambda img, text, *args, **kwargs: current.append(text))
    cap = FakeCapture([np.full((480, 640, 3), 10 * (index + 1), dtype=np.uint8) for index in range(len(queue) + 2)])
    camera.run_camera(cap, detector or FakeDetector(), repository, clock=lambda: clock_state["now"])
    return per_frame


def _center(rect):
    x0, y0, x1, y1 = rect
    return (x0 + x1) // 2, (y0 + y1) // 2


def _click(rect):
    return ("click", *_center(rect))


def _open(mode, name):
    """Steps that choose a mode, type `name` and click Aceptar."""
    return [_click(capture_ui.menu_layout(640, 480)[mode]), ("text", name),
            _click(capture_ui.name_layout(640, 480)["accept"])]


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


def test_choosing_static_and_typing_a_new_name_opens_it_with_zero_samples(monkeypatch):
    repository = FakeRepository()

    frames = _play(monkeypatch, _open("static", "hola"), repository)

    assert repository.opened == [("hola", "static")]
    assert "HOLA · estática · 0 muestras" in frames[-1]


def test_name_input_shows_the_chosen_mode_and_the_typed_name(monkeypatch):
    steps = [_click(capture_ui.menu_layout(640, 480)["motion"]), ("text", "ho")]

    frames = _play(monkeypatch, steps, FakeRepository())

    assert "Expresión en movimiento" in frames[-1]
    assert "ho" in frames[-1]


def test_backspace_deletes_the_last_typed_character(monkeypatch):
    repository = FakeRepository()
    steps = [_click(capture_ui.menu_layout(640, 480)["static"]), ("text", "holx"), ("key", 8), ("text", "a"),
             _click(capture_ui.name_layout(640, 480)["accept"])]

    _play(monkeypatch, steps, repository)

    assert repository.opened == [("hola", "static")]


def test_enter_confirms_the_name_like_aceptar(monkeypatch):
    repository = FakeRepository()
    steps = [_click(capture_ui.menu_layout(640, 480)["static"]), ("text", "hola"), ("key", 13)]

    frames = _play(monkeypatch, steps, repository)

    assert repository.opened == [("hola", "static")]
    assert "HOLA · estática · 0 muestras" in frames[-1]


def test_existing_expression_opens_with_its_motion_sample_count(monkeypatch):
    repository = FakeRepository({("hola", "motion"): 12})

    frames = _play(monkeypatch, _open("motion", "hola"), repository)

    assert repository.opened == [("hola", "motion")]
    assert "HOLA · en movimiento · 12 muestras" in frames[-1]


def test_names_can_have_enye_and_accents(monkeypatch):
    repository = FakeRepository()

    _play(monkeypatch, _open("static", "añó"), repository)

    assert repository.opened == [("añó", "static")]


def test_clicks_land_on_the_buttons_when_the_window_is_resized(monkeypatch):
    repository = FakeRepository()

    frames = _play(monkeypatch, _open("static", "hola"), repository, window=(1280, 720))

    assert repository.opened == [("hola", "static")]
    assert "HOLA · estática · 0 muestras" in frames[-1]


def test_volver_goes_back_to_the_menu(monkeypatch):
    steps = _open("static", "hola") + [_click(capture_ui.expression_layout(640, 480)["back"])]

    frames = _play(monkeypatch, steps, FakeRepository())

    assert "Expresión estática" in frames[-1]
    assert "Expresión en movimiento" in frames[-1]
    assert not any("HOLA" in text for text in frames[-1])


def test_volver_in_the_name_input_goes_back_to_the_menu(monkeypatch):
    steps = [_click(capture_ui.menu_layout(640, 480)["static"]), ("text", "ho"),
             _click(capture_ui.name_layout(640, 480)["back"])]

    frames = _play(monkeypatch, steps, FakeRepository())

    assert "Expresión en movimiento" in frames[-1]


def _static_hola(*extra):
    """Steps that open `hola` in static mode, then `extra`."""
    return _open("static", "hola") + list(extra)


def _capture_button():
    return _click(capture_ui.expression_layout(640, 480)["capture"])


def _approve_button():
    return _click(capture_ui.review_layout(640, 480)["approve"])


def test_capturar_freezes_the_frame_and_shows_only_approve_and_discard(monkeypatch):
    images = []
    detector = FakeDetector([_hand(), _hand(5.0)])

    frames = _play(monkeypatch, _static_hola(_capture_button(), ("key", -1), ("key", -1)), FakeRepository(),
                   detector=detector, images=images)

    assert "Aprobar" in frames[-1] and "No aprobar" in frames[-1]
    assert "Capturar" not in frames[-1] and "Volver" not in frames[-1]
    assert images[-1][200, 320, 0] == images[-2][200, 320, 0]  # frozen: later frames repeat the same image


def test_the_live_video_keeps_moving_before_capturing(monkeypatch):
    images = []

    _play(monkeypatch, _static_hola(("key", -1), ("key", -1)), FakeRepository(), detector=FakeDetector([_hand()]),
          images=images)

    assert images[-1][200, 320, 0] != images[-2][200, 320, 0]


def test_aprobar_saves_one_static_sample_with_each_hand_labeled_left_or_right(monkeypatch):
    repository = FakeRepository({("hola", "static"): 12})
    detector = FakeDetector([_hand(), _hand(5.0)])

    frames = _play(monkeypatch, _static_hola(_capture_button(), _approve_button()), repository, detector=detector)

    assert len(repository.static_saved) == 1
    label, hands = repository.static_saved[0]
    assert label == "hola"
    assert [hand["side"] for hand in hands] == ["left", "right"]
    expected = [value for point in dataset.normalize_landmarks(_hand(5.0)) for value in point]
    assert hands[1]["points"] == expected
    assert len(hands[0]["points"]) == 63
    assert hands[1]["wrist"] == [5.0, 0.0, 0.0]
    assert "Guardada muestra: HOLA (2 manos)" in frames[-1]
    assert "HOLA · estática · 13 muestras" in frames[-1]


def test_aprobar_goes_back_to_live_video_with_capturar_enabled_again(monkeypatch):
    repository = FakeRepository()

    frames = _play(monkeypatch, _static_hola(_capture_button(), _approve_button()), repository,
                   detector=FakeDetector([_hand()]))

    assert "Guardada muestra: HOLA (1 mano)" in frames[-1]
    assert "Capturar" in frames[-1] and "Volver" in frames[-1]
    assert "Aprobar" not in frames[-1]


def test_capturar_with_no_hand_does_not_enter_the_review(monkeypatch):
    repository = FakeRepository()

    frames = _play(monkeypatch, _static_hola(_capture_button(), _approve_button()), repository,
                   detector=FakeDetector())

    assert "Aprobar" not in frames[-1]
    assert repository.static_saved == []


def test_motion_expressions_have_no_capturar_button(monkeypatch):
    frames = _play(monkeypatch, _open("motion", "hola"), FakeRepository(), detector=FakeDetector([_hand()]))

    assert "Capturar" not in frames[-1]
    assert "Volver" in frames[-1]
