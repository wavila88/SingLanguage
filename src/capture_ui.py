"""State and layout of the capture window's screens (menu, name input, open expression).

Pure logic, no drawing: `camera.py` draws what this module describes. Rectangles are
(x0, y0, x1, y1) in video-frame pixels, scaled from the 640 x 480 reference of the design.
"""
from bisect import bisect_right

from dataset import hand_record
from widgets import BUTTON_HEIGHT, BUTTON_MARGIN, REFERENCE_WIDTH

MODE_BUTTONS = ("Expresión estática", "Expresión en movimiento")
MODE_KEYS = ("static", "motion")
MODE_NAMES = {"static": "estática", "motion": "en movimiento"}
MODE_TITLES = dict(zip(MODE_KEYS, MODE_BUTTONS))

NO_HAND_MESSAGE = "No se capturó: no se detectó ninguna mano"
DISCARDED_MESSAGE = "Muestra descartada"
DEFAULT_FRAME_MS = 33  # replay length of the last frame when the recording has a single frame

KEY_BACKSPACE = 8
KEY_ENTER = (10, 13)
SPACE = 32

CARD_HEIGHT = 216
BACK_WIDTH = 120
CHIP_HEIGHT = 36


def _scaled(width, *values):
    scale = width / REFERENCE_WIDTH
    return [round(value * scale) for value in values]


def menu_layout(width, height):
    margin, button_height = _scaled(width, BUTTON_MARGIN, BUTTON_HEIGHT)
    button_width = (width - 3 * margin) // 2
    top = height - margin - button_height
    return {
        key: (margin + index * (button_width + margin), top, margin + index * (button_width + margin) + button_width,
              top + button_height)
        for index, key in enumerate(MODE_KEYS)
    }


def name_layout(width, height):
    margin, button_height, card_height, pad = _scaled(width, BUTTON_MARGIN, BUTTON_HEIGHT, CARD_HEIGHT, 16)
    card_top = height - margin - card_height
    left, right = margin, width - margin
    field_top = card_top + _scaled(width, 72)[0]
    buttons_top = card_top + card_height - pad - button_height
    half = (right - left - 3 * pad) // 2
    return {
        "card": (left, card_top, right, height - margin),
        "title": (left + pad, card_top + _scaled(width, 28)[0]),
        "label": (left + pad, card_top + _scaled(width, 58)[0]),
        "field": (left + pad, field_top, right - pad, field_top + button_height),
        "hint": (left + pad, card_top + _scaled(width, 138)[0]),
        "back": (left + pad, buttons_top, left + pad + half, buttons_top + button_height),
        "accept": (left + 2 * pad + half, buttons_top, left + 2 * pad + 2 * half, buttons_top + button_height),
    }


def expression_layout(width, height):
    margin, button_height, back_width, chip_height = _scaled(width, BUTTON_MARGIN, BUTTON_HEIGHT, BACK_WIDTH, CHIP_HEIGHT)
    top = height - margin - button_height
    return {
        "chip": (margin, margin, width - margin, margin + chip_height),
        "back": (margin, top, margin + back_width, top + button_height),
        "capture": (2 * margin + back_width, top, width - margin, top + button_height),
        "stop": (margin, top, width - margin, top + button_height),
        "message": (margin, 2 * margin + chip_height, width - margin, 2 * margin + 2 * chip_height),
    }


def review_layout(width, height):
    """Aprobar and No aprobar side by side on the bottom strip, like the menu buttons."""
    margin, button_height = _scaled(width, BUTTON_MARGIN, BUTTON_HEIGHT)
    button_width = (width - 3 * margin) // 2
    top = height - margin - button_height
    return {
        "discard": (margin, top, margin + button_width, top + button_height),
        "approve": (2 * margin + button_width, top, 2 * margin + 2 * button_width, top + button_height),
    }


def _inside(rect, x, y):
    return rect[0] <= x < rect[2] and rect[1] <= y < rect[3]


class CaptureUI:
    """Which screen the capture window is on and what clicks and keys do on it."""

    def __init__(self, repository):
        self._repository = repository
        self.screen = "menu"
        self.mode = None
        self.name = ""
        self.expression = None
        self.count = 0
        self.live_hands = []  # (side, landmarks) of the frame being shown; the camera loop refreshes it
        self.captured = []
        self.frozen = None  # the captured video frame, set by the camera loop while reviewing
        self.message = ""
        self.now = 0.0  # seconds, refreshed by the camera loop once per frame
        self.recording = []  # {"ms", "hands", "image"} for every frame since "Grabar", hand or not
        self.record_start = 0.0
        self.replay_start = 0.0

    def click(self, x, y, width, height):
        if self.screen == "menu":
            for mode, rect in menu_layout(width, height).items():
                if _inside(rect, x, y):
                    self.mode, self.name, self.screen = mode, "", "name"
        elif self.screen == "name":
            layout = name_layout(width, height)
            if _inside(layout["back"], x, y):
                self.screen = "menu"
            elif _inside(layout["accept"], x, y):
                self._accept()
        elif self.screen == "expression":
            layout = expression_layout(width, height)
            if _inside(layout["back"], x, y):
                self.screen, self.message = "menu", ""
            elif self.mode == "static" and _inside(layout["capture"], x, y):
                if self.live_hands:
                    self.captured, self.message, self.screen = list(self.live_hands), "", "review"
                else:
                    self.message = NO_HAND_MESSAGE
            elif self.mode == "motion" and _inside(layout["capture"], x, y):
                self.recording, self.record_start, self.message, self.screen = [], self.now, "", "recording"
        elif self.screen == "recording":
            if _inside(expression_layout(width, height)["stop"], x, y):
                self.replay_start, self.screen = self.now, "review"
        elif self.screen == "review":
            layout = review_layout(width, height)
            if _inside(layout["approve"], x, y):
                self._approve()
            elif _inside(layout["discard"], x, y):
                self._discard()

    def key(self, code):
        if self.screen != "name" or code < 0:
            return
        if code == KEY_BACKSPACE:
            self.name = self.name[:-1]
        elif code in KEY_ENTER:
            self._accept()
        elif code == SPACE or chr(code).isalnum():
            self.name += chr(code)

    def record(self, image):
        """Keep the video frame being shown, with the hands seen in it, while recording."""
        ms = round((self.now - self.record_start) * 1000)
        self.recording.append({"ms": ms, "hands": list(self.live_hands), "image": image})

    @property
    def elapsed(self):
        return self.now - self.record_start

    def review_image(self):
        """The frame to show while reviewing: the frozen capture, or the recording replayed in a loop."""
        if self.mode == "static":
            return self.frozen
        times = [frame["ms"] for frame in self.recording]
        gap = times[-1] / (len(times) - 1) if len(times) > 1 else DEFAULT_FRAME_MS
        position = (self.now - self.replay_start) * 1000 % max(times[-1] + gap, 1)
        return self.recording[max(bisect_right(times, position) - 1, 0)]["image"]

    def _discard(self):
        self.message = DISCARDED_MESSAGE
        self.captured, self.recording, self.frozen, self.screen = [], [], None, "expression"

    def _approve(self):
        if self.mode == "motion":
            self._approve_motion()
            return
        hands = [hand_record(side, landmarks) for side, landmarks in self.captured]
        self._repository.save_static_sample(self.expression, hands)
        self.count += 1
        noun = "mano" if len(hands) == 1 else "manos"
        self.message = f"Guardada muestra: {self.expression.upper()} ({len(hands)} {noun})"
        self.captured, self.frozen, self.screen = [], None, "expression"

    def _approve_motion(self):
        with_hands = [frame for frame in self.recording if frame["hands"]]
        frames = [
            {"index": index, "ms": frame["ms"],
             "hands": [hand_record(side, landmarks) for side, landmarks in frame["hands"]]}
            for index, frame in enumerate(with_hands)
        ]
        self._repository.save_motion_sample(self.expression, frames)
        self.count += 1
        noun = "frame" if len(frames) == 1 else "frames"
        self.message = f"Guardada secuencia: {self.expression.upper()} ({len(frames)} {noun})"
        self.recording, self.screen = [], "expression"

    def _accept(self):
        if not self.name.strip():
            return
        self.count = self._repository.open_expression(self.name, self.mode)
        self.expression, self.screen = self.name, "expression"

    @property
    def title(self):
        return MODE_TITLES[self.mode]

    @property
    def chip_text(self):
        noun = "muestra" if self.count == 1 else "muestras"
        return f"{self.expression.upper()} · {MODE_NAMES[self.mode]} · {self.count} {noun}"
