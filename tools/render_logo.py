"""Render the LessToken mark to every shipped icon asset.

Geometry is defined on the 100x100 grid documented in LOGO_SPEC.md. The mark is
drawn directly with Pillow rather than rasterised from SVG, so the generator
needs no dependency beyond Pillow, which the project already ships.

Run:  python tools/render_logo.py
"""
from __future__ import annotations

from dataclasses import dataclass

Colour = tuple[int, int, int, int]

NAVY: Colour = (0x0B, 0x2B, 0x45, 255)
CYAN: Colour = (0x06, 0xB6, 0xD4, 255)
WHITE: Colour = (0xFF, 0xFF, 0xFF, 255)

GROUND_RADIUS = 22.0
SUPERSAMPLE = 8
CUT_THRESHOLD = 48


@dataclass(frozen=True)
class Cut:
    """One optical cut of the mark, in 100x100 grid units.

    ring:    (x, y, w, h, corner_radius, stroke_width)
    strokes: (x, y, w, h, colour) in draw order -- L stem, L foot, T bar, T stem
    """

    ring: tuple[float, float, float, float, float, float]
    strokes: tuple[tuple[float, float, float, float, Colour], ...]


LG = Cut(
    ring=(4.0, 4.0, 92.0, 92.0, 18.5, 2.0),
    strokes=(
        (24.0, 25.0, 12.0, 50.0, WHITE),
        (24.0, 63.0, 52.0, 12.0, WHITE),
        (42.0, 25.0, 34.0, 12.0, CYAN),
        (53.0, 25.0, 12.0, 42.0, CYAN),
    ),
)

SM = Cut(
    ring=(5.0, 5.0, 90.0, 90.0, 17.5, 4.5),
    strokes=(
        (22.0, 23.0, 15.0, 54.0, WHITE),
        (22.0, 62.0, 56.0, 15.0, WHITE),
        (41.0, 23.0, 37.0, 15.0, CYAN),
        (52.0, 23.0, 15.0, 44.0, CYAN),
    ),
)


def cut_for(size: int) -> Cut:
    """Pick the optical cut appropriate to a pixel size."""
    return SM if size < CUT_THRESHOLD else LG
