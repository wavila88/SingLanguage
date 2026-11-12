import sys
from pathlib import Path

import cv2

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from camera import open_camera, run_camera
from dbConf.database import PostgresSampleRepository, connect_from_env, create_sample_tables
from hands import HandDetector


def main():
    cap = open_camera()
    try:
        if not cap.isOpened():
            print("Error: no se pudo abrir la cámara. Revisa que esté conectada y que no la use otra app.", file=sys.stderr)
            sys.exit(1)
        try:
            detector = HandDetector(max_num_hands=2)
        except Exception as error:
            print(f"Error: no se pudo iniciar el detector de manos: {error}", file=sys.stderr)
            sys.exit(1)
        conn = connect_from_env()
        try:
            create_sample_tables(conn)
            run_camera(cap, detector, PostgresSampleRepository(conn))
        finally:
            conn.close()
    finally:
        cap.release()


if __name__ == "__main__":
    main()
