import pickle
import sys
import time
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from camera import open_camera, run_camera
from dataset import motion_features, normalize_landmarks
from hands import HandDetector

MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "language_sing_model.pkl"
MOTION_MODEL_PATH = Path(__file__).resolve().parents[2] / "data" / "motion_phrases_model.pkl"
MIN_FRAMES = 5
MIN_PROBABILITY = 0.4  # lowered from 0.6: with few recordings the right phrase wins with 40-60%
NOT_RECOGNIZED = "No reconocido"
NOTHING = "nada"  # samples recorded as "no sign"; when it wins, nothing is shown


def describe_hand(model, hands):
    if len(hands) != 1:
        return None
    features = [value for point in normalize_landmarks(hands[0]) for value in point]
    probabilities = model.predict_proba([features])[0]
    best = max(range(len(probabilities)), key=lambda i: probabilities[i])
    if model.classes_[best] == NOTHING:
        return None
    return f"{model.classes_[best].upper()} {round(probabilities[best] * 100)}%"


def describe_prediction(model, frames):
    """`HOLA 87%` for a recorded sequence of frames, or `No reconocido` when the model is not sure enough."""
    if len(frames) < MIN_FRAMES:
        return NOT_RECOGNIZED
    probabilities = model.predict_proba([motion_features(frames)])[0]
    best = max(range(len(probabilities)), key=lambda i: probabilities[i])
    if probabilities[best] < MIN_PROBABILITY:
        return NOT_RECOGNIZED
    if model.classes_[best] == NOTHING:
        return ""
    return f"{model.classes_[best].upper()} {round(probabilities[best] * 100)}%"


def run_recognition(cap, detector, model, motion_model=None, clock=time.monotonic):
    """Vowels are recognized live; with a motion model there is also Grabar and Detener to recognize a phrase."""
    recognize = (lambda frames: describe_prediction(motion_model, frames)) if motion_model is not None else None
    run_camera(cap, detector, predict=lambda d: describe_hand(model, d.landmarks()), clock=clock,
               recognize=recognize)


def load_motion_model(path=MOTION_MODEL_PATH):
    """The trained motion model, or None (with a hint on stderr) when it has not been trained yet."""
    if not Path(path).exists():
        print("Aviso: no se encontró el modelo de movimiento; solo se reconocerán las vocales. "
              "Entrénalo con: python src/train/train_phrases.py", file=sys.stderr)
        return None
    with Path(path).open("rb") as file:
        return pickle.load(file)


def main():
    with MODEL_PATH.open("rb") as file:
        model = pickle.load(file)
    cap = open_camera()
    run_recognition(cap, HandDetector(max_num_hands=2), model, load_motion_model())


if __name__ == "__main__":
    main()
