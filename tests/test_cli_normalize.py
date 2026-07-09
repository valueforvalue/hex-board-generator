"""Unit tests for validate_and_normalize() in generate_board.py.

Run with:  python -m unittest tests.test_cli_normalize
"""
import argparse
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import generate_board as gb


def _parse(argv):
    """Build a minimal argparse.Namespace from a list of CLI tokens."""
    parser = argparse.ArgumentParser()
    parser.add_argument("size", type=int, nargs="?", default=None)
    parser.add_argument("--game", type=str, default="hex",
                        choices=["hex", "havannah", "trike", "rex", "yavalath"])
    parser.add_argument("--variant", type=str, default=None,
                        choices=["rex", "yavalath"])
    parser.add_argument("--paper", type=str, default=None)
    parser.add_argument("--stone-size", type=float, default=None)
    parser.add_argument("--margin", type=float, default=None)
    parser.add_argument("--pen-paper", action="store_true", default=False)
    parser.add_argument("--coords", action="store_true", default=False)
    parser.add_argument("--cell-coords", action="store_true", default=False)
    parser.add_argument("--theme", type=str, default="classic")
    parser.add_argument("--label-set", type=str, default="wb")
    parser.add_argument("--corner-dots", action="store_true", default=False)
    parser.add_argument("--stone-mode", action="store_true", default=False)
    parser.add_argument("--n-up", type=int, default=1)
    parser.add_argument("--pad", type=int, default=None)
    parser.add_argument("--sizes", type=str, default=None)
    parser.add_argument("--rules", action="store_true", default=False)
    parser.add_argument("--tile", type=str, default=None)
    parser.add_argument("--format", type=str, default="pdf")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--safemode", dest="mode", action="store_const",
                            const="safe", default="safe")
    mode_group.add_argument("--makeitwork", dest="mode", action="store_const",
                            const="makeitwork")
    mode_group.add_argument("--unsafe", dest="mode", action="store_const",
                            const="unsafe")
    return parser.parse_args(argv)


class RexAliasTests(unittest.TestCase):
    def test_rex_alias_resolves(self):
        args = _parse(["--game", "rex"])
        args, fn, label, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.game, "hex")
        self.assertEqual(args.variant, "rex")
        self.assertIn("REX HEXHEX", label)

    def test_yavalath_alias_resolves(self):
        args = _parse(["--game", "yavalath"])
        args, fn, label, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.game, "hex")
        self.assertEqual(args.variant, "yavalath")
        self.assertIn("YAVALATH HEXHEX", label)

    def test_rex_alias_conflict_with_variant(self):
        args = _parse(["--game", "rex", "--variant", "yavalath"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn("conflicts", error)


class DefaultSizeTests(unittest.TestCase):
    def test_hex_default_size(self):
        args = _parse([])
        args, _, label, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.size, 11)
        self.assertIn("HEX 11x11", label)
        self.assertTrue(any("default size" in w for w in warnings))

    def test_havannah_default_size(self):
        args = _parse(["--game", "havannah"])
        args, _, label, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.size, 10)
        self.assertIn("HAVANNAH BASE-10", label)

    def test_trike_default_size(self):
        args = _parse(["--game", "trike"])
        args, _, label, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.size, 13)
        self.assertIn("TRIKE SIDE-13", label)

    def test_explicit_size_preserved(self):
        args = _parse(["7"])
        args, _, label, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.size, 7)
        self.assertIn("HEX 7x7", label)


class VariantValidationTests(unittest.TestCase):
    def test_variant_requires_hex(self):
        args = _parse(["--game", "havannah", "--variant", "rex"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn("requires --game hex", error)

    def test_size_too_small(self):
        args = _parse(["1"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn("at least 2", error)


class WarningTests(unittest.TestCase):
    def test_label_set_warning_havannah(self):
        args = _parse(["--game", "havannah", "--label-set", "rb"])
        _, _, _, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(any("label-set is ignored" in w for w in warnings))

    def test_label_set_warning_trike(self):
        args = _parse(["--game", "trike", "--label-set", "rb"])
        _, _, _, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(any("label-set is ignored" in w for w in warnings))

    def test_label_set_warning_yavalath(self):
        args = _parse(["--variant", "yavalath", "--label-set", "rb"])
        _, _, _, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(any("label-set is ignored" in w for w in warnings))

    def test_corner_dots_warning_yavalath(self):
        args = _parse(["--variant", "yavalath", "--corner-dots"])
        _, _, _, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(any("corner-dots is ignored" in w for w in warnings))

    def test_corner_dots_warning_trike(self):
        args = _parse(["--game", "trike", "--corner-dots"])
        _, _, _, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(any("corner-dots is ignored" in w for w in warnings))


class PaperAutoPickTests(unittest.TestCase):
    def test_no_paper_no_stone_defaults_to_letter(self):
        args = _parse([])
        args, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertEqual(args.paper, "letter")

    def test_stone_size_triggers_auto_pick(self):
        args = _parse(["--stone-size", "19"])
        args, _, _, _, _, _, warnings, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertIsNotNone(args.paper)
        self.assertTrue(any("Auto-selected paper" in w for w in warnings))

    def test_unknown_paper_errors(self):
        args = _parse(["--paper", "postcard"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn("unknown paper", error)


class StoneModeTests(unittest.TestCase):
    def test_stone_mode_auto_enables_with_stone_size(self):
        args = _parse(["--stone-size", "19"])
        _, _, _, _, stone_mode, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(stone_mode)

    def test_stone_mode_explicit(self):
        args = _parse(["--stone-mode"])
        _, _, _, _, stone_mode, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(stone_mode)


class ShowCoordsTests(unittest.TestCase):
    def test_pen_paper_enables_coords(self):
        args = _parse(["--pen-paper"])
        _, _, _, _, _, show_coords, _, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(show_coords)

    def test_coords_flag_enables_coords(self):
        args = _parse(["--coords"])
        _, _, _, _, _, show_coords, _, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertTrue(show_coords)

    def test_no_flags_disables_coords(self):
        args = _parse([])
        _, _, _, _, _, show_coords, _, error = gb.validate_and_normalize(args)
        self.assertIsNone(error)
        self.assertFalse(show_coords)


class TileTests(unittest.TestCase):
    def test_no_tile_means_none(self):
        args = _parse([])
        gb.validate_and_normalize(args)
        self.assertIsNone(args.tile_rows)
        self.assertIsNone(args.tile_cols)

    def test_tile_2x2(self):
        args = _parse(["--tile", "2x2"])
        gb.validate_and_normalize(args)
        self.assertEqual(args.tile_rows, 2)
        self.assertEqual(args.tile_cols, 2)

    def test_tile_3x1(self):
        args = _parse(["--tile", "3x1"])
        gb.validate_and_normalize(args)
        self.assertEqual(args.tile_rows, 3)
        self.assertEqual(args.tile_cols, 1)

    def test_tile_case_insensitive(self):
        args = _parse(["--tile", "2X2"])
        gb.validate_and_normalize(args)
        self.assertEqual(args.tile_rows, 2)
        self.assertEqual(args.tile_cols, 2)

    def test_tile_invalid_format(self):
        args = _parse(["--tile", "abc"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn("RxC", error)

    def test_tile_wrong_parts(self):
        args = _parse(["--tile", "2x2x2"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn("RxC", error)

    def test_tile_zero_errors(self):
        args = _parse(["--tile", "0x0"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)
        self.assertIn(">= 1", error)

    def test_tile_non_integer_errors(self):
        args = _parse(["--tile", "2.5x2"])
        _, _, _, _, _, _, _, error = gb.validate_and_normalize(args)
        self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()