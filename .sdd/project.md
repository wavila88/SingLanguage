# Project: SignLanguage
Sources read: README.md, requirements.txt, src/database.py, src/schema.sql, .sdd/specs/003-dataset-collector/spec.md
Last scan: 2026-11-08
Updated: 2026-11-09 after spec 003 phase 1

## Stack
- Python 3 (← README.md)
- opencv-python >= 4.8.0 for camera capture and UI overlay (← requirements.txt)
- mediapipe >= 0.10.0 for 21-point hand landmark detection (← requirements.txt)
- numpy >= 1.24.0, pandas >= 2.0.0 for landmark normalization and later training export (← requirements.txt)
- scikit-learn >= 1.3.0 for vowel classification model training and inference (← requirements.txt)
- psycopg[binary] >= 3.2.0 for the Neon Postgres connection (← requirements.txt)

## Architecture
- Pattern: Progressive modular Python scripts (← README.md)
- Layers:
  - `src/` → Application entrypoints, camera handling, landmark extraction, and ML pipeline (← README.md)
  - `src/database.py` + `src/schema.sql` → Neon connection and dataset tables (← spec 003)
  - `data/` → MediaPipe model file and serialized `.pkl` models. Collected samples are not stored here (← spec 003)
  - `tests/` → Automated unit tests (← README.md)
- Dataset tables: `epression` (id, label) is the parent with one row per vowel. `samples` (id, epression_id, points JSONB, created_at) is the child with one row per capture; `points` holds the 21 normalized points (63 numbers). `samples.epression_id` references `epression.id` and deleting an epression row deletes its samples. No photos are stored (← spec 003)
- Dependency rules: `src/main.py` orchestrates camera and modules inside `src/` (← README.md). Camera and capture code must not import the Postgres driver. `main.py` injects the repository, the same way it injects `HandDetector` (← spec 003). `src/database.py` is the only module that reads `DATABASE_URL` (← src/database.py)

## Conventions
- Snake_case for Python modules, functions, and variables (← README.md)
- Exit camera loops cleanly with `q` key and release OpenCV resources (← README.md)
- `DATABASE_URL` comes from the environment or `.env`. Never hardcode it and never commit `.env` (← spec 003)

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
