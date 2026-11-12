# Train a model for motion phrases and recognize vowels and motion in the live window
Size: complex — a new model fed by recorded frame sequences, a new training entrypoint, and a recording flow inside the recognition window

## Goal
From the motion samples already saved in Neon by spec 006, the developer runs one command that trains a motion model and shows how well it recognizes samples it did not train on. The live window `src/recognize_message.py` then recognizes both the static vowels, as it does today, and the motion phrases the developer records in front of it.

## Happy path
- HP-1: Given at least 2 motion phrases with 3 or more recordings each, when the developer runs `python src/train/train_phrases.py`, then a motion model is trained on the recorded sequences, saved to `data/motion_phrases_model.pkl`, and the console prints, for each phrase, how many of its recordings were recognized when held out (e.g. `Movimiento · hola: 4 de 5 reconocidas`).
- HP-2: Given a saved motion model and a recorded sequence, when it is predicted, then the phrase and its probability come back as text like `HOLA 87%`.
- HP-3: Given `src/recognize_message.py` running with the vowel model, when one hand is shown, then the vowel and its probability appear as they do today (`A 87%`).
- HP-4: Given the recognition window with the motion model available, when the user clicks "Grabar", then a 2-second countdown ("Prepárate...") runs, then the window shows "Grabando..." with the elapsed time and the button turns into "Detener".
- HP-5: Given a recording is in progress, when the user clicks "Detener", then the sequence is recognized and the window shows its phrase and probability (e.g. `HOLA 87%`) until the next "Grabar". Nothing is saved to the database.
- HP-6: Given the vowel samples and `data/language_sing_model.pkl` from before, when `src/train/train.py` runs, then it keeps working exactly as today.

## Sad paths
- SP-1: Given fewer than 2 motion phrases with 3 or more recordings, when the command runs, then no model is written and the console says why, e.g. `Movimiento: se necesitan al menos 2 frases con 3 muestras; hay 1 (hola: 6)`, and it exits with code 1.
- SP-2: Given `DATABASE_URL` is missing or the database is unreachable, when the training command runs, then it prints an error to stderr, exits with code 1 and leaves the model file as it was.
- SP-3: Given a prediction whose best probability is below 60%, when it is predicted, then the result is `No reconocido` instead of a phrase.
- SP-4: Given phrase names that differ only by case or surrounding spaces (e.g. `Hola`, `hola `), when the command runs, then they count as one phrase.
- SP-5: Given a recording with fewer than 5 frames with a hand, when training, then it is left out and the console says how many were left out; when stopped in the recognition window, then the result is `No reconocido`.
- SP-6: Given `data/motion_phrases_model.pkl` does not exist, when the recognition window starts, then it still recognizes the vowels, hides "Grabar" and prints to stderr that the motion model is missing and how to create it.

## Out of scope
- A model for static phrases made of one or two hands (two-hand poses): the static vowels keep their own model and window behavior. It can be a later spec.
- Continuous recognition of motion without pressing "Grabar" and "Detener".
- Capturing more samples, and normalizing phrase names when they are typed in the capture window.
- Retraining or changing the vowel model, and deep-learning models.
- Recognizing a phrase reliably from a handful of recordings: the result depends on how many are captured.

## Touches
- `src/train/train_phrases.py` (new entrypoint, same pattern as `train.py`: adds `src/` to the path, prints Spanish messages, exits 1 on failure)
- `src/recognize_message.py` (`describe_prediction`, loads the motion model, injects the recognition into the window)
- `src/camera.py` (the recognition window gets the Grabar, countdown, Detener and result flow, reusing what the capture window already has)
- `src/dataset.py` (turns a recorded sequence into a fixed-length feature list; no third-party imports)
- `src/dbConf/database.py` (loads motion samples with their frames, per phrase)
- `data/motion_phrases_model.pkl` (gitignored like the other `.pkl` files)
- `tests/test_train_phrases.py`, `tests/test_dataset.py`, `tests/test_recognize_message.py`

## Decisions and open questions
- Answer received: the work is training on the data already in the database, and `recognize_message.py` is the one that recognizes, both the static vowels and the motion phrases. The code that turns a sequence into text lives in that file, not in a new module.
- Static means the vowels for this change. Training a model for static two-hand phrases was in the first draft of this spec and was dropped to keep the MVP small; the vowels keep the old model.
- Motion is recognized by recording, as it was trained: "Grabar", the gesture, "Detener", then the result. Continuous recognition would give many false positives with this few samples. This is the default chosen; it can change if the developer prefers otherwise.
- The recognition window keeps only the hands of each frame while recording (not the video), because nothing is saved.
- Current data (checked in Neon): `hola` 6, `adios` 6 and `gracias` 5 motion recordings.
- One model for motion, same family as today (random forest), no new dependency.
- Features: every sequence is resampled to a fixed number of frames over its own duration (16 by default), counted from its first saved frame, with the left hand first and the right hand second in each frame, a missing hand as zeros plus a presence flag, and the total duration added.
- Evaluation: each recording is held out in turn and predicted by a model trained on the rest (leave-one-out), so small counts still give a result.
- Minimums of 2 phrases, 3 recordings each, 5 frames per recording and the 60% threshold are defaults and can be tuned after the first results.
- Phrase names are compared lowercase and trimmed when training, because capture stores them as typed.
