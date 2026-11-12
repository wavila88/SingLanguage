from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_FILES = ("segoeui.ttf", "arial.ttf")
BOLD_FONT_FILES = ("seguisb.ttf", "arialbd.ttf")
FONT_SIZE = 22
WHITE = (255, 255, 255)


@lru_cache(maxsize=None)
def _font(size, bold=False):
    for name in (BOLD_FONT_FILES if bold else FONT_FILES):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def draw_text(frame, text, origin, color=WHITE, size=FONT_SIZE, anchor="ls", bold=False):
    """Draw `text` in place on a BGR frame; `origin` is the left end of the baseline
    (anchor "ls") or the center of the text (anchor "mm").

    Unlike cv2.putText, this renders ñ and accented letters.
    """
    font = _font(size, bold)
    # Only the text's own region goes through Pillow; converting the whole frame per text is too slow.
    left, top, right, bottom = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox(origin, text, font=font, anchor=anchor)
    left, top = max(int(left) - 2, 0), max(int(top) - 2, 0)
    right, bottom = min(int(right) + 3, frame.shape[1]), min(int(bottom) + 3, frame.shape[0])
    if right <= left or bottom <= top:
        return frame
    region = frame[top:bottom, left:right]
    image = Image.fromarray(region[:, :, ::-1])
    ImageDraw.Draw(image).text((origin[0] - left, origin[1] - top), text, font=font, fill=color[::-1], anchor=anchor)
    region[:] = np.asarray(image)[:, :, ::-1]
    return frame


def text_width(text, size, bold=False):
    return round(_font(size, bold).getlength(text))
