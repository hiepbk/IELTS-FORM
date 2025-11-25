#!/usr/bin/env python3
"""Generate a simple IELTS icon PNG using Tkinter's PhotoImage."""

import os
import tkinter as tk

SIZE = 96
PADDING = 18
OUTPUT_NAME = "ielts_icon.png"


def draw_background(photo: tk.PhotoImage) -> None:
    """Fill with vertical gradient."""
    top_color = (74, 118, 255)
    bottom_color = (33, 63, 153)
    for y in range(SIZE):
        ratio = y / (SIZE - 1)
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        photo.put(color, to=(0, y, SIZE, y + 1))


def draw_letters(photo: tk.PhotoImage) -> None:
    """Draw simple blocky 'L' and 'R' letters for Listening/Reading."""
    fg = "#ffffff"
    # L shape
    l_left = PADDING
    l_right = l_left + 12
    l_bottom = SIZE - PADDING
    photo.put(fg, to=(l_left, PADDING, l_right, l_bottom))
    photo.put(fg, to=(l_left, l_bottom - 10, SIZE // 2 - PADDING, l_bottom))

    # R vertical stem
    stem_left = SIZE // 2 + 4
    stem_right = stem_left + 12
    photo.put(fg, to=(stem_left, PADDING, stem_right, SIZE - PADDING))

    # R top bowl
    bowl_top = PADDING
    bowl_bottom = bowl_top + 24
    bowl_right = SIZE - PADDING
    photo.put(fg, to=(stem_right, bowl_top, bowl_right, bowl_top + 10))
    photo.put(fg, to=(stem_right, bowl_bottom - 10, bowl_right, bowl_bottom))
    photo.put(fg, to=(bowl_right - 10, bowl_top, bowl_right, bowl_bottom))

    # R leg
    leg_top = bowl_bottom - 6
    leg_right = bowl_right
    leg_width = 18
    photo.put(
        fg,
        to=(
            leg_right - leg_width,
            leg_top,
            leg_right,
            leg_top + 12,
        ),
    )


def save_icon(path: str) -> None:
    root = tk.Tk()
    root.withdraw()
    photo = tk.PhotoImage(width=SIZE, height=SIZE)
    draw_background(photo)
    draw_letters(photo)
    photo.write(path, format="png")
    root.destroy()


def main() -> None:
    target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_NAME)
    save_icon(target_path)
    print(f"Icon generated at {target_path}")


if __name__ == "__main__":
    main()

