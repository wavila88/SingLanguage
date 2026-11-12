import pickle
from pathlib import Path

import cv2

from camera import run_camera
from dataset import motion_features, normalize_landmarks
from hands import HandDetector

MODEL_PATH = Path(__file__).resolve().parents[1] / "data" / "language_sing_model.pkl"
MIN_PROBABILITY = 0.6
NOT_RECOGNIZED = "No reconocido"


def describe_hand(model, hands):
    if len(hands) != 1:
        return None
    features = [value for point in normalize_landmarks(hands[0]) for value in point]
    probabilities = model.predict_proba([features])[0]
    best = max(range(len(probabilities)), key=lambda i: probabilities[i])
    return f"{model.classes_[best].upper()} {round(probabilities[best] * 100)}%"


def describe_prediction(model, frames):
    """`HOLA 87%` for a recorded sequence of frames, or `No reconocido` when the model is not sure enough."""
    probabilities = model.predict_proba([motion_features(frames)])[0]
    best = max(range(len(probabilities)), key=lambda i: probabilities[i])
    if probabilities[best] < MIN_PROBABILITY:
        return NOT_RECOGNIZED
    return f"{model.classes_[best].upper()} {round(probabilities[best] * 100)}%"


def run_recognition(cap, detector, model):
    run_camera(cap, detector, predict=lambda d: describe_hand(model, d.landmarks()))


def main():
    with MODEL_PATH.open("rb") as file:
        model = pickle.load(file)
    cap = cv2.VideoCapture(0)
    run_recognition(cap, HandDetector(max_num_hands=2), model)


if __name__ == "__main__":
    main()
