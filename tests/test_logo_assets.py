"""Tests for the logo asset generator. Geometry mirrors LOGO_SPEC.md."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.render_logo import CUT_THRESHOLD, LG, SM, cut_for


def test_cut_for_selects_small_below_threshold():
    assert cut_for(16) is SM
    assert cut_for(32) is SM
    assert cut_for(CUT_THRESHOLD - 1) is SM


def test_cut_for_selects_large_at_and_above_threshold():
    assert cut_for(CUT_THRESHOLD) is LG
    assert cut_for(180) is LG
    assert cut_for(256) is LG


def _right_edge(rect):
    x, _y, w, _h, _colour = rect
    return x + w


def test_foot_ends_flush_with_bar():
    """LOGO_SPEC.md 3.4 constraint 2: foot and bar share a right edge."""
    for cut in (LG, SM):
        _stem, foot, bar, _tstem = cut.strokes
        assert _right_edge(foot) == _right_edge(bar)


def test_t_stem_bites_into_l_foot():
    """LOGO_SPEC.md 3.4 constraint 1: the stem descends past the foot's top."""
    for cut, expected_bite in ((LG, 4.0), (SM, 5.0)):
        _stem, foot, _bar, tstem = cut.strokes
        foot_top = foot[1]
        tstem_bottom = tstem[1] + tstem[3]
        assert tstem_bottom - foot_top == expected_bite


def test_t_stem_stays_within_the_foot():
    """The stem must cross the foot, not overhang its terminal."""
    for cut in (LG, SM):
        _stem, foot, _bar, tstem = cut.strokes
        assert foot[0] < tstem[0]
        assert _right_edge(tstem) < _right_edge(foot)


from tools.render_logo import CYAN, NAVY, WHITE, render


def test_render_returns_requested_size():
    for size in (16, 32, 48, 180, 256):
        img = render(size)
        assert img.size == (size, size)
        assert img.mode == "RGBA"


def test_render_corner_is_transparent_when_rounded():
    """The rounded ground must leave the canvas corner empty."""
    img = render(256)
    assert img.getpixel((0, 0))[3] == 0


def test_render_corner_is_opaque_when_square():
    """ground_radius=0 gives a full-bleed square for apple-touch-icon."""
    img = render(180, ground_radius=0.0)
    assert img.getpixel((0, 0))[3] == 255


def test_render_centre_uses_only_brand_colours():
    """Sample the L stem, the T bar and the ground; no stray colours.

    Sample points sit well inside their shapes, but LANCZOS can overshoot
    slightly near edges, so allow a small per-channel tolerance rather than
    asserting exact equality.
    """
    img = render(256).convert("RGBA")
    scale = 256 / 100.0
    samples = {
        "l_stem": ((30 * scale, 40 * scale), WHITE),
        "t_bar": ((60 * scale, 30 * scale), CYAN),
        "ground": ((50 * scale, 85 * scale), NAVY),
    }
    for name, ((x, y), expected) in samples.items():
        actual = img.getpixel((int(x), int(y)))
        drift = max(abs(a - e) for a, e in zip(actual, expected))
        assert drift <= 2, f"{name} was {actual}, expected ~{expected}"
