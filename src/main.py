import sys

import cv2

from camera import run_camera
from hands import HandDetector


class ConsoleSampleRepository:
    """Temporary until the Postgres repository (spec 003, phase 3)."""

    def save_sample(self, label, points):
        print(f"Muestra {label.upper()}:")
        for index, (x, y, z) in enumerate(points):
            print(f"  {index:2d}: x={x:.4f} y={y:.4f} z={z:.4f}")


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
        run_camera(cap, detector, ConsoleSampleRepository())
    finally:
        cap.release()


if __name__ == "__main__":
    main()
