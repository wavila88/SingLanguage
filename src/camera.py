import time

import cv2
import numpy as np

from dataset import VOWELS, normalize_landmarks
from hands import NO_HAND_TEXT

WINDOW_NAME = "SignLanguage - Camara"
MESSAGE_SECONDS = 2

WINDOW_SCALE_WIDTH = 0.9
WINDOW_SCALE_HEIGHT = 0.85


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
            cv2.putText(frame, NO_HAND_TEXT, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            frame = detector.draw(frame)
    return frame


def render_frame(frame, window_w, window_h):
    """Scale the video to fit the window keeping its aspect ratio, centered on black bars."""
    height, width = frame.shape[:2]
    scale = min(window_w / width, window_h / height)
    video_w, video_h = int(width * scale), int(height * scale)
    canvas = np.zeros((window_h, window_w, 3), np.uint8)
    canvas[(window_h - video_h) // 2:(window_h + video_h) // 2,
           (window_w - video_w) // 2:(window_w + video_w) // 2] = cv2.resize(frame, (video_w, video_h))
    return canvas


def run_camera(cap, detector=None, repository=None, predict=None):
    try:
        window_size = None
        message = ""
        message_at = 0.0
        while True:
            ret, frame = cap.read()
            if not ret or (window_size is not None and window_closed()):
                break
            if window_size is None:
                height, width = frame.shape[:2]
                window_size = setup_window(width / height)
            frame = draw_frame(frame, detector)
            if predict is not None and detector is not None:
                text = predict(detector)
                if text:
                    cv2.putText(frame, text, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            if message and time.monotonic() - message_at > MESSAGE_SECONDS:
                message = ""
            if message:
                cv2.putText(frame, message, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow(WINDOW_NAME, render_frame(frame, *get_window_size(window_size)))
            key = chr(cv2.waitKey(1) & 0xFF)
            if key == "q":
                break
            if repository is not None and key in VOWELS and detector is not None:
                hands = detector.landmarks()
                if len(hands) == 1:
                    repository.save_sample(key, normalize_landmarks(hands[0]))
                    message = f"Guardada muestra: {key.upper()}"
                    message_at = time.monotonic()
                else:
                    print(f"No se guardó {key.upper()}: se detectaron {len(hands)} manos, se requiere 1")
    except KeyboardInterrupt:
        # Ctrl+C can land in the middle of a MediaPipe call; closing the landmarker then blocks
        # forever waiting on that call. Skip close and let process exit release the native resources.
        detector = None
    finally:
        if detector is not None:
            detector.close()
        cap.release()
        cv2.destroyAllWindows()
