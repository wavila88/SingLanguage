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
    image = Image.fromarray(frame[:, :, ::-1])
    ImageDraw.Draw(image).text(origin, text, font=_font(size, bold), fill=color[::-1], anchor=anchor)
    frame[:] = np.asarray(image)[:, :, ::-1]
    return frame
