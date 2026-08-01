"""Render the LessToken mark to every shipped icon asset.

Geometry is defined on the 100x100 grid documented in LOGO_SPEC.md. The mark is
drawn directly with Pillow rather than rasterised from SVG, so the generator
needs no dependency beyond Pillow, which the project already ships.

Run:  python tools/render_logo.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

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


def render(
    size: int,
    cut: Cut | None = None,
    ground_radius: float | None = None,
) -> Image.Image:
    """Draw the mark at `size` pixels square.

    Drawn at SUPERSAMPLE x and downsampled with LANCZOS -- Pillow's own
    rounded_rectangle antialiasing is too coarse at favicon sizes.

    Pass ground_radius=0.0 for a full-bleed square (iOS applies its own mask,
    so a pre-rounded apple-touch-icon would be rounded twice).
    """
    if cut is None:
        cut = cut_for(size)
    if ground_radius is None:
        ground_radius = GROUND_RADIUS

    n = size * SUPERSAMPLE
    k = n / 100.0
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([0, 0, n - 1, n - 1], radius=ground_radius * k, fill=NAVY)

    rx, ry, rw, rh, radius, stroke = cut.ring
    draw.rounded_rectangle(
        [rx * k, ry * k, (rx + rw) * k - 1, (ry + rh) * k - 1],
        radius=radius * k,
        outline=CYAN,
        width=max(1, round(stroke * k)),
    )

    for x, y, w, h, colour in cut.strokes:
        draw.rectangle([x * k, y * k, (x + w) * k - 1, (y + h) * k - 1], fill=colour)

    return img.resize((size, size), Image.LANCZOS)


ICO_SIZES: tuple[int, ...] = (16, 32, 48, 256)


def write_ico(path: Path, sizes: tuple[int, ...] = ICO_SIZES) -> None:
    """Write a multi-resolution .ico, each frame using its own optical cut.

    Pillow's `sizes=` argument alone would downsample a single base image and
    lose the small cut. `append_images` embeds distinct frames, so the 16 and 32
    keep SM while 48 and 256 keep LG.
    """
    ordered = sorted(sizes)
    frames = [render(size) for size in ordered]
    frames[-1].save(
        path,
        format="ICO",
        sizes=[(size, size) for size in ordered],
        append_images=frames[:-1],
    )


def _hex(colour: Colour) -> str:
    return "#%02X%02X%02X" % colour[:3]


def svg(cut: Cut = SM) -> str:
    """Emit the mark as a standalone SVG document.

    Defaults to the small cut: the only SVG we ship is the web favicon, which
    browsers render in a tab strip at well under 48px.
    """
    rx, ry, rw, rh, radius, stroke = cut.ring
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">',
        f'  <rect x="0" y="0" width="100" height="100" '
        f'rx="{GROUND_RADIUS:g}" fill="{_hex(NAVY)}"/>',
        f'  <rect x="{rx:g}" y="{ry:g}" width="{rw:g}" height="{rh:g}" '
        f'rx="{radius:g}" fill="none" stroke="{_hex(CYAN)}" '
        f'stroke-width="{stroke:g}"/>',
    ]
    for x, y, w, h, colour in cut.strokes:
        lines.append(
            f'  <rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'fill="{_hex(colour)}"/>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


ROOT = Path(__file__).resolve().parent.parent

APPLE_TOUCH_SIZE = 180


def build(root: Path) -> list[Path]:
    """Write every shipped asset under `root`. Returns the paths written."""
    assets = root / "assets"
    public = root / "web" / "public"
    assets.mkdir(parents=True, exist_ok=True)
    public.mkdir(parents=True, exist_ok=True)

    desktop_icon = assets / "icon.ico"
    web_icon = public / "favicon.ico"
    web_svg = public / "favicon.svg"
    apple_icon = public / "apple-touch-icon.png"

    write_ico(desktop_icon)
    write_ico(web_icon, sizes=(16, 32))
    web_svg.write_text(svg(), encoding="utf-8")
    render(APPLE_TOUCH_SIZE, ground_radius=0.0).save(apple_icon)

    return [desktop_icon, web_icon, web_svg, apple_icon]


def main() -> None:
    for path in build(ROOT):
        print(f"wrote {path.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
