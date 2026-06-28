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


# Side label text per color convention.
LABEL_SETS = {
    "wb":  ("White Side", "Black Side"),
    "rb":  ("Red Side",   "Blue Side"),
}


def grid_extent_r_units(N):
    """Return (w_units, h_units): grid extent in r units for NxN pointy-top board."""
    return (SQRT3 * (1.5 * (N - 1) + 1), 1.5 * (N - 1) + 2)


def pick_page_size(name, board_size):
    """Return page size in points, auto-rotating to landscape when wider fits better.

    For N >= 3 the hex grid is wider than tall, so landscape uses paper better.
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


def auto_pick_paper(board_size, stone_diameter_mm, margin_pt, mode="safe"):
    """Find the smallest paper that fits the board + stone requirement.

    `mode` controls the maximum stone-to-hex flat-to-flat ratio:
      - safe      : 0.70  (30% margin, default)
      - makeitwork: 0.85  (tight fit, stones nearly fill hex)
      - unsafe    : 1.00  (stones flush with hex walls, no margin)

    Returns (paper_name, orientation, achieved_ratio) or (None, None, ratio).
    """
    ratio = FIT_RATIOS[mode]
    min_flat_to_flat_mm = stone_diameter_mm / ratio
    min_r_pt = (min_flat_to_flat_mm / MM_PER_INCH * PT_PER_INCH) / SQRT3
    # Apply same 8% label safety as compute_r().
    min_r_pt /= 0.92

    gw_units, gh_units = grid_extent_r_units(board_size)
    need_w_pt = gw_units * min_r_pt + 2 * margin_pt
    need_h_pt = gh_units * min_r_pt + 2 * margin_pt

    # Walk papers smallest-first; check both orientations.
    for name, (pw, ph) in PAPERS_BY_AREA:
        for orient_w, orient_h, label in ((pw, ph, "portrait"), (ph, pw, "landscape")):
            if orient_w >= need_w_pt and orient_h >= need_h_pt:
                return name, label, ratio
    return None, None, ratio


def compute_r(page_w, page_h, margin, board_size):
    """Largest r that fits the page after margin, with 8% safety so labels don't clip."""
    gw_units, gh_units = grid_extent_r_units(board_size)
    max_w = page_w - 2 * margin
    max_h = page_h - 2 * margin
    safety = 0.92  # reserve room for side labels
    return min(max_w / gw_units, max_h / gh_units) * safety, max_w, max_h


def hex_fits_stone(r_pt, stone_diameter_mm):
    """Return (flat_to_flat_mm, ratio) for diagnostic."""
    flat_to_flat_mm = SQRT3 * r_pt / PT_PER_INCH * MM_PER_INCH
    return flat_to_flat_mm, stone_diameter_mm / flat_to_flat_mm


def draw_board_into_region(c, board_size, region, margin_pt,
                           pen_paper, coords, theme, label_set, corner_dots,
                           draw_title=True):
    """Draw one hex board into a rectangular region of an existing canvas.

    `region` = (x, y, w, h): bottom-left corner plus size of the region.
    The board fills the region (with its own internal margin_pt).
    Returns the r used (in points).
    """
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
        title = (f"HEX BOARD \u2014 PAPER & PENCIL ({board_size} \u00d7 {board_size})"
                 if pen_paper else
                 f"HEX BOARD ({board_size} \u00d7 {board_size})")
        title_color = "#FFFFFF" if theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 12)  # smaller for sub-boards
        c.setFillColor(colors.HexColor(title_color))
        c.drawCentredString(center_x, ry + rh - 12, title)

    def get_hex_points(cx, cy, radius):
        pts = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3
            pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return pts

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

    c.setLineCap(1)
    c.setLineWidth(3)
    white_color = colors.HexColor(theme_def["white"])
    black_color = colors.HexColor(theme_def["black"])

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

    if coords or pen_paper:
        coord_color = "#CCCCCC" if theme == "dark" else "#555555"
        c.setFont("Helvetica", 7 if r < 15 else 9)
        c.setFillColor(colors.HexColor(coord_color))
        col_label_y = r * 1.5 * 0 + offset_y - r * 1.15
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * 0) + offset_x
            label = chr(ord('a') + col) if board_size <= 26 else str(col + 1)
            c.drawCentredString(cx, col_label_y, label)
        row_label_x = r * SQRT3 * 0 + offset_x - r * 1.25
        for row in range(board_size):
            cy = r * 1.5 * row + offset_y
            c.drawCentredString(row_label_x, cy - 3, str(row + 1))

    return r


def draw_hex_board(output_filename, board_size, paper="letter", margin_pt=None,
                   pen_paper=False, coords=True, mode="safe",
                   theme="classic", label_set="wb", corner_dots=False, rules=False):
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
        draw_title=False,
    )

    if pen_paper:
        footer_color = "#AAAAAA" if theme == "dark" else "#777777"
        first_player = "Red" if label_set == "rb" else "Black (or Red)"
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor(footer_color))
        c.drawCentredString(page_w / 2, max(14, margin_pt / 2),
            f"Notation: <col><row> e.g. f7  \u2022  {first_player} moves first.  \u2022  Connect your two sides to win.")

    if rules:
        c.showPage()
        draw_rules_page(c, page_w, page_h, theme=theme, label_set=label_set)
        c.showPage()
    else:
        c.showPage()
    c.save()

    return r


def draw_rules_page(c, page_w, page_h, theme="classic", label_set="wb"):
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
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.HexColor(text_color))
    c.drawString(x, y, "How to Play Hex")
    y -= 30

    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawString(x, y, "Invented by Piet Hein (1942) \u2022 Rediscovered by John Nash (1949)")
    y -= 30

    def section(title_text):
        nonlocal y
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor(accent))
        c.drawString(x, y, title_text)
        y -= 18

    def body(text):
        nonlocal y
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor(text_color))
        words = text.split()
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Helvetica", 11) > max_w:
                c.drawString(x, y, line)
                y -= 14
                line = w
            else:
                line = test
        if line:
            c.drawString(x, y, line)
            y -= 14
        y -= 4

    section("Players")
    body("Two players. One plays " + p1 + ", the other plays " + p2 + ".")

    section("Setup")
    body("Use the board on the previous page. Decide who goes first (typically the " + p2.split()[0] + " player).")

    section("Goal")
    body("Be the first to form a connected chain of your own stones linking your two assigned sides of the board.")

    section("How to play")
    body("On your turn, place a stone of your color on any empty hex cell. Stones are never moved or removed.")

    section("Win condition")
    body("Connect your two opposite sides with a chain of your stones. A draw is impossible \u2014 the Brouwer fixed-point theorem guarantees one player must win.")

    section("The swap rule (recommended for fairness)")
    body("After the first player makes their opening move, the second player may choose to either keep their color or swap colors. This largely nullifies the first-move advantage.")

    section("Coordinate notation")
    body("Columns are lettered a, b, c, ... from left to right. Rows are numbered 1, 2, 3, ... from bottom to top. A cell's address is column+row, e.g. \u201cf7\u201d refers to column f, row 7.")

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor(subtle_color))
    c.drawCentredString(page_w / 2, margin / 2,
        "Hex is a member of the connection game family. See en.wikipedia.org/wiki/Hex_(board_game) for the full rules.")


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

    if args.sizes:
        sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
        if not sizes:
            print("Error: --sizes requires a comma-separated list.", file=sys.stderr)
            sys.exit(2)
        # Title for booklet.
        title_color = "#FFFFFF" if args.theme == "dark" else "#1A1A1A"
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.HexColor(title_color))
        title = "HEX BOARD REFERENCE  " + "  \u2022  ".join(
            f"{s}x{s}" for s in sizes
        )
        c.setTitle("Hex Board Reference")
        c.drawCentredString(pw / 2, ph - max(14, margin_pt / 2), title)
        for sz in sizes:
            draw_board_into_region(
                c, sz, (0, 0, pw, ph), margin_pt,
                args.pen_paper, show_coords, args.theme, args.label_set, args.corner_dots,
                draw_title=True,
            )
            c.showPage()
            # Page bg fill resets each page.
            if theme_def["page_bg"]:
                c.setFillColor(colors.HexColor(theme_def["page_bg"]))
                c.rect(0, 0, pw, ph, fill=True, stroke=False)
        print(f"Generated {len(sizes)}-page reference: sizes {sizes} on {args.paper}.")
        if args.rules:
            draw_rules_page(c, pw, ph, theme=args.theme, label_set=args.label_set)
            c.showPage()
            print("  + rules page")

    elif args.pad:
        for i in range(args.pad):
            draw_board_into_region(
                c, args.size, (0, 0, pw, ph), margin_pt,
                args.pen_paper, show_coords, args.theme, args.label_set, args.corner_dots,
                draw_title=True,
            )
            c.showPage()
            if theme_def["page_bg"]:
                c.setFillColor(colors.HexColor(theme_def["page_bg"]))
                c.rect(0, 0, pw, ph, fill=True, stroke=False)
        print(f"Generated {args.pad}-sheet pad of {args.size}x{args.size} boards on {args.paper}.")
        if args.rules:
            draw_rules_page(c, pw, ph, theme=args.theme, label_set=args.label_set)
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
        c.setTitle(f"Hex Board {args.size}x{args.size} ({n}-up)")
        c.drawCentredString(pw / 2, ph - 12, f"{args.size}x{args.size}  \u00d7  {n} PER PAGE")

        for i in range(n):
            r = i // cols
            cn = i % cols
            x = gutter + cn * (cell_w + gutter)
            y = gutter + r * (cell_h + gutter)
            draw_board_into_region(
                c, args.size, (x, y, cell_w, cell_h), margin_pt,
                args.pen_paper, show_coords, args.theme, args.label_set, args.corner_dots,
                draw_title=False,
            )
        c.showPage()
        print(f"Generated 1-page {cols}x{rows} handout ({n} copies of {args.size}x{args.size}) on {args.paper}.")

    if args.rules:
        draw_rules_page(c, pw, ph, theme=args.theme, label_set=args.label_set)
        c.showPage()
        print("  + rules page")

    c.save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a printable Hex board PDF.")
    parser.add_argument("size", type=int, help="Board size (e.g., 11 for 11x11)")
    parser.add_argument("-o", "--output", type=str, default="hex_board.pdf", help="Output PDF path")
    parser.add_argument("-p", "--paper", type=str, default=None,
                        help=f"Paper size. Choices: {', '.join(PAPER_SIZES)}. "
                             "If omitted and --stone-size is given, auto-pick the smallest paper that fits.")
    parser.add_argument("--stone-size", type=float, default=None,
                        help="Stone diameter in mm (e.g., 19 for 19mm Go stones). "
                             "Triggers auto paper selection and prints fit diagnostics.")
    parser.add_argument("--margin", type=float, default=None,
                        help="Override page margin in points (1 inch = 72 pt)")
    parser.add_argument("--pen-paper", action="store_true",
                        help="Paper-and-pencil mode: thicker hex strokes, "
                             "coordinate labels (a..k, 1..N) along edges, "
                             "and a notation hint in the footer. Default for pen/marker play.")
    parser.add_argument("--coords", action="store_true",
                        help="Show coordinate labels (a..k, 1..N) along edges. "
                             "Automatically enabled by --pen-paper.")
    parser.add_argument("--no-coords", action="store_true",
                        help="Suppress coordinate labels (default behavior)")
    parser.add_argument("--theme", type=str, default="classic",
                        choices=list(THEMES.keys()),
                        help="Visual theme: classic (default), light, dark, wood")
    parser.add_argument("--label-set", type=str, default="wb",
                        choices=list(LABEL_SETS.keys()),
                        help="Side label convention: wb (White/Black, default) or rb (Red/Blue)")
    parser.add_argument("--corner-dots", action="store_true",
                        help="Mark the four corner hexes with filled dots "
                             "(per Hex board convention; corners belong to both adjacent sides)")
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

    if args.size < 2:
        print("Error: Board size must be at least 2.", file=sys.stderr)
        sys.exit(1)

    margin_pt = args.margin if args.margin is not None else None

    # If --stone-size given and no explicit --paper, auto-pick.
    if args.paper is None:
        if args.stone_size is None:
            args.paper = "letter"
        else:
            margin_for_calc = margin_pt if margin_pt is not None else min(DEFAULT_MARGINS_PT.values())
            picked, orient, ratio = auto_pick_paper(
                args.size, args.stone_size, margin_for_calc, mode=args.mode
            )
            if picked is None:
                print(f"Error: no paper size is large enough for {args.size}x{args.size} "
                      f"board with {args.stone_size} mm stones in {args.mode} mode. "
                      f"Try --makeitwork or --unsafe, or a smaller board size.",
                      file=sys.stderr)
                sys.exit(2)
            args.paper = picked
            print(f"Auto-selected paper: {picked} ({orient}) for "
                  f"{args.size}x{args.size} board with {args.stone_size} mm stones "
                  f"[mode={args.mode}, ratio={ratio:.0%}].")

    if args.paper not in PAPER_SIZES:
        print(f"Error: unknown paper '{args.paper}'. Choices: {', '.join(PAPER_SIZES)}", file=sys.stderr)
        sys.exit(1)

    # Pre-flight check: does the chosen paper satisfy the fit ratio for the stone?
    if args.stone_size is not None and args.mode == "safe":
        pw, ph = pick_page_size(args.paper, args.size)
        margin_for_check = margin_pt if margin_pt is not None else DEFAULT_MARGINS_PT[args.paper]
        r_check, _, _ = compute_r(pw, ph, margin_for_check, args.size)
        flat_mm = SQRT3 * r_check / PT_PER_INCH * MM_PER_INCH
        if args.stone_size / flat_mm > FIT_RATIOS["safe"]:
            print(f"Error: stone {args.stone_size} mm does not fit comfortably on {args.paper} "
                  f"(hex flat-to-flat {flat_mm:.1f} mm, ratio {args.stone_size/flat_mm:.0%} > 70%). "
                  f"Use --makeitwork or omit --paper to auto-pick a bigger paper.",
                  file=sys.stderr)
            sys.exit(2)

    # Coordinates: on by default for pen-paper, off otherwise unless --coords.
    show_coords = args.pen_paper or args.coords
    if args.no_coords:
        show_coords = False

    # Multi-board dispatch: --sizes, --pad, or --n-up > 1 take over.
    if args.sizes or args.pad or (args.n_up and args.n_up > 1):
        _generate_multi(args, show_coords)
        sys.exit(0)

    r = draw_hex_board(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                      pen_paper=args.pen_paper, coords=show_coords, mode=args.mode,
                      theme=args.theme, label_set=args.label_set, corner_dots=args.corner_dots,
                      rules=args.rules)

    # Diagnostics.
    flat_mm, _ = hex_fits_stone(r, args.stone_size or 0)
    pw, ph = pick_page_size(args.paper, args.size)
    orient = "landscape" if pw > ph else "portrait"
    print(f"Generated {args.size}x{args.size} board on {args.paper} ({orient}).")
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