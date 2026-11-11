# Tasks: Capture static and motion expressions with one or two hands
Spec: ./spec.md
Test command: `pytest`

Tests drive the window as in `tests/test_camera.py`: `cv2` is monkeypatched, a fake capture feeds frames, keys come from a fake `waitKey`, and clicks are simulated by calling the callback the loop registers with `cv2.setMouseCallback`, at the window coordinates of the drawn button. Postgres checks go in `tests/test_dataset.py` and skip without `DATABASE_URL`; everything else uses fake repositories.

## Phase 1 — Menu on open, keys do nothing, close only with the X (covers HP-1, HP-11, SP-7)
Test: `tests/test_camera.py` asserts the first frame draws the buttons "Expresión estática" and "Expresión en movimiento", that `q` and `a` with one hand visible neither close the window nor save, and that closing with the X releases camera and detector; `tests/test_recognize_message.py` asserts the recognition window also ignores `q` and closes only with the X; `tests/test_textdraw.py` asserts that `draw_text` renders `ó` and `ñ` differently from `o` and `n`. All window texts now go through `draw_text`, so the existing tests that captured `cv2.putText` capture `camera.draw_text` instead.
Manual check: Run `python src/capture/capture_words.py`, see the two buttons, press `q` and `a` and confirm nothing happens, then close with the X and confirm the camera light turns off, and that the accents in the buttons are drawn correctly; repeat the `q` and X check in `python src/recognize_message.py`.
Note: update the `q` convention in `.sdd/project.md` and the quit instructions in `CLAUDE.md` to "close with the window's X".

- [x] 1.1 Failing test — result: `ModuleNotFoundError: No module named 'textdraw'` (tests/test_textdraw.py) and 9 failed in the rest: `AttributeError: module 'src.camera' has no attribute 'draw_text'` plus the menu and `q` tests
- [x] 1.2 Implementation — files: `src/textdraw.py` (new: `draw_text` with `anchor`, Pillow), `src/widgets.py` (new: Figma palette, rounded translucent strip and primary button), `src/camera.py` (`draw_menu`: Figma-styled primary buttons side by side on a bottom strip, all text through `draw_text`, `q` and vowel-save logic removed), `requirements.txt` (pillow), `tests/test_camera.py`, `tests/test_hands.py`, `tests/test_recognize_message.py` (updated), `.sdd/project.md`, `CLAUDE.md`
- [x] 1.3 Passing test — result: `python -m pytest -q` → 26 passed
- [x] 1.4 Developer approval

## Phase 2 — Choose a mode, type a name, open the expression with its sample count, and go back (covers HP-2, HP-3, HP-10)
Test: `tests/test_camera.py` asserts that clicking "Expresión estática", typing `hola` (with a Backspace) and clicking "Aceptar" or pressing Enter opens `hola` on a fake repository and shows "HOLA · estática · 0 muestras", that an existing expression with 12 motion samples shows "HOLA · en movimiento · 12 muestras", that the clicks land when the window is resized, and that "Volver" returns to the menu; `tests/test_dataset.py` asserts against Neon that opening `hola` twice creates one `epression` row, that the count is per kind, and that existing samples count as static.
Manual check: Open the capture window, choose "Expresión estática", type `hola`, confirm, and see the count; type a name with ñ and an accent (e.g. `añó`) and confirm the window receives and draws them (if it does not, stop and decide a fallback); click "Volver", choose "Expresión en movimiento", type `hola` again, and confirm Neon still has a single `hola` row.

- [x] 2.1 Failing test — result: `ModuleNotFoundError: No module named 'capture_ui'` (tests/test_camera.py) and `AttributeError: 'PostgresSampleRepository' object has no attribute 'open_expression'` (2 tests in tests/test_dataset.py)
- [x] 2.2 Implementation — files: `src/capture_ui.py` (new: screen state, typing, layouts), `src/camera.py` (mouse callback, key routing, name-input and expression screens), `src/widgets.py` (secondary button, field, card, disabled button, palette), `src/textdraw.py` (`text_width`), `src/dbConf/schema.sql` (`samples.kind`), `src/dbConf/database.py` (`open_expression`), `src/dataset.py` (protocol), `tests/test_camera.py`, `tests/test_dataset.py`
- [x] 2.3 Passing test — result: `python -m pytest -q` → 37 passed (incluye las 2 pruebas contra Neon)
- [x] 2.4 Developer approval

## Phase 3 — Capture a static pose with one or two hands, review it frozen, and approve it (covers HP-4, HP-5, HP-12)
Test: `tests/test_camera.py` asserts that "Capturar" freezes the frame and shows only "Aprobar" and "No aprobar", and that "Aprobar" saves one static sample with each hand labeled left or right (normalized points plus raw wrist), shows "Guardada muestra: HOLA (2 manos)" and the count +1, and returns to live video; `tests/test_hands.py` asserts handedness matches the mirrored frame; `tests/test_dataset.py` asserts the static row in Neon; `tests/test_train.py` asserts training still uses only the one-hand vowel samples in the old format.
Manual check: Open `hola` in static mode, show both hands, click "Capturar", check the frozen image, click "Aprobar", and confirm the message, the new count and a new `samples` row in Neon; then run `python src/train/train.py` and confirm it still trains.

- [ ] 4.1 Failing test — result: ________
- [ ] 4.2 Implementation — files: ________
- [ ] 4.3 Passing test — result: ________
- [ ] 4.4 Developer approval

## Phase 5 — Discard a static capture, or refuse it with no hand (covers HP-9 for static, SP-3)
Test: `tests/test_camera.py` asserts that "No aprobar" saves nothing, keeps the count, shows "Muestra descartada" and returns to live video, and that "Capturar" with no hand shows "No se capturó: no se detectó ninguna mano" without entering review.
Manual check: Capture, click "No aprobar", and confirm the count did not change; hide your hands, click "Capturar", and confirm the message appears.

- [ ] 5.1 Failing test — result: ________
- [ ] 5.2 Implementation — files: ________
- [ ] 5.3 Passing test — result: ________
- [ ] 5.4 Developer approval

## Phase 6 — Record a motion sequence, replay it, and approve or discard it (covers HP-6, HP-7, HP-8, HP-9 for motion)
Test: `tests/test_camera.py` asserts that "Grabar" shows "Grabando..." with the elapsed time and turns into "Detener", that "Detener" replays the recorded frames in a loop at their recorded timing with only "Aprobar"/"No aprobar", that "Aprobar" saves one motion sample whose frames are in order with index and ms offset and without the no-hand frames, and shows "Guardada secuencia: HOLA (N frames)" with the count +1, and that "No aprobar" saves nothing; `tests/test_dataset.py` asserts the parent row with no `points`, the child frame rows in Neon, and that deleting the sample deletes its frames.
Manual check: Open `hola` in motion mode, record a wave, watch the replay, approve it, and confirm the message, the new count and the frame rows in Neon; record again and discard it.

- [ ] 6.1 Failing test — result: ________
- [ ] 6.2 Implementation — files: ________
- [ ] 6.3 Passing test — result: ________
- [ ] 6.4 Developer approval

## Phase 7 — Recording limits and interrupted captures (covers SP-4, SP-5, SP-6)
Test: `tests/test_camera.py` asserts that stopping with fewer than 5 hand frames shows "No se grabó: secuencia demasiado corta" without replay, that a recording reaching 10 s (fake clock) stops on its own and enters replay, and that closing the window while recording or under review saves nothing.
Manual check: Click "Grabar" then "Detener" right away and see the message; leave a recording running and confirm the replay starts at 10 s; close the window during a replay and confirm no new row in Neon.

- [ ] 7.1 Failing test — result: ________
- [ ] 7.2 Implementation — files: ________
- [ ] 7.3 Passing test — result: ________
- [ ] 7.4 Developer approval

## Phase 8 — Database failures (covers SP-2, SP-8, SP-9)
Test: `tests/test_camera.py` asserts with a failing fake repository that confirming a name keeps the name input and shows "No se pudo conectar con la base de datos", and that "Aprobar" (static and motion) shows "No se pudo guardar la muestra", stays in review and saves on a retry; `tests/test_dataset.py` asserts a motion sample whose frame insert fails leaves neither parent nor frames; a capture entrypoint test asserts that without `DATABASE_URL` it prints to stderr and exits with code 1 before opening the camera.
Manual check: Run the capture app with `DATABASE_URL` unset and confirm the error and exit; open the app, turn off the network, then confirm a name and click "Aprobar" on a capture and see each message, and turn the network back on and confirm "Aprobar" now saves.

- [ ] 8.1 Failing test — result: ________
- [ ] 8.2 Implementation — files: ________
- [ ] 8.3 Passing test — result: ________
- [ ] 8.4 Developer approval
