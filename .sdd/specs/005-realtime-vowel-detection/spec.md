# Realtime Vowel Detection
Size: complex — a new entrypoint, a trained model loaded at runtime, and camera, MediaPipe and scikit-learn working together.

## Goal
The developer opens a second camera window that shows, live, the vowel the trained model recognizes from the hand and its confidence percentage. The existing sample-collection window keeps working, under a more descriptive name.

## Happy path
- HP-1: Given `data/language_sing_model.pkl` exists and the camera is connected, when the developer runs `python src/recognize_message.py`, then a window opens showing the video with the detected vowel and its confidence percentage for the hand in view.
- HP-2: Given exactly one hand is visible, when the model classifies its 21 landmarks, then the window shows the predicted vowel (a, e, i, o or u) and the percentage of confidence for that prediction.
- HP-3: Given the developer runs `python src/capture/capture_words.py`, then the sample-collection window behaves as before (`src/main.py` today), with no change in its keys or messages.

## Sad paths
- SP-1: Given `data/language_sing_model.pkl` does not exist, when the developer runs `python src/recognize_message.py`, then an error is printed to stderr and the program exits with code 1 before the camera opens.
- SP-2: Given the camera cannot be opened, when the developer runs `python src/recognize_message.py`, then an error is printed to stderr and the program exits with code 1.
- SP-3: Given no hand is visible, when the frame is processed, then the window shows "Mano no detectada" and no vowel or percentage.
- SP-4: Given two or more hands are visible, when the frame is processed, then the window shows a message asking for one hand and no vowel or percentage.
- SP-5: Given the developer presses `q`, when the window is open, then the camera and the window are released and the program ends.

## Out of scope
- Training or retraining the model (covered in spec 004).
- Saving samples from the recognition window.
- Recognizing words, phrases or sequences.
- Smoothing predictions over several frames.

## Touches
- `src/main.py` → moves to `src/capture/capture_words.py`. Its behavior stays the same. It lives in its own `src/capture/` folder, so it must add `src` to `sys.path` the same way `src/train/train.py` does, to import `camera`, `dbConf` and `hands`.
- `src/recognize_message.py` — new recognition entrypoint, in `src/` next to the camera and hands modules. It loads the model and injects the trained model and the detector into the shared camera loop, the same way `main.py` injects the repository.
- `src/camera.py` — shared window and frame drawing code. The recognition window reuses it for display; the sample-saving key handling stays in the capture flow.
- `src/hands.py` — `HandDetector` provides the landmarks; no change expected.
- `src/dataset.py` — `normalize_landmarks` turns the landmarks into the 63 features the model was trained on.
- `src/train/train.py` — the model file written by spec 004 is the input here; no change expected.
- `tests/` — tests use a fake camera, a fake detector and a fake model.
- `README.md` and `.sdd/project.md` — the run commands and the entrypoint names change (`python src/main.py` becomes `python src/capture/capture_words.py`, and the recognition command is added).

## Decisions and open questions
- Model path: `data/language_sing_model.pkl`, as chosen by the developer. Spec 004 still says `data/vowel_model.pkl`; that spec needs to be updated to match.
- Rename: `src/main.py` moves to `src/capture/capture_words.py`, as chosen by the developer. This keeps `src/train/` for training code only, as spec 004 requires.
- The name `capture_words.py` does not match what it does today: it captures vowel samples, and words are out of scope here. Kept on purpose: the developer plans to use it for word capture in the future.
- New entrypoint: `src/recognize_message.py`, chosen by the developer. It sits in `src/`, so it needs no `sys.path` change.
- Confidence: the highest probability from the model, shown as a whole-number percentage.
- Features are the same 63 normalized numbers used in training. Landmarks are normalized with `normalize_landmarks`, not raw.
- Pressing `q` closes the window, as in the collection window.
