import cv2

from hands import NO_HAND_TEXT

WINDOW_NAME = "SignLanguage - Camara"
OVERLAY_TEXT = "Hola Mundo - Presiona 'q' para salir"


def draw_frame(frame, detector):
    frame = cv2.flip(frame, 1)
    cv2.putText(frame, OVERLAY_TEXT, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    if detector is not None:
        if detector.process(frame) == 0:
            cv2.putText(frame, NO_HAND_TEXT, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            frame = detector.draw(frame)
    return frame


def run_camera(cap, detector=None):
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = draw_frame(frame, detector)
            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
