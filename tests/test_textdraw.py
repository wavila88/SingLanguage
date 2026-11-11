import numpy as np

from textdraw import draw_text


def _render(text, color=(255, 255, 255)):
    frame = np.zeros((40, 300, 3), dtype=np.uint8)
    draw_text(frame, text, (5, 30), color)
    return frame


def test_draw_text_paints_the_frame_in_place():
    assert _render("hola").any()


def test_accented_vowels_and_enie_are_drawn_as_themselves():
    assert not np.array_equal(_render("ó"), _render("o"))
    assert not np.array_equal(_render("ñ"), _render("n"))
    assert not np.array_equal(_render("ó"), _render("?"))
    assert not np.array_equal(_render("ó"), _render("ñ"))


def test_color_is_blue_green_red_like_the_rest_of_opencv():
    frame = _render("I", color=(0, 0, 255))

    assert frame[:, :, 2].max() > 0
    assert frame[:, :, 0].max() == 0
    assert frame[:, :, 1].max() == 0


def test_text_can_be_centered_on_its_origin():
    frame = np.zeros((60, 300, 3), dtype=np.uint8)

    draw_text(frame, "Expresión estática", (150, 30), anchor="mm")

    columns = np.where(frame.any(axis=(0, 2)))[0]
    rows = np.where(frame.any(axis=(1, 2)))[0]
    assert abs((columns.min() + columns.max()) / 2 - 150) <= 3
    assert abs((rows.min() + rows.max()) / 2 - 30) <= 8
