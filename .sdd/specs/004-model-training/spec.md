# Model Training
Size: simple — One command sends the stored samples to scikit-learn and writes one model file.

## Goal
Use scikit-learn and the stored vowel samples to train a classifier and generate a model file. The same run reports whether that model recognizes the vowel "a". It does not read a sign from the camera.

## Happy path
- HP-1: Given stored samples exist and `DATABASE_URL` is set, when the developer runs `python src/train/train.py`, then those samples are sent to scikit-learn, `data/vowel_model.pkl` is written, and the camera is not opened.
- HP-2: Given the model was just generated, when the held-out stored "a" sample is classified, then the run reports whether it was recognized as "a".
- HP-3: Given `data/vowel_model.pkl` already exists, when the developer runs the command again, then that same file is replaced and no second model file is created.

## Sad paths
- SP-1: Given the samples cannot be loaded, when the developer runs `python src/train/train.py`, then an error is printed to stderr, the program exits with code 1, and the current model file is left unchanged.

## Out of scope
- Showing a live vowel prediction on the camera (covered in `005-realtime-vowel-detection`).
- Collecting or editing samples, and any camera-window control for training.
- Training from a CSV or from photos.
- Words, phrases, or sequences in Lengua de Señas Colombiana.
- A new model file on each run, a minimum sample count, a minimum accuracy, and partial-file failures.

## Touches
- `src/train/` — the training entrypoint and any other training-only module. `src/main.py` stays the camera and does not train.
- `src/dbConf` — the Postgres sample repository supplies each sample's vowel and its 63 numbers.
- `data/` — the one serialized `.pkl` model. Samples stay in Neon, not here.
- `tests/` — a fake repository stands in for Postgres.

## Decisions and open questions
- The work is one command: send the stored samples to scikit-learn and write the model. Error stories are limited to "the samples could not be loaded".
- Samples come from `samples` joined to `epression`, not from a CSV. The README still mentions a CSV; that path was replaced in spec 003.
- Training lives in `src/train/`. The command is `python src/train/train.py`. Other training-only files go in that folder, not beside `main.py`. It does not open the camera and does not import the camera module.
- The classifier is scikit-learn `RandomForestClassifier`. Features are the 63 stored numbers. Labels are a, e, i, o, and u. Points are not normalized again.
- The test pattern is one existing `samples` row whose `epression` label is `a`: the 63 numbers saved when that vowel was captured. It is not a photo, not a hardcoded hand shape, and not a new camera capture. That row is held out of training and the run reports whether it was recognized as "a".
- The model path is always `data/vowel_model.pkl`. Running the command again replaces that file. It does not create a second model. The file stays gitignored.
- Tests use an in-memory fake. Only the database module reads `DATABASE_URL`. The connection string is never hardcoded.
