# Tasks: Realtime Vowel Detection
Spec: ./spec.md
Test command: `pytest`

## Phase 1 — Show the recognized vowel and its confidence for one hand (covers HP-1, HP-2, SP-5)
Test: `tests/test_recognize_message.py` asserts that with one hand and a fake model, the window text shows the predicted vowel and its whole-number percentage, and that `q` releases the camera and the detector.
Manual check: Run `python src/recognize_message.py`, show one hand, and confirm a vowel and a percentage appear; press `q` and confirm the window closes.

- [x] 1.1 Failing test — result: `FAILED: ModuleNotFoundError: No module named 'recognize_message'` (tests/test_recognize_message.py)
- [x] 1.2 Implementation — files: `src/recognize_message.py` (new: `describe_hand`, `run_recognition`, `main`), `src/camera.py` (`run_camera` acepta `predict` opcional y dibuja su texto)
- [x] 1.3 Passing test — result: `python -m pytest -q` → 18 passed
- [x] 1.4 Developer approval

## Phase 2 — Keep the sample-collection window working under its new name (covers HP-3)
Test: `tests/test_capture_words.py` asserts that the module at `src/capture/capture_words.py` injects the repository into the camera loop, and that pressing a vowel key with one hand saves a sample and shows its confirmation message.
Manual check: Run `python src/capture/capture_words.py`, press `a` with one hand visible, and confirm "Guardada muestra: A" appears.


- [x] 2.2 Implementation — files: `src/main.py` → `src/capture/capture_words.py` (moved with `git mv`; adds `src` to `sys.path`), `tests/test_camera.py` and `tests/test_hands.py` (import of `main` now from `capture.capture_words`)
- [x] 2.4 Developer approval
