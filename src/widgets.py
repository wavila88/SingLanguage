import numpy as np
from PIL import Image, ImageDraw

# Palette from the Figma "Sistema de interfaz · LSC" (spec 006, design/interfaz-lsc.png). RGB + alpha.
STRIP_FILL = (16, 28, 40, 245)
PRIMARY_FILL = (143, 228, 206, 255)
PRIMARY_BORDER = (183, 243, 228, 166)
PRIMARY_TEXT = (16, 45, 40)  # RGB
PRIMARY_DISABLED_FILL = (37, 54, 62, 255)
SECONDARY_BORDER = (143, 228, 206, 255)
FIELD_BORDER = (183, 243, 228, 102)
FIELD_BORDER_FOCUS = (143, 228, 206, 255)
FIELD_FILL = (16, 28, 40, 255)
TEXT = (232, 246, 242)  # RGB
TEXT_SECONDARY = (160, 178, 184)  # RGB
CARD_RADIUS = 16

# Sizes at the 640 x 480 reference of the design; everything is scaled by frame width / 640.
REFERENCE_WIDTH = 640
STRIP_HEIGHT = 96
BUTTON_HEIGHT = 48
BUTTON_MARGIN = 16
BUTTON_RADIUS = 12
BUTTON_TEXT_SIZE = 20


def scale_for(frame):
    return frame.shape[1] / REFERENCE_WIDTH


def draw_rounded_rect(frame, top_left, bottom_right, fill, outline=None, radius=0):
    """Blend a rounded rectangle (RGBA fill and outline) in place on a BGR frame."""
    x0, y0 = top_left
    x1, y1 = max(bottom_right[0] - 1, x0), max(bottom_right[1] - 1, y0)
    image = Image.fromarray(frame[:, :, ::-1]).convert("RGBA")
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        (x0, y0, x1, y1), radius=min(radius, (y1 - y0) // 2), fill=fill, outline=outline, width=2)
    frame[:] = np.asarray(Image.alpha_composite(image, layer).convert("RGB"))[:, :, ::-1]
    return frame


def draw_strip(frame, height=STRIP_HEIGHT):
    """Translucent strip along the bottom edge that holds the controls."""
    scaled = round(height * scale_for(frame))
    return draw_rounded_rect(frame, (0, frame.shape[0] - scaled), (frame.shape[1], frame.shape[0]), STRIP_FILL)


def draw_primary_button(frame, top_left, bottom_right, scale=1.0):
    """Button shape only; the caller draws the label (PRIMARY_TEXT, bold, BUTTON_TEXT_SIZE) at its center."""
    return draw_rounded_rect(frame, top_left, bottom_right, PRIMARY_FILL, PRIMARY_BORDER, round(BUTTON_RADIUS * scale))


def draw_primary_disabled_button(frame, top_left, bottom_right, scale=1.0):
    return draw_rounded_rect(frame, top_left, bottom_right, PRIMARY_DISABLED_FILL, None, round(BUTTON_RADIUS * scale))


def draw_secondary_button(frame, top_left, bottom_right, scale=1.0):
    """Outline-only button; the caller draws the label in TEXT."""
    return draw_rounded_rect(frame, top_left, bottom_right, (0, 0, 0, 0), SECONDARY_BORDER, round(BUTTON_RADIUS * scale))


def draw_field(frame, top_left, bottom_right, scale=1.0, focused=False):
    """Text input box; the caller draws the text."""
    border = FIELD_BORDER_FOCUS if focused else FIELD_BORDER
    return draw_rounded_rect(frame, top_left, bottom_right, FIELD_FILL, border, round(BUTTON_RADIUS * scale))


def draw_card(frame, top_left, bottom_right, scale=1.0):
    """Translucent rounded panel that holds a form."""
    return draw_rounded_rect(frame, top_left, bottom_right, STRIP_FILL, None, round(CARD_RADIUS * scale))
