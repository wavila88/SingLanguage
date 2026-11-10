# Tasks: Model Training
Spec: ./spec.md
Test command: `pytest`

## Phase 1 — Send the stored samples to training and write the model (covers HP-1, HP-2, HP-3)
Test: `tests/test_train.py` asserts that the stored samples are sent to training, `vowel_model.pkl` is written, a second run replaces that same file, the held-out "a" check is reported, and neither the camera nor a database driver is opened.
Manual check: Run `python src/train/train.py`, then run it again, and confirm the same `data/vowel_model.pkl` is replaced and the output says whether "a" was recognized.

- [x] 1.1 Failing test — result: `FAILED: ModuleNotFoundError: No module named 'train'` (tests/test_train.py)
- [x] 1.2 Implementation — files: `src/train/train.py` (new: `train_model`, `main`), `src/dbConf/database.py` (added `PostgresSampleRepository.load_samples`)
- [x] 1.3 Passing test — result: `python -m pytest -q` → 13 passed
- [x] 1.4 Developer approval

## Phase 2 — Report an error when the samples cannot be loaded (covers SP-1)
Test: `tests/test_train.py` asserts that a missing `DATABASE_URL`, an unreachable database, or no samples prints an error to stderr, exits with code 1, and leaves the current model file unchanged.
Manual check: Unset `DATABASE_URL`, run `python src/train/train.py`, and confirm the stderr error, exit code 1, and that `data/vowel_model.pkl` is unchanged.

- [x] 2.1 Failing test — result: `FAILED: KeyError: 'DATABASE_URL'`, `FAILED: OperationalError: no se pudo conectar`, `FAILED: StopIteration` (tests/test_train.py, 3 tests)
- [x] 2.2 Implementation — files: `src/train/train.py` (`main` checks `DATABASE_URL`, catches errors → stderr + `sys.exit(1)`; `train_model` raises `ValueError` when there are no samples; added `import os`, `import sys`)
- [x] 2.3 Passing test — result: `python -m pytest -q` → 16 passed
- [x] 2.4 Developer approval
