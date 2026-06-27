#!/usr/bin/env python3
import argparse
import sys
import math
from reportlab.lib.pagesizes import letter, legal, A3, A4, landscape

# Tabloid / Ledger (11 x 17 in) is not in reportlab by default.
TABLOID = (11 * 72, 17 * 72)
# ANSI B (17 x 22 in) for the biggest standard fit.
ANSI_B = (17 * 72, 22 * 72)

PAPER_SIZES = {
    "letter":  letter,
    "legal":   legal,
    "tabloid": TABLOID,
    "ledger":  TABLOID,   # alias
    "a3":      A3,
    "a4":      A4,
    "ansi-b":  ANSI_B,
}


def pick_page_size(name, board_size, sqrt3):
    """Return a page size in points, auto-rotating to landscape when wider fits better.

    For an NxN pointy-top hex grid the bounding box (in r units) is:
        width  = sqrt(3) * (1.5*(N-1) + 1)
        height = 1.5*(N-1) + 2
    so width > height for N >= 3. Landscape gives more usable width.
    """
    base = PAPER_SIZES[name.lower()]
    w, h = base
    # Hex grid is wider than tall for N >= 3; prefer landscape.
    if board_size >= 3 and w < h:
        return landscape(base)
    return base
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def draw_hex_board(output_filename, board_size, paper="letter"):
    page_width, page_height = pick_page_size(paper, board_size, math.sqrt(3))
    margin = 36

    # Target printable area
    max_w = page_width - (2 * margin)
    max_h = page_height - (2 * margin)
    center_x = page_width / 2
    center_y = page_height / 2

    sqrt3 = math.sqrt(3)

    # Calculate optimal radius 'r' for pointy-topped hexagons
    # Grid width = r * sqrt(3) * (1.5 * (N - 1) + 1)
    # Grid height = r * (1.5 * (N - 1) + 2)
    grid_w_unscaled = sqrt3 * (1.5 * (board_size - 1) + 1)
    grid_h_unscaled = 1.5 * (board_size - 1) + 2
    
    r_width = max_w / grid_w_unscaled
    r_height = max_h / grid_h_unscaled
    r = min(r_width, r_height)  # 5% padding to ensure labels fit
    
    # Calculate offsets to perfectly center the rhombus grid
    min_x = -r * sqrt3 / 2
    max_x = r * sqrt3 * (1.5 * (board_size - 1) + 0.5)
    min_y = -r
    max_y = r * 1.5 * (board_size - 1) + r
    
    grid_w = max_x - min_x
    grid_h = max_y - min_y
    
    offset_x = center_x - (min_x + grid_w / 2)
    offset_y = center_y - (min_y + grid_h / 2)

    c = canvas.Canvas(output_filename, pagesize=(page_width, page_height))
    c.setTitle(f"Hex Board ({board_size}x{board_size})")

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(colors.HexColor("#1A1A1A"))
    c.drawCentredString(center_x, page_height - 30, f"HEX BOARD ({board_size} × {board_size})")

    # Pointy-topped hex vertices: 30, 90, 150, 210, 270, 330 degrees
    def get_hex_points(cx, cy, radius):
        pts = []
        for i in range(6):
            angle = math.pi / 6 + i * math.pi / 3 
            pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return pts

    # 1. Draw Grid Cells
    c.setStrokeColor(colors.HexColor("#7F8C8D"))
    c.setLineWidth(1)
    
    for row in range(board_size):
        for col in range(board_size):
            cx = r * sqrt3 * (col + 0.5 * row) + offset_x
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

    # 2. Draw Continuous Thick Perimeter Lines
    c.setLineCap(1)
    c.setLineWidth(4)
    
    white_color = colors.HexColor("#95A5A6")
    black_color = colors.HexColor("#1A1A1A")

    # Bottom Edge (White) - Row 0
    c.setStrokeColor(white_color)
    path = c.beginPath()
    pts = get_hex_points(r * sqrt3 * (0 + 0) + offset_x, r * 1.5 * 0 + offset_y, r)
    path.moveTo(pts[3][0], pts[3][1])
    for col in range(board_size):
        pts = get_hex_points(r * sqrt3 * (col + 0) + offset_x, r * 1.5 * 0 + offset_y, r)
        path.lineTo(pts[4][0], pts[4][1])
        path.lineTo(pts[5][0], pts[5][1])
    c.drawPath(path)

    # Top Edge (White) - Row N-1
    path = c.beginPath()
    row = board_size - 1
    pts = get_hex_points(r * sqrt3 * (0 + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
    path.moveTo(pts[2][0], pts[2][1])
    for col in range(board_size):
        pts = get_hex_points(r * sqrt3 * (col + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
        path.lineTo(pts[1][0], pts[1][1])
        path.lineTo(pts[0][0], pts[0][1])
    c.drawPath(path)

    # Left Edge (Black) - Col 0
    c.setStrokeColor(black_color)
    path = c.beginPath()
    col = 0
    pts = get_hex_points(r * sqrt3 * (col + 0.5 * 0) + offset_x, r * 1.5 * 0 + offset_y, r)
    path.moveTo(pts[3][0], pts[3][1])
    for row in range(board_size):
        pts = get_hex_points(r * sqrt3 * (col + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
        path.lineTo(pts[2][0], pts[2][1])
        path.lineTo(pts[1][0], pts[1][1])
    c.drawPath(path)

    # Right Edge (Black) - Col N-1
    path = c.beginPath()
    col = board_size - 1
    pts = get_hex_points(r * sqrt3 * (col + 0.5 * 0) + offset_x, r * 1.5 * 0 + offset_y, r)
    path.moveTo(pts[4][0], pts[4][1])
    for row in range(board_size):
        pts = get_hex_points(r * sqrt3 * (col + 0.5 * row) + offset_x, r * 1.5 * row + offset_y, r)
        path.lineTo(pts[5][0], pts[5][1])
        path.lineTo(pts[0][0], pts[0][1])
    c.drawPath(path)

    # 3. Draw Edge Labels
    def draw_label(lbl_text, col, row, color, offset_x_shift, offset_y_shift, angle):
        cx = r * sqrt3 * (col + 0.5 * row) + offset_x
        cy = r * 1.5 * row + offset_y
        c.saveState()
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(color)
        c.translate(cx + offset_x_shift, cy + offset_y_shift)
        c.rotate(angle)
        c.drawCentredString(0, 0, lbl_text.upper())
        c.restoreState()

    mid = board_size // 2
    lbl_dist = r * 1.4
    
    # Top and Bottom (White)
    draw_label("White Side", mid, 0, white_color, 0, -lbl_dist, 0)
    draw_label("White Side", mid, board_size - 1, white_color, 0, lbl_dist, 0)
    
    # Left and Right (Black) - The axis angles at exactly 60 degrees.
    draw_label("Black Side", 0, mid, black_color, -lbl_dist * 0.866, lbl_dist * 0.5, 60)
    draw_label("Black Side", board_size - 1, mid, black_color, lbl_dist * 0.866, -lbl_dist * 0.5, 60)

    c.showPage()
    c.save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a pristine printable Hex board PDF.")
    parser.add_argument("size", type=int, help="Board size (e.g., 11)")
    parser.add_argument("-o", "--output", type=str, default="hex_board.pdf", help="Output file path")
    parser.add_argument("-p", "--paper", type=str, default="letter",
                        choices=list(PAPER_SIZES.keys()),
                        help="Paper size (auto-rotates to landscape when wider fits better)")
    args = parser.parse_args()

    if args.size < 2:
        print("Error: Board size must be at least 2.")
        sys.exit(1)

    draw_hex_board(args.output, args.size, paper=args.paper)
    print(f"Generated {args.size}x{args.size} board on {args.paper}: '{args.output}'")