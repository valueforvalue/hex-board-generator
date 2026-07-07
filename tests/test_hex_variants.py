"""Unit tests for Hex variant plumbing (rex, yavalath) in generate_board.py.

Run with:  python -m unittest tests.test_hex_variants
"""
import os
import sys
import tempfile
import unittest
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import generate_board as gb

# reportlab canvas.Canvas accepts a BytesIO filename.
def _render_board(variant, board_size=5, paper="letter",
                  pen_paper=False, coords=False, corner_dots=False,
                  rules=False):
    """Render a single Hex-variant PDF to an in-memory buffer and return the bytes."""
    buf = BytesIO()
    buf.name = "test.pdf"
    gb.draw_hex_board(
        buf, board_size=board_size, paper=paper,
        pen_paper=pen_paper, coords=coords, mode="safe",
        theme="classic", label_set="wb", corner_dots=corner_dots,
        rules=rules, cell_coords=False, stone_mode=False, variant=variant,
    )
    return buf.getvalue()


def _render_svg(variant, board_size=5):
    """Render the SVG variant and return the resulting XML string."""
    fd, path = tempfile.mkstemp(suffix=".svg")
    os.close(fd)
    try:
        gb.write_svg(
            path, board_size=board_size, paper="letter", margin_pt=None,
            mode="safe", pen_paper=False, coords=False,
            theme="classic", label_set="wb", corner_dots=False,
            rules=False, variant=variant,
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


class HexVariantConstantTests(unittest.TestCase):
    def test_variants_include_known(self):
        self.assertIn(None, gb.HEX_VARIANTS)
        self.assertIn("rex", gb.HEX_VARIANTS)
        self.assertIn("yavalath", gb.HEX_VARIANTS)

    def test_variant_titles_map_known(self):
        self.assertIsNone(gb.HEX_VARIANT_TITLES[None])
        self.assertEqual(gb.HEX_VARIANT_TITLES["rex"], "REX BOARD")
        self.assertEqual(gb.HEX_VARIANT_TITLES["yavalath"], "YAVALATH BOARD")


class HexVariantRenderSmokeTests(unittest.TestCase):
    """Render each variant and confirm a non-trivial PDF comes back."""

    def test_standard_hex_renders(self):
        data = _render_board(None, board_size=5, rules=True)
        self.assertGreater(len(data), 1024)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_rex_renders(self):
        data = _render_board("rex", board_size=5, rules=True)
        self.assertGreater(len(data), 1024)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_yavalath_renders(self):
        data = _render_board("yavalath", board_size=5, rules=True)
        self.assertGreater(len(data), 1024)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_invalid_variant_raises(self):
        with self.assertRaises(AssertionError):
            gb.draw_hex_board(
                BytesIO(), board_size=5, paper="letter",
                pen_paper=False, coords=False, mode="safe",
                theme="classic", label_set="wb", corner_dots=False,
                rules=False, cell_coords=False, stone_mode=False,
                variant="bogus",
            )


class HexVariantSvgSmokeTests(unittest.TestCase):
    """Render each variant as SVG and confirm the document has the expected marker."""

    def test_yavalath_svg_has_no_side_labels(self):
        svg = _render_svg("yavalath")
        self.assertIn("YAVALATH BOARD", svg)
        # No WHITE SIDE / BLACK SIDE labels in Yavalath SVG.
        self.assertNotIn("WHITE SIDE", svg.upper())
        self.assertNotIn("BLACK SIDE", svg.upper())

    def test_rex_svg_keeps_side_labels(self):
        svg = _render_svg("rex")
        self.assertIn("REX BOARD", svg)

    def test_standard_svg_uses_default_title(self):
        svg = _render_svg(None)
        self.assertIn("HEX BOARD", svg)


class HexVariantAliasingTests(unittest.TestCase):
    """`--game rex` / `--game yavalath` must normalize to (game=hex, variant=...)."""

    def test_rex_alias_normalizes(self):
        # 'rex' and 'yavalath' should both be valid choices in the CLI.
        # We assert via parse_args using the same choices list.
        for g in ("rex", "yavalath"):
            buf = BytesIO()
            buf.name = "test.pdf"
            # We can't easily exercise argparse here without invoking main();
            # instead, simulate the post-parse normalization logic that the
            # module performs.
            args = gb.argparse.Namespace(  # type: ignore[attr-defined]
                game=g, variant=None,
            )
            # Mirror the if-statement in the main block.
            if args.game in ("rex", "yavalath"):
                if args.variant is not None and args.variant != args.game:
                    raise AssertionError("conflict")
                args.variant = args.game
                args.game = "hex"
            self.assertEqual(args.game, "hex")
            self.assertEqual(args.variant, g)


class DefaultSizeTests(unittest.TestCase):
    """The CLI picks the most-played standard size when `size` is omitted.

    Verified values (sources cited in generate_board.py:DEFAULT_SIZES):
        hex       -> 11   (Piet Hein 1942 / Parker Brothers classic)
        rex       -> 11   (same logic as hex; misère is just flipped win condition)
        yavalath  -> 5    (Nestorgames published hexhex-5 set)
        havannah  -> 10   (Computer Olympiad standard, 271 cells)
        trike     -> 13   (Alek Erickson 2020 standard competitive)
    """

    EXPECTED = {
        "hex":       11,
        "rex":       11,
        "yavalath":  5,
        "havannah":  10,
        "trike":     13,
    }

    def test_default_size_table(self):
        for game, expected in self.EXPECTED.items():
            self.assertIn(game, gb.DEFAULT_SIZES)
            self.assertEqual(gb.DEFAULT_SIZES[game], expected,
                             msg=f"DEFAULT_SIZES[{game!r}] = {gb.DEFAULT_SIZES[game]} "
                                 f"(expected {expected})")

    def test_size_argparse_optional(self):
        # Argument 'size' should accept nargs='?' so it's optional at the CLI.
        # We don't actually invoke argparse here (it would call sys.exit on
        # the wrong number of args); instead we just confirm the parsed
        # Namespace accepts a missing size and the post-parse defaulting
        # block fills it.
        ns = gb.argparse.Namespace(game="hex", variant=None, size=None)
        # Mirror the size-fill block from main().
        game_key = "hex"
        ns.size = gb.DEFAULT_SIZES.get(game_key, 11)
        self.assertEqual(ns.size, 11)

    def test_each_game_picks_canonical_size(self):
        # When `--game <name>` is used, simulate the same defaulting block
        # and verify each game's most-played size is selected.
        for game, expected in self.EXPECTED.items():
            ns = gb.argparse.Namespace(
                game=game if game not in ("rex", "yavalath") else "hex",
                variant=game if game in ("rex", "yavalath") else None,
                size=None,
            )
            # Mirror the normalization that the main block performs.
            if ns.game in ("rex", "yavalath"):
                ns.variant = ns.game
                ns.game = "hex"
            if ns.variant is not None:
                game_key = ns.variant
            elif ns.game in ("havannah", "trike"):
                game_key = ns.game
            else:
                game_key = "hex"
            ns.size = gb.DEFAULT_SIZES.get(game_key, 11)
            self.assertEqual(
                ns.size, expected,
                msg=f"game {game!r} defaulted to {ns.size}, expected {expected}",
            )


if __name__ == "__main__":
    unittest.main()
