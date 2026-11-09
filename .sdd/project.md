# Project: SignLanguage
Sources read: README.md, requirements.txt
Last scan: 2026-11-08

## Stack
- Python 3 (← README.md)
- opencv-python >= 4.8.0 for camera capture and UI overlay (← requirements.txt)
- mediapipe >= 0.10.0 for 21-point hand landmark detection (← requirements.txt)
- numpy >= 1.24.0, pandas >= 2.0.0 for landmark normalization and CSV dataset storage (← requirements.txt)
- scikit-learn >= 1.3.0 for vowel classification model training and inference (← requirements.txt)

## Architecture
- Pattern: Progressive modular Python scripts (← README.md)
- Layers:
  - `src/` → Application entrypoints, camera handling, landmark extraction, and ML pipeline (← README.md)
  - `data/` → Collected CSV datasets and serialized `.pkl` models (← README.md)
  - `tests/` → Automated unit tests (← README.md)
- Dependency rules: `src/main.py` orchestrates camera and modules inside `src/` (← README.md)

## Conventions
- Snake_case for Python modules, functions, and variables (← README.md)
- Exit camera loops cleanly with `q` key and release OpenCV resources (← README.md)

## Frontend
- N/A (Local desktop window via OpenCV `imshow`) (← README.md)

## Tests
- Frameworks: `pytest >= 7.4.0` (← requirements.txt)
- Location and naming: `tests/test_*.py` (← README.md)
- Command: `pytest` (← README.md)

## Run the app
- `python src/main.py` → Opens local OpenCV camera window (← README.md)

## Not detected / questions
- Exact Python version installed in your local environment (e.g., 3.10, 3.11, 3.12).
- Default camera index (`0` assumed for built-in/primary webcam).
