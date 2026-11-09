# Tasks: Camera Hello World
Spec: ./spec.md
Test command: `pytest`

## Phase 1 — Live mirrored camera feed and clean exit on 'q' (covers HP-1, HP-2)
Test: `tests/test_camera.py` asserts that frames are flipped horizontally, the status overlay is drawn, and pressing `q` exits the loop while releasing the capture and destroying OpenCV windows.
Manual check: Run `python src/main.py`, verify the mirrored webcam window displays `"Hola Mundo - Presiona 'q' para salir"`, and press `q` to close it cleanly.

- [x] 1.1 Failing test — result: FAILED: ModuleNotFoundError: No module named 'src' (src/camera.py not written yet)
- [x] 1.2 Implementation — files: `src/camera.py`, `src/main.py`, `src/__init__.py`, `pytest.ini`
- [x] 1.3 Passing test — result: 1 passed (`python -m pytest tests/test_camera.py -q`)
- [x] 1.4 Developer approval

## Phase 2 — Graceful exit on unavailable camera or broken frame read (covers SP-1, SP-2)
Test: `tests/test_camera.py` asserts that when `isOpened()` is false or `read()` returns `(False, None)`, an error message is logged and resources are safely released without raising an unhandled exception.
Manual check: Run `python src/main.py` with an invalid camera index or busy camera and verify a clear error message is printed and the program exits cleanly.

- [x] 2.1 Failing test — result: FAILED: DID NOT RAISE SystemExit (test_main_reports_error_and_exits_when_camera_cannot_open)
- [x] 2.2 Implementation — files: `src/main.py` (check `cap.isOpened()`, print error to stderr, `sys.exit(1)`), `pytest.ini` (added `src` to pythonpath)
- [x] 2.3 Passing test — result: 2 passed (`python -m pytest tests/test_camera.py -q`)
- [x] 2.4 Developer approval
