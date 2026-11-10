import math
from typing import Protocol

VOWELS = "aeiou"

WRIST = 0
MIDDLE_MCP = 9


class SampleRepository(Protocol):
    def save_sample(self, label, points): ...


def normalize_landmarks(landmarks):
    """Coordinates relative to the wrist, divided by the wrist-to-middle-knuckle distance."""
    wrist = landmarks[WRIST]
    scale = math.dist(wrist, landmarks[MIDDLE_MCP])
    return [
        ((x - wrist[0]) / scale, (y - wrist[1]) / scale, (z - wrist[2]) / scale)
        for x, y, z in landmarks
    ]
