# Dataset Collector
Size: complex — Adds the save flow: normalized vowel capture, a repository port, and Postgres. The live interpretation flow stays out.

## Goal
The developer records many normalized hand-shape samples for A, E, I, O, and U. `run_camera` saves them through a repository interface and does not know that Neon, Postgres, or a test double is behind it. This spec only fills the dataset. It does not interpret a sign.

## Happy path
- HP-1: Given the camera window is open and exactly one hand is visible, when the user presses `a`, `e`, `i`, `o`, or `u`, then one normalized sample for that vowel is saved through the repository and the window confirms the vowel and the save.
- HP-2: Given the Postgres repository is injected and `DATABASE_URL` points at Neon, when a vowel is captured, then a new row is stored and earlier rows remain.
- HP-3: Given tests inject a fake repository, when a vowel is captured, then the fake receives the labeled sample and no database driver is opened.
- HP-4: Given samples already exist, when a frame is shown, then the hand skeleton is still drawn and the window shows how many samples are stored for each vowel. It never shows a predicted vowel.
- HP-5: Given the camera loop is running, when the user presses `q`, then the hand detector, the repository, and the camera are released and the window closes.

## Sad paths
- SP-1: Given no hand or two hands are visible, when the user presses a vowel key, then nothing is saved.
- SP-2: Given the repository fails while saving, when the user presses a vowel key with one hand visible, then an error is shown, no partial sample is stored, and the camera keeps running.
- SP-3: Given `DATABASE_URL` is missing or Neon cannot be reached, when the user runs `python src/main.py`, then an error is printed to stderr, the program exits with code 1, and the camera is not left open.

## Out of scope
- The communicate flow: reading a sign in real time and showing what it means.
- Training or evaluating a classifier, and writing a `.pkl` model.
- Sign sequences, words, or phrases in Lengua de Señas Colombiana.
- Feeding Neon by hand, by MCP, or from a separate admin screen.
- A dependency-injection container, a CSV dataset, or committing `.env`.

## Touches
- `src/` — `HandDetector` still supplies the 21 points; `run_camera` calls only a sample-repository port; `src/main.py` injects the Postgres repository the same way it injects `HandDetector`.
- `tests/` — a fake repository stands in for Postgres.

## Decisions and open questions
- Two flows share the camera and the landmarks. This spec is only the save flow. Interpretation is a later spec and must not be added here.
- Injection matches the current detector: pass the repository into `run_camera`. No container. Capture code never imports the Postgres driver.
- Production storage is Neon through `DATABASE_URL`. Tests use an in-memory fake. The connection string is never hardcoded.
- One keypress stores one sample row: the 21 normalized points as one JSONB value (63 numbers). `epression` (id, label) is the parent table with one row per vowel (a, e, i, o, u). `samples` (id, epression_id, points, created_at) is the child table: `epression_id` references `epression.id`, and deleting an epression row deletes its samples. A letter has many samples. No photo is stored: the model trains on the points, not on images.
- Normalization stores the shape, not the place on screen: coordinates are relative to the wrist and divided by the hand scale.
- The overlay stays in Spanish, consistent with "Mano no detectada", and shows the stored count per vowel.
- `q` still exits cleanly. A failed save does not stop the camera.
