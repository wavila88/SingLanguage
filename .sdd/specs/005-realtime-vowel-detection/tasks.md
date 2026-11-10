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

- [ ] 2.1 Failing test — result: ________
- [ ] 2.2 Implementation — files: ________
- [ ] 2.3 Passing test — result: ________
- [ ] 2.4 Developer approval

## Phase 3 — Stop with an error when the model or the camera is missing (covers SP-1, SP-2)
Test: `tests/test_recognize_message.py` asserts that a missing `data/language_sing_model.pkl` or a camera that does not open prints an error to stderr, exits with code 1, and that the camera is not opened when the model is missing.
Manual check: Rename `data/language_sing_model.pkl` temporarily, run `python src/recognize_message.py`, and confirm the stderr error and exit code 1; restore the file afterwards.

- [ ] 3.1 Failing test — result: ________
- [ ] 3.2 Implementation — files: ________
- [ ] 3.3 Passing test — result: ________
- [ ] 3.4 Developer approval

## Phase 4 — Show a message instead of a vowel when there are zero or several hands (covers SP-3, SP-4)
Test: `tests/test_recognize_message.py` asserts that with no hand the window shows "Mano no detectada" and no vowel or percentage, and that with two hands it shows a message asking for one hand and no vowel or percentage.
Manual check: Run `python src/recognize_message.py`, first with no hand in view, then with two hands, and confirm the messages in each case.

- [ ] 4.1 Failing test — result: ________
- [ ] 4.2 Implementation — files: ________
- [ ] 4.3 Passing test — result: ________
- [ ] 4.4 Developer approval
