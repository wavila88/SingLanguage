# Hand Landmarks
Size: complex — Adds MediaPipe hand detection, a new `src/hands.py` module, and drawing of up to two hands on the existing camera loop.

## Goal
The developer sees up to two hands detected in the live camera window, with the 21 landmarks and finger connections drawn, so the next spec can record those coordinates as a dataset.

## Happy path
- HP-1: Given the camera window is open and one hand is visible, when a frame is processed, then the 21 landmarks and the finger connections are drawn on that hand.
- HP-2: Given two hands are visible, when a frame is processed, then both hands are drawn the same way.
- HP-3: Given no hand is visible, when a frame is processed, then the video keeps running and the window shows "Mano no detectada".

## Sad paths
- SP-1: Given MediaPipe fails to initialize, when the user runs `python src/main.py`, then an error is printed to stderr and the program exits with code 1, releasing the camera.
- SP-2: Given the camera loop is running, when the user presses `q`, then the hand detector and the camera are both released and the window closes.

## Out of scope
- Recording landmark coordinates to CSV (covered in `003-dataset-collector`).
- Normalizing coordinates or classifying vowels (covered in `004` and `005`).

## Touches
- `src/` — new `src/hands.py` for MediaPipe hand detection and drawing; `src/camera.py` calls it per frame; `src/main.py` wires it in.

## Decisions and open questions
- Draw landmarks plus finger connections, not landmark index numbers.
- Detect up to two hands; draw whichever MediaPipe returns.
- When no hand is found, show the overlay text "Mano no detectada".
- Hand detector lives in `src/hands.py` and is injected into `run_camera`, so tests can fake it.
