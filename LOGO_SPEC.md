# LessToken Logo Mark — Design Spec

Status: **approved and implemented**. `tools/render_logo.py` is the generator — it
renders every asset in §6 from the geometry in §3. This document is the source of truth
for that geometry: change the spec first, then regenerate with `python tools/render_logo.py`.

## 1. Concept

A rounded-square app mark holding an interlocked **L** and **T**. The L is white and
structural; the T is cyan and sits on top of it. A thin cyan ring runs just inside the
edge so the mark keeps a defined boundary on both light cards and dark footers.

Decisions this locks in:

| Decision | Choice | Why |
| --- | --- | --- |
| Container | Rounded square, `rx` 22% | Modern app-icon standard; holds up better than a circle below 32px |
| Letterform | Interlocked (*kenetli*) — T's stem descends into L's foot | More character than side-by-side; the two letters share a joint |
| Ground | Dark navy `#0B2B45` | Reads as a deliberate ground, not a default black |
| Accent | Cyan T `#06B6D4` | Two-colour mark; the T is the letter that carries the accent |
| Boundary | Thin cyan ring `#06B6D4` | Keeps the navy square from dissolving into a dark footer |

## 2. Colour

**One cyan only.** `#06B6D4` is taken directly from the brand gradient
`linear-gradient(135deg, #0369a1 0%, #06b6d4 100%)`, which appears 12 times across the
lesstoken-landing repo — the most-used gradient on the site. The T and the ring share it.

| Role | Hex | Applied to |
| --- | --- | --- |
| Ground | `#0B2B45` | Rounded-square fill |
| Accent (T) | `#06B6D4` | T bar + T stem |
| Letter (L) | `#FFFFFF` | L stem + L foot |
| Ring | `#06B6D4` | Inset rounded-rect stroke |

The mark is a fixed asset: **it does not respond to light/dark mode.** The same three
values ship in every context. The ring is what makes that safe.

Contrast of `#06B6D4` on `#0B2B45` is **6.0 : 1**, well above the 3:1 WCAG threshold for
non-text graphics. A brighter cyan (`#4FD8F0`, 8.6:1) was considered and rejected: exact
brand match was judged more valuable than extra punch at 16px, a size the mark is already
documented as pushing (§5).

## 3. Geometry

All coordinates are on a **100 × 100 grid**, rendered at `viewBox="0 0 100 100"`.
Letterform rects are square-cornered (`rx=0`) — sharp terminals survive downscaling
better than rounded ones.

### 3.1 Two optical variants

This is the core of the spec. The mark is **not one file scaled** — a single ring weight
either looks heavy at 96px or vanishes at 32px. Two cuts:

| | `lt-lg` | `lt-sm` |
| --- | --- | --- |
| Use at | **48px and up** | **below 48px** |
| Ring stroke | 2 | 4.5 |
| Letter stroke | 12 | 15 |
| L-stem → T-bar gap | 6 | 4 |
| Content bounds | x 24–76, y 25–75 | x 22–78, y 23–77 |

The small cut is heavier and tighter: thicker strokes so the letters hold, a narrower
gap so the pair reads as one unit rather than two drifting shapes.

### 3.2 `lt-lg` — 48px and up

| Element | x | y | w | h | Fill |
| --- | --- | --- | --- | --- | --- |
| Ground | 0 | 0 | 100 | 100 | `#0B2B45`, `rx=22` |
| Ring | 4 | 4 | 92 | 92 | none, stroke `#06B6D4` @ 2, `rx=18.5` |
| L stem | 24 | 25 | 12 | 50 | `#FFFFFF` |
| L foot | 24 | 63 | 52 | 12 | `#FFFFFF` |
| T bar | 42 | 25 | 34 | 12 | `#06B6D4` |
| T stem | 53 | 25 | 12 | 42 | `#06B6D4` |

### 3.3 `lt-sm` — below 48px

| Element | x | y | w | h | Fill |
| --- | --- | --- | --- | --- | --- |
| Ground | 0 | 0 | 100 | 100 | `#0B2B45`, `rx=22` |
| Ring | 5 | 5 | 90 | 90 | none, stroke `#06B6D4` @ 4.5, `rx=17.5` |
| L stem | 22 | 23 | 15 | 54 | `#FFFFFF` |
| L foot | 22 | 62 | 56 | 15 | `#FFFFFF` |
| T bar | 41 | 23 | 37 | 15 | `#06B6D4` |
| T stem | 52 | 23 | 15 | 44 | `#06B6D4` |

### 3.4 The interlock

Three constraints define the joint. Any change to the letterforms must preserve them:

1. **The T's stem descends past the top of the L's foot** — 4 units in `lt-lg`,
   5 in `lt-sm`. Flush contact reads as two stacked shapes; the bite reads as a joint.
2. **The L's foot ends flush with the T's bar.** Both terminate at x=76 (`lt-lg`) /
   x=78 (`lt-sm`), so the mark closes on a single right-hand edge.

   This was corrected after rasterising at 256px. The first draft ended the foot at 68 —
   only 3 units past the T's stem — which rendered as a stray white nub rather than a
   deliberate terminal. Running the foot out to meet the bar reads as designed. Any
   future change to the foot's width must keep this alignment.
3. **No keyline separates them.** Colour alone does the separation. A navy keyline thin
   enough to look right at 96px would disappear by 32px, so it is deliberately absent.

Draw order: ground → ring → L (white) → T (cyan). The cyan sits on top.

## 4. Source

### `lt-lg`

```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="100" height="100" rx="22" fill="#0B2B45"/>
  <rect x="4" y="4" width="92" height="92" rx="18.5" fill="none" stroke="#06B6D4" stroke-width="2"/>
  <rect x="24" y="25" width="12" height="50" fill="#FFFFFF"/>
  <rect x="24" y="63" width="52" height="12" fill="#FFFFFF"/>
  <rect x="42" y="25" width="34" height="12" fill="#06B6D4"/>
  <rect x="53" y="25" width="12" height="42" fill="#06B6D4"/>
</svg>
```

### `lt-sm`

```svg
<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="100" height="100" rx="22" fill="#0B2B45"/>
  <rect x="5" y="5" width="90" height="90" rx="17.5" fill="none" stroke="#06B6D4" stroke-width="4.5"/>
  <rect x="22" y="23" width="15" height="54" fill="#FFFFFF"/>
  <rect x="22" y="62" width="56" height="15" fill="#FFFFFF"/>
  <rect x="41" y="23" width="37" height="15" fill="#06B6D4"/>
  <rect x="52" y="23" width="15" height="44" fill="#06B6D4"/>
</svg>
```

## 5. Usage

**Clear space** — keep free space equal to 12.5% of the mark's width (the ground's corner
radius ÷ 2) on all four sides. At 40px that is 5px.

**Minimum sizes**

| Size | Verdict |
| --- | --- |
| 32px and up | Full mark. Both letters and the interlock read. |
| 16px | **At its limit.** The ring survives and the two letters stay distinguishable, but the interlock detail is gone — it reads as an abstract cyan-and-white glyph. Acceptable for a browser tab. |
| Below 16px | Not supported. |

If a true sub-16px asset is ever needed, drop the ring entirely and let the navy square
carry the edge, rather than shrinking the current cut further.

**Don't**

- Don't scale `lt-lg` below 48px, or `lt-sm` above it.
- Don't recolour the ground, the ring, or either letter.
- Don't add a drop shadow, gradient, or glow — the mark is flat.
- Don't place the mark on a mid-tone cyan or navy background; the ring stops working.
- Don't rotate, skew, or condense.

## 6. Export list

Mapped to the files that actually consume an icon in this repo today.

| Asset | Cut | Consumer |
| --- | --- | --- |
| `assets/icon.ico` (16, 32, 48, 256) | `lt-sm` for 16/32, `lt-lg` for 48/256 | `src/aiclipboardoptimizer/gui.py:24` `_icon_path()` → `iconbitmap` at lines 141, 189; and `.github/workflows/build-release.yml:33` (`--icon`, `--add-data`) |
| `web/public/favicon.svg` | `lt-sm` | `web/index.html:5` `<link rel="icon" type="image/svg+xml">` |
| `web/public/favicon.ico` (16, 32) | `lt-sm` | `web/index.html:6` `<link rel="alternate icon">` — fallback for browsers without SVG favicon support |
| `web/public/apple-touch-icon.png` (180) | `lt-lg` | `web/index.html:7` `<link rel="apple-touch-icon">` — iOS home screen |

All three web assets exist under `web/public/` and `web/index.html` points at them; the
Vite placeholder `/vite.svg` is no longer referenced. Because the SVG and the ICO are the
same asset served to the same tab, one declared as the other's fallback, the rasteriser
matches SVG stroke semantics: SVG centres a stroke on the path, so `render()` expands the
ring's bounding box by half a stroke to compensate for Pillow stroking inward.

`installer.nsi` needs no change — it sets `DisplayIcon` to `$INSTDIR\LessToken.exe`
(line 45) and has no `MUI_ICON`, so it inherits whatever PyInstaller embeds.

## 7. Open questions

1. ~~**Brand token divergence.**~~ **Resolved** — the mark uses `#06B6D4`, taken from the
   landing site's dominant gradient. See §2.
2. **Brand token, follow-up.** Neither `web/tailwind.config.js` nor
   `lesstoken-landing/tailwind.config.js` declares a cyan today — both set `primary` to
   `#3B82F6` (blue), even though the landing site's own gradient is cyan. Adding
   `brand: '#06B6D4'` to both would make the mark and the UI share one source of truth.
   Out of scope for this spec; worth its own change.
3. **Wordmark.** This spec covers the mark only. Is a lockup — mark + "LessToken" set in
   a chosen typeface — in scope, or is the mark standalone for now?
4. **Marketing site favicon.** lesstoken.app is a separate repo
   (`C:\Projects\lesstoken-landing`). The export list in §6 covers this repo only.
   Confirm whether the landing site's favicon is tracked here or separately.
