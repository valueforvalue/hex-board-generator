"""Unit tests for Trike geometry helpers in generate_board.py.

Run with:  python -m unittest tests.test_trike_geometry
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import generate_board as gb


class TrikeCellCountTests(unittest.TestCase):
    def test_known_values(self):
        # Triangular numbers T_n = n*(n+1)/2.
        self.assertEqual(gb.trike_cell_count(1), 1)
        self.assertEqual(gb.trike_cell_count(2), 3)
        self.assertEqual(gb.trike_cell_count(7), 28)
        self.assertEqual(gb.trike_cell_count(13), 91)
        self.assertEqual(gb.trike_cell_count(19), 190)

    def test_enumeration_matches_formula(self):
        for N in (1, 2, 5, 7, 10, 13):
            cells = list(gb.trike_cells(N))
            self.assertEqual(len(cells), gb.trike_cell_count(N))


class TrikeInBoundsTests(unittest.TestCase):
    def test_center_in_bounds(self):
        # The "centroid" cell at ((N-1)//2, (N-1)//2) — only fully inside for N odd.
        for N in (3, 5, 7):
            mid = (N - 1) // 2
            self.assertTrue(gb.trike_in_bounds(mid, mid, N))

    def test_three_vertices_in_bounds(self):
        for N in (2, 5, 7, 13):
            for q, r in gb.trike_vertices(N):
                self.assertTrue(gb.trike_in_bounds(q, r, N))

    def test_three_vertex_count(self):
        for N in (1, 2, 5, 13):
            self.assertEqual(len(gb.trike_vertices(N)), 3)

    def test_three_vertices_are_distinct(self):
        for N in (2, 5, 13):
            verts = gb.trike_vertices(N)
            self.assertEqual(len(set(verts)), len(verts))

    def test_out_of_bounds_rejected(self):
        # Just outside the triangle of side 5.
        self.assertFalse(gb.trike_in_bounds(-1, 0, 5))   # left of left edge
        self.assertFalse(gb.trike_in_bounds(0, -1, 5))   # below bottom row
        self.assertFalse(gb.trike_in_bounds(5, 0, 5))    # past bottom-right corner
        self.assertFalse(gb.trike_in_bounds(0, 5, 5))    # above top apex
        self.assertFalse(gb.trike_in_bounds(3, 3, 5))    # q+r = 6 >= 5

    def test_in_bounds_predicate(self):
        # Verify the predicate matches the enumeration for several sizes.
        for N in (3, 7, 13):
            cells = set(gb.trike_cells(N))
            for q in range(-2, N + 2):
                for r in range(-2, N + 2):
                    expected = (q, r) in cells
                    self.assertEqual(gb.trike_in_bounds(q, r, N), expected)


class TrikeExtentTests(unittest.TestCase):
    def test_extent_encloses_all_cells(self):
        # For each cell, the cell center must fit within the declared extent
        # bounding box (in R-units, since R=1 here). The triangle apex has
        # cx = R*sqrt(3)*(0 + (N-1)/2) which is less than half the width —
        # the apex is directly above the midpoint of the bottom edge.
        for N in (3, 5, 7, 13):
            gw, gh = gb.trike_extent_r_units(N)
            # All cells must satisfy 0 <= cx <= gw and 0 <= cy <= gh.
            for q, r in gb.trike_cells(N):
                cx, cy = gb.axial_to_pixel(q, r, 1.0)
                self.assertGreaterEqual(cx, -1e-9)
                self.assertLessEqual(cx, gw + 1e-9)
                self.assertGreaterEqual(cy, -1e-9)
                self.assertLessEqual(cy, gh + 1e-9)

    def test_apex_x_is_half_width(self):
        # The apex vertex (0, N-1) sits at cx = √3·(N-1)/2; the full-cell
        # bottom-edge width is √3·N, so the apex is offset from the bottom
        # midpoint toward the origin side by √3·R/2.
        for N in (3, 5, 7):
            gw, _ = gb.trike_extent_r_units(N)
            q, r = gb.trike_vertices(N)[2]  # (0, N-1)
            cx, _ = gb.axial_to_pixel(q, r, 1.0)
            self.assertAlmostEqual(cx, math.sqrt(3) * (N - 1) / 2, places=9)
            self.assertAlmostEqual(gw, math.sqrt(3) * N, places=9)

    def test_extent_encloses_full_cell_vertices(self):
        # Paper-fit math uses the full cell vertex extent. The extent (gw, gh)
        # is the total board width/height in R units. Cells extend √3·R/2
        # beyond their center horizontally and R/2 vertically at the flat
        # edges. Compute the actual leftmost/rightmost/topmost/bottommost
        # vertex across all cells and assert it fits within (gw, gh) when
        # centered on the cell-center bounding box.
        for N in (3, 5, 7, 13):
            gw, gh = gb.trike_extent_r_units(N)
            xs, ys = [], []
            for q, r in gb.trike_cells(N):
                cx, cy = gb.axial_to_pixel(q, r, 1.0)
                xs.extend([cx - math.sqrt(3) / 2, cx + math.sqrt(3) / 2])
                ys.extend([cy - 0.5, cy + 0.5])
            actual_w = max(xs) - min(xs)
            actual_h = max(ys) - min(ys)
            self.assertAlmostEqual(actual_w, gw, places=9)
            self.assertAlmostEqual(actual_h, gh, places=9)

    def test_auto_pick_paper_for_trike_side13_19mm_stones(self):
        from generate_board import auto_pick_paper, trike_extent_r_units, PAPER_SIZES
        paper, orient, ratio = auto_pick_paper(
            board_size=13, stone_diameter_mm=19.0, margin_pt=36,
            mode="safe", extent_fn=trike_extent_r_units,
        )
        self.assertIsNotNone(paper)
        self.assertEqual(ratio, 0.70)
        pw, ph = PAPER_SIZES[paper]
        if orient == "landscape":
            pw, ph = ph, pw
        # side-13 Trike is large enough that 19mm stones need at least legal.
        self.assertGreaterEqual(pw * ph, 8.5 * 11.0)


if __name__ == "__main__":
    unittest.main()