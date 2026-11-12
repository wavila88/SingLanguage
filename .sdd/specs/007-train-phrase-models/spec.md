# Train a model for motion phrases and recognize vowels and motion in the live window, also continuously
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
- HP-7: Given `src/recognize/recognize_message_v2.py` running with both models, when the user moves the hands for a sign and then holds them still for 0.4 s (or takes them out of the frame), then the movement is recognized with the motion model and its word (e.g. `HOLA`) is added to the message, with no Grabar or Detener.
- HP-8: Given the v2 window, when one hand stays still for 0.7 s, then the average of that pause is recognized with the static (vowel) model and its letter is added to the message, once per pause; the hand has to move again for the next letter (so `L`, `L` needs a movement between them).
- HP-9: Given a movement that gave a word, when the hands stay still after it, then that stillness is not read as a letter; given a movement that gave nothing (a transition, e.g. from A to E), then the stillness after it is read as a letter.
- HP-10: Given signs recognized in a row, when they are shown, then the message appears on a strip at the bottom of the window, with letters in a row joined by `, ` and words separated by a space (e.g. `HOLA A, E GRACIAS`).
- HP-11: Given a message on the strip, when 4 s pass without a new sign, then it clears and the strip shows `Haz un signo frente a la cámara`.
- HP-12: Given `src/recognize/recognize_message.py` (moved into `src/recognize/`, next to v2), when it runs, then it works exactly as before, with Grabar and Detener.

## Sad paths
- SP-1: Given fewer than 2 motion phrases with 3 or more recordings, when the command runs, then no model is written and the console says why, e.g. `Movimiento: se necesitan al menos 2 frases con 3 muestras; hay 1 (hola: 6)`, and it exits with code 1.
- SP-2: Given `DATABASE_URL` is missing or the database is unreachable, when the training command runs, then it prints an error to stderr, exits with code 1 and leaves the model file as it was.
- SP-3: Given a prediction whose best probability is below 60%, when it is predicted, then the result is `No reconocido` instead of a phrase.
- SP-4: Given phrase names that differ only by case or surrounding spaces (e.g. `Hola`, `hola `), when the command runs, then they count as one phrase.
- SP-5: Given a recording with fewer than 5 frames with a hand, when training, then it is left out and the console says how many were left out; when stopped in the recognition window, then the result is `No reconocido`.
- SP-6: Given `data/motion_phrases_model.pkl` does not exist, when the recognition window starts, then it still recognizes the vowels, hides "Grabar" and prints to stderr that the motion model is missing and how to create it.
- SP-7: Given the v2 window, when a model says `nada`, or its best probability is below the threshold (40% motion, 60% static), or a movement has fewer than 5 frames, then nothing is added to the message.
- SP-8: Given two hands held still in the v2 window, when 0.7 s pass, then no letter is added (the static model only knows one hand).
- SP-9: Given small jitter of a still hand, when it is measured, then it does not count as movement: the wrist speed is measured against the frame 0.15 s before, in hand sizes per second, with 1 hand size per second as the limit.
- SP-10: Given `data/motion_phrases_model.pkl` does not exist, when the v2 window starts, then it still adds letters and prints the same stderr hint as SP-6.
- SP-11: Given a message wider than the window, when it is drawn, then its end is kept visible.

## Out of scope
- A model for static phrases made of one or two hands (two-hand poses): the static vowels keep their own model and window behavior. It can be a later spec.
- A fixed 3-second cut or a sliding window for continuous recognition: v2 cuts each sign by pauses (see Decisions). A sliding window can be a later change if signers do not pause between signs.
- Joining spelled letters into one word (`H, O, L, A` stays as letters), and a Borrar button: the message clears by itself.
- Capturing more samples, and normalizing phrase names when they are typed in the capture window.
- Retraining or changing the vowel model, and deep-learning models.
- Recognizing a phrase reliably from a handful of recordings: the result depends on how many are captured.

## Touches
- `src/train/train_phrases.py` (new entrypoint, same pattern as `train.py`: adds `src/` to the path, prints Spanish messages, exits 1 on failure)
- `src/recognize/recognize_message.py` (moved from `src/`; `describe_prediction`, loads the motion model, injects the recognition into the window; adds `src/` to the path like `capture_words.py`)
- `src/recognize/recognize_message_v2.py` (new entrypoint: cuts signs by pauses, builds the message, draws the bottom strip; reuses the constants and `load_motion_model` of v1)
- `pytest.ini` (adds `src/recognize` to `pythonpath`)
- `src/camera.py` (the recognition window gets the Grabar, countdown, Detener and result flow, reusing what the capture window already has; `run_camera` gets an optional `overlay(frame, detector, now)` for v2)
- `src/dataset.py` (turns a recorded sequence into a fixed-length feature list; no third-party imports)
- `src/dbConf/database.py` (loads motion samples with their frames, per phrase)
- `data/motion_phrases_model.pkl` (gitignored like the other `.pkl` files)
- `tests/test_train_phrases.py`, `tests/test_dataset.py`, `tests/test_recognize_message.py`, `tests/test_recognize_message_v2.py`

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
- Continuous recognition (v2, added after phase 2): a new window next to the first one, both in `src/recognize/`, so Grabar and Detener stay available to compare. It cuts signs by pauses, because the motion model was trained on whole gestures cut by Grabar and Detener, and a pause-cut stretch looks like one. Fixed 3-second cuts were discarded because they split signs.
- Stillness is also a sign: one hand still for 0.7 s is looked up in the vowel model. A movement that gave a word blocks the letter after it; one that gave nothing was a transition and allows it.
- Starting values, to tune after trying: 0.4 s to end a movement, 0.7 s for a static sign, 4 s to clear, 1 hand size per second over 0.15 s counts as movement, 40% threshold for motion and 60% for static.
- The message is drawn on the bottom strip (`widgets.draw_strip`) with `draw_text`; letters in a row use `, `, words use a space. v2 shows no vowel percentage and no buttons.
