import time

import cv2
import numpy as np

from capture_ui import (CaptureUI, MODE_BUTTONS, MODE_KEYS, RecognizeUI, expression_layout, menu_layout,
                        name_layout, review_layout)
from hands import NO_HAND_TEXT
from textdraw import draw_text, text_width
from widgets import (BUTTON_TEXT_SIZE, PRIMARY_TEXT, TEXT, TEXT_SECONDARY, draw_card, draw_field, draw_primary_button,
                     draw_primary_disabled_button, draw_rounded_rect, draw_secondary_button, draw_strip, scale_for,
                     FIELD_BORDER, STRIP_FILL)

WINDOW_NAME = "SignLanguage - Camara"
NAME_PLACEHOLDER = "Nombre de la expresión"
NAME_LABEL = "Nombre de la expresión"
NAME_HINT = "Puedes usar ñ y acentos."

WINDOW_SCALE_WIDTH = 0.9
WINDOW_SCALE_HEIGHT = 0.85


def open_camera(index=0):
    """Open the webcam at its widest view: zoom at minimum (ignored when the camera has no zoom)."""
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_ZOOM, 0)
        cap.set(cv2.CAP_PROP_ZOOM, 100)
    return cap


def get_screen_size():
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1280, 720


def setup_window(aspect_ratio):
    """Resizable window sized to most of the screen, preserving the video aspect ratio, and centered."""
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    screen_w, screen_h = get_screen_size()
    scale = min(screen_w * WINDOW_SCALE_WIDTH / aspect_ratio, screen_h * WINDOW_SCALE_HEIGHT)
    width, height = int(aspect_ratio * scale), int(scale)
    cv2.resizeWindow(WINDOW_NAME, width, height)
    cv2.moveWindow(WINDOW_NAME, (screen_w - width) // 2, (screen_h - height) // 2)
    return width, height


def window_closed():
    try:
        return cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True


def get_window_size(default):
    """Current window client size, or `default` when it cannot be read."""
    x, y, w, h = cv2.getWindowImageRect(WINDOW_NAME)
    return (w, h) if w > 0 and h > 0 else default


def draw_frame(frame, detector):
    frame = cv2.flip(frame, 1)
    if detector is not None:
        if detector.process(frame) == 0:
            draw_text(frame, NO_HAND_TEXT, (10, 60), (0, 0, 255))
        else:
            frame = detector.draw(frame)
    return frame


def _label(frame, text, rect, color, scale, bold=True, size=BUTTON_TEXT_SIZE):
    draw_text(frame, text, ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2), color[::-1],
              size=max(1, round(size * scale)), anchor="mm", bold=bold)


def draw_menu(frame):
    """Draw the mode buttons side by side on a bottom strip, leaving the center of the video free."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    draw_strip(frame)
    layout = menu_layout(width, height)
    for key, label in zip(MODE_KEYS, MODE_BUTTONS):
        rect = layout[key]
        draw_primary_button(frame, rect[:2], rect[2:], scale)
        _label(frame, label, rect, PRIMARY_TEXT, scale)
    return frame


def draw_name_input(frame, ui):
    """Card with the chosen mode, the name field and the Volver and Aceptar buttons."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    layout = name_layout(width, height)
    draw_card(frame, layout["card"][:2], layout["card"][2:], scale)
    draw_text(frame, ui.title, layout["title"], TEXT[::-1], size=round(22 * scale), anchor="lm", bold=True)
    draw_text(frame, NAME_LABEL, layout["label"], TEXT_SECONDARY[::-1], size=round(13 * scale), anchor="lm")
    field = layout["field"]
    draw_field(frame, field[:2], field[2:], scale, focused=bool(ui.name))
    text_origin = (field[0] + round(14 * scale), (field[1] + field[3]) // 2)
    text_size = round(18 * scale)
    if ui.name:
        draw_text(frame, ui.name, text_origin, TEXT[::-1], size=text_size, anchor="lm")
        cursor_x = text_origin[0] + text_width(ui.name, text_size) + round(2 * scale)
        cv2.line(frame, (cursor_x, field[1] + round(10 * scale)), (cursor_x, field[3] - round(10 * scale)),
                 TEXT[::-1], max(1, round(scale)))
    else:
        draw_text(frame, NAME_PLACEHOLDER, text_origin, TEXT_SECONDARY[::-1], size=text_size, anchor="lm")
    draw_text(frame, NAME_HINT, layout["hint"], TEXT_SECONDARY[::-1], size=round(13 * scale), anchor="lm")
    draw_secondary_button(frame, layout["back"][:2], layout["back"][2:], scale)
    _label(frame, "Volver", layout["back"], TEXT, scale)
    accept = layout["accept"]
    if ui.name.strip():
        draw_primary_button(frame, accept[:2], accept[2:], scale)
        _label(frame, "Aceptar", accept, PRIMARY_TEXT, scale)
    else:
        draw_primary_disabled_button(frame, accept[:2], accept[2:], scale)
        _label(frame, "Aceptar", accept, TEXT_SECONDARY, scale)
    return frame


def draw_chip(frame, ui, layout, scale):
    """Chip with the open expression, its mode and sample count, and the last result message below it."""
    chip = layout["chip"]
    draw_rounded_rect(frame, chip[:2], chip[2:], STRIP_FILL, FIELD_BORDER, round(10 * scale))
    draw_text(frame, ui.chip_text, (chip[0] + round(12 * scale), (chip[1] + chip[3]) // 2), TEXT[::-1],
              size=round(16 * scale), anchor="lm", bold=True)
    if ui.message:
        message = layout["message"]
        draw_rounded_rect(frame, message[:2], message[2:], STRIP_FILL, None, round(10 * scale))
        draw_text(frame, ui.message, (message[0] + round(12 * scale), (message[1] + message[3]) // 2),
                  TEXT[::-1], size=round(16 * scale), anchor="lm")


def draw_expression(frame, ui):
    """The open expression with its Volver button and, in static mode, Capturar."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    layout = expression_layout(width, height)
    draw_chip(frame, ui, layout, scale)
    draw_strip(frame)
    back = layout["back"]
    draw_secondary_button(frame, back[:2], back[2:], scale)
    _label(frame, "Volver", back, TEXT, scale)
    capture = layout["capture"]
    draw_primary_button(frame, capture[:2], capture[2:], scale)
    _label(frame, "Capturar" if ui.mode == "static" else "Grabar", capture, PRIMARY_TEXT, scale)
    return frame


def draw_countdown(frame, ui):
    """Big number counting down to the start of the recording, so the hands can get in place."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    if ui.expression:
        draw_chip(frame, ui, expression_layout(width, height), scale)
    draw_text(frame, "Prepárate...", (width // 2, height // 2 - round(60 * scale)), TEXT[::-1],
              size=round(28 * scale), anchor="mm", bold=True)
    draw_text(frame, str(ui.countdown_left), (width // 2, height // 2 + round(10 * scale)), TEXT[::-1],
              size=round(96 * scale), anchor="mm", bold=True)
    return frame


def draw_recording(frame, ui):
    """The elapsed recording time and the Detener button."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    layout = expression_layout(width, height)
    if ui.expression:
        draw_chip(frame, ui, layout, scale)
    message = layout["message"]
    draw_rounded_rect(frame, message[:2], message[2:], STRIP_FILL, None, round(10 * scale))
    draw_text(frame, f"Grabando... {ui.elapsed:.1f} s", (message[0] + round(12 * scale), (message[1] + message[3]) // 2),
              TEXT[::-1], size=round(16 * scale), anchor="lm", bold=True)
    draw_strip(frame)
    stop = layout["stop"]
    draw_primary_button(frame, stop[:2], stop[2:], scale)
    _label(frame, "Detener", stop, PRIMARY_TEXT, scale)
    return frame


def draw_review(frame, ui):
    """The frozen capture with only Aprobar and No aprobar."""
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    draw_chip(frame, ui, expression_layout(width, height), scale)
    draw_strip(frame)
    layout = review_layout(width, height)
    discard, approve = layout["discard"], layout["approve"]
    draw_secondary_button(frame, discard[:2], discard[2:], scale)
    _label(frame, "No aprobar", discard, TEXT, scale)
    draw_primary_button(frame, approve[:2], approve[2:], scale)
    _label(frame, "Aprobar", approve, PRIMARY_TEXT, scale)
    return frame


def draw_recognize_screen(frame, ui):
    """Recognition window: the last result, if any, and the Grabar button; the recording screens are shared."""
    if ui.screen == "countdown":
        return draw_countdown(frame, ui)
    if ui.screen == "recording":
        return draw_recording(frame, ui)
    height, width = frame.shape[:2]
    scale = scale_for(frame)
    layout = expression_layout(width, height)
    if ui.result:
        message = layout["message"]
        draw_rounded_rect(frame, message[:2], message[2:], STRIP_FILL, None, round(10 * scale))
        draw_text(frame, ui.result, (message[0] + round(12 * scale), (message[1] + message[3]) // 2),
                  TEXT[::-1], size=round(18 * scale), anchor="lm", bold=True)
    draw_strip(frame)
    button = layout["stop"]
    draw_primary_button(frame, button[:2], button[2:], scale)
    _label(frame, "Grabar", button, PRIMARY_TEXT, scale)
    return frame


def draw_capture_screen(frame, ui):
    if ui.screen == "name":
        return draw_name_input(frame, ui)
    if ui.screen == "expression":
        return draw_expression(frame, ui)
    if ui.screen == "countdown":
        return draw_countdown(frame, ui)
    if ui.screen == "recording":
        return draw_recording(frame, ui)
    if ui.screen == "review":
        return draw_review(frame, ui)
    return draw_menu(frame)


def window_to_frame(x, y, frame_size, window_size):
    """Translate a click in the window to video-frame pixels (the video is scaled and centered on black bars)."""
    frame_w, frame_h = frame_size
    window_w, window_h = window_size
    scale = min(window_w / frame_w, window_h / frame_h)
    return (x - (window_w - frame_w * scale) / 2) / scale, (y - (window_h - frame_h * scale) / 2) / scale


def render_frame(frame, window_w, window_h):
    """Scale the video to fit the window keeping its aspect ratio, centered on black bars."""
    height, width = frame.shape[:2]
    scale = min(window_w / width, window_h / height)
    video_w, video_h = int(width * scale), int(height * scale)
    canvas = np.zeros((window_h, window_w, 3), np.uint8)
    canvas[(window_h - video_h) // 2:(window_h + video_h) // 2,
           (window_w - video_w) // 2:(window_w + video_w) // 2] = cv2.resize(frame, (video_w, video_h))
    return canvas


def run_camera(cap, detector=None, repository=None, predict=None, clock=time.monotonic, recognize=None,
               overlay=None):
    """`overlay(frame, detector, now)`, when given, draws on every frame after the hands and texts."""
    try:
        window_size = None
        ui = CaptureUI(repository) if repository is not None else RecognizeUI(recognize) if recognize else None
        clicks = []
        while True:
            ret, frame = cap.read()
            if not ret or (window_size is not None and window_closed()):
                break
            if window_size is None:
                height, width = frame.shape[:2]
                window_size = setup_window(width / height)
                if ui is not None:
                    cv2.setMouseCallback(WINDOW_NAME, lambda event, x, y, flags, param: (
                        clicks.append((x, y)) if event == cv2.EVENT_LBUTTONDOWN else None))
            frame = draw_frame(frame, detector)
            if ui is not None:
                ui.now = clock()
                ui.live_hands = list(zip(detector.handedness(), detector.landmarks())) if detector else []
                current_size = get_window_size(window_size)
                frame_size = (frame.shape[1], frame.shape[0])
                while clicks:
                    x, y = window_to_frame(*clicks.pop(0), frame_size, current_size)
                    ui.click(x, y, *frame_size)
                ui.update()
                if ui.screen == "recording":
                    ui.record(frame.copy())
                if ui.screen == "review" and ui.mode == "static" and ui.frozen is None:
                    ui.frozen = frame.copy()
                if ui.screen == "review":
                    frame = ui.review_image().copy()
            recording_motion = isinstance(ui, RecognizeUI) and ui.screen in ("countdown", "recording")
            if predict is not None and detector is not None and not recording_motion:  # vowels would distract from the gesture
                text = predict(detector)
                if text:
                    draw_text(frame, text, (10, 120))
            if ui is not None:
                (draw_recognize_screen if isinstance(ui, RecognizeUI) else draw_capture_screen)(frame, ui)
            if overlay is not None:
                overlay(frame, detector, clock())
            cv2.imshow(WINDOW_NAME, render_frame(frame, *get_window_size(window_size)))
            key = cv2.waitKey(1)
            if ui is not None:
                ui.key(key)
    except KeyboardInterrupt:
        # Ctrl+C can land in the middle of a MediaPipe call; closing the landmarker then blocks
        # forever waiting on that call. Skip close and let process exit release the native resources.
        detector = None
    finally:
        if detector is not None:
            detector.close()
        cap.release()
        cv2.destroyAllWindows()
