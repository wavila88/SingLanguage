# Tasks: Dataset Collector
Spec: ./spec.md
Test command: `pytest`

## Phase 1 — Connect to Neon and create the sample tables (required by HP-2)
Test: `tests/test_dataset.py` asserts that a connection from `DATABASE_URL` creates `samples` and `sample_points`, and that `sample_points.sample_id` references `samples.id` with points removed when the sample is removed.
Manual check: Open Neon and confirm `samples`, `sample_points`, and the foreign key from `sample_points.sample_id` to `samples.id`.

- [x] 1.1 Failing test — result: FAILED: ModuleNotFoundError: No module named 'src.database'
- [x] 1.2 Implementation — files: `src/schema.sql` (samples and sample_points), `src/database.py` (connect + create_sample_tables), `requirements.txt` (psycopg)
- [x] 1.3 Passing test — result: 1 passed (`python -m pytest tests/test_dataset.py -q`); full suite 8 passed
- [x] 1.4 Developer approval

## Phase 2 — Save one normalized vowel through the repository (covers HP-1, HP-3)
Test: `tests/test_dataset.py` asserts that pressing `a`, `e`, `i`, `o`, or `u` with one hand saves one normalized 21-point sample to a fake repository, the window confirms that vowel, and no database driver is opened.
Manual check: Run `python src/main.py`, show one hand, press `a`, and confirm the window reports the saved vowel.

- [x] 2.1 Failing test — result: FAILED: ModuleNotFoundError: No module named 'src.dataset' (`tests/test_dataset.py`)
- [x] 2.2 Implementation — files: `src/dataset.py` (new: `VOWELS`, `SampleRepository` port, `normalize_landmarks`), `src/camera.py` (`run_camera(cap, detector, repository)` saves on a vowel key with one hand and shows the confirmation), `src/hands.py` (`HandDetector.landmarks()`)
- [x] 2.3 Passing test — result: 13 passed (`python -m pytest -q`); the 5 vowel cases and the normalization case pass
- [x] 2.4 Developer approval

## Phase 3 — Parent epression and child samples, points as JSON, no photos (covers HP-2, replaces the sample_points model)
Decision: `epression` (id, label) is the parent with one row per vowel (a, e, i, o, u). `samples` (id, epression_id, points JSONB, created_at) is the child: each vowel press adds one row with the 21 normalized points as 63 numbers, linked to its epression. `sample_points` is removed. No photos are stored.
Test: `tests/test_dataset.py` asserts that the label `e` exists once in `epression`, and that a second save adds another `samples` row linked to `e` with 63 numbers while the first remains.
Manual check: Press `e` twice and confirm Neon has one `epression` row for `e`, and two `samples` rows whose `epression_id` points to it, each with 63 numbers in `points`.

- [x] 3.1 Failing test — result: FAILED: UndefinedTable: relation "letters" does not exist (`tests/test_dataset.py`)
- [x] 3.2 Implementation — files: `src/dbConf/schema.sql` (epression parent seeded with a, e, i, o, u; samples child with epression_id FK), `src/dbConf/database.py` (`save_sample` inserts a child row linked to its epression, raises ValueError for an unknown vowel). One-time migration in Neon: dropped `sample_points`, `samples` and `letters`, and recreated `epression` and `samples`
- [x] 3.3 Passing test — result: 1 passed (`pytest tests/test_dataset.py -v`); full suite 8 passed
- [ ] 3.4 Developer approval

## Phase 4 — Append the sample to Neon as samples and sample_points (covers HP-2) — pendiente, se reemplaza por la fase 3
Test: `tests/test_dataset.py` asserts that a second save inserts another `samples` row and 21 `sample_points` rows linked by `sample_id`, and that the first sample remains.
Manual check: Press `e` twice and confirm Neon has two `samples` rows, each with 21 `sample_points`, and the first was not replaced.

- [ ] 4.1 Failing test — result: ________
- [ ] 4.2 Implementation — files: ________
- [ ] 4.3 Passing test — result: ________
- [ ] 4.4 Developer approval

## Phase 5 — Show the stored count per vowel, not a prediction (covers HP-4)
Test: `tests/test_dataset.py` asserts that the window shows the repository count for each vowel, the hand skeleton is still drawn, and no predicted vowel appears.
Manual check: Save a few vowels, then confirm the on-screen counts match and the window never guesses a letter.

- [ ] 5.1 Failing test — result: ________
- [ ] 5.2 Implementation — files: ________
- [ ] 5.3 Passing test — result: ________
- [ ] 5.4 Developer approval

## Phase 6 — Release the repository when the user presses q (covers HP-5)
Test: `tests/test_dataset.py` asserts that pressing `q` releases the hand detector, the repository, and the camera, and that the window closes.
Manual check: Press `q` and confirm the camera light turns off and no process stays open.

- [ ] 6.1 Failing test — result: ________
- [ ] 6.2 Implementation — files: ________
- [ ] 6.3 Passing test — result: ________
- [ ] 6.4 Developer approval

## Phase 7 — Keep the camera running when a save fails (covers SP-2)
Test: `tests/test_dataset.py` asserts that a repository error while saving shows an error, stores no partial sample, and the camera loop continues until `q`.
Manual check: Force a save failure, confirm the error and that the window stays open until you press `q`.

- [ ] 7.1 Failing test — result: ________
- [ ] 7.2 Implementation — files: ________
- [ ] 7.3 Passing test — result: ________
- [ ] 7.4 Developer approval

## Phase 8 — Exit when Neon cannot be used at startup (covers SP-3)
Test: `tests/test_dataset.py` asserts that a missing `DATABASE_URL` or an unreachable Neon prints an error to stderr, exits with code 1, and does not leave the camera open.
Manual check: Rename `.env` temporarily, run `python src/main.py`, and confirm the error, exit code 1, and that the camera light never stays on.

- [ ] 8.1 Failing test — result: ________
- [ ] 8.2 Implementation — files: ________
- [ ] 8.3 Passing test — result: ________
- [ ] 8.4 Developer approval
