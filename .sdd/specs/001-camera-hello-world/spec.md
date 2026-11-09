# Camera Hello World
Size: simple — Single user goal (open webcam in mirror mode, render overlay text, and close cleanly) across one module with no AI or external data dependencies yet.

## Goal
Allow the developer to open their local webcam in real time with a mirrored view and on-screen status overlay, verifying that OpenCV can capture and render video frames cleanly.

## Happy path
- HP-1: Given an available webcam at the default camera index, when the user runs `python src/main.py`, then an OpenCV window opens showing the live horizontally-flipped (mirror) video feed with a `"Hola Mundo - Presiona 'q' para salir"` overlay.
- HP-2: Given the live camera window is open, when the user presses the `q` key, then the camera device is released and all OpenCV windows close cleanly with exit code 0.

## Sad paths
- SP-1: Given no webcam is connected or the camera is locked by another application, when the user runs `python src/main.py`, then the program logs a clear error message indicating the camera could not be opened and exits gracefully without crashing.
- SP-2: Given an active webcam stream, when a frame fails to be read mid-stream, then the loop terminates safely, releases the camera resource, and closes the window.

## Out of scope
- Hand detection or MediaPipe landmarks (covered in `002-hand-landmarks`).
- Recording images or CSV data (covered in `003-dataset-collector`).
- Vowel classification or AI inference (covered in `004` and `005`).

## Decisions and open questions
- Default camera index is set to `0` (primary system webcam).
- Video frames are flipped horizontally (`cv2.flip(frame, 1)`) by default so moving the hand right moves it right on screen (mirror mode).
- Window title defaults to `"SignLanguage - Camara"`.
