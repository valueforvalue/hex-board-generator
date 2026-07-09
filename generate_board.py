#!/usr/bin/env python3
"""
Generate a printable HEX board PDF sized to fit a given paper and (optionally)
optimized for a specific Go-stone diameter.

Geometry: pointy-top hexes in odd-r offset layout.
  - Hex width  = sqrt(3) * r
  - Hex height = 2 * r
  - Grid width  = r * sqrt(3) * (1.5*(N-1) + 1)
  - Grid height = r * (1.5*(N-1) + 2)
"""
import argparse
import math
import sys
from reportlab.lib.pagesizes import letter, legal, A3, A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas


SQRT3 = math.sqrt(3)
MM_PER_INCH = 25.4
PT_PER_INCH = 72


# Paper sizes in points (width, height), portrait orientation.
PAPER_SIZES = {
    "letter":  letter,           # 8.5 x 11 in
    "legal":   legal,            # 8.5 x 14 in
    "tabloid": (11 * 72, 17 * 72),  # 11 x 17 in (Ledger)
    "ledger":  (11 * 72, 17 * 72),  # alias
    "a4":      A4,               # 8.27 x 11.69 in
    "a3":      A3,               # 11.69 x 16.54 in
    "ansi-b":  (17 * 72, 22 * 72),  # 17 x 22 in
}

# Default margin per paper (points). Tighter on small paper to maximize hex size.
DEFAULT_MARGINS_PT = {
    "letter":  18,   # 0.25 in
    "legal":   24,   # 0.33 in
    "tabloid": 36,   # 0.5 in
    "ledger":  36,
    "a4":      24,
    "a3":      36,
    "ansi-b":  54,   # 0.75 in
}

# Sort papers by area ascending for auto-recommendation.
PAPERS_BY_AREA = sorted(PAPER_SIZES.items(), key=lambda kv: kv[1][0] * kv[1][1])


# Visual themes control cell fill colors, grid stroke, and side band colors.
# Each theme returns: (fill_a, fill_b, grid_stroke, white_band, black_band, page_bg)
THEMES = {
    "classic": {
        "fill_a":   "#FAFAFA",
        "fill_b":   "#F2F2F2",
        "stroke":   "#7F8C8D",
        "white":    "#95A5A6",  # light gray for white side band
        "black":    "#1A1A1A",  # dark for black side band
        "page_bg":  None,        # no background fill
    },
    "light": {
        "fill_a":   "#FFFFFF",
        "fill_b":   "#FFFFFF",
        "stroke":   "#888888",
        "white":    "#B0B0B0",
        "black":    "#202020",
        "page_bg":  "#FFFFFF",
    },
    "dark": {
        "fill_a":   "#2C3E50",
        "fill_b":   "#34495E",
        "stroke":   "#7F8C8D",
        "white":    "#ECF0F1",
        "black":    "#F39C12",  # orange so the black-side band is visible on dark bg
        "page_bg":  "#1A1A1A",
    },
    "wood": {
        "fill_a":   "#F5DEB3",  # wheat
        "fill_b":   "#DEB887",  # burlywood
        "stroke":   "#8B4513",  # saddle brown
        "white":    "#A0522D",  # sienna
        "black":    "#3B1F0F",  # dark brown
        "page_bg":  "#FAEBD7",  # antique white
    },
}


# Go-style column labels: a..h, skip i, then j..z (skipping i per Go convention).
def _go_col_letter(col):
    return chr(ord('a') + col + (1 if col >= 8 else 0))


# Side label text per color convention.
LABEL_SETS = {
    "wb":  ("White Side", "Black Side"),
    "rb":  ("Red Side",   "Blue Side"),
}


# ──────────────────────────────────────────────────────────────────────────────
# Hex variants (sub-games sharing the hexhex-N rhombus geometry)
#
#   None     — standard Hex, perimeter bands, connect opposite sides to win.
#   "rex"    — misère Hex. Same bands, same connections, but: the player who
#              connects their sides LOSES. Goal: force opponent to connect.
#   "yavalath" — Yavalath by Cameron Browne (2007). No perimeter bands (stones
#              only on cells, no edges to connect). Place a stone per turn,
#              win by making a line of 4 in a row, lose by making a line of
#              exactly 3 in a row (without also making a line of 4).
# ──────────────────────────────────────────────────────────────────────────────
HEX_VARIANTS = (None, "rex", "yavalath")
HEX_VARIANT_TITLES = {
    None:      None,                # use the default HEX BOARD title
    "rex":     "REX BOARD",         # misère Hex
    "yavalath": "YAVALATH BOARD",
}


# ──────────────────────────────────────────────────────────────────────────────
# Default board sizes per game/variant.
#
#   hex        — 11×11 (Piet Hein 1942 / Parker Brothers classic; the standard
#                hex size in serious play)
#   rex        — same as hex (also plays on 11×11); larger sizes are playable
#                but go much longer for misère swings
#   yavalath   — hexhex-5 (Nestorgames published size; 61 cells, the canonical
#                set that also plays Pentalath and the 3-player variant)
#   havannah   — base-10 (Computer Olympiad standard; 271 cells, common in
#                competitive play)
#   trike      — side-13 (standard competitive play; Alek Erickson 2020 design)
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_SIZES = {
    "hex":       11,
    "rex":       11,
    "yavalath":  5,
    "havannah":  10,
    "trike":     13,
}


# ──────────────────────────────────────────────────────────────────────────────
# Shared hex geometry (pointy-top hexes)
#
# Pointy-top hex centered at origin with circumradius r has vertices at angles
# (π/6 + i·π/3), i = 0..5. Width (flat-to-flat) = √3·r, height (point-to-point)
# = 2·r. Used by both Hex (odd-r offset layout) and Havannah (axial layout).
# ──────────────────────────────────────────────────────────────────────────────


def hex_vertices(cx, cy, radius):
    """Return the 6 (x, y) vertices of a pointy-top hex centered at (cx, cy)."""
    return [
        (cx + radius * math.cos(math.pi / 6 + i * math.pi / 3),
         cy + radius * math.sin(math.pi / 6 + i * math.pi / 3))
        for i in range(6)
    ]


def axial_to_pixel(q, r, R):
    """Convert axial coords (q, r) with q+r+s=0 to pixel center for pointy-top hex.

    `R` is the circumradius (point-to-point distance / 2). Returns (cx, cy)
    measured from the hex board's own origin (the center cell sits at (0, 0)).

    Adjacent cells (q,r) and (q,r+1) share a horizontal flat edge — center
    distance = R*sqrt(3) = flat-to-flat width.
    """
    cx = R * SQRT3 * (q + r / 2)
    cy = R * 1.5 * r
    return cx, cy


def grid_extent_r_units(N):
    """Return (w_units, h_units): grid extent in r units for NxN pointy-top board."""
    return (SQRT3 * (1.5 * (N - 1) + 1), 1.5 * (N - 1) + 2)


# ──────────────────────────────────────────────────────────────────────────────
# Havannah geometry
#
# A base-N Havannah board is a regular hexagon with N cells per side. Cells use
# axial coords (q, r) with s = -q - r. The center cell is (0, 0). The six corner
# cells are the cells furthest from the origin along the six axial directions:
#   (N-1, -(N-1)), (N-1, 0), (0, N-1), (-(N-1), N-1), (-(N-1), 0), (0, -(N-1))
# Total cells = 3N² − 3N + 1.  Examples: N=8 → 169, N=10 → 271.
# ──────────────────────────────────────────────────────────────────────────────


def havannah_cell_count(N):
    return 3 * N * N - 3 * N + 1


def havannah_in_bounds(q, r, N):
    """True iff axial cell (q, r) is part of the base-N board."""
    s = -q - r
    return max(abs(q), abs(r), abs(s)) <= N - 1


def havannah_cells(N):
    """Yield (q, r) for every cell on a base-N board, in a stable order."""
    for q in range(-(N - 1), N):
        for r in range(-(N - 1), N):
            if havannah_in_bounds(q, r, N):
                yield q, r


def havannah_corners(N):
    """Return the six (q, r) corner cells (axial coords)."""
    return [
        (N - 1, -(N - 1)),
        (N - 1, 0),
        (0, N - 1),
        (-(N - 1), N - 1),
        (-(N - 1), 0),
        (0, -(N - 1)),
    ]


def havannah_extent_r_units(N):
    """Return (w_units, h_units): grid extent in R units for base-N board.

    Pointy-top axial layout: cells (q, r) center at
      cx = R·√3·(q + r/2),  cy = R·1.5·r.
    Cells are pointy-top hexagons with flat-to-flat width √3·R, so each cell
    extends √3·R/2 beyond its center along the x-axis and R/2 along the y-axis
    at the flat edges (the pointy vertices stick out by R, but the bounding-box
    extent is governed by the flats at top/bottom of the hex shape).

    Cell-center extent:    width = 2·√3·(N−1), height = 3·(N−1)
    Full-cell extent:      width = 2·√3·(N−1) + √3 = √3·(2N−1)
                           height = 3·(N−1) + 1
    """
    return (2 * SQRT3 * (N - 1) + SQRT3, 3 * (N - 1) + 1)


# ──────────────────────────────────────────────────────────────────────────────
# Trike geometry
#
# A side-N Trike board is a triangular region of pointy-top hex cells, point up.
# Cells use axial coords (q, r) with the in-bounds predicate:
#     0 ≤ q and 0 ≤ r and q + r < N
# The three vertices of the triangle are the cells (0, 0) [bottom-left],
# (N − 1, 0) [bottom-right], and (0, N − 1) [top].
# Cell count = N·(N + 1)/2. Examples: N=7 → 28, N=13 → 91, N=19 → 190.
# ──────────────────────────────────────────────────────────────────────────────


def trike_cell_count(N):
    return N * (N + 1) // 2


def trike_in_bounds(q, r, N):
    return q >= 0 and r >= 0 and (q + r) < N


def trike_cells(N):
    """Yield (q, r) for every cell on a side-N Trike board, row-major order."""
    for r in range(N):
        for q in range(N - r):
            yield q, r


def trike_vertices(N):
    """Return the three (q, r) corner cells of the triangular board."""
    return [(0, 0), (N - 1, 0), (0, N - 1)]


def trike_extent_r_units(N):
    """Return (w_units, h_units): grid extent in R units for side-N board.

    With cell centers at cx = R·√3·(q + r/2), cy = R·1.5·r:
      Vertices: (0,0), (N−1,0), (0, N−1)
                → (0, 0), (√3·(N−1)·R, 0), (√3·(N−1)/2 · R, 1.5·(N−1)·R)
    Cells are pointy-top hexagons with flat-to-flat width √3·R, so each cell
    extends √3·R/2 beyond its center along the x-axis. The bottom row r=0 has
    its leftmost vertex at cx = -√3·R/2 and rightmost at cx = √3·(N−1)·R + √3·R/2.

    Cell-center extent: width = √3·(N − 1), height = 1.5·(N − 1)
    Full-cell extent:   width = √3·N,         height = 1.5·(N − 1) + 1
    """
    return (SQRT3 * N, 1.5 * (N - 1) + 1)


def pick_page_size(name, board_size, extent_fn=None):
    """Return page size in points, auto-rotating to landscape when wider fits better.

    For N >= 3 the hex grid is wider than tall (Hex) or square (Havannah), so
    landscape uses paper better in both cases. `extent_fn` lets callers pass a
    game-specific extent calculator; defaults to the Hex (odd-r offset) one.
    """
    base = PAPER_SIZES[name.lower()]
    w, h = base
    if board_size >= 3 and w < h:
        return landscape(base)
    return base


# Maximum stone-to-hex flat-to-flat ratio per mode.
# Comfortable = 0.70 (30% margin).  Tight = 0.85.  Flush = 1.00 (no margin).
FIT_RATIOS = {
    "safe":      0.70,
    "makeitwork": 0.85,
    "unsafe":    1.00,
}


def auto_pick_paper(board_size, stone_diameter_mm, margin_pt, mode="safe",
                    extent_fn=None):
    """Find the smallest paper that fits the board + stone requirement.

    `mode` controls the maximum stone-to-hex flat-to-flat ratio:
      - safe      : 0.70  (30% margin, default)
      - makeitwork: 0.85  (tight fit, stones nearly fill hex)
      - unsafe    : 1.00  (stones flush with hex walls, no margin)

    `extent_fn(N)` returns (gw_units, gh_units) for the board geometry.
    Defaults to the Hex (odd-r offset) extent.

    Returns (paper_name, orientation, achieved_ratio) or (None, None, ratio).
    """
    ratio = FIT_RATIOS[mode]
    min_flat_to_flat_mm = stone_diameter_mm / ratio
    min_r_pt = (min_flat_to_flat_mm / MM_PER_INCH * PT_PER_INCH) / SQRT3
    # Apply same 8% label safety as compute_r().
    min_r_pt /= 0.92

    if extent_fn is None:
        extent_fn = grid_extent_r_units
    gw_units, gh_units = extent_fn(board_size)
    need_w_pt = gw_units * min_r_pt + 2 * margin_pt
    need_h_pt = gh_units * min_r_pt + 2 * margin_pt

    # Walk papers smallest-first; check both orientations.
    for name, (pw, ph) in PAPERS_BY_AREA:
        for orient_w, orient_h, label in ((pw, ph, "portrait"), (ph, pw, "landscape")):
            if orient_w >= need_w_pt and orient_h >= need_h_pt:
                return name, label, ratio
    return None, None, ratio


def compute_r(page_w, page_h, margin, board_size, extent_fn=None):
    """Largest r that fits the page after margin, with 8% safety so labels don't clip.

    `extent_fn(N)` defaults to grid_extent_r_units (Hex). Pass havannah_extent_r_units
    for Havannah boards.
    """
    if extent_fn is None:
        extent_fn = grid_extent_r_units
    return compute_r_for_extent(page_w, page_h, margin, *extent_fn(board_size))


def compute_r_for_extent(page_w, page_h, margin, extent_w_units, extent_h_units):
    """Same as compute_r() but takes an explicit extent (game-agnostic)."""
    max_w = page_w - 2 * margin
    max_h = page_h - 2 * margin
    safety = 0.92
    return min(max_w / extent_w_units, max_h / extent_h_units) * safety, max_w, max_h


def hex_fits_stone(r_pt, stone_diameter_mm):
    """Return (flat_to_flat_mm, ratio) for diagnostic."""
    flat_to_flat_mm = SQRT3 * r_pt / PT_PER_INCH * MM_PER_INCH
    return flat_to_flat_mm, stone_diameter_mm / flat_to_flat_mm


def draw_board_into_region(c, board_size, region, margin_pt,
                           pen_paper, coords, theme, label_set, corner_dots,
                           draw_title=True, cell_coords=False, variant=None):
    """Draw one hex board into a rectangular region of an existing canvas.

    `region` = (x, y, w, h): bottom-left corner plus size of the region.
    The board fills the region (with its own internal margin_pt).
    Returns the r used (in points).

    `variant`: None (standard Hex), "rex" (misere Hex), or "yavalath"
    (no perimeter bands; 4-in-a-row wins, 3-in-a-row loses).
    """
    assert variant in HEX_VARIANTS, f"unknown hex variant {variant!r}"
    rx, ry, rw, rh = region
    # Per-region page bg fill (for theme).
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(rx, ry, rw, rh, fill=True, stroke=False)

    # Largest r fitting this region.
    gw_units, gh_units = grid_extent_r_units(board_size)
    r = min(rw / gw_units, rh / gh_units) * 0.92

    center_x = rx + rw / 2
    center_y = ry + rh / 2

    min_x = -r * SQRT3 / 2
    max_x = r * SQRT3 * (1.5 * (board_size - 1) + 0.5)
    min_y = -r
    max_y = r * 1.5 * (board_size - 1) + r
    grid_w = max_x - min_x
    grid_h = max_y - min_y
    offset_x = center_x - (min_x + grid_w / 2)
    offset_y = center_y - (min_y + grid_h / 2)

    label_a, label_b = LABEL_SETS[label_set]

    if draw_title:
        title_override = HEX_VARIANT_TITLES.get(variant)
        if title_override is not None:
            size_label = (f"hexhex-{board_size}"
                          if variant in ("yavalath", "rex")
                          else f"{board_size} \u00d7 {board_size}")
            title = (f"{title_override} \u2014 PAPER & PENCIL ({size_label})"
                     if pen_paper else
                     f"{title_override} ({size_label})")
        else:
            title = (f"HEX BOARD \u2014 PAPER & PENCIL ({board_size} \u00d7 {board_size})"
                     if pen_paper else
                     f"HEX BOARD ({board_size} \u00d7 {board_size})")
        title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 12)  # smaller for sub-boards
        c.setFillColor(colors.HexColor(title_color))
        c.drawCentredString(center_x, ry + rh - 12, title)

    def get_hex_points(cx, cy, radius):
        return hex_vertices(cx, cy, radius)

    c.setStrokeColor(colors.HexColor(theme_def["stroke"]))
    c.setLineWidth(1.0)
    for row in range(board_size):
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * row) + offset_x
            cy = r * 1.5 * row + offset_y
            pts = get_hex_points(cx, cy, r)
            if (row + col) % 2 == 0:
                c.setFillColor(colors.HexColor(theme_def["fill_a"]))
            else:
                c.setFillColor(colors.HexColor(theme_def["fill_b"]))
            path = c.beginPath()
            path.moveTo(pts[0][0], pts[0][1])
            for p in pts[1:]:
                path.lineTo(p[0], p[1])
            path.close()
            c.drawPath(path, fill=True, stroke=True)

    if corner_dots:
        c.setFillColor(colors.HexColor(theme_def["black"]))
        for cr, cc in [(0, 0), (0, board_size - 1),
                       (board_size - 1, 0), (board_size - 1, board_size - 1)]:
            ccx = r * SQRT3 * (cc + 0.5 * cr) + offset_x
            ccy = r * 1.5 * cr + offset_y
            c.circle(ccx, ccy, r * 0.18, fill=True, stroke=False)

    white_color = colors.HexColor(theme_def["white"])
    black_color = colors.HexColor(theme_def["black"])

    # Perimeter bands + side labels are only meaningful for connection games
    # that win by linking sides. Yavalath places stones on cells only; no
    # bands or "White Side"/"Black Side" labels needed.
    if variant == "yavalath":
        # Draw a Yavalath footer hint inside the board region if --pen-paper.
        if pen_paper and draw_title:
            hint_color = "#888888" if theme != "dark" else "#BBBBBB"
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.HexColor(hint_color))
            c.drawCentredString(center_x, ry + 8,
                "Yavalath: 4 in a row wins  \u2022  3 in a row loses")
        return r

    c.setLineCap(1)
    c.setLineWidth(3)
    c.setStrokeColor(white_color)
    path = c.beginPath()
    pts = get_hex_points(r * SQRT3 * 0 + offset_x, r * 1.5 * 0 + offset_y, r)
    path.moveTo(pts[3][0], pts[3][1])
    for col in range(board_size):
        pts = get_hex_points(r * SQRT3 * col + offset_x, r * 1.5 * 0 + offset_y, r)
        path.lineTo(pts[4][0], pts[4][1])
        path.lineTo(pts[5][0], pts[5][1])
    c.drawPath(path)

    path = c.beginPath()
    row = board_size - 1
    pts = get_hex_points(r * SQRT3 * (0 + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
    path.moveTo(pts[2][0], pts[2][1])
    for col in range(board_size):
        pts = get_hex_points(r * SQRT3 * (col + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
        path.lineTo(pts[1][0], pts[1][1])
        path.lineTo(pts[0][0], pts[0][1])
    c.drawPath(path)

    c.setStrokeColor(black_color)
    path = c.beginPath()
    col = 0
    pts = get_hex_points(r * SQRT3 * col + offset_x, r * 1.5 * 0 + offset_y, r)
    path.moveTo(pts[3][0], pts[3][1])
    for row in range(board_size):
        pts = get_hex_points(r * SQRT3 * (col + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
        path.lineTo(pts[2][0], pts[2][1])
        path.lineTo(pts[1][0], pts[1][1])
    c.drawPath(path)

    path = c.beginPath()
    col = board_size - 1
    pts = get_hex_points(r * SQRT3 * (col + 0.5 * 0) + offset_x, r * 1.5 * 0 + offset_y, r)
    path.moveTo(pts[4][0], pts[4][1])
    for row in range(board_size):
        pts = get_hex_points(r * SQRT3 * (col + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
        path.lineTo(pts[5][0], pts[5][1])
        path.lineTo(pts[0][0], pts[0][1])
    c.drawPath(path)

    lbl_scale = 0.7 if r < 15 else 1.0
    lbl_dist = r * 1.4 * lbl_scale
    c.setFont("Helvetica-Bold", 10 if r < 15 else 12)

    def draw_label(text, col, row, color, dx, dy, angle):
        cx = r * SQRT3 * (col + 0.5 * row) + offset_x
        cy = r * 1.5 * row + offset_y
        c.saveState()
        c.setFillColor(color)
        c.translate(cx + dx, cy + dy)
        c.rotate(angle)
        c.drawCentredString(0, 0, text.upper())
        c.restoreState()

    mid = board_size // 2
    draw_label(label_a, mid, 0, white_color, 0, -lbl_dist, 0)
    draw_label(label_a, mid, board_size - 1, white_color, 0, lbl_dist, 0)
    draw_label(label_b, 0, mid, black_color, -lbl_dist * 0.866, lbl_dist * 0.5, 60)
    draw_label(label_b, board_size - 1, mid, black_color, lbl_dist * 0.866, -lbl_dist * 0.5, 60)

    # pen-paper / coords: print labels INSIDE each cell when hexes are large enough
    # to be legible; fall back to outside-edge labels for tiny boards.
    inside_cell = r >= 11
    if (coords or pen_paper) and not inside_cell:
        coord_color = "#CCCCCC" if theme == "dark" else "#555555"
        c.setFont("Helvetica-Bold", 9 if r < 15 else 11)
        c.setFillColor(colors.HexColor(coord_color))
        col_label_y = r * 1.5 * 0 + offset_y - r * 1.05
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * 0) + offset_x
            label = _go_col_letter(col) if board_size <= 25 else str(col + 1)
            c.drawCentredString(cx, col_label_y, label)
        row_label_x = r * SQRT3 * 0 + offset_x - r * 1.05
        for row in range(board_size):
            cy = r * 1.5 * row + offset_y
            c.drawCentredString(row_label_x, cy - 3, str(row + 1))

    if cell_coords or ((coords or pen_paper) and inside_cell):
        cell_color = "#7A7A7A" if theme == "dark" else "#A8A8A8"
        cell_font = max(6, r * 0.32)
        c.setFont("Helvetica", cell_font)
        c.setFillColor(colors.HexColor(cell_color))
        for row in range(board_size):
            for col in range(board_size):
                ccx = r * SQRT3 * (col + 0.5 * row) + offset_x
                ccy = r * 1.5 * row + offset_y
                col_lbl = _go_col_letter(col) if board_size <= 25 else str(col + 1)
                c.drawCentredString(ccx, ccy - cell_font * 0.35, f"{col_lbl}{row + 1}")

    return r


def hex_to_svg(cx, cy, radius):
    """Return SVG points string for a flat-top hex centered at (cx, cy)."""
    pts = []
    for i in range(6):
        angle = math.pi / 3 + math.pi / 3 * i  # 60, 120, 180, 240, 300, 360
        pts.append(f"{cx + radius * math.cos(angle):.2f},{cy + radius * math.sin(angle):.2f}")
    return " ".join(pts)


def write_svg(output_filename, board_size, paper="letter", margin_pt=None, mode="safe",
              pen_paper=False, coords=True, theme="classic", label_set="wb",
              corner_dots=False, rules=False, variant=None):
    """Render the board as SVG (vector, web-friendly). Single page only."""
    page_w, page_h = pick_page_size(paper, board_size)
    if margin_pt is None:
        if mode in ("makeitwork", "unsafe"):
            margin_pt = 4
        else:
            margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, _, _ = compute_r(page_w, page_h, margin_pt, board_size)

    theme_def = THEMES[theme]
    label_a, label_b = LABEL_SETS[label_set]
    h = r * SQRT3 / 2

    # Center the rhombus.
    min_x = -r * SQRT3 / 2
    max_x = r * SQRT3 * (1.5 * (board_size - 1) + 0.5)
    min_y = -r
    max_y = r * 1.5 * (board_size - 1) + r
    grid_w = max_x - min_x
    grid_h = max_y - min_y
    center_x = page_w / 2
    center_y = page_h / 2
    offset_x = center_x - (min_x + grid_w / 2)
    offset_y = center_y - (min_y + grid_h / 2)

    bg = theme_def["page_bg"] or "#FFFFFF"
    title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle = "#AAAAAA" if theme == "dark" else "#777777"

    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w:.0f}" height="{page_h:.0f}" viewBox="0 0 {page_w:.0f} {page_h:.0f}">',
           f'<rect width="{page_w:.0f}" height="{page_h:.0f}" fill="{bg}"/>']

    # Title
    title_override = HEX_VARIANT_TITLES.get(variant)
    if title_override is not None:
        size_label = (f"hexhex-{board_size}"
                      if variant in ("yavalath", "rex")
                      else f"{board_size} \u00d7 {board_size}")
        title = (f"{title_override} \u2014 PAPER & PENCIL ({size_label})"
                 if pen_paper else
                 f"{title_override} ({size_label})")
    else:
        title = (f"HEX BOARD \u2014 PAPER & PENCIL ({board_size} \u00d7 {board_size})"
                 if pen_paper else f"HEX BOARD ({board_size} \u00d7 {board_size})")
    title_y = page_h - max(14, margin_pt / 2)
    out.append(
        f'<text x="{center_x:.2f}" y="{title_y:.2f}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="16" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>'
    )

    # Hex cells
    for row in range(board_size):
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * row) + offset_x
            cy = r * 1.5 * row + offset_y
            fill = theme_def["fill_a"] if (row + col) % 2 == 0 else theme_def["fill_b"]
            pts = hex_to_svg(cx, cy, r)
            out.append(
                f'<polygon points="{pts}" fill="{fill}" stroke="{theme_def["stroke"]}" stroke-width="1"/>'
            )

    # Corner dots
    if corner_dots:
        for cr, cc in [(0, 0), (0, board_size - 1),
                       (board_size - 1, 0), (board_size - 1, board_size - 1)]:
            ccx = r * SQRT3 * (cc + 0.5 * cr) + offset_x
            ccy = r * 1.5 * cr + offset_y
            out.append(f'<circle cx="{ccx:.2f}" cy="{ccy:.2f}" r="{r * 0.18:.2f}" fill="{theme_def["black"]}"/>')

    # Perimeter bands: white (row 0 and row N-1), black (col 0 and col N-1).
    # Emit each edge as a separate <line> so styling is clean.
    def line(a, b, color, width=4):
        return (f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
                f'stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')

    # Helper for vertex at row,col,index (flat-top vertex numbering same as PDF).
    def vert(row, col, i):
        cx = r * SQRT3 * (col + 0.5 * row) + offset_x
        cy = r * 1.5 * row + offset_y
        angle = math.pi / 3 + math.pi / 3 * i
        return (cx + r * math.cos(angle), cy + r * math.sin(angle))

    # White band: row 0 (v0-v1) and row N-1 (v3-v4).
    if variant != "yavalath":
        for col in range(board_size):
            out.append(line(vert(0, col, 0), vert(0, col, 1), theme_def["white"]))
        for col in range(board_size):
            out.append(line(vert(board_size - 1, col, 3), vert(board_size - 1, col, 4), theme_def["white"]))
        # Black band: col 0 (v2-v3 then v3-v4) and col N-1 (v5-v0 then v0-v1).
        for row in range(board_size):
            out.append(line(vert(row, 0, 1), vert(row, 0, 2), theme_def["black"]))
        for row in range(board_size):
            out.append(line(vert(row, board_size - 1, 4), vert(row, board_size - 1, 5), theme_def["black"]))

        # Side labels
        mid = board_size // 2
        lbl_dist = r * 1.4 if not pen_paper else r * 2.2
        def lbl(text, col, row, color, dx, dy, angle):
            cx = r * SQRT3 * (col + 0.5 * row) + offset_x
            cy = r * 1.5 * row + offset_y
            out.append(
                f'<text x="{cx + dx:.2f}" y="{cy + dy:.2f}" font-family="Helvetica,Arial,sans-serif" '
                f'font-size="12" font-weight="bold" fill="{color}" text-anchor="middle" '
                f'transform="rotate({angle} {cx + dx:.2f} {cy + dy:.2f})">{text}</text>'
            )

        lbl(label_a.upper(), mid, 0, theme_def["white"], 0, -lbl_dist, 0)
        lbl(label_a.upper(), mid, board_size - 1, theme_def["white"], 0, lbl_dist, 0)
        lbl(label_b.upper(), 0, mid, theme_def["black"], -lbl_dist * 0.866, lbl_dist * 0.5, 60)
        lbl(label_b.upper(), board_size - 1, mid, theme_def["black"], lbl_dist * 0.866, -lbl_dist * 0.5, -60)

    # Edge coords: only when hexes are too small for legible inside-cell labels.
    if (coords or pen_paper) and r < 11:
        coord_color = "#CCCCCC" if theme == "dark" else "#555555"
        col_label_y = r * 1.5 * 0 + offset_y - r * 1.05
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * 0) + offset_x
            label = _go_col_letter(col) if board_size <= 25 else str(col + 1)
            out.append(
                f'<text x="{cx:.2f}" y="{col_label_y:.2f}" font-family="Helvetica,Arial,sans-serif" '
                f'font-weight="bold" font-size="11" fill="{coord_color}" text-anchor="middle">{label}</text>'
            )
        row_label_x = r * SQRT3 * 0 + offset_x - r * 1.05
        for row in range(board_size):
            cy = r * 1.5 * row + offset_y
            out.append(
                f'<text x="{row_label_x:.2f}" y="{cy - 3:.2f}" font-family="Helvetica,Arial,sans-serif" '
                f'font-weight="bold" font-size="11" fill="{coord_color}" text-anchor="middle">{row + 1}</text>'
            )

    # Inside-cell coords (Go notation): default for pen-paper / --coords on legible boards.
    if (coords or pen_paper) and r >= 11:
        cell_color = "#7A7A7A" if theme == "dark" else "#A8A8A8"
        cell_font = max(6, r * 0.32)
        for row in range(board_size):
            for col in range(board_size):
                ccx = r * SQRT3 * (col + 0.5 * row) + offset_x
                ccy = r * 1.5 * row + offset_y
                col_lbl = _go_col_letter(col) if board_size <= 25 else str(col + 1)
                out.append(
                    f'<text x="{ccx:.2f}" y="{ccy + cell_font * 0.35:.2f}" font-family="Helvetica,Arial,sans-serif" '
                    f'font-size="{cell_font:.1f}" fill="{cell_color}" text-anchor="middle">{col_lbl}{row + 1}</text>'
                )

    if pen_paper:
        first_player = "Red" if label_set == "rb" else "Black (or Red)"
        if stone_mode:
            hint = "Place stones in hex centers. \u2022 Notation: &lt;col&gt;&lt;row&gt; e.g. f7."
        else:
            hint = "Mark cells with X / O / your initial. \u2022 Notation: &lt;col&gt;&lt;row&gt; e.g. f7."
        if variant == "yavalath":
            footer = (f"{hint}  \u2022  {first_player} moves first.  "
                      f"\u2022  4 in a row wins, 3 in a row loses.")
        elif variant == "rex":
            footer = (f"{hint}  \u2022  {first_player} moves first.  "
                      f"\u2022  Rex (mis\u00e8re): connecting your two sides LOSES.")
        else:
            footer = (f"{hint}  \u2022  {first_player} moves first.  "
                      f"\u2022  Connect your two sides to win.")
        out.append(
            f'<text x="{center_x:.2f}" y="{max(14, margin_pt / 2):.2f}" font-family="Helvetica,Arial,sans-serif" '
            f'font-size="8" font-style="italic" fill="{subtle}" text-anchor="middle">{footer}</text>'
        )

    out.append('</svg>')
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def draw_hex_board(output_filename, board_size, paper="letter", margin_pt=None,
                   pen_paper=False, coords=True, mode="safe",
                   theme="classic", label_set="wb", corner_dots=False, rules=False,
                   cell_coords=False, stone_mode=False, variant=None):
    assert variant in HEX_VARIANTS, f"unknown hex variant {variant!r}"
    page_w, page_h = pick_page_size(paper, board_size)
    if margin_pt is None:
        if mode in ("makeitwork", "unsafe"):
            margin_pt = 4
        else:
            margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, max_w, max_h = compute_r(page_w, page_h, margin_pt, board_size)

    c = canvas.Canvas(output_filename, pagesize=(page_w, page_h))
    theme_def = THEMES[theme]

    # Page-level title only for single-board output (draw_board_into_region handles sub-board titles).
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    title_override = HEX_VARIANT_TITLES.get(variant)
    if title_override is not None:
        size_label = (f"hexhex-{board_size}"
                      if variant in ("yavalath", "rex")
                      else f"{board_size} \u00d7 {board_size}")
        title = (f"{title_override} \u2014 PAPER & PENCIL ({size_label})"
                 if pen_paper else
                 f"{title_override} ({size_label})")
    else:
        title = (f"HEX BOARD \u2014 PAPER & PENCIL ({board_size} \u00d7 {board_size})"
                 if pen_paper else
                 f"HEX BOARD ({board_size} \u00d7 {board_size})")
    c.setTitle(title)
    title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor(title_color))
    title_y = max(14, margin_pt / 2)
    c.drawCentredString(page_w / 2, page_h - title_y, title)

    draw_board_into_region(
        c, board_size, (0, 0, page_w, page_h), margin_pt,
        pen_paper, coords, theme, label_set, corner_dots,
        draw_title=False, cell_coords=cell_coords, variant=variant,
    )

    if pen_paper:
        footer_color = "#AAAAAA" if theme == "dark" else "#777777"
        first_player = "Red" if label_set == "rb" else "Black (or Red)"
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor(footer_color))
        if stone_mode:
            hint = "Place stones in hex centers. \u2022 Notation: <col><row> e.g. f7."
        else:
            hint = f"Mark cells with X / O / your initial. \u2022 Notation: <col><row> e.g. f7."
        if variant == "yavalath":
            footer = (f"{hint}  \u2022  {first_player} moves first.  "
                      f"\u2022  4 in a row wins, 3 in a row loses.")
        elif variant == "rex":
            footer = (f"{hint}  \u2022  {first_player} moves first.  "
                      f"\u2022  Rex (mis\u00e8re): connecting your two sides LOSES; "
                      f"force the opponent to connect.")
        else:
            footer = (f"{hint}  \u2022  {first_player} moves first.  "
                      f"\u2022  Connect your two sides to win.")
        c.drawCentredString(page_w / 2, max(14, margin_pt / 2), footer)

    if rules:
        c.showPage()
        draw_rules_page(c, page_w, page_h, theme=theme, label_set=label_set,
                        stone_mode=stone_mode, variant=variant)
        c.showPage()
    else:
        c.showPage()
    c.save()

    return r


def draw_rules_page(c, page_w, page_h, theme="classic", label_set="wb",
                    stone_mode=False, variant=None):
    """Draw a one-page rules summary as the final page of the PDF.

    `variant`: None = standard Hex, "rex" = misère Hex, "yavalath" = Yavalath.
    """
    if variant == "yavalath":
        return _draw_yavalath_rules_page(c, page_w, page_h, theme=theme,
                                         stone_mode=stone_mode)
    if variant == "rex":
        return _draw_rex_rules_page(c, page_w, page_h, theme=theme,
                                    stone_mode=stone_mode)
    return _draw_hex_rules_page(c, page_w, page_h, theme=theme,
                                label_set=label_set, stone_mode=stone_mode)


# ──────────────────────────────────────────────────────────────────────────────
# Winning-position diagrams
#
# Each game has a small (4-7 cell) illustrative position that demonstrates its
# win condition. These are drawn inline on the rules page using themed
# stones/cells so they match the surrounding visuals.
#
# Layout contract for all diagram helpers:
#   region = (x, y, w, h): bottom-left corner + size in points (page coords).
#   The diagram fills the region (centered, aspect preserved). Helpers return
#   the (r, board_w, board_h) used so the caller can place captions relative
#   to the actual drawn board if needed.
# ──────────────────────────────────────────────────────────────────────────────


def _draw_hex_cell(c, cx, cy, r, fill_color, stroke_color, line_width=0.8):
    """Draw one pointy-top hex cell centered at (cx, cy)."""
    pts = hex_vertices(cx, cy, r)
    c.setStrokeColor(colors.HexColor(stroke_color))
    c.setLineWidth(line_width)
    c.setFillColor(colors.HexColor(fill_color))
    path = c.beginPath()
    path.moveTo(pts[0][0], pts[0][1])
    for p in pts[1:]:
        path.lineTo(p[0], p[1])
    path.close()
    c.drawPath(path, fill=True, stroke=True)


def _draw_stone(c, cx, cy, r, color, outline_color=None, outline_width=0.5):
    """Draw a filled circular stone centered at (cx, cy) with radius `r`."""
    c.setFillColor(colors.HexColor(color))
    if outline_color:
        c.setStrokeColor(colors.HexColor(outline_color))
        c.setLineWidth(outline_width)
        c.circle(cx, cy, r, fill=True, stroke=True)
    else:
        c.circle(cx, cy, r, fill=True, stroke=False)


def _draw_hex_diagram(c, region, board_size, stones, winning_path,
                      theme="classic", side_bands=True, label_set="wb"):
    """Draw a small Hex/Rex/Yavalath board region with stones and a winning
    path highlighted.

    `stones`: dict mapping (row, col) -> "W" or "B".
    `winning_path`: list of (row, col) cells forming the winning chain
                    (drawn with a thick colored outline).
    """
    rx, ry, rw, rh = region
    theme_def = THEMES[theme]

    bg = theme_def.get("page_bg")
    if bg:
        c.setFillColor(colors.HexColor(bg))
        c.rect(rx, ry, rw, rh, fill=True, stroke=False)

    gw_units, gh_units = grid_extent_r_units(board_size)
    r = min(rw / gw_units, rh / gh_units) * 0.95
    board_w = gw_units * r
    board_h = gh_units * r
    board_cx = rx + rw / 2
    board_cy = ry + rh / 2
    offset_x = board_cx - board_w / 2
    offset_y = board_cy - board_h / 2

    # Draw cell backgrounds.
    for row in range(board_size):
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * row) + offset_x
            cy = r * 1.5 * row + offset_y
            fill = theme_def["fill_a"] if (row + col) % 2 == 0 else theme_def["fill_b"]
            _draw_hex_cell(c, cx, cy, r, fill, theme_def["stroke"], line_width=0.8)

    # Place stones (skip if cell is on the winning path; we draw highlight first).
    stone_radius = r * 0.78
    for (row, col), color_letter in stones.items():
        if (row, col) in set(winning_path):
            continue
        cx = r * SQRT3 * (col + 0.5 * row) + offset_x
        cy = r * 1.5 * row + offset_y
        stone_color = theme_def["white"] if color_letter == "W" else theme_def["black"]
        _draw_stone(c, cx, cy, stone_radius, stone_color,
                    outline_color=theme_def["stroke"], outline_width=0.5)

    # Highlight winning path with a thick outline ring around each cell.
    if winning_path:
        win_color = theme_def["black"] if any(
            stones.get(rc) == "B" for rc in winning_path
        ) else theme_def["white"]
        # Use the opposite color for highlight so it's visible on top of stones.
        highlight = (theme_def["black"]
                     if win_color == theme_def["white"]
                     else theme_def["white"])
        c.setStrokeColor(colors.HexColor(highlight))
        c.setLineWidth(2.5)
        c.setFillColor(colors.HexColor(highlight))
        for (row, col) in winning_path:
            cx = r * SQRT3 * (col + 0.5 * row) + offset_x
            cy = r * 1.5 * row + offset_y
            c.circle(cx, cy, r * 0.92, fill=False, stroke=True)

        # Re-draw winning stones on top of the highlight so the highlight
        # forms a ring around the stone, not over it.
        for (row, col) in winning_path:
            color_letter = stones.get((row, col))
            if color_letter:
                cx = r * SQRT3 * (col + 0.5 * row) + offset_x
                cy = r * 1.5 * row + offset_y
                stone_color = (theme_def["white"] if color_letter == "W"
                               else theme_def["black"])
                _draw_stone(c, cx, cy, stone_radius, stone_color,
                            outline_color=theme_def["stroke"], outline_width=0.5)

    return r, board_w, board_h


def _draw_hex_win_diagram(c, region, theme="classic"):
    """Standard Hex: White wins with a top-bottom chain on a 5x5 board."""
    # Compact 5x5 example: White connects top-bottom edge.
    stones = {
        (0, 2): "W", (1, 2): "W", (2, 2): "W", (3, 2): "W", (4, 2): "W",
        (0, 1): "B", (1, 1): "B", (2, 1): "B",
        (1, 3): "B", (2, 3): "B", (3, 3): "B",
        (3, 0): "B", (4, 0): "B",
        (0, 3): "B", (4, 1): "B",
    }
    winning_path = [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
    return _draw_hex_diagram(c, region, board_size=5, stones=stones,
                             winning_path=winning_path, theme=theme)


def _draw_rex_win_diagram(c, region, theme="classic"):
    """Rex: White connects top-bottom (which means White LOSES).
    The losing chain is highlighted.
    """
    stones = {
        (0, 2): "W", (1, 2): "W", (2, 2): "W", (3, 2): "W", (4, 2): "W",
        (0, 1): "B", (1, 1): "B", (2, 1): "B",
        (1, 3): "B", (2, 3): "B", (3, 3): "B",
        (3, 0): "B", (4, 0): "B",
        (0, 3): "B", (4, 1): "B",
    }
    losing_path = [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
    return _draw_hex_diagram(c, region, board_size=5, stones=stones,
                             winning_path=losing_path, theme=theme)


def _draw_yavalath_win_diagram(c, region, theme="classic"):
    """Yavalath: White wins with 4-in-a-row on a hexagon board (base-5).

    Uses Havannah axial coordinates. White has a 4-in-a-row diagonal;
    Black stones are placed so no Black line reaches exactly 3.
    """
    stones = {
        # White 4-in-a-row diagonal: (2,-2) -> (1,-1) -> (0,0) -> (-1,1)
        (2, -2): "W", (1, -1): "W", (0, 0): "W", (-1, 1): "W",
        # Black filler — verified no 3-in-a-row
        (-4, 2): "B", (-3, -1): "B", (-3, 1): "B", (-2, 3): "B",
        (-1, -3): "B", (-1, 4): "B", (0, 1): "B", (1, -3): "B",
        (1, -2): "B", (2, -4): "B", (3, -4): "B", (3, 1): "B",
    }
    winning_path = [(2, -2), (1, -1), (0, 0), (-1, 1)]
    return _draw_havannah_diagram(c, region, base=5, stones_axial=stones,
                                  winning_path_axial=winning_path, theme=theme)


def _draw_havannah_cell(c, cx, cy, r, fill_color, stroke_color):
    """Draw one Havannah hex cell (pointy-top)."""
    _draw_hex_cell(c, cx, cy, r, fill_color, stroke_color, line_width=0.8)


def _draw_havannah_diagram(c, region, base, stones_axial, winning_path_axial,
                           highlight_ring=False, theme="classic"):
    """Draw a small Havannah board region with stones and a winning structure.

    `stones_axial`: dict mapping (q, r) -> "W" or "B".
    `winning_path_axial`: list of (q, r) cells forming the winning structure.
    `highlight_ring`: if True, draw a closed loop around the ring cells instead
                      of outlining each cell individually.
    """
    rx, ry, rw, rh = region
    theme_def = THEMES[theme]

    bg = theme_def.get("page_bg")
    if bg:
        c.setFillColor(colors.HexColor(bg))
        c.rect(rx, ry, rw, rh, fill=True, stroke=False)

    gw_units, gh_units = havannah_extent_r_units(base)
    # Slightly smaller r to leave caption room.
    r = min(rw / gw_units, rh / gh_units) * 0.95
    board_w = gw_units * r
    board_h = gh_units * r
    board_cx = rx + rw / 2
    board_cy = ry + rh / 2
    offset_x = board_cx
    offset_y = board_cy

    stone_radius = r * 0.78
    winning_set = set(winning_path_axial)

    # Cells.
    for q, rr in havannah_cells(base):
        cx, cy = axial_to_pixel(q, rr, r)
        cx += offset_x
        cy += offset_y
        fill = _havannah_cell_color(theme_def, q, rr)
        _draw_havannah_cell(c, cx, cy, r, fill, theme_def["stroke"])

    # Stones not on the winning path.
    for (q, rr), color_letter in stones_axial.items():
        if (q, rr) in winning_set:
            continue
        cx, cy = axial_to_pixel(q, rr, r)
        stone_color = theme_def["white"] if color_letter == "W" else theme_def["black"]
        _draw_stone(c, cx + offset_x, cy + offset_y, stone_radius, stone_color,
                    outline_color=theme_def["stroke"], outline_width=0.5)

    # Highlight: for ring, draw a closed loop; for bridge/fork, outline cells.
    if highlight_ring and winning_path_axial:
        # Closed loop connecting adjacent cells on the path. We approximate
        # by drawing a polyline through the cell centers.
        pts = []
        for (q, rr) in winning_path_axial:
            cx, cy = axial_to_pixel(q, rr, r)
            pts.append((cx + offset_x, cy + offset_y))
        if pts:
            pts.append(pts[0])  # close the loop
            win_color = (theme_def["white"]
                         if any(stones_axial.get(p) == "W" for p in winning_path_axial)
                         else theme_def["black"])
            highlight = (theme_def["black"]
                         if win_color == theme_def["white"]
                         else theme_def["white"])
            c.setStrokeColor(colors.HexColor(highlight))
            c.setLineWidth(2.5)
            path = c.beginPath()
            path.moveTo(pts[0][0], pts[0][1])
            for p in pts[1:]:
                path.lineTo(p[0], p[1])
            path.close()
            c.drawPath(path, stroke=True, fill=False)
    elif winning_path_axial:
        # Cell-by-cell outline (bridge/fork).
        win_color = (theme_def["white"]
                     if any(stones_axial.get(p) == "W" for p in winning_path_axial)
                     else theme_def["black"])
        highlight = (theme_def["black"]
                     if win_color == theme_def["white"]
                     else theme_def["white"])
        c.setStrokeColor(colors.HexColor(highlight))
        c.setLineWidth(2.5)
        for (q, rr) in winning_path_axial:
            cx, cy = axial_to_pixel(q, rr, r)
            c.circle(cx + offset_x, cy + offset_y, r * 0.92,
                     fill=False, stroke=True)

    # Re-draw winning-path stones on top of the highlight.
    for (q, rr) in winning_path_axial:
        color_letter = stones_axial.get((q, rr))
        if not color_letter:
            continue
        cx, cy = axial_to_pixel(q, rr, r)
        stone_color = theme_def["white"] if color_letter == "W" else theme_def["black"]
        _draw_stone(c, cx + offset_x, cy + offset_y, stone_radius, stone_color,
                    outline_color=theme_def["stroke"], outline_width=0.5)

    return r, board_w, board_h


def _draw_havannah_ring_diagram(c, region, theme="classic"):
    """Havannah ring win: a 6-cell closed loop around the center on base-4.

    Forms a perfect hexagon at axial distance 1 from the origin, surrounding
    the center cell (0,0). Every consecutive pair is adjacent — a valid ring.
    """
    stones = {
        # Hexagon ring of White stones at radius 1 from origin.
        (1, 0): "W", (1, -1): "W", (0, -1): "W",
        (-1, 0): "W", (-1, 1): "W", (0, 1): "W",
        # Black filler inside and outside the ring.
        (0, 0): "B",
        (2, 0): "B", (2, -1): "B", (1, -2): "B",
        (-1, -1): "B", (-2, 0): "B", (-2, 1): "B",
        (-1, 2): "B", (0, 2): "B", (1, 1): "B",
    }
    ring = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
    return _draw_havannah_diagram(c, region, base=4, stones_axial=stones,
                                  winning_path_axial=ring, highlight_ring=True,
                                  theme=theme)


def _draw_havannah_bridge_diagram(c, region, theme="classic"):
    """Havannah bridge win: White connects two corners on base-5."""
    stones = {
        # Connect corner (4, -4) to corner (-4, 4) through the center.
        (4, -4): "W", (3, -3): "W", (2, -2): "W", (1, -1): "W",
        (0, 0): "W", (-1, 1): "W", (-2, 2): "W", (-3, 3): "W", (-4, 4): "W",
        # Some Black stones to make it look like a real game.
        (3, -2): "B", (2, 0): "B", (1, 1): "B", (-1, 2): "B",
        (-2, 3): "B", (2, -3): "B", (-3, 4): "B", (4, -3): "B",
    }
    bridge = [(4, -4), (3, -3), (2, -2), (1, -1), (0, 0),
              (-1, 1), (-2, 2), (-3, 3), (-4, 4)]
    return _draw_havannah_diagram(c, region, base=5, stones_axial=stones,
                                  winning_path_axial=bridge, theme=theme)


def _draw_havannah_fork_diagram(c, region, theme="classic"):
    """Havannah fork win: White connects three edges on base-5.

    Forms a Y-shape: bottom stem (0,-4) up to center (0,0), then branches
    to right edge (4,0) and left edge (-4,0). All stones are connected
    through the center — a single group touching 3 edges.
    """
    stones = {
        # Bottom stem.
        (0, -4): "W", (0, -3): "W", (0, -2): "W", (0, -1): "W",
        # Center junction.
        (0, 0): "W",
        # Right branch.
        (1, 0): "W", (2, 0): "W", (3, 0): "W", (4, 0): "W",
        # Left branch.
        (-1, 0): "W", (-2, 0): "W", (-3, 0): "W", (-4, 0): "W",
        # Black filler.
        (1, -1): "B", (2, -1): "B", (3, -1): "B",
        (-1, -1): "B", (-2, -1): "B", (-3, -1): "B",
        (1, 1): "B", (2, 1): "B", (3, 1): "B",
        (-1, 1): "B", (-2, 1): "B", (-3, 1): "B",
    }
    fork = [(0, -4), (0, -3), (0, -2), (0, -1), (0, 0),
            (1, 0), (2, 0), (3, 0), (4, 0),
            (-1, 0), (-2, 0), (-3, 0), (-4, 0)]
    return _draw_havannah_diagram(c, region, base=5, stones_axial=stones,
                                  winning_path_axial=fork, theme=theme)


def _draw_trike_diagram(c, region, side, stones_axial, pawn_axial, score_cells,
                        theme="classic"):
    """Draw a small Trike board region with checkers and a pawn, plus
    highlight cells that score (adjacent to pawn).

    `stones_axial`: dict (q, r) -> "W" or "B" for placed checkers.
    `pawn_axial`: (q, r) location of the pawn.
    `score_cells`: list of (q, r) cells that score (adjacent to pawn).
    """
    rx, ry, rw, rh = region
    theme_def = THEMES[theme]

    bg = theme_def.get("page_bg")
    if bg:
        c.setFillColor(colors.HexColor(bg))
        c.rect(rx, ry, rw, rh, fill=True, stroke=False)

    gw_units, gh_units = trike_extent_r_units(side)
    # Trike boards anchor the bottom edge at anchor_y = r (one cell above
    # the bottom of the region) so the apex has clearance. Apply the same
    # 0.96 safety used by draw_trike_board_into_region.
    r = min(rw / gw_units, rh / gh_units) * 0.93
    board_w = gw_units * r
    board_h = gh_units * r
    board_cx = rx + rw / 2
    anchor_x = board_cx - board_w / 2
    anchor_y = ry + r

    stone_radius = r * 0.78
    score_set = set(score_cells)

    # Cells.
    for q, rr in trike_cells(side):
        cx, cy = axial_to_pixel(q, rr, r)
        cx += anchor_x
        cy += anchor_y
        fill = _trike_cell_color(theme_def, q, rr)
        _draw_hex_cell(c, cx, cy, r, fill, theme_def["stroke"], line_width=0.8)

    # Stones.
    for (q, rr), color_letter in stones_axial.items():
        if (q, rr) == pawn_axial:
            continue
        cx, cy = axial_to_pixel(q, rr, r)
        stone_color = theme_def["white"] if color_letter == "W" else theme_def["black"]
        _draw_stone(c, cx + anchor_x, cy + anchor_y, stone_radius, stone_color,
                    outline_color=theme_def["stroke"], outline_width=0.5)

    # Highlight score cells with a dotted ring (different look from winning paths).
    c.setStrokeColor(colors.HexColor(theme_def["black"]))
    c.setLineWidth(1.5)
    c.setDash(3, 2)
    for (q, rr) in score_cells:
        cx, cy = axial_to_pixel(q, rr, r)
        c.circle(cx + anchor_x, cy + anchor_y, r * 0.85,
                 fill=False, stroke=True)
    c.setDash()  # reset

    # Draw pawn last so it sits on top.
    pq, pr = pawn_axial
    pcx, pcy = axial_to_pixel(pq, pr, r)
    _draw_stone(c, pcx + anchor_x, pcy + anchor_y, stone_radius,
                "#888888", outline_color=theme_def["stroke"], outline_width=0.7)
    # Small "P" label on the pawn.
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", max(6, int(r * 0.5)))
    c.drawCentredString(pcx + anchor_x, pcy + anchor_y - r * 0.18, "P")

    return r, board_w, board_h


def _draw_trike_win_diagram(c, region, theme="classic"):
    """Trike: pawn trapped on side-5, with mixed White/Black scoring cells."""
    # side-5 board. Pawn at (2, 1) (central-ish cell). Adjacent cells (axial
    # neighbors) are the score cells: (1,1), (3,1), (2,0), (2,2), (1,2), (3,0).
    pawn = (2, 1)
    score_cells = [(1, 1), (3, 1), (2, 0), (2, 2), (1, 2), (3, 0)]
    stones = {
        # Pawn cell (drawn last as the pawn itself, no checker).
        # 3 White scoring cells, 3 Black scoring cells.
        (1, 1): "W", (2, 0): "W", (1, 2): "W",
        (3, 1): "B", (2, 2): "B", (3, 0): "B",
        # Some extra non-scoring checkers to look like a real game.
        (0, 0): "W", (0, 1): "W", (4, 0): "B", (0, 4): "B", (4, 0): "B",
    }
    return _draw_trike_diagram(c, region, side=5, stones_axial=stones,
                               pawn_axial=pawn, score_cells=score_cells,
                               theme=theme)


def _rules_body_lines(c, x, y_state, text, max_w, font="Helvetica", size=12,
                     line_height=15, bottom_limit=None):
    """Word-wrap `text` into lines and draw them, advancing the y cursor.

    `y_state` is a single-element list [y] used as a mutable cell so the caller
    can read the advanced cursor after return. Stops drawing if y would drop
    below `bottom_limit` (so body text doesn't run into the page footer).
    Returns the final y position.
    """
    y = y_state[0]
    c.setFont(font, size)
    words = text.split()
    line = ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font, size) > max_w:
            if bottom_limit is not None and y < bottom_limit:
                y_state[0] = y
                return y
            c.drawString(x, y, line)
            y -= line_height
            line = w
        else:
            line = test
    if line:
        if bottom_limit is not None and y < bottom_limit:
            y_state[0] = y
            return y
        c.drawString(x, y, line)
        y -= line_height
    y -= 4
    y_state[0] = y
    return y


def _draw_hex_rules_page(c, page_w, page_h, theme="classic",
                         label_set="wb", stone_mode=False):
    """Draw a one-page Hex rules summary as the final page of the PDF."""
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    text_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle_color = "#888888" if theme != "dark" else "#BBBBBB"
    accent = theme_def["black"]
    p1, p2 = LABEL_SETS[label_set]

    margin = 54  # 0.75 inch
    x = margin
    y = page_h - margin
    max_w = page_w - 2 * margin

    # Title
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.HexColor(text_color))
    c.drawString(x, y, "How to Play Hex")
    y -= 36

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawString(x, y, "Invented by Piet Hein (1942) \u2022 Rediscovered by John Nash (1949)")
    y -= 36

    def section(title_text):
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(accent))
        c.drawString(x, y, title_text)
        y -= 20

    def body(text):
        nonlocal y
        c.setFillColor(colors.HexColor(text_color))
        y = _rules_body_lines(c, x, [y], text, max_w,
                              bottom_limit=margin / 2 + 30)

    def diagram(draw_fn, caption, height_pt=140):
        """Reserve vertical space, draw a centered diagram + caption, advance y."""
        nonlocal y
        y -= 6
        region = (x, y - height_pt, max_w, height_pt)
        draw_fn(c, region, theme=theme)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor(subtle_color))
        c.drawCentredString(page_w / 2, y - height_pt - 12, caption)
        y -= height_pt + 36

    section("Players")
    body("Two players. One plays " + p1 + ", the other plays " + p2 + ".")

    section("Setup")
    if stone_mode:
        body("Use the board on the previous page with your stone set. Each player has stones of their own color. Decide who goes first (typically the " + p2.split()[0] + " player).")
    else:
        body("Use the board on the previous page with pen and paper. Each player needs a pen or marker. Decide who goes first (typically the " + p2.split()[0] + " player).")

    section("Goal")
    body("Be the first to form a connected chain of your own stones linking your two assigned sides of the board.")

    section("How to play")
    if stone_mode:
        body("On your turn, place a stone of your color on any empty hex cell, centered within the hex. Stones are never moved or removed.")
    else:
        body("On your turn, mark any empty hex cell with your symbol (X, O, your initial, or a color). Marks are never erased or overwritten.")

    section("Win condition")
    body("Connect your two opposite sides with a chain of your stones. A draw is impossible \u2014 the Brouwer fixed-point theorem guarantees one player must win.")

    diagram(_draw_hex_win_diagram,
            "Example: White wins by connecting the top and bottom edges.",
            height_pt=80)

    section("The swap rule (recommended for fairness)")
    body("After the first player makes their opening move, the second player may choose to either keep their color or swap colors. This largely nullifies the first-move advantage.")

    section("Coordinate notation")
    body("Columns use standard Go notation: a\u2013h, then j\u2013z (the letter i is skipped, per Go convention). Rows are numbered 1\u2013N from bottom to top. A cell's address is column+row, e.g. \u201cf7\u201d refers to column f, row 7.")

    # Footer
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor(subtle_color))
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawCentredString(page_w / 2, margin / 2 - 6,
        "Hex is a member of the connection game family. See en.wikipedia.org/wiki/Hex_(board_game) for the full rules.")


def _draw_rex_rules_page(c, page_w, page_h, theme="classic", stone_mode=False):
    """One-page rules summary for Rex, the misère variant of Hex."""
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    text_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle_color = "#888888" if theme != "dark" else "#BBBBBB"
    accent = theme_def["black"]
    p1, p2 = LABEL_SETS["wb"]

    margin = 54
    x = margin
    y = page_h - margin
    max_w = page_w - 2 * margin

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.HexColor(text_color))
    c.drawString(x, y, "How to Play Rex")
    y -= 36

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawString(x, y, "Mis\u00e8re Hex \u2022 algebraic variant of the classic connection game")
    y -= 36

    def section(title_text):
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(accent))
        c.drawString(x, y, title_text)
        y -= 20

    def body(text):
        nonlocal y
        c.setFillColor(colors.HexColor(text_color))
        y = _rules_body_lines(c, x, [y], text, max_w,
                              bottom_limit=margin / 2 + 30)

    def diagram(draw_fn, caption, height_pt=80):
        """Reserve vertical space, draw a centered diagram + caption, advance y."""
        nonlocal y
        y -= 6
        region = (x, y - height_pt, max_w, height_pt)
        draw_fn(c, region, theme=theme)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor(subtle_color))
        c.drawCentredString(page_w / 2, y - height_pt - 12, caption)
        y -= height_pt + 36

    section("Players")
    body("Two players. One plays " + p1 + ", the other plays " + p2 + ".")

    section("Setup")
    if stone_mode:
        body("Use the board on the previous page with two colors of stones. Decide who goes first.")
    else:
        body("Use the board on the previous page with pen and paper. Two symbols or colors. Decide who goes first.")

    section("Goal")
    body("Rex is the misère variant of Hex: the player who connects their two sides LOSES. Win by forcing your opponent to be the first to complete a chain.")

    section("How to play")
    if stone_mode:
        body("On your turn, place a stone of your color on any empty hex cell, centered within the hex. Stones are never moved or removed.")
    else:
        body("On your turn, mark any empty hex cell with your symbol. Marks are never erased or overwritten.")

    section("Win condition")
    body("You win when your opponent completes a connected chain linking their two assigned sides. A draw is impossible \u2014 the Brouwer fixed-point theorem still guarantees one player must connect first.")

    diagram(_draw_rex_win_diagram,
            "Example: White has just connected top and bottom \u2014 White LOSES, Black wins.",
            height_pt=80)

    section("Strategy hint")
    body("Rex slows the game down \u2014 both players are trying not to win. Look for 'forced' threats that compress your opponent's options until they have no choice but to complete their own chain.")

    section("Coordinate notation")
    body("Columns use standard Go notation: a\u2013h, then j\u2013z (the letter i is skipped, per Go convention). Rows are numbered 1\u2013N from bottom to top. A cell's address is column+row, e.g. \u201cf7\u201d refers to column f, row 7.")

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor(subtle_color))
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawCentredString(page_w / 2, margin / 2 - 6,
        "Rex is a member of the Hex family of connection games.")


def _draw_yavalath_rules_page(c, page_w, page_h, theme="classic", stone_mode=False):
    """One-page rules summary for Yavalath (Cameron Browne, 2007)."""
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    text_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle_color = "#888888" if theme != "dark" else "#BBBBBB"
    accent = theme_def["black"]

    margin = 54
    x = margin
    y = page_h - margin
    max_w = page_w - 2 * margin

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.HexColor(text_color))
    c.drawString(x, y, "How to Play Yavalath")
    y -= 36

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawString(x, y, "Designed by Cameron Browne's Ludi program \u2022 Nestorgames, 2007")
    y -= 36

    def section(title_text):
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(accent))
        c.drawString(x, y, title_text)
        y -= 20

    def body(text):
        nonlocal y
        c.setFillColor(colors.HexColor(text_color))
        y = _rules_body_lines(c, x, [y], text, max_w,
                              bottom_limit=margin / 2 + 30)

    def diagram(draw_fn, caption, height_pt=80):
        """Reserve vertical space, draw a centered diagram + caption, advance y."""
        nonlocal y
        y -= 6
        region = (x, y - height_pt, max_w, height_pt)
        draw_fn(c, region, theme=theme)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor(subtle_color))
        c.drawCentredString(page_w / 2, y - height_pt - 12, caption)
        y -= height_pt + 36

    section("Players")
    body("Two players. Each has stones of their own color (White and Black).")

    section("Setup")
    if stone_mode:
        body("Use the hexagon board on the previous page. Each player needs 30 stones of their color (about half the 61 cells). The board is a regular hexagon — no side bands, cells only.")
    else:
        body("Use the hexagon board on the previous page. Each player needs 30 markers in two colors. The board is a regular hexagon — no side bands, cells only.")

    section("Goal")
    body("Be the first to place 4 of your stones in an unbroken straight line in any direction. BUT if you ever place 3 in a row (and only 3, not 4), you LOSE.")

    section("How to play")
    body("On your turn, place a stone on any empty hex cell. Stones are never moved or removed. Lines of 4 or more win immediately; a line of exactly 3 loses immediately (unless it is also part of a line of 4 or more, in which case the 4 wins).")

    section("The 3-or-4 rule")
    body("This is the twist that defines Yavalath: making a line of exactly three stones loses the game. So you may not 'play around' an opponent's setup with three-of-a-kind threats \u2014 the threat backfires.")

    diagram(_draw_yavalath_win_diagram,
            "Example: White wins with 4 in a row (the lighter stones).",
            height_pt=70)

    section("Setup (optional swap rule)")
    body("White plays first. On White's second turn, Black may take White's opening stone and switch colors. This balances the first-player advantage. The same set also plays Pentalath (5-in-a-row with Go-style captures) and a three-player variant.")

    section("Coordinate notation")
    body("Cells use axial coordinates (q, r). The center cell is (0, 0). The six corner cells are at distance 4 from center. Notation: q,r (e.g. \u201c2,-1\u201d).")

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor(subtle_color))
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawCentredString(page_w / 2, margin / 2 - 6,
        "Yavalath rules by Cameron Browne \u2022 nestorgames.com rulebook PDF")


# ──────────────────────────────────────────────────────────────────────────────
# Havannah drawing
# ──────────────────────────────────────────────────────────────────────────────


def _havannah_cell_color(theme_def, q, r):
    """Alternating fill based on (q + r) parity, matching Hex's checkerboard."""
    return theme_def["fill_a"] if (q + r) & 1 else theme_def["fill_b"]


def draw_havannah_board_into_region(c, base, region, margin_pt,
                                    pen_paper, coords, theme, corner_dots,
                                    draw_title=True, cell_coords=False,
                                    game_label="HAVANNAH"):
    """Draw a base-N Havannah board into a rectangular region.

    `region` = (x, y, w, h): bottom-left corner plus size of the region.
    The board fills the region (with its own internal margin_pt).
    Returns the r used (in points).
    """
    rx, ry, rw, rh = region
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(rx, ry, rw, rh, fill=True, stroke=False)

    gw_units, gh_units = havannah_extent_r_units(base)
    r = min(rw / gw_units, rh / gh_units) * 0.92

    center_x = rx + rw / 2
    center_y = ry + rh / 2

    # Havannah hex grid is symmetric about its center; extent is ±(N - 0.5)·r.
    extent = (base - 0.5) * r
    offset_x = center_x
    offset_y = center_y

    if draw_title:
        title = (f"{game_label} BOARD \u2014 PAPER & PENCIL (BASE-{base})"
                 if pen_paper else
                 f"{game_label} BOARD (BASE-{base})")
        title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor(title_color))
        c.drawCentredString(center_x, ry + rh - 12, title)

    c.setStrokeColor(colors.HexColor(theme_def["stroke"]))
    c.setLineWidth(1.0)
    for q, rr in havannah_cells(base):
        cx, cy = axial_to_pixel(q, rr, r)
        cx += offset_x
        cy += offset_y
        pts = hex_vertices(cx, cy, r)
        c.setFillColor(colors.HexColor(_havannah_cell_color(theme_def, q, rr)))
        path = c.beginPath()
        path.moveTo(pts[0][0], pts[0][1])
        for p in pts[1:]:
            path.lineTo(p[0], p[1])
        path.close()
        c.drawPath(path, fill=True, stroke=True)

    # Optional corner dots: Havannah has 6 corner cells (no side bands).
    if corner_dots:
        c.setFillColor(colors.HexColor(theme_def["black"]))
        for q, rr in havannah_corners(base):
            cx, cy = axial_to_pixel(q, rr, r)
            c.circle(cx + offset_x, cy + offset_y, r * 0.18, fill=True, stroke=False)

    # Cell labels (axial q,r). Only when cells are large enough to be legible.
    show_cell_labels = cell_coords or ((coords or pen_paper) and r >= 11)
    if show_cell_labels:
        cell_color = "#FFFFFF" if theme == "dark" else "#444444"
        cell_font = max(6, r * 0.28)
        c.setFont("Helvetica", cell_font)
        c.setFillColor(colors.HexColor(cell_color))
        for q, rr in havannah_cells(base):
            cx, cy = axial_to_pixel(q, rr, r)
            c.drawCentredString(cx + offset_x, cy + offset_y - cell_font * 0.35, f"{q},{rr}")

    return r


def write_havannah_svg(output_filename, base, paper="letter", margin_pt=None, mode="safe",
                       pen_paper=False, coords=True, theme="classic",
                       corner_dots=False, rules=False, game_label="HAVANNAH"):
    """Render a Havannah board as SVG (vector, web-friendly). Single page only."""
    page_w, page_h = pick_page_size(paper, base)
    if margin_pt is None:
        if mode in ("makeitwork", "unsafe"):
            margin_pt = 4
        else:
            margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, _, _ = compute_r(page_w, page_h, margin_pt, base, extent_fn=havannah_extent_r_units)

    theme_def = THEMES[theme]
    center_x = page_w / 2
    center_y = page_h / 2

    bg = theme_def["page_bg"] or "#FFFFFF"
    title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle = "#888888" if theme != "dark" else "#BBBBBB"

    # Reserve title strip + footer strip so they don't overlap the board.
    title_strip = 28
    footer_strip = 18 if pen_paper else 0
    board_top = page_h - title_strip
    board_h = board_top - footer_strip
    board_cx = page_w / 2
    board_cy = footer_strip + board_h / 2

    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w:.0f}" height="{page_h:.0f}" viewBox="0 0 {page_w:.0f} {page_h:.0f}">',
           f'<rect width="{page_w:.0f}" height="{page_h:.0f}" fill="{bg}"/>']

    title = (f"{game_label} BOARD \u2014 PAPER & PENCIL (BASE-{base})"
             if pen_paper else f"{game_label} BOARD (BASE-{base})")
    title_y = page_h - max(14, margin_pt / 2)
    out.append(
        f'<text x="{board_cx:.2f}" y="{title_y:.2f}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="16" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>'
    )

    for q, rr in havannah_cells(base):
        cx, cy = axial_to_pixel(q, rr, r)
        cx += board_cx
        cy += board_cy
        pts = hex_vertices(cx, cy, r)
        fill = _havannah_cell_color(theme_def, q, rr)
        pts_str = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        out.append(
            f'<polygon points="{pts_str}" fill="{fill}" stroke="{theme_def["stroke"]}" stroke-width="1"/>'
        )

    if corner_dots:
        for q, rr in havannah_corners(base):
            cx, cy = axial_to_pixel(q, rr, r)
            out.append(
                f'<circle cx="{cx + board_cx:.2f}" cy="{cy + board_cy:.2f}" '
                f'r="{r * 0.18:.2f}" fill="{theme_def["black"]}"/>'
            )

    if (coords or pen_paper) and r >= 11:
        cell_color = "#FFFFFF" if theme == "dark" else "#444444"
        cell_font = max(6, r * 0.28)
        for q, rr in havannah_cells(base):
            cx, cy = axial_to_pixel(q, rr, r)
            out.append(
                f'<text x="{cx + board_cx:.2f}" y="{cy + board_cy + cell_font * 0.35:.2f}" '
                f'font-family="Helvetica,Arial,sans-serif" font-size="{cell_font:.1f}" '
                f'fill="{cell_color}" text-anchor="middle">{q},{rr}</text>'
            )

    if pen_paper:
        hint = "Mark cells with X / O / your initial.  \u2022  Notation: q,r (axial)."
        footer = (f"{hint}  \u2022  White moves first.  "
                  f"\u2022  Connect any two of: 2 corners, 3 edges, or a ring.")
        out.append(
            f'<text x="{board_cx:.2f}" y="{max(14, footer_strip / 2 + 6):.2f}" '
            f'font-family="Helvetica,Arial,sans-serif" font-size="8" font-style="italic" '
            f'fill="{subtle}" text-anchor="middle">{footer}</text>'
        )

    out.append('</svg>')
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def draw_havannah_board(output_filename, base, paper="letter", margin_pt=None,
                        pen_paper=False, coords=True, mode="safe",
                        theme="classic", corner_dots=False, rules=False,
                        cell_coords=False, stone_mode=False,
                        game_label="HAVANNAH"):
    page_w, page_h = pick_page_size(paper, base)
    if margin_pt is None:
        if mode in ("makeitwork", "unsafe"):
            margin_pt = 4
        else:
            margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, max_w, max_h = compute_r(page_w, page_h, margin_pt, base,
                                extent_fn=havannah_extent_r_units)

    c = canvas.Canvas(output_filename, pagesize=(page_w, page_h))
    theme_def = THEMES[theme]

    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    title = (f"{game_label} BOARD \u2014 PAPER & PENCIL (BASE-{base})"
             if pen_paper else
             f"{game_label} BOARD (BASE-{base})")
    c.setTitle(title)
    title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor(title_color))
    title_y = max(14, margin_pt / 2)
    c.drawCentredString(page_w / 2, page_h - title_y, title)

    # Reserve title strip at top + footer strip at bottom (for pen-paper footer).
    title_strip = 28
    footer_strip = 18 if pen_paper else 0
    board_region = (0, footer_strip, page_w, page_h - title_strip - footer_strip)

    draw_havannah_board_into_region(
        c, base, board_region, margin_pt,
        pen_paper, coords, theme, corner_dots,
        draw_title=False, cell_coords=cell_coords,
        game_label=game_label,
    )

    if pen_paper:
        footer_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
        if stone_mode:
            hint = "Place stones in hex centers.  \u2022  Notation: q,r (axial)."
        else:
            hint = "Mark cells with X / O / your initial.  \u2022  Notation: q,r (axial)."
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor(footer_color))
        c.drawCentredString(page_w / 2, max(14, margin_pt / 2),
            f"{hint}  \u2022  White moves first.  \u2022  Connect any two of: 2 corners, 3 edges, or a ring.")

    if rules:
        c.showPage()
        draw_havannah_rules_page(c, page_w, page_h, theme=theme, stone_mode=stone_mode)
        c.showPage()
    else:
        c.showPage()
    c.save()

    return r


def draw_havannah_rules_page(c, page_w, page_h, theme="classic", stone_mode=False):
    """Draw a one-page Havannah rules summary as the final page of the PDF."""
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    text_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle_color = "#888888" if theme != "dark" else "#BBBBBB"
    accent = theme_def["black"]

    margin = 54  # 0.75 inch
    x = margin
    y = page_h - margin
    max_w = page_w - 2 * margin

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.HexColor(text_color))
    c.drawString(x, y, "How to Play Havannah")
    y -= 36

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawString(x, y, "Invented by Christian Freeling (1981) \u2022 Connection game family")
    y -= 36

    def section(title_text):
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(accent))
        c.drawString(x, y, title_text)
        y -= 20

    def body(text):
        nonlocal y
        c.setFillColor(colors.HexColor(text_color))
        y = _rules_body_lines(c, x, [y], text, max_w,
                              bottom_limit=margin / 2 + 30)

    def diagrams_row(items, total_height_pt=110, caption_pt=18):
        """Render a horizontal row of small diagrams.

        `items`: list of (draw_fn, caption) tuples. Each gets equal horizontal
        space. The row reserves `total_height_pt` vertically; each caption sits
        `caption_pt` below the row.
        """
        nonlocal y
        y -= 6
        n = len(items)
        gap = 14
        cell_w = (max_w - gap * (n - 1)) / n
        for i, (draw_fn, caption) in enumerate(items):
            cell_x = x + i * (cell_w + gap)
            region = (cell_x, y - total_height_pt + caption_pt, cell_w,
                      total_height_pt - caption_pt)
            draw_fn(c, region, theme=theme)
            c.setFont("Helvetica-Oblique", 9)
            c.setFillColor(colors.HexColor(subtle_color))
            c.drawCentredString(cell_x + cell_w / 2, y - total_height_pt,
                                caption)
        y -= total_height_pt + 22

    section("Players")
    body("Two players. One plays white stones, the other plays black stones.")

    section("Setup")
    if stone_mode:
        body("Use the board on the previous page with your stone set. Each player has stones of their own color.")
    else:
        body("Use the board on the previous page with pen and paper. Each player needs a pen or marker.")

    section("Goal")
    body("Be the first to complete any one of three structures using connected stones of your color:")

    section("Win condition 1: ring")
    body("Form a closed loop around one or more cells (the encircled cells may be occupied by either player or empty).")

    section("Win condition 2: bridge")
    body("Connect any two of the six corner cells of the board.")

    section("Win condition 3: fork")
    body("Connect any three of the six edges of the board. (Corner cells are not part of an edge.)")

    diagrams_row([
        (_draw_havannah_ring_diagram,    "Ring"),
        (_draw_havannah_bridge_diagram,  "Bridge"),
        (_draw_havannah_fork_diagram,    "Fork"),
    ], total_height_pt=95)

    section("How to play")
    if stone_mode:
        body("On your turn, place a stone of your color on any empty hex cell, centered within the hex. Stones are never moved or removed.")
    else:
        body("On your turn, mark any empty hex cell with your symbol (X, O, your initial, or a color). Marks are never erased or overwritten.")

    section("The pie rule (recommended for fairness)")
    body("After the first player makes their opening move, the second player may choose to either keep their color or swap colors. This largely nullifies the first-move advantage.")

    section("Coordinate notation")
    body("Cells use axial (cube) coordinates (q, r) with s = \u2212q \u2212 r. A cell's address is the pair q,r, e.g. \"3,\u22122\".")

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor(subtle_color))
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawCentredString(page_w / 2, margin / 2 - 6,
        "Havannah is a member of the connection game family. See en.wikipedia.org/wiki/Havannah_(board_game) for the full rules.")


# ──────────────────────────────────────────────────────────────────────────────
# Trike drawing
# ──────────────────────────────────────────────────────────────────────────────


def _trike_cell_color(theme_def, q, r):
    """Alternating fill based on (q + r) parity, matching Hex/Havannah."""
    return theme_def["fill_a"] if (q + r) & 1 else theme_def["fill_b"]


def draw_trike_board_into_region(c, side, region, margin_pt,
                                 pen_paper, coords, theme,
                                 draw_title=True, cell_coords=False):
    """Draw a side-N Trike board (point-up triangle) into a rectangular region.

    `region` = (x, y, w, h): bottom-left corner plus size of the region.
    The board fills the region (with its own internal margin_pt).
    Returns the r used (in points).
    """
    rx, ry, rw, rh = region
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(rx, ry, rw, rh, fill=True, stroke=False)

    gw_units, gh_units = trike_extent_r_units(side)
    # Reserve ~2r of vertical slack: hex vertices extend r above the top cell
    # center and r below the bottom cell center, so the bounding box of all
    # drawn hexes is larger than the cell-center bounding box by 2r in y.
    # Use a binary search-friendly closed form: r such that
    #   r*gh_units + 2r = rh   →   r = rh / (gh_units + 2)
    r_y = rh / (gh_units + 2)
    r_x = rw / gw_units
    r = min(r_x, r_y) * 0.96

    # Triangle vertices in local coords:
    #   bottom-left  = (0, 0)
    #   bottom-right = (R*sqrt(3)*(N-1), 0)
    #   top          = (R*sqrt(3)*(N-1)/2, R*1.5*(N-1))
    # Center horizontally; align bottom edge with the bottom of the region so
    # the apex has clearance toward the top.
    triangle_w = gw_units * r
    triangle_h = gh_units * r
    board_cx = rx + rw / 2
    anchor_x = board_cx - triangle_w / 2
    anchor_y = ry + r  # bottom-left vertex's hex center; its bottom edge is at ry.

    if draw_title:
        title = (f"TRIKE BOARD \u2014 PAPER & PENCIL (SIDE-{side})"
                 if pen_paper else
                 f"TRIKE BOARD (SIDE-{side})")
        title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor(title_color))
        c.drawCentredString(board_cx, ry + rh - 12, title)

    c.setStrokeColor(colors.HexColor(theme_def["stroke"]))
    c.setLineWidth(1.0)
    for q, rr in trike_cells(side):
        cx, cy = axial_to_pixel(q, rr, r)
        cx += anchor_x
        cy += anchor_y
        pts = hex_vertices(cx, cy, r)
        c.setFillColor(colors.HexColor(_trike_cell_color(theme_def, q, rr)))
        path = c.beginPath()
        path.moveTo(pts[0][0], pts[0][1])
        for p in pts[1:]:
            path.lineTo(p[0], p[1])
        path.close()
        c.drawPath(path, fill=True, stroke=True)

    # Cell labels (axial q,r). Only when cells are large enough.
    show_cell_labels = cell_coords or ((coords or pen_paper) and r >= 11)
    if show_cell_labels:
        cell_color = "#FFFFFF" if theme == "dark" else "#444444"
        cell_font = max(5, r * 0.24)
        c.setFont("Helvetica", cell_font)
        c.setFillColor(colors.HexColor(cell_color))
        for q, rr in trike_cells(side):
            cx, cy = axial_to_pixel(q, rr, r)
            c.drawCentredString(cx + anchor_x, cy + anchor_y - cell_font * 0.35, f"{q},{rr}")

    return r


def write_trike_svg(output_filename, side, paper="letter", margin_pt=None, mode="safe",
                    pen_paper=False, coords=True, theme="classic", rules=False):
    """Render a side-N Trike board as SVG (vector, web-friendly). Single page only."""
    page_w, page_h = pick_page_size(paper, side)
    if margin_pt is None:
        if mode in ("makeitwork", "unsafe"):
            margin_pt = 4
        else:
            margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, _, _ = compute_r(page_w, page_h, margin_pt, side, extent_fn=trike_extent_r_units)

    theme_def = THEMES[theme]
    subtle = "#888888" if theme != "dark" else "#BBBBBB"
    title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    bg = theme_def["page_bg"] or "#FFFFFF"

    # Reserve title + footer strips so they don't overlap the board.
    title_strip = 28
    footer_strip = 18 if pen_paper else 0
    board_top = page_h - title_strip
    board_h = board_top - footer_strip
    board_cx = page_w / 2
    board_cy = footer_strip + board_h / 2

    gw_units, gh_units = trike_extent_r_units(side)
    triangle_w = gw_units * r
    triangle_h = gh_units * r
    anchor_x = board_cx - triangle_w / 2
    anchor_y = footer_strip + r  # bottom-left vertex's hex center; bottom edge at footer_strip.

    out = [f'<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w:.0f}" height="{page_h:.0f}" viewBox="0 0 {page_w:.0f} {page_h:.0f}">',
           f'<rect width="{page_w:.0f}" height="{page_h:.0f}" fill="{bg}"/>']

    title = (f"TRIKE BOARD \u2014 PAPER & PENCIL (SIDE-{side})"
             if pen_paper else f"TRIKE BOARD (SIDE-{side})")
    title_y = page_h - max(14, margin_pt / 2)
    out.append(
        f'<text x="{board_cx:.2f}" y="{title_y:.2f}" font-family="Helvetica,Arial,sans-serif" '
        f'font-size="16" font-weight="bold" fill="{title_color}" text-anchor="middle">{title}</text>'
    )

    for q, rr in trike_cells(side):
        cx, cy = axial_to_pixel(q, rr, r)
        cx += anchor_x
        cy += anchor_y
        pts = hex_vertices(cx, cy, r)
        fill = _trike_cell_color(theme_def, q, rr)
        pts_str = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
        out.append(
            f'<polygon points="{pts_str}" fill="{fill}" stroke="{theme_def["stroke"]}" stroke-width="1"/>'
        )

    if (coords or pen_paper) and r >= 11:
        cell_color = "#FFFFFF" if theme == "dark" else "#444444"
        cell_font = max(5, r * 0.24)
        for q, rr in trike_cells(side):
            cx, cy = axial_to_pixel(q, rr, r)
            out.append(
                f'<text x="{cx + anchor_x:.2f}" y="{cy + anchor_y + cell_font * 0.35:.2f}" '
                f'font-family="Helvetica,Arial,sans-serif" font-size="{cell_font:.1f}" '
                f'fill="{cell_color}" text-anchor="middle">{q},{rr}</text>'
            )

    if pen_paper:
        hint = "Mark cells with X / O / your initial.  \u2022  Notation: q,r (axial)."
        footer = (f"{hint}  \u2022  P1 places first checker + pawn, P2 may swap.  "
                  f"\u2022  Highest adjacent-checker score when pawn is trapped wins.")
        out.append(
            f'<text x="{board_cx:.2f}" y="{max(14, footer_strip / 2 + 6):.2f}" '
            f'font-family="Helvetica,Arial,sans-serif" font-size="8" font-style="italic" '
            f'fill="{subtle}" text-anchor="middle">{footer}</text>'
        )

    out.append('</svg>')
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def draw_trike_board(output_filename, side, paper="letter", margin_pt=None,
                     pen_paper=False, coords=True, mode="safe",
                     theme="classic", rules=False,
                     cell_coords=False, stone_mode=False):
    page_w, page_h = pick_page_size(paper, side)
    if margin_pt is None:
        if mode in ("makeitwork", "unsafe"):
            margin_pt = 4
        else:
            margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, max_w, max_h = compute_r(page_w, page_h, margin_pt, side,
                                extent_fn=trike_extent_r_units)

    c = canvas.Canvas(output_filename, pagesize=(page_w, page_h))
    theme_def = THEMES[theme]

    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    title = (f"TRIKE BOARD \u2014 PAPER & PENCIL (SIDE-{side})"
             if pen_paper else
             f"TRIKE BOARD (SIDE-{side})")
    c.setTitle(title)
    title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor(title_color))
    title_y = max(14, margin_pt / 2)
    c.drawCentredString(page_w / 2, page_h - title_y, title)

    title_strip = 28
    footer_strip = 18 if pen_paper else 0
    board_region = (0, footer_strip, page_w, page_h - title_strip - footer_strip)
    draw_trike_board_into_region(
        c, side, board_region, margin_pt,
        pen_paper, coords, theme,
        draw_title=False, cell_coords=cell_coords,
    )

    if pen_paper:
        footer_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
        if stone_mode:
            hint = "Place stones/checkers on hexes.  \u2022  Notation: q,r (axial)."
        else:
            hint = "Mark cells with X / O / your initial.  \u2022  Notation: q,r (axial)."
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor(footer_color))
        c.drawCentredString(page_w / 2, max(14, margin_pt / 2),
            f"{hint}  \u2022  P1 places first checker + pawn, P2 may swap.  \u2022  Highest adjacent-checker score when pawn is trapped wins.")

    if rules:
        c.showPage()
        draw_trike_rules_page(c, page_w, page_h, theme=theme, stone_mode=stone_mode)
        c.showPage()
    else:
        c.showPage()
    c.save()

    return r


def draw_trike_rules_page(c, page_w, page_h, theme="classic", stone_mode=False):
    """Draw a one-page Trike rules summary as the final page of the PDF."""
    theme_def = THEMES[theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, page_w, page_h, fill=True, stroke=False)

    text_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
    subtle_color = "#888888" if theme != "dark" else "#BBBBBB"
    accent = theme_def["black"]

    margin = 54  # 0.75 inch
    x = margin
    y = page_h - margin
    max_w = page_w - 2 * margin

    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.HexColor(text_color))
    c.drawString(x, y, "How to Play Trike")
    y -= 36

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawString(x, y, "Designed by Alek Erickson (2020) \u2022 Combinatorial abstract")
    y -= 36

    def section(title_text):
        nonlocal y
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(accent))
        c.drawString(x, y, title_text)
        y -= 20

    def body(text):
        nonlocal y
        c.setFillColor(colors.HexColor(text_color))
        y = _rules_body_lines(c, x, [y], text, max_w,
                              bottom_limit=margin / 2 + 30)

    def diagram(draw_fn, caption, height_pt=110):
        """Reserve vertical space, draw a centered diagram + caption, advance y."""
        nonlocal y
        y -= 6
        region = (x, y - height_pt, max_w, height_pt)
        draw_fn(c, region, theme=theme)
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(colors.HexColor(subtle_color))
        c.drawCentredString(page_w / 2, y - height_pt - 12, caption)
        y -= height_pt + 36

    section("Players")
    body("Two players. One plays white checkers, the other plays black checkers. A single neutral pawn is shared.")

    section("Setup")
    if stone_mode:
        body("Use the board on the previous page. Each player needs their own colored checkers plus one shared neutral pawn.")
    else:
        body("Use the board on the previous page with pen and paper. Each player needs a pen or marker plus one shared neutral pawn (a coin or stone works).")

    section("Goal")
    body("Trap the pawn. When no legal move is possible, each player scores 1 point for every checker of their own color that is adjacent to \u2014 or sitting under \u2014 the pawn. The player with the higher score wins.")

    diagram(_draw_trike_win_diagram,
            "Pawn trapped \u2014 White scores the lighter dotted cells, Black scores the darker ones.",
            height_pt=110)

    section("How to play")
    if stone_mode:
        body("On your turn, move the pawn any number of empty cells in a straight line in any of the six axial directions. The pawn cannot pass over or land on an occupied cell. When you move the pawn, place a checker of your own color on the destination cell, then move the pawn on top of it.")
    else:
        body("On your turn, move the pawn any number of empty cells in a straight line in any of the six axial directions. The pawn cannot pass over or land on an occupied cell. When you move the pawn, mark the destination cell with your symbol (X, O, or your initial), then move the pawn on top of it.")

    section("Pie rule (recommended for fairness)")
    body("Player 1 makes the opening move. Player 2 may then either make a normal move, or swap sides and take the opening position. The pie rule cancels the first-move advantage. Board sizes 7\u201310 suit learning; 13\u201315 are standard for serious play; 7\u201319 are supported.")

    section("Coordinate notation")
    body("Cells use axial coordinates (q, r). A cell's address is the pair q,r, e.g. \"3,1\". The triangle's three vertex cells are (0, 0), (N\u22121, 0), and (0, N\u22121).")

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor(subtle_color))
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawCentredString(page_w / 2, margin / 2 - 6,
        "Trike is a combinatorial abstract. See boardgamegeek.com/boardgame/307379/trike for the full rules.")


def _n_up_layout(n):
    """Return (cols, rows) for a roughly-square N-up layout."""
    cols = int(math.ceil(math.sqrt(n)))
    rows = int(math.ceil(n / cols))
    return cols, rows


def _generate_multi(args, show_coords):
    """Render --sizes, --pad, or --n-up boards into a single PDF."""
    pw, ph = pick_page_size(args.paper, args.size)
    c = canvas.Canvas(args.output, pagesize=(pw, ph))
    theme_def = THEMES[args.theme]
    if theme_def["page_bg"]:
        c.setFillColor(colors.HexColor(theme_def["page_bg"]))
        c.rect(0, 0, pw, ph, fill=True, stroke=False)

    margin_pt = args.margin if args.margin is not None else (
        4 if args.mode in ("makeitwork", "unsafe") else DEFAULT_MARGINS_PT[args.paper]
    )

    is_havannah = args.game == "havannah" or args.variant == "yavalath"
    is_trike = args.game == "trike"
    is_yavalath = args.variant == "yavalath"

    def draw_board_into(region, size, draw_title, cell_coords):
        if is_havannah:
            return draw_havannah_board_into_region(
                c, size, region, margin_pt,
                args.pen_paper, show_coords, args.theme, args.corner_dots,
                draw_title=draw_title, cell_coords=cell_coords,
                game_label="YAVALATH" if is_yavalath else "HAVANNAH",
            )
        if is_trike:
            return draw_trike_board_into_region(
                c, size, region, margin_pt,
                args.pen_paper, show_coords, args.theme,
                draw_title=draw_title, cell_coords=cell_coords,
            )
        return draw_board_into_region(
            c, size, region, margin_pt,
            args.pen_paper, show_coords, args.theme, args.label_set, args.corner_dots,
            draw_title=draw_title, cell_coords=cell_coords, variant=args.variant,
        )

    def draw_rules(c, pw, ph):
        if is_havannah and not is_yavalath:
            return draw_havannah_rules_page(c, pw, ph, theme=args.theme,
                                            stone_mode=args.stone_mode or args.stone_size is not None)
        if is_yavalath:
            return _draw_yavalath_rules_page(c, pw, ph, theme=args.theme,
                                             stone_mode=args.stone_mode or args.stone_size is not None)
        if is_trike:
            return draw_trike_rules_page(c, pw, ph, theme=args.theme,
                                         stone_mode=args.stone_mode or args.stone_size is not None)
        return draw_rules_page(c, pw, ph, theme=args.theme, label_set=args.label_set,
                               stone_mode=args.stone_mode or args.stone_size is not None,
                               variant=args.variant)

    if args.sizes:
        sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
        if not sizes:
            print("Error: --sizes requires a comma-separated list.", file=sys.stderr)
            sys.exit(2)
        # Title for booklet.
        title_color = "#FFFFFF" if args.theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(title_color))
        if is_yavalath:
            ref_label = "YAVALATH REFERENCE  "
            sz_label = lambda s: f"hexhex-{s}"
            doc_title = "Yavalath Reference"
        elif is_havannah:
            ref_label = "HAVANNAH REFERENCE  "
            sz_label = lambda s: f"base-{s}"
            doc_title = "Havannah Reference"
        elif is_trike:
            ref_label = "TRIKE REFERENCE  "
            sz_label = lambda s: f"side-{s}"
            doc_title = "Trike Reference"
        elif args.variant == "rex":
            ref_label = "REX REFERENCE  "
            sz_label = lambda s: f"hexhex-{s}"
            doc_title = "Rex Reference"
        else:
            ref_label = "HEX BOARD REFERENCE  "
            sz_label = lambda s: f"{s}x{s}"
            doc_title = "Hex Board Reference"
        title = ref_label + "  \u2022  ".join(sz_label(s) for s in sizes)
        c.setTitle(doc_title)
        c.drawCentredString(pw / 2, ph - max(14, margin_pt / 2), title)
        for sz in sizes:
            draw_board_into((0, 0, pw, ph), sz, draw_title=True, cell_coords=args.cell_coords)
            c.showPage()
            # Page bg fill resets each page.
            if theme_def["page_bg"]:
                c.setFillColor(colors.HexColor(theme_def["page_bg"]))
                c.rect(0, 0, pw, ph, fill=True, stroke=False)
        print(f"Generated {len(sizes)}-page reference: sizes {sizes} on {args.paper}.")
        if args.rules:
            draw_rules(c, pw, ph)
            c.showPage()
            print("  + rules page")

    elif args.pad:
        for i in range(args.pad):
            draw_board_into((0, 0, pw, ph), args.size, draw_title=True,
                            cell_coords=args.cell_coords)
            c.showPage()
            if theme_def["page_bg"]:
                c.setFillColor(colors.HexColor(theme_def["page_bg"]))
                c.rect(0, 0, pw, ph, fill=True, stroke=False)
        if is_yavalath:
            print(f"Generated {args.pad}-sheet pad of hexhex-{args.size} Yavalath boards on {args.paper}.")
        elif is_havannah:
            print(f"Generated {args.pad}-sheet pad of base-{args.size} Havannah boards on {args.paper}.")
        elif is_trike:
            print(f"Generated {args.pad}-sheet pad of side-{args.size} Trike boards on {args.paper}.")
        elif args.variant == "yavalath":
            print(f"Generated {args.pad}-sheet pad of hexhex-{args.size} Yavalath boards on {args.paper}.")
        elif args.variant == "rex":
            print(f"Generated {args.pad}-sheet pad of hexhex-{args.size} Rex boards on {args.paper}.")
        else:
            print(f"Generated {args.pad}-sheet pad of {args.size}x{args.size} boards on {args.paper}.")
        if args.rules:
            draw_rules(c, pw, ph)
            c.showPage()
            print("  + rules page")

    else:  # --n-up
        n = args.n_up
        cols, rows = _n_up_layout(n)
        gutter = 18  # points between boards
        cell_w = (pw - gutter * (cols + 1)) / cols
        cell_h = (ph - gutter * (rows + 1)) / rows
        # Title across top.
        title_color = "#FFFFFF" if args.theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor(title_color))
        if is_yavalath:
            c.setTitle(f"Yavalath Board hexhex-{args.size} ({n}-up)")
            c.drawCentredString(pw / 2, ph - 12, f"HEXHEX-{args.size}  \u00d7  {n} PER PAGE")
        elif is_havannah:
            c.setTitle(f"Havannah Board base-{args.size} ({n}-up)")
            c.drawCentredString(pw / 2, ph - 12, f"BASE-{args.size}  \u00d7  {n} PER PAGE")
        elif is_trike:
            c.setTitle(f"Trike Board side-{args.size} ({n}-up)")
            c.drawCentredString(pw / 2, ph - 12, f"SIDE-{args.size}  \u00d7  {n} PER PAGE")
        else:
            c.setTitle(f"Hex Board {args.size}x{args.size} ({n}-up)")
            c.drawCentredString(pw / 2, ph - 12, f"{args.size}x{args.size}  \u00d7  {n} PER PAGE")

        for i in range(n):
            r = i // cols
            cn = i % cols
            x = gutter + cn * (cell_w + gutter)
            y = gutter + r * (cell_h + gutter)
            draw_board_into((x, y, cell_w, cell_h), args.size, draw_title=False,
                            cell_coords=args.cell_coords)
        c.showPage()
        if is_havannah:
            print(f"Generated 1-page {cols}x{rows} handout ({n} copies of base-{args.size} Havannah) on {args.paper}.")
        elif is_trike:
            print(f"Generated 1-page {cols}x{rows} handout ({n} copies of side-{args.size} Trike) on {args.paper}.")
        else:
            print(f"Generated 1-page {cols}x{rows} handout ({n} copies of {args.size}x{args.size}) on {args.paper}.")

    if args.rules:
        draw_rules(c, pw, ph)
        c.showPage()
        print("  + rules page")

    c.save()


def validate_and_normalize(args):
    """Normalize and validate parsed argparse args; return dispatch-ready values.

    Resolves `--game rex` / `--game yavalath` aliases, derives the default
    size, picks the game-extent helper + label string, applies paper
    auto-selection when `--stone-size` is set, checks stone fit, emits
    warnings for flags that are silently ignored on certain games, and
    returns a tuple of values the dispatch block needs.

    Returns:
        (args, game_extent_fn, game_label, margin_pt, stone_mode,
         show_coords, warnings, error)

    `args` is mutated in place and also returned for convenience.
    `warnings` is a list of human-readable strings; `error` is None on
    success or a string the caller should print and exit(2) on.

    Per the locked decision in issue #3: this function does NOT call
    `sys.exit` itself. The caller handles exit so the function stays
    unit-testable.
    """
    warnings = []
    error = None

    # --game rex / --game yavalath are convenience aliases for
    # --game hex --variant rex / --variant yavalath.
    if args.game in ("rex", "yavalath"):
        if args.variant is not None and args.variant != args.game:
            error = (f"--variant {args.variant!r} conflicts with "
                     f"--game {args.game!r}. Pick one.")
            return args, None, None, None, False, False, warnings, error
        args.variant = args.game
        args.game = "hex"

    # Derive the default size from the (now-resolved) game/variant.
    if args.size is None:
        if args.variant is not None:
            game_key = args.variant
        elif args.game in ("havannah", "trike"):
            game_key = args.game
        else:
            game_key = "hex"
        args.size = DEFAULT_SIZES.get(game_key, 11)
        warnings.append(
            f"Using default size {args.size} for {game_key} "
            f"(most-played standard). Pass an integer to override."
        )

    # --variant only makes sense with --game hex.
    if args.variant is not None and args.game != "hex":
        error = (f"--variant {args.variant!r} requires --game hex "
                 f"(got --game {args.game!r}).")
        return args, None, None, None, False, False, warnings, error

    # Pick the geometry helper + display label.
    if args.game == "havannah" or args.variant == "yavalath":
        game_extent_fn = havannah_extent_r_units
        if args.variant == "yavalath":
            game_label = f"YAVALATH HEXHEX-{args.size}"
        else:
            game_label = f"HAVANNAH BASE-{args.size}"
    elif args.game == "trike":
        game_extent_fn = trike_extent_r_units
        game_label = f"TRIKE SIDE-{args.size}"
    else:
        game_extent_fn = grid_extent_r_units
        if args.variant == "yavalath":
            game_label = f"YAVALATH HEXHEX-{args.size}"
        elif args.variant == "rex":
            game_label = f"REX HEXHEX-{args.size}"
        else:
            game_label = f"HEX {args.size}x{args.size}"

    if args.size < 2:
        error = "Board size must be at least 2."
        return args, game_extent_fn, game_label, None, False, False, warnings, error

    # Flags that are silently ignored on certain games — warn loudly.
    if args.game in ("havannah", "trike") and args.label_set != "wb":
        flag_game = "Havannah" if args.game == "havannah" else "Trike"
        warnings.append(
            f"--label-set is ignored for {flag_game} (no side bands)."
        )
    if args.variant == "yavalath":
        if args.label_set != "wb":
            warnings.append(
                "--label-set is ignored for Yavalath (no side bands)."
            )
        if args.corner_dots:
            warnings.append(
                "--corner-dots is ignored for Yavalath (no marked corners)."
            )
    if args.game == "trike" and args.corner_dots:
        warnings.append(
            "--corner-dots is ignored for Trike (no marked corners)."
        )

    margin_pt = args.margin if args.margin is not None else None

    # --stone-mode auto-enables when a stone size was specified.
    stone_mode = args.stone_mode or args.stone_size is not None

    # Paper auto-selection when --stone-size is given and --paper is omitted.
    if args.paper is None:
        if args.stone_size is None:
            args.paper = "letter"
        else:
            margin_for_calc = (margin_pt if margin_pt is not None
                              else min(DEFAULT_MARGINS_PT.values()))
            picked, orient, ratio = auto_pick_paper(
                args.size, args.stone_size, margin_for_calc, mode=args.mode,
                extent_fn=game_extent_fn,
            )
            if picked is None:
                error = (f"no paper size is large enough for {game_label} "
                         f"board with {args.stone_size} mm stones in "
                         f"{args.mode} mode. Try --makeitwork or --unsafe, "
                         f"or a smaller board size.")
                return args, game_extent_fn, game_label, margin_pt, stone_mode, False, warnings, error
            args.paper = picked
            warnings.append(
                f"Auto-selected paper: {picked} ({orient}) for {game_label} "
                f"board with {args.stone_size} mm stones "
                f"[mode={args.mode}, ratio={ratio:.0%}]."
            )

    if args.paper not in PAPER_SIZES:
        error = (f"unknown paper '{args.paper}'. "
                 f"Choices: {', '.join(PAPER_SIZES)}")
        return args, game_extent_fn, game_label, margin_pt, stone_mode, False, warnings, error

    # Stone-fit check (safe mode only — makeitwork/unsafe allow over-70%).
    if args.stone_size is not None and args.mode == "safe":
        pw, ph = pick_page_size(args.paper, args.size)
        margin_for_check = (margin_pt if margin_pt is not None
                            else DEFAULT_MARGINS_PT[args.paper])
        r_check, _, _ = compute_r(pw, ph, margin_for_check, args.size,
                                  extent_fn=game_extent_fn)
        flat_mm = SQRT3 * r_check / PT_PER_INCH * MM_PER_INCH
        if args.stone_size / flat_mm > FIT_RATIOS["safe"]:
            error = (f"stone {args.stone_size} mm does not fit comfortably on "
                     f"{args.paper} (hex flat-to-flat {flat_mm:.1f} mm, "
                     f"ratio {args.stone_size/flat_mm:.0%} > 70%). "
                     f"Use --makeitwork or omit --paper to auto-pick a "
                     f"bigger paper.")
            return args, game_extent_fn, game_label, margin_pt, stone_mode, False, warnings, error

    show_coords = args.pen_paper or args.coords
    return args, game_extent_fn, game_label, margin_pt, stone_mode, show_coords, warnings, error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a printable Hex/Havannah board PDF.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("size", type=int, nargs="?", default=None,
                        help="Board size (e.g., 11 for 11x11 Hex, or 10 for base-10 Havannah). "
                             "Defaults to the most-played standard size for the selected "
                             "--game/--variant: hex 11, rex 11, yavalath 5, havannah 10, trike 13.")
    parser.add_argument("--game", type=str, default="hex",
                        choices=["hex", "havannah", "trike", "rex", "yavalath"],
                        help="Which board game to render. hex (default) renders an N×N rhombus; "
                             "havannah renders a base-N regular hexagon; trike renders a "
                             "side-N triangular board. rex and yavalath are aliases for "
                             "--variant rex / --variant yavalath. Size units differ per game — "
                             "see README.")
    parser.add_argument("--variant", type=str, default=None,
                        choices=[v for v in HEX_VARIANTS if v is not None],
                        help="Hex sub-variant: 'rex' for misère Hex (connecting your sides "
                             "loses), or 'yavalath' for the 4-in-a-row / 3-in-a-row game. "
                             "Only valid with --game hex (or its rex/yavalath aliases). "
                             "Yavalath has no perimeter bands; Rex uses standard Hex bands "
                             "with reversed win condition.")
    parser.add_argument("-o", "--output", type=str, default="hex_board.pdf", help="Output PDF path")
    parser.add_argument("-p", "--paper", type=str, default=None,
                        help=f"Paper size. Choices: {', '.join(PAPER_SIZES)}. "
                             "If omitted and --stone-size is given, auto-pick the smallest paper that fits.")
    parser.add_argument("--stone-size", type=float, default=None,
                        help="Stone diameter in mm (e.g., 19 for 19mm Go stones). "
                             "Triggers auto paper selection and prints fit diagnostics.")
    parser.add_argument("--margin", type=float, default=None,
                        help="Override page margin in points (1 inch = 72 pt)")
    parser.add_argument("--pen-paper", action=argparse.BooleanOptionalAction, default=False,
                        help="Paper-and-pencil mode: thicker hex strokes, "
                             "coordinate labels (a..k, 1..N) along edges, "
                             "and a notation hint in the footer. Default for pen/marker play.")
    parser.add_argument("--coords", action=argparse.BooleanOptionalAction, default=False,
                        help="Show coordinate labels (a..k, 1..N) along edges. "
                             "Automatically enabled by --pen-paper.")
    parser.add_argument("--cell-coords", action=argparse.BooleanOptionalAction, default=False,
                        help="Print coordinate label inside each hex cell (e.g. f7)")
    parser.add_argument("--theme", type=str, default="classic",
                        choices=list(THEMES.keys()),
                        help="Visual theme: classic (default), light, dark, wood")
    parser.add_argument("--label-set", type=str, default="wb",
                        choices=list(LABEL_SETS.keys()),
                        help="Side label convention: wb (White/Black, default) or rb (Red/Blue)")
    parser.add_argument("--corner-dots", action="store_true",
                        help="Mark the four corner hexes with filled dots "
                             "(per Hex board convention; corners belong to both adjacent sides)")
    parser.add_argument("--stone-mode", action=argparse.BooleanOptionalAction, default=False,
                        help="Tweak instructions for stone play (place stones in hex centers). "
                             "Auto-enabled when --stone-size is given.")
    parser.add_argument("--n-up", type=int, default=1, metavar="N",
                        help="Pack N boards onto each page (e.g., 4 for a 2x2 grid handout).")
    parser.add_argument("--pad", type=int, default=None, metavar="N",
                        help="Generate N copies of the board, one per page (like the original "
                             "1942 Polygon 50-sheet pads).")
    parser.add_argument("--sizes", type=str, default=None, metavar="LIST",
                        help="Comma-separated list of board sizes (e.g., '9,11,13'). "
                             "Produces one board per page, useful as a reference booklet.")
    parser.add_argument("--rules", action="store_true",
                        help="Append a Hex rules summary page at the end of the PDF")
    parser.add_argument("--format", type=str, default="pdf", choices=["pdf", "svg"],
                        help="Output format: pdf (default) or svg")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--safemode", dest="mode", action="store_const", const="safe",
                            default="safe",
                            help="Default. Stone must be <= 70%% of hex flat-to-flat (comfortable).")
    mode_group.add_argument("--makeitwork", dest="mode", action="store_const", const="makeitwork",
                            help="Allow tight fit: stone up to 85%% of hex flat-to-flat. "
                                 "Auto-picks smallest paper that fits and pushes hex size to the edge.")
    mode_group.add_argument("--unsafe", dest="mode", action="store_const", const="unsafe",
                            help="No margin: stones flush with hex walls. For testing only.")
    args = parser.parse_args()

    args, game_extent_fn, game_label, margin_pt, stone_mode, show_coords, warnings, error = validate_and_normalize(args)
    for w in warnings:
        print(f"Warning: {w}", file=sys.stderr)
    if error is not None:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(2)

    # SVG output: single-board only (no multi-board SVG, no rules).
    if args.format == "svg":
        if args.sizes or args.pad or (args.n_up and args.n_up > 1) or args.rules:
            print("Error: --format svg is single-page only; not compatible with "
                  "--n-up, --pad, --sizes, or --rules.", file=sys.stderr)
            sys.exit(2)
        if args.game == "havannah" or args.variant == "yavalath":
            write_havannah_svg(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                               mode=args.mode, pen_paper=args.pen_paper, coords=show_coords,
                               theme=args.theme, corner_dots=args.corner_dots,
                               game_label="YAVALATH" if args.variant == "yavalath" else "HAVANNAH")
            if args.variant == "yavalath":
                print(f"Generated Yavalath hexhex-{args.size} SVG: {args.output}")
            else:
                print(f"Generated Havannah base-{args.size} SVG: {args.output}")
        elif args.game == "trike":
            write_trike_svg(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                            mode=args.mode, pen_paper=args.pen_paper, coords=show_coords,
                            theme=args.theme)
            print(f"Generated Trike side-{args.size} SVG: {args.output}")
        else:
            write_svg(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                      mode=args.mode, pen_paper=args.pen_paper, coords=show_coords,
                      theme=args.theme, label_set=args.label_set, corner_dots=args.corner_dots,
                      variant=args.variant)
            if args.variant == "yavalath":
                print(f"Generated Yavalath hexhex-{args.size} SVG: {args.output}")
            elif args.variant == "rex":
                print(f"Generated Rex hexhex-{args.size} SVG: {args.output}")
            else:
                print(f"Generated {args.size}x{args.size} SVG: {args.output}")
        sys.exit(0)

    # Multi-board dispatch: --sizes, --pad, or --n-up > 1 take over.
    if args.sizes or args.pad or (args.n_up and args.n_up > 1):
        _generate_multi(args, show_coords)
        sys.exit(0)

    if args.game == "havannah" or args.variant == "yavalath":
        r = draw_havannah_board(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                                pen_paper=args.pen_paper, coords=show_coords, mode=args.mode,
                                theme=args.theme, corner_dots=args.corner_dots,
                                rules=args.rules, cell_coords=args.cell_coords,
                                stone_mode=stone_mode,
                                game_label="YAVALATH" if args.variant == "yavalath" else "HAVANNAH")
    elif args.game == "trike":
        r = draw_trike_board(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                             pen_paper=args.pen_paper, coords=show_coords, mode=args.mode,
                             theme=args.theme,
                             rules=args.rules, cell_coords=args.cell_coords,
                             stone_mode=stone_mode)
    else:
        r = draw_hex_board(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                          pen_paper=args.pen_paper, coords=show_coords, mode=args.mode,
                          theme=args.theme, label_set=args.label_set, corner_dots=args.corner_dots,
                          rules=args.rules, cell_coords=args.cell_coords, stone_mode=stone_mode,
                          variant=args.variant)

    # Diagnostics.
    flat_mm, _ = hex_fits_stone(r, args.stone_size or 0)
    pw, ph = pick_page_size(args.paper, args.size)
    orient = "landscape" if pw > ph else "portrait"
    print(f"Generated {game_label} board on {args.paper} ({orient}).")
    if args.stone_size:
        ratio = args.stone_size / flat_mm
        if ratio <= 0.70:
            status = "comfortable"
        elif ratio <= 0.85:
            status = "tight"
        elif ratio <= 1.00:
            status = "flush (no margin)"
        else:
            status = "OVERSIZE — stones will overlap adjacent cells"
        print(f"  hex flat-to-flat: {flat_mm:.1f} mm; "
              f"stone/flat ratio: {ratio:.0%} ({status}) [mode={args.mode}].")