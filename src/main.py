import sys

import cv2

from camera import run_camera
from hands import HandDetector


def main():
    cap = cv2.VideoCapture(0)
    try:
        if not cap.isOpened():
            print("Error: no se pudo abrir la cámara. Revisa que esté conectada y que no la use otra app.", file=sys.stderr)
            sys.exit(1)
        try:
            detector = HandDetector(max_num_hands=2)
        except Exception as error:
            print(f"Error: no se pudo iniciar el detector de manos: {error}", file=sys.stderr)
            sys.exit(1)
        run_camera(cap, detector)
    finally:
        cap.release()


if __name__ == "__main__":
    main()
