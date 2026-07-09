"""Unit tests for Havannah geometry helpers in generate_board.py.

Run with:  python -m unittest tests.test_havannah_geometry
"""
import math
import os
import sys
import unittest

# Make generate_board importable when running from the project root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import generate_board as gb


class HavannahCellCountTests(unittest.TestCase):
    def test_known_values(self):
        # From formula 3N^2 - 3N + 1.
        self.assertEqual(gb.havannah_cell_count(1), 1)
        self.assertEqual(gb.havannah_cell_count(2), 7)
        self.assertEqual(gb.havannah_cell_count(8), 169)
        self.assertEqual(gb.havannah_cell_count(10), 271)

    def test_enumeration_matches_formula(self):
        for N in (2, 3, 5, 8, 10):
            cells = list(gb.havannah_cells(N))
            self.assertEqual(len(cells), gb.havannah_cell_count(N))


class HavannahInBoundsTests(unittest.TestCase):
    def test_center_in_bounds(self):
        for N in (2, 5, 10):
            self.assertTrue(gb.havannah_in_bounds(0, 0, N))

    def test_corners_in_bounds(self):
        for N in (2, 5, 8):
            for q, r in gb.havannah_corners(N):
                self.assertTrue(gb.havannah_in_bounds(q, r, N))

    def test_corner_count_is_six(self):
        for N in (2, 3, 8, 10):
            self.assertEqual(len(gb.havannah_corners(N)), 6)

    def test_corners_are_distinct(self):
        for N in (3, 8):
            corners = gb.havannah_corners(N)
            self.assertEqual(len(set(corners)), len(corners))

    def test_out_of_bounds_rejected(self):
        # One step outside the regular hexagon of base-5.
        self.assertFalse(gb.havannah_in_bounds(5, 0, 5))   # too far right
        self.assertFalse(gb.havannah_in_bounds(0, 5, 5))   # too far down
        self.assertFalse(gb.havannah_in_bounds(5, -5, 5))  # off a hex corner


class AxialToPixelTests(unittest.TestCase):
    def test_origin_is_zero(self):
        self.assertEqual(gb.axial_to_pixel(0, 0, 1.0), (0.0, 0.0))

    def test_neighbors_at_unit_distance(self):
        # For pointy-top axial layout, distance between adjacent cells should
        # equal flat-to-flat width = R*sqrt(3).
        R = 10.0
        neighbors = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        for q, r in neighbors:
            cx, cy = gb.axial_to_pixel(q, r, R)
            d = math.hypot(cx, cy)
            self.assertAlmostEqual(d, R * math.sqrt(3), places=6)

    def test_symmetric_neighbors(self):
        # (1,0) and (-1,0) should be mirror images on the x-axis.
        a = gb.axial_to_pixel(1, 0, 10.0)
        b = gb.axial_to_pixel(-1, 0, 10.0)
        self.assertAlmostEqual(a[0], -b[0])
        self.assertAlmostEqual(a[1], b[1])


class HavannahExtentTests(unittest.TestCase):
    def test_extent_encloses_all_cells(self):
        # For each cell, distance from origin along each axis must fit within
        # the declared extent (in R-units).
        for N in (3, 5, 8, 10):
            gw, gh = gb.havannah_extent_r_units(N)
            for q, r in gb.havannah_cells(N):
                cx, cy = gb.axial_to_pixel(q, r, 1.0)
                # Bounding box uses pixel coords directly as R-units (since R=1).
                self.assertLessEqual(abs(cx), gw / 2 + 1e-9)
                self.assertLessEqual(abs(cy), gh / 2 + 1e-9)

    def test_extent_encloses_full_cell_vertices(self):
        # Paper-fit math uses the full cell vertex extent, not just the
        # center. Cells extend √3·R/2 horizontally and R/2 vertically at the
        # flat edges. The extent (gw, gh) is the total board size in R units,
        # centered on the cell-center bounding box (which is also the axial
        # origin for Havannah since it's symmetric around (0, 0)).
        for N in (3, 5, 8, 10):
            gw, gh = gb.havannah_extent_r_units(N)
            xs, ys = [], []
            for q, r in gb.havannah_cells(N):
                cx, cy = gb.axial_to_pixel(q, r, 1.0)
                xs.extend([cx - math.sqrt(3) / 2, cx + math.sqrt(3) / 2])
                ys.extend([cy - 0.5, cy + 0.5])
            actual_w = max(xs) - min(xs)
            actual_h = max(ys) - min(ys)
            self.assertAlmostEqual(actual_w, gw, places=9)
            self.assertAlmostEqual(actual_h, gh, places=9)

    def test_auto_pick_paper_for_havannah_base8_19mm_stones(self):
        # Havannah base-8 (169 cells) with 19mm stones should pick a paper
        # large enough to hold the board at the safe 0.70 stone/hex ratio.
        from generate_board import auto_pick_paper, havannah_extent_r_units
        paper, orient, ratio = auto_pick_paper(
            board_size=8, stone_diameter_mm=19.0, margin_pt=36,
            mode="safe", extent_fn=havannah_extent_r_units,
        )
        self.assertIsNotNone(paper)
        self.assertEqual(ratio, 0.70)
        # The chosen paper, with margin, must accommodate the full-cell extent.
        from generate_board import PAPER_SIZES
        pw, ph = PAPER_SIZES[paper]
        if orient == "landscape":
            pw, ph = ph, pw
        gw, gh = havannah_extent_r_units(8)
        # We don't recompute r here; just assert the paper is at least tabloid.
        self.assertGreaterEqual(pw * ph, 11.0 * 14.0)


if __name__ == "__main__":
    unittest.main()