import cv2

WINDOW_NAME = "SignLanguage - Camara"
OVERLAY_TEXT = "Hola Mundo - Presiona 'q' para salir"


def run_camera(cap):
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            cv2.putText(frame, OVERLAY_TEXT, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
