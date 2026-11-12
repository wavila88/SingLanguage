import math
from typing import Protocol

VOWELS = "aeiou"

WRIST = 0
MIDDLE_MCP = 9


class SampleRepository(Protocol):
    def save_sample(self, label, points): ...

    def open_expression(self, label, kind): ...

    def save_static_sample(self, label, hands): ...


def hand_record(side, landmarks):
    """What is stored for one visible hand: its side, normalized points and raw wrist position."""
    return {
        "side": side,
        "points": [value for point in normalize_landmarks(landmarks) for value in point],
        "wrist": list(landmarks[WRIST]),
    }


def normalize_landmarks(landmarks):
    """Coordinates relative to the wrist, divided by the wrist-to-middle-knuckle distance."""
    wrist = landmarks[WRIST]
    scale = math.dist(wrist, landmarks[MIDDLE_MCP])
    return [
        ((x - wrist[0]) / scale, (y - wrist[1]) / scale, (z - wrist[2]) / scale)
        for x, y, z in landmarks
    ]
