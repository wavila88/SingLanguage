import cv2
import numpy as np

from hands import NO_HAND_TEXT

WINDOW_NAME = "SignLanguage - Camara"
OVERLAY_TEXT = "Hola Mundo - Presiona 'q' para salir"

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


def get_window_size(default):
    """Current window client size, or `default` when it cannot be read."""
    x, y, w, h = cv2.getWindowImageRect(WINDOW_NAME)
    return (w, h) if w > 0 and h > 0 else default


def draw_frame(frame, detector):
    frame = cv2.flip(frame, 1)
    cv2.putText(frame, OVERLAY_TEXT, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
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


def run_camera(cap, detector=None):
    try:
        window_size = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if window_size is None:
                height, width = frame.shape[:2]
                window_size = setup_window(width / height)
            frame = draw_frame(frame, detector)
            cv2.imshow(WINDOW_NAME, render_frame(frame, *get_window_size(window_size)))
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        if detector is not None:
            detector.close()
        cap.release()
        cv2.destroyAllWindows()
