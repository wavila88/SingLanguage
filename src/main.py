import cv2

from camera import run_camera


def main():
    cap = cv2.VideoCapture(0)
    run_camera(cap)


if __name__ == "__main__":
    main()
