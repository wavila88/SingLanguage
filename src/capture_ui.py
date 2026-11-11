"""State and layout of the capture window's screens (menu, name input, open expression).

Pure logic, no drawing: `camera.py` draws what this module describes. Rectangles are
(x0, y0, x1, y1) in video-frame pixels, scaled from the 640 x 480 reference of the design.
"""
from widgets import BUTTON_HEIGHT, BUTTON_MARGIN, REFERENCE_WIDTH

MODE_BUTTONS = ("Expresión estática", "Expresión en movimiento")
MODE_KEYS = ("static", "motion")
MODE_NAMES = {"static": "estática", "motion": "en movimiento"}
MODE_TITLES = dict(zip(MODE_KEYS, MODE_BUTTONS))

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
            if _inside(expression_layout(width, height)["back"], x, y):
                self.screen = "menu"

    def key(self, code):
        if self.screen != "name" or code < 0:
            return
        if code == KEY_BACKSPACE:
            self.name = self.name[:-1]
        elif code in KEY_ENTER:
            self._accept()
        elif code == SPACE or chr(code).isalnum():
            self.name += chr(code)

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
