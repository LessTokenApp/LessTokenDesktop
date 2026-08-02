"""Tests for the logo asset generator. Geometry mirrors LOGO_SPEC.md."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.render_logo import CUT_THRESHOLD, LG, SM, cut_for


def _stroke_bounds(cut):
    """(min_x, max_x, min_y, max_y) of the letterform rects, in grid units."""
    xs = [x for x, _y, _w, _h, _c in cut.strokes]
    ys = [y for _x, y, _w, _h, _c in cut.strokes]
    rights = [x + w for x, _y, w, _h, _c in cut.strokes]
    bottoms = [y + h for _x, y, _w, h, _c in cut.strokes]
    return min(xs), max(rights), min(ys), max(bottoms)


def _stem_to_bar_gap(cut):
    """LOGO_SPEC.md 3.1: distance from the L stem's right edge to the T bar."""
    stem, _foot, bar, _tstem = cut.strokes
    return bar[0] - (stem[0] + stem[2])


def test_ring_stroke_width_per_cut():
    """LOGO_SPEC.md 3.1: the ring is 2 at large, 4.5 at small."""
    assert LG.ring[5] == 2.0
    assert SM.ring[5] == 4.5
    assert LG.ring[5] != SM.ring[5]


def test_letter_stroke_width_per_cut():
    """LOGO_SPEC.md 3.1: letter strokes are 12 at large, 15 at small."""
    assert LG.strokes[0][2] == 12.0
    assert SM.strokes[0][2] == 15.0
    assert LG.strokes[0][2] != SM.strokes[0][2]


def test_stem_to_bar_gap_per_cut():
    """LOGO_SPEC.md 3.1: the small cut tightens the gap from 6 to 4."""
    assert _stem_to_bar_gap(LG) == 6.0
    assert _stem_to_bar_gap(SM) == 4.0
    assert _stem_to_bar_gap(LG) != _stem_to_bar_gap(SM)


def test_content_bounds_per_cut():
    """LOGO_SPEC.md 3.1: the small cut is set wider on the grid."""
    assert _stroke_bounds(LG) == (24.0, 76.0, 25.0, 75.0)
    assert _stroke_bounds(SM) == (22.0, 78.0, 23.0, 77.0)
    assert _stroke_bounds(LG) != _stroke_bounds(SM)


def test_the_two_cuts_are_not_the_same_geometry():
    """The whole point of two cuts: they must actually differ."""
    assert LG.ring != SM.ring
    assert LG.strokes != SM.strokes


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


from PIL import Image, ImageChops

from tools.render_logo import ICO_SIZES, write_ico


def test_ico_contains_every_requested_size(tmp_path):
    path = tmp_path / "icon.ico"
    write_ico(path)
    with Image.open(path) as ico:
        assert sorted(ico.ico.sizes()) == sorted((s, s) for s in ICO_SIZES)


def test_ico_frames_keep_their_own_optical_cut(tmp_path):
    """Each frame must be the cut for its size, not a downsample of the 256."""
    path = tmp_path / "icon.ico"
    write_ico(path)
    with Image.open(path) as ico:
        for size in ICO_SIZES:
            ico.size = (size, size)
            embedded = ico.convert("RGBA")
            expected = render(size, cut_for(size))
            assert ImageChops.difference(embedded, expected).getbbox() is None, (
                f"{size}px frame does not match a direct render of its cut"
            )


def test_ico_accepts_a_reduced_size_set(tmp_path):
    path = tmp_path / "favicon.ico"
    write_ico(path, sizes=(16, 32))
    with Image.open(path) as ico:
        assert sorted(ico.ico.sizes()) == [(16, 16), (32, 32)]


def test_ico_rejects_an_empty_size_set(tmp_path):
    """An empty set used to die on frames[-1] with a bare IndexError."""
    with pytest.raises(ValueError, match="at least one size"):
        write_ico(tmp_path / "icon.ico", sizes=())


def test_ico_rejects_sizes_outside_the_container_limit(tmp_path):
    """Pillow silently drops frames above 256 -- refuse them instead."""
    for bad in ((16, 512), (0,), (-8, 32), (257,)):
        with pytest.raises(ValueError, match="between 1 and 256"):
            write_ico(tmp_path / "icon.ico", sizes=bad)


import xml.etree.ElementTree as ET

from tools.render_logo import GROUND_RADIUS, svg


def test_svg_is_well_formed_and_uses_the_unit_grid():
    root = ET.fromstring(svg())
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.get("viewBox") == "0 0 100 100"


def test_svg_has_ground_ring_and_four_letter_strokes():
    root = ET.fromstring(svg())
    rects = root.findall("{http://www.w3.org/2000/svg}rect")
    assert len(rects) == 6


def test_svg_uses_only_brand_colours():
    root = ET.fromstring(svg())
    used = set()
    for rect in root.findall("{http://www.w3.org/2000/svg}rect"):
        for attr in ("fill", "stroke"):
            value = rect.get(attr)
            if value and value != "none":
                used.add(value.upper())
    assert used == {"#0B2B45", "#06B6D4", "#FFFFFF"}


def test_svg_geometry_matches_the_cut():
    """Regression guard: the emitted numeric geometry must match `cut`.

    The existing SVG tests only check well-formedness, rect count, and
    colour set -- a version of svg() that emitted the ring as x1/y1/x2/y2
    instead of x/y/width/height would still pass all of them. This asserts
    the actual x/y/width/height values against the source Cut.
    """
    ns = "{http://www.w3.org/2000/svg}rect"
    for cut in (LG, SM):
        root = ET.fromstring(svg(cut))
        rects = root.findall(ns)

        ground = rects[0]
        assert float(ground.get("x")) == 0
        assert float(ground.get("y")) == 0
        assert float(ground.get("width")) == 100
        assert float(ground.get("height")) == 100
        assert float(ground.get("rx")) == GROUND_RADIUS

        ring = rects[1]
        rx, ry, rw, rh, radius, stroke = cut.ring
        assert float(ring.get("x")) == rx
        assert float(ring.get("y")) == ry
        assert float(ring.get("width")) == rw
        assert float(ring.get("height")) == rh
        assert float(ring.get("rx")) == radius
        assert float(ring.get("stroke-width")) == stroke

        for rect, (x, y, w, h, _colour) in zip(rects[2:], cut.strokes):
            assert float(rect.get("x")) == x
            assert float(rect.get("y")) == y
            assert float(rect.get("width")) == w
            assert float(rect.get("height")) == h


from tools.render_logo import build


def test_build_writes_every_expected_asset(tmp_path):
    written = build(tmp_path)
    names = {path.relative_to(tmp_path).as_posix() for path in written}
    assert names == {
        "assets/icon.ico",
        "web/public/favicon.ico",
        "web/public/favicon.svg",
        "web/public/apple-touch-icon.png",
    }
    for path in written:
        assert path.exists()
        assert path.stat().st_size > 0


def test_apple_touch_icon_is_full_bleed(tmp_path):
    """iOS masks the icon itself -- a pre-rounded one would round twice."""
    build(tmp_path)
    with Image.open(tmp_path / "web" / "public" / "apple-touch-icon.png") as img:
        assert img.size == (180, 180)
        assert img.convert("RGBA").getpixel((0, 0))[3] == 255


def test_desktop_icon_keeps_all_four_sizes(tmp_path):
    build(tmp_path)
    with Image.open(tmp_path / "assets" / "icon.ico") as ico:
        assert sorted(ico.ico.sizes()) == [(16, 16), (32, 32), (48, 48), (256, 256)]


def test_web_favicon_keeps_only_the_two_tab_sizes(tmp_path):
    """build() must pass the reduced set: a browser tab never needs 48 or 256."""
    build(tmp_path)
    with Image.open(tmp_path / "web" / "public" / "favicon.ico") as ico:
        assert sorted(ico.ico.sizes()) == [(16, 16), (32, 32)]
