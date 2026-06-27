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


def draw_hex_board(output_filename, board_size, paper="letter", margin_pt=None,
                   pen_paper=False, coords=True):
    page_w, page_h = pick_page_size(paper, board_size)
    if margin_pt is None:
        margin_pt = DEFAULT_MARGINS_PT[paper.lower()]
    r, max_w, max_h = compute_r(page_w, page_h, margin_pt, board_size)

    center_x = page_w / 2
    center_y = page_h / 2

    # Center the rhombus precisely.
    min_x = -r * SQRT3 / 2
    max_x = r * SQRT3 * (1.5 * (board_size - 1) + 0.5)
    min_y = -r
    max_y = r * 1.5 * (board_size - 1) + r
    grid_w = max_x - min_x
    grid_h = max_y - min_y
    offset_x = center_x - (min_x + grid_w / 2)
    offset_y = center_y - (min_y + grid_h / 2)

    c = canvas.Canvas(output_filename, pagesize=(page_w, page_h))
    title = (f"HEX BOARD \u2014 PAPER & PENCIL ({board_size} \u00d7 {board_size})"
             if pen_paper else
             f"HEX BOARD ({board_size} \u00d7 {board_size})")
    c.setTitle(title)

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#1A1A1A"))
    c.drawCentredString(center_x, page_h - margin_pt / 2, title)

    def get_hex_points(cx, cy, radius):
        pts = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3  # 30, 90, ..., 330 deg (pointy-top)
            pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return pts

    # 1. Draw hex cells.
    c.setStrokeColor(colors.HexColor("#7F8C8D"))
    c.setLineWidth(1.5 if pen_paper else 1)
    for row in range(board_size):
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * row) + offset_x
            cy = r * 1.5 * row + offset_y
            pts = get_hex_points(cx, cy, r)

            if (row + col) % 2 == 0:
                c.setFillColor(colors.HexColor("#FAFAFA"))
            else:
                c.setFillColor(colors.HexColor("#F2F2F2"))

            path = c.beginPath()
            path.moveTo(pts[0][0], pts[0][1])
            for p in pts[1:]:
                path.lineTo(p[0], p[1])
            path.close()
            c.drawPath(path, fill=True, stroke=True)

    # 2. Draw thick perimeter bands.
    c.setLineCap(1)
    c.setLineWidth(4)
    white_color = colors.HexColor("#95A5A6")
    black_color = colors.HexColor("#1A1A1A")

    # White: row 0 (bottom in user code's coord) and row N-1 (top).
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

    # Black: col 0 and col N-1.
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

    # 3. Edge labels.
    def draw_label(text, col, row, color, dx, dy, angle):
        cx = r * SQRT3 * (col + 0.5 * row) + offset_x
        cy = r * 1.5 * row + offset_y
        c.saveState()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(color)
        c.translate(cx + dx, cy + dy)
        c.rotate(angle)
        c.drawCentredString(0, 0, text.upper())
        c.restoreState()

    mid = board_size // 2
    lbl_dist = r * 1.4 if not pen_paper else r * 2.2
    draw_label("White Side", mid, 0, white_color, 0, -lbl_dist, 0)
    draw_label("White Side", mid, board_size - 1, white_color, 0, lbl_dist, 0)
    draw_label("Black Side", 0, mid, black_color, -lbl_dist * 0.866, lbl_dist * 0.5, 60)
    draw_label("Black Side", board_size - 1, mid, black_color, lbl_dist * 0.866, -lbl_dist * 0.5, 60)

    # 4. Coordinate labels and footer (paper & pencil mode).
    if coords or pen_paper:
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#555555"))
        # Column labels a..k along the top edge (row 0 hex centers, offset slightly outward).
        col_label_y = r * 1.5 * 0 + offset_y - r * 1.15
        for col in range(board_size):
            cx = r * SQRT3 * (col + 0.5 * 0) + offset_x
            label = chr(ord('a') + col) if board_size <= 26 else str(col + 1)
            c.drawCentredString(cx, col_label_y, label)
        # Row labels 1..N along the left edge (col 0 hex centers).
        row_label_x = r * SQRT3 * 0 + offset_x - r * 1.25
        for row in range(board_size):
            cy = r * 1.5 * row + offset_y
            c.drawCentredString(row_label_x, cy - 3, str(row + 1))

    if pen_paper:
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.HexColor("#777777"))
        c.drawCentredString(center_x, margin_pt / 2,
            f"Notation: <col><row> e.g. f7  \u2022  Black (or Red) moves first.  \u2022  Connect your two sides to win.")

    c.showPage()
    c.save()

    return r


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

    r = draw_hex_board(args.output, args.size, paper=args.paper, margin_pt=margin_pt,
                      pen_paper=args.pen_paper, coords=show_coords)

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