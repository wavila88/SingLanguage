# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Run everything from the repo root, with the venv active. Dependencies: `pip install -r requirements.txt`.

- Run the sample-collection window (spec 003/004 data capture): `python src/capture/capture_words.py` (needs `DATABASE_URL`)
- Run the live vowel recognition window (spec 005): `python src/recognize_message.py` (needs `data/language_sing_model.pkl`)
- Train the model from the stored samples: `python src/train/train.py` (needs `DATABASE_URL`)
- All tests: `pytest` (or `python -m pytest -q`)
- One test file: `pytest tests/test_camera.py`
- One test: `pytest tests/test_camera.py::test_run_camera_mirrors_and_exits_on_q`

`README.md` still says `python src/main.py`, but that file was renamed to `src/capture/capture_words.py` (uncommitted in the working tree). Use the new path.

Tests do not open a real camera window: `test_camera.py` and `test_recognize_message.py` monkeypatch `cv2` and use a fake capture. `test_dataset.py` skips when `DATABASE_URL` is unset; `test_train.py` uses fake repositories and sets `DATABASE_URL` per test.

## Architecture

The app is a set of small flat-import Python modules plus three entrypoints. There is no package install; imports rely on path setup.

**Import paths.** `pytest.ini` sets `pythonpath = . src`, so tests can do `from camera import ...` or `from src import camera` (both styles appear; they load the same file under different module names). `src/capture/capture_words.py` and `src/train/train.py` insert `src/` into `sys.path` themselves before importing siblings. `src/recognize_message.py` relies on Python putting its own directory (`src/`) on `sys.path` when run as a script. Keep new entrypoints consistent with one of these patterns.

**Shared loop.** `src/camera.py::run_camera(cap, detector, repository, predict)` is the single camera/OpenCV loop used by both windows. It mirrors each frame, runs `HandDetector` (MediaPipe, `src/hands.py`), optionally overlays `predict(detector)` text, and handles the `q` key and cleanup in a `finally`. A vowel key press saves a sample only when `repository` is given and exactly one hand is visible.
- `capture_words.py` injects a `PostgresSampleRepository` (collection mode).
- `recognize_message.py` injects a `predict` callback (inference mode) and passes no repository, so it cannot save samples.

**Data flow for the ML pipeline.**
1. Capture: landmarks from `HandDetector.landmarks()` → `dataset.normalize_landmarks` (wrist-relative, divided by wrist→middle-MCP distance, giving 63 floats) → `samples` table as JSONB.
2. Train: `train/train.py::train_model` loads all samples, holds out the first `a` sample as a sanity check, fits a `RandomForestClassifier`, and pickles it to `data/language_sing_model.pkl`.
3. Infer: `recognize_message.describe_hand` applies the same `normalize_landmarks` and feature flattening, then `predict_proba` gives `"A 87%"`-style text. Any change to normalization or feature order must be made in `dataset.py` and kept in sync between training and inference.

**Persistence.** `src/dbConf/database.py` is the only module that reads `DATABASE_URL` (loaded from `.env` via python-dotenv) and owns the Postgres (Neon) connection. `schema.sql` creates `epression` (one row per vowel a/e/i/o/u) and `samples` (FK to `epression`, cascade delete). Camera and capture modules must not import the Postgres driver; `main`-level code injects the repository, as `capture_words.py` does.

**Dependency direction.** Entrypoints (`capture_words.py`, `recognize_message.py`, `train.py`) compose `camera`, `hands`, `dataset` and `dbConf`. `camera.py` depends on `hands.py` and `dataset.py` only. `dataset.py` has no third-party imports.

**Specs.** `.sdd/specs/<NNN-name>/` holds `spec.md` (happy/sad paths, HP-n/SP-n) and `tasks.md` (phased TDD checklist, each phase with a test and a manual check). `.sdd/project.md` is the project standards file. Commits follow the `NNN-name fase N: ...` pattern.

## Gotchas

- Model and sample data: `data/*.pkl` is gitignored and `.env` must never be committed. `data/hand_landmarker.task` is the MediaPipe model and is tracked.
- Windows-specific: `camera.get_screen_size` uses `ctypes.windll`, with a 1280x720 fallback. `cv2.waitKey` and `getWindowProperty` drive the loop, so tests monkeypatch `cv2` functions rather than opening windows.
- Camera index `0` is hard-coded in both entrypoints.
- Do not call `HandDetector.close()` after a Ctrl+C during detection: MediaPipe's close blocks on the interrupted call. `run_camera` skips it on `KeyboardInterrupt`.
- User-facing messages (window text, stderr errors) are in Spanish; keep new messages consistent.
