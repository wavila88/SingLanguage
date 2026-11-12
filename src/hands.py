import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision

NO_HAND_TEXT = "Mano no detectada"

MODEL_PATH = "data/hand_landmarker.task"
MIN_CONFIDENCE = 0.3

# Standard MediaPipe hand connections (indices of the 21 landmarks).
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
]

LANDMARK_COLOR = (0, 255, 255)
CONNECTION_COLOR = (255, 255, 255)


class HandDetector:
    """Detects hand landmarks with MediaPipe Tasks and draws them on the frame."""

    def __init__(self, max_num_hands=2, model_path=MODEL_PATH):
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            num_hands=max_num_hands,
            min_hand_detection_confidence=MIN_CONFIDENCE,
            min_hand_presence_confidence=MIN_CONFIDENCE,
            min_tracking_confidence=MIN_CONFIDENCE,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._hands_landmarks = []
        self._handedness = []

    def process(self, frame):
        """Detect hands in the frame and return how many were found."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb.astype(np.uint8))
        result = self._landmarker.detect(image)
        self._hands_landmarks = result.hand_landmarks
        self._handedness = [hand[0].category_name.lower() for hand in result.handedness]
        return self.hands_count()

    def hands_count(self):
        return len(self._hands_landmarks)

    def landmarks(self):
        """21 (x, y, z) points for each hand in the last processed frame."""
        return [[(lm.x, lm.y, lm.z) for lm in hand] for hand in self._hands_landmarks]

    def handedness(self):
        """"left" or "right" for each hand in the last processed frame, in the same order as `landmarks()`.

        MediaPipe assumes a mirrored (selfie) image, which is what the camera loop feeds it, so the label
        is the side the hand appears on in the window.
        """
        return list(self._handedness)

    def draw(self, frame):
        """Draw 21 landmarks and finger connections for the last processed frame."""
        height, width = frame.shape[:2]
        for hand_landmarks in self._hands_landmarks:
            points = [(int(lm.x * width), int(lm.y * height)) for lm in hand_landmarks]
            for start, end in HAND_CONNECTIONS:
                cv2.line(frame, points[start], points[end], CONNECTION_COLOR, 2)
            for point in points:
                cv2.circle(frame, point, 4, LANDMARK_COLOR, -1)
        return frame

    def close(self):
        self._landmarker.close()
