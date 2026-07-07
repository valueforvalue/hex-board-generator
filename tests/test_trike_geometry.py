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
        # Top vertex should sit at x = gw/2 (the midpoint of the bottom edge).
        for N in (3, 5, 7):
            gw, _ = gb.trike_extent_r_units(N)
            q, r = gb.trike_vertices(N)[2]  # (0, N-1)
            cx, _ = gb.axial_to_pixel(q, r, 1.0)
            self.assertAlmostEqual(cx, gw / 2, places=9)


if __name__ == "__main__":
    unittest.main()