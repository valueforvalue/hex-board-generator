# hex-board-generator

Generates printable PDF (and SVG) game boards for **Hex**, **Rex** (misère
Hex), **Yavalath**, **Havannah**, and **Trike** — sized for Go stones,
paper-and-pencil play, or arbitrary paper. Entry point is
`generate_board.py`; behavior is parameterized via `argparse` flags rather
than a config file.

## Language

**Game**: One of `hex`, `rex`, `yavalath`, `havannah`, `trike`. Selected by
`--game` (or its alias `--variant`).
_Avoid_: "mode", "board type" (ambiguous with paper/layout type).

**Variant**: A Hex sub-game (currently `rex` and `yavalath`) passed via
`--variant`. Variants share Hex's geometry; only the rules page and footer
change.
_Avoid_: "mode", "flavor".

**hexhex-N**: The standard rhombus-shaped N×N Hex board, also used by Rex
and Yavalath. Cells are addressed in **odd-r offset** layout, columns
`a..` (skipping `i`) and rows `1..N` per Go convention.
_Avoid_: "hex grid", "hex board" (too generic — Havannah is also hex).

**base-N Havannah**: A regular hexagon of cells, side length N. Cell count
is `3N² − 3N + 1`. Cells are addressed in **axial (cube) coordinates**
`(q, r)` with `s = −q − r`. Center is `(0, 0)`.
_Avoid_: "N×N Havannah" (wrong geometry — it's hexagonal, not square).

**side-N Trike**: A triangle of hex cells, side length N. Cell count is
`N(N+1)/2`. Cells addressed in axial `(q, r)` with predicate
`q ≥ 0 and r ≥ 0 and q + r < N`.
_Avoid_: "N×N Trike" (wrong shape).

**R (cell radius)**: The hex flat-to-flat radius in points. All sizing math
is derived from a single `R` per board, computed by
`compute_r()` / `compute_r_for_extent()` to fit the chosen paper + margin.
_Avoid_: "size" (overloaded with the `size` CLI arg, which means N).

**Stone size**: The Go-stone diameter in mm, passed via `--stone-size`.
Triggers `auto_pick_paper()` and `stone-mode` footer/rules language.
_Avoid_: "piece size" (the game doesn't ship pieces — these are user stones).

**Theme**: Color preset selected via `--theme`. One of `classic` (default),
`light`, `dark`, `wood`. Cell colors come from `_havannah_cell_color` /
`_trike_cell_color` (game-specific).
_Avoid_: "skin", "color scheme".

**Label set**: Side-band label style for Hex (`wb` White/Black default, or
`rb` Red/Blue). Ignored for Havannah/Trike/Yavalath (no side bands) — a
warning is printed.
_Avoid_: "color set", "side labels".

**Corner dots**: Filled circles marking the four corner hexes per Hex board
convention (corner cells belong to both adjacent sides). Opt-in for Hex
and Havannah; ignored for Trike/Yavalath.
_Avoid_: "corner markers", "anchor dots".

**Fit mode**: One of `safemode` (default, stone ≤ 70% of hex flat-to-flat),
`makeitwork` (≤ 85%, margin shrinks to 4pt), `unsafe` (≤ 100%, flush).
_Avoid_: "scale mode", "size mode".

**Pen-paper mode**: `--pen-paper` flag. Thicker hex strokes, Go-style
coordinate labels inside cells, footer with notation/first-player/win
hint. Mutually orthogonal to stone mode (which is auto-enabled by
`--stone-size`).
_Avoid_: "pen and paper mode" — keep the flag spelling.

**Rules sheet**: `--rules` flag. Appends one page of game-specific rules
(drawn by `_draw_<game>_rules_page`) with a small winning-position
diagram for that game.

## Relationships

- A **hexhex-N** board has `N²` cells.
- A **base-N Havannah** has `3N² − 3N + 1` cells.
- A **side-N Trike** has `N(N+1)/2` cells.
- **Rex** and **Yavalath** are **Hex variants** — they reuse hexhex-N
  geometry; only the rules page and footer text differ.
- **Havannah** and **Trike** are separate **games** with their own
  geometry helpers (`havannah_*`, `trike_*`) and draw entry points
  (`draw_havannah_board`, `draw_trike_board`).
- A **fit mode** constrains `R` given a **stone size** and **paper**.
- A **theme** supplies colors consumed by both the board renderer and the
  rules-sheet diagrams.

## Example dialogue

- "I want a hexhex-9 with `--variant rex`, dark theme, and a rules page."
  → `python generate_board.py 9 --variant rex --theme dark --rules`
- "Generate base-8 Havannah on ANSI-B for 22mm stones."
  → `python generate_board.py 8 --game havannah --paper ansi-b --stone-size 22`
- "Make a side-13 Trike reference booklet (13/15/19)."
  → `python generate_board.py --game trike --sizes 13,15,19`

## Historical

- **Rex** was originally implemented as a separate `--game rex` choice; it
  is now `--game hex --variant rex` (or the alias `--game rex`). Old
  callers still work — both routes funnel through the Hex draw path.
- The Havannah/Trike geometry helpers (`havannah_*`, `trike_*`) were
  factored out of inline math in `generate_board.py` to make the cell
  counts and in-bounds predicates unit-testable. Tests live under
  `tests/test_havannah_geometry.py`, `tests/test_trike_geometry.py`,
  `tests/test_hex_variants.py`.

## Adding features

See [`docs/agents/feature-protocol.md`](docs/agents/feature-protocol.md)
for the canonical procedure.

## Laws (non-negotiable)

- The `--label-set` flag is **Hex only**. New games without side bands
  must print a warning when it's set, never silently ignore it. (Origin:
  the four `_draw_<game>_rules_page` paths enforce this in
  `generate_board.py`; CI smoke matrix would catch a regression.)
- All geometry-changing flags (`--game`, `--variant`, `--pen-paper`,
  `--n-up`, `--sizes`, `--pad`, `--rules`) must round-trip cleanly
  through `args` in `_generate_multi()` — no flag may be silently
  dropped between the four game dispatch paths. (Origin: CLI smoke
  matrix in `.github/workflows/test.yml`.)
- CLI smoke matrix in `.github/workflows/test.yml` is the regression
  net: every flag combination that ships must have at least one matrix
  entry, and every matrix entry must succeed (PDF + SVG).