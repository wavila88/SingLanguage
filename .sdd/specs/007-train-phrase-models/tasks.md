# Tasks: Train a model for motion phrases and recognize vowels and motion in the live window, also continuously
Spec: ./spec.md
Test command: `pytest`

## Phase 1 — Train the motion model, see how well it recognizes held-out samples, and predict a sequence (covers HP-1, HP-2, SP-3, SP-4, SP-5 for training)
Test: `tests/test_train_phrases.py` asserts, with a fake repository of recorded sequences, that the motion model is trained and saved to the given path, that the console result lists each phrase as "N de M reconocidas" from leaving each sample out in turn, that `Hola` and `hola ` count as one phrase, that sequences under 5 frames are left out with their count reported, and that predicting a sequence returns text like "HOLA 87%" or "No reconocido" below 60%; `tests/test_dataset.py` asserts the motion features have the same length for sequences of different duration and frame count, and that times are counted from the first saved frame, and that the repository loads motion samples with their frames from Neon.
Manual check: With `hola` and `gracias` recorded (3 or more each), run `python src/train/train_phrases.py` and read the per-phrase result for motion; confirm `data/motion_phrases_model.pkl` was written.

- [x] 1.1 Failing test — result: `ModuleNotFoundError: No module named 'phrases'` (tests/test_train_phrases.py) and 5 failed in tests/test_dataset.py (`AttributeError: module 'dataset' has no attribute 'motion_features'`, `... 'load_motion_samples'`); the developer then asked to remove these phase tests from the suite
- [x] 1.2 Implementation — files: `src/train/train_phrases.py` (new: `train_motion_model`, leave-one-out evaluation, `format_result`, `main`), `src/recognize_message.py` (`describe_prediction`, 60% threshold), `src/dataset.py` (`hand_features`, `motion_features`, `normalize_phrase`), `src/dbConf/database.py` (`load_motion_samples`)
- [x] 1.3 Passing test — result: 58 passed with the phase tests; after removing them at the developer's request the rest of the suite passes; `python src/train/train_phrases.py` on the real recordings → hola 6 de 6, adios 6 de 6, gracias 5 de 5
- [x] 1.4 Developer approval

## Phase 2 — Recognize the vowels and the motion phrases in `recognize_message.py` (covers HP-3, HP-4, HP-5, SP-5 for the window, SP-6)
Test: `tests/test_recognize_message.py` asserts that with one hand shown the vowel text still appears as today, that clicking "Grabar" shows the 2-second countdown and then "Grabando..." with the elapsed time and "Detener", that "Detener" shows the predicted phrase and probability (e.g. "HOLA 87%") from the frames recorded and saves nothing, that a recording under 5 frames with a hand shows "No reconocido", that the existing tests (close only with the X, keys do nothing) still pass, and that without the motion model the vowels still work and "Grabar" is not shown.
Manual check: Run `python src/recognize_message.py`, show a vowel and see its percentage; click "Grabar", wait the countdown, make the `hola` gesture, click "Detener" and read the phrase; then rename `data/motion_phrases_model.pkl` temporarily and confirm the vowels still work and the stderr message appears.

- [x] 2.1 Failing test — result: `ImportError: cannot import name 'load_motion_model' from 'recognize_message'` (tests/test_recognize_message.py); the developer then asked to remove these phase tests from the suite
- [x] 2.2 Implementation — files: `src/recognize_message.py` (`run_recognition` with the motion model and `clock`, `load_motion_model`, under-5-frames guard), `src/capture_ui.py` (`RecognizeUI`), `src/camera.py` (`recognize`, `draw_recognize_screen`, countdown and recording screens shared)
- [x] 2.3 Passing test — result: 53 passed with the phase tests; after removing them at the developer's request the rest of the suite passes; real model on saved recordings → hola 95%, adios 97%, gracias 98%, 3 frames → No reconocido
- [x] 2.4 Developer approval

## Phase 3 — Not enough data or database failures when training (covers SP-1, SP-2, HP-6)
Test: `tests/test_train_phrases.py` asserts that with fewer than 2 phrases of 3 recordings no model file is written, the console says "se necesitan al menos 2 frases con 3 muestras; hay 1 (hola: 6)" and it exits with code 1, and that a missing `DATABASE_URL` or an unreachable database prints an error to stderr, exits with code 1 and leaves the model file as it was; `tests/test_train.py` keeps passing unchanged to show the vowel training is untouched.
Manual check: Run the training with only one phrase recorded and read the message; run it with `DATABASE_URL` unset and confirm the error and exit; then run `python src/train/train.py` and confirm it still trains.

- [x] 3.1 Failing test — result: 3 failed (tests/test_train_phrases.py): `This solver needs samples of at least 2 classes in the data, but the data contains only one class: np.str_('hola')` instead of the "se necesitan al menos 2 frases" message; the 2 database tests already passed because `main` already handled them
- [x] 3.2 Implementation — files: `src/train/train_phrases.py` (`MIN_PHRASES`, `MIN_SAMPLES_PER_PHRASE`, count per phrase and stop before writing the model)
- [x] 3.3 Passing test — result: 52 passed (`pytest`), `tests/test_train.py` unchanged
- [ ] 3.4 Developer approval

## Phase 4 — Continuous recognition in `recognize_message_v2.py`, next to the first window in `src/recognize/` (covers HP-7 to HP-12, SP-7 to SP-11)
Test: `tests/test_recognize_message_v2.py` asserts, with fake models and synthetic hands (no camera), that a movement followed by 0.4 s still adds the motion word, that hands leaving mid-movement also close it, that one hand still for 0.7 s adds the letter once and not again until it moves, that the stillness after a word adds no letter while the stillness after a movement that gave nothing does, that `nada`, low probability, under 5 frames and two still hands add nothing, that jitter under 1 hand size per second is not movement, that letters join with `, ` and words with a space, that the message clears after 4 s and the placeholder shows, and that the window runs through `run_camera` with the bottom strip; `tests/test_recognize_message.py` keeps passing after the move.
Manual check: Run `python src/recognize/recognize_message_v2.py`, sign `hola`, pause, hold an A, move, hold an E, and read `HOLA A, E` on the bottom strip; wait 4 s and see it clear; then run `python src/recognize/recognize_message.py` and confirm Grabar and Detener still work.

- [ ] 4.1 Failing test — result: ________
- [ ] 4.2 Implementation — files: ________
- [ ] 4.3 Passing test — result: ________
- [ ] 4.4 Developer approval
