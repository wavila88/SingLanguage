# Tasks: Hand Landmarks
Spec: ./spec.md
Test command: `python -m pytest`

## Phase 1 — Draw one or two hands, or show "Mano no detectada" (covers HP-1, HP-2, HP-3)
Test: `tests/test_hands.py` asserts that one detected hand draws 21 landmarks and connections, two hands draw both, and no hand draws the "Mano no detectada" overlay instead.
Manual check: Run `python src/main.py`, show one hand, then both, then none, and confirm the skeleton and the "Mano no detectada" text.

- [x] 1.1 Failing test — result: FAILED: ImportError: cannot import name 'hands' from 'src' (src/hands.py not written yet)
- [x] 1.2 Implementation — files: `src/hands.py` (new HandDetector), `src/camera.py` (draw_frame + optional detector), `src/main.py` (wires HandDetector)
- [x] 1.3 Passing test — result: 5 passed (`python -m pytest tests/test_hands.py tests/test_camera.py -q`); test_hands no-hand assertion corrected (it wrongly demanded the warning be the only text)
- [x] 1.4 Developer approval

## Phase 2 — Exit cleanly when MediaPipe fails or the user presses q (covers SP-1, SP-2)
Test: `tests/test_hands.py` asserts that a MediaPipe init failure prints an error and exits with code 1, and that pressing `q` releases both the hand detector and the camera.
Manual check: Run `python src/main.py`, press `q`, and confirm the camera light turns off and no process stays open.

- [x] 2.1 Failing test — result: 2 failed: `test_q_releases_both_detector_and_camera` (AssertionError: assert False is True — detector never closed) and `test_detector_init_failure_prints_error_exits_1_and_releases_camera` (RuntimeError propagates from main.main instead of a controlled exit code 1)
- [x] 2.2 Implementation — files: `src/camera.py` (run_camera closes the detector in `finally` alongside the camera), `src/main.py` (try/except around HandDetector init → error to stderr + exit 1, camera released in `finally`; removed the now-redundant `detector.close()` since run_camera owns it)
- [x] 2.3 Passing test — result: 7 passed (`python -m pytest -q`); note: the Phase 1 FakeDetector helper gained a `close()` method so it matches the detector interface — no test assertions changed
- [x] 2.4 Developer approval
