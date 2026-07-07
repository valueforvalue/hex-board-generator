# HEX Board Generator

[![Test](https://github.com/valueforvalue/hex-board-generator/actions/workflows/test.yml/badge.svg)](https://github.com/valueforvalue/hex-board-generator/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Generate printable **Hex**, **Rex**, **Yavalath**, **Havannah**, and **Trike** board PDFs sized for Go stones, paper-and-pencil play, or any custom layout.

11×11 is the classic Hex board size. This generator also supports 7×7, 9×9, 13×13, 14×14, 19×19, and any other N×N — the same hexhex-N geometry covers both Hex and the misère variant Rex. For Yavalath, hexhex-5 (61 cells) is the standard published size. For Havannah, base-8 (169 cells) and base-10 (271 cells) are the standard sizes. For Trike, side-7 (28 cells) through side-19 (190 cells) are supported, with 13–15 standard for serious play.

## Quick start

```bash
python generate_board.py                                # size defaults per game (11, 10, 13, 5)
python generate_board.py 11 --pen-paper              # paper & pencil mode
python generate_board.py 11 --stone-size 19          # auto-pick paper for 19mm stones
python generate_board.py --game havannah              # base-10 Havannah (default)
python generate_board.py --game havannah --size 8     # base-8 Havannah override
python generate_board.py 10 --game havannah --rules  # base-10 with rules page
python generate_board.py --game yavalath --rules      # hexhex-5 Yavalath (default)
python generate_board.py 9 --variant rex --rules     # hexhex-9 Rex (misere Hex)
python generate_board.py 7 --game trike              # side-7 Trike
python generate_board.py 13 --game trike --rules     # side-13 Trike with rules

Default sizes (most-played standard):
- `--game hex` / `--variant rex`: 11
- `--game yavalath`: 5
- `--game havannah`: 10
- `--game trike`: 13
```

## Board sizing notes

| Paper        | Size (in)       | Max hex flat-to-flat | Fits |
|--------------|-----------------|----------------------|------|
| Letter       | 8.5 × 11        | ~16 mm               | Mini stones |
| Legal        | 8.5 × 14        | ~19 mm               | 13mm stones |
| Tabloid      | 11 × 17         | ~25 mm               | 19mm stones |
| A3           | 11.7 × 16.5     | ~26 mm               | 19mm stones |
| ANSI-B       | 17 × 22         | ~32 mm               | 22mm stones (Go standard) |

Stone diameter should be ≤ 70% of hex flat-to-flat for comfortable play.

## Features

### Themes (`--theme`)

| Command | Theme |
|---------|-------|
| `--theme classic` *(default)* | Light gray cells, gray/black bands |
| `--theme light` | Pure white cells, no checkerboard |
| `--theme dark` | Black background, dark blue cells, orange bands |
| `--theme wood` | Beige/brown wood-look, antique-white background |

### Label conventions (`--label-set`)

- `wb` *(default)* — "White Side" / "Black Side" (classic)
- `rb` — "Red Side" / "Blue Side" (modern convention)

### Corner dots (`--corner-dots`)

Marks the four corner hexes with filled circles per Hex board convention. Corner cells belong to both adjacent sides.

### Paper & pencil mode (`--pen-paper`)

- Thicker hex strokes
- Go-style coordinate labels inside each cell (`a`–`h`, `j`–`z` columns; rows `1`–`N`)
- Footer hint: notation, first player, win condition
- With `--stone-size`, instructions adapt for stone play (place stones in hex centers)

### Coordinate labels (`--coords` / `--no-coords` / `--cell-coords`)

- `--coords` / `--pen-paper` — show Go-style labels inside each cell (default for legible boards)
- `--no-coords` — suppress all coordinate labels
- `--cell-coords` — same as `--coords` (kept for clarity)

### Stone play mode (`--stone-mode`)

Auto-enabled when `--stone-size` is given. Tweaks the footer and rules page for stone play instead of pen-and-paper (e.g. "place stones in hex centers" rather than "mark with X/O").

### Fit modes (`--safemode` / `--makeitwork` / `--unsafe`)

- `safemode` *(default)* — stone ≤ 70% of hex flat-to-flat (comfortable)
- `makeitwork` — stone ≤ 85% (tight fit; shrinks margin to 4pt to fill page)
- `unsafe` — stone ≤ 100% (flush; for testing only)

### Multi-board output

| Flag | Output |
|------|--------|
| `--n-up N` | N boards per page (e.g. `--n-up 4` for a 2×2 grid handout) |
| `--pad N` | N copies, one per page (1942 Polygon 50-sheet pad style) |
| `--sizes 9,11,13` | One page per size (reference booklet) |

### Rules sheet (`--rules`)

Append a one-page rules summary at the end of the PDF. Content adapts to the selected `--game/--variant`: Hex covers Players, Setup, Goal, How to play, Win condition, the swap rule, and coordinate notation; Havannah and Trike cover their own win conditions and notation; Rex covers the misère flip; Yavalath covers the 4-wins / 3-loses rule, optional swap rule, and Pentalath bonus. Adapts to the chosen `--theme` and `--label-set`.

## Havannah

Havannah is a connection game on a regular hexagonal board (no side bands).
Add `--game havannah` to render a Havannah board instead of Hex. Size is the
**base** — the number of cells along each of the six edges:

| Base | Total cells | Standard for |
|------|-------------|--------------|
| 8    | 169         | Beginners (Ravensburger) |
| 10   | 271         | Standard / Computer Olympiad |

Cells are addressed in **axial (cube) coordinates** `(q, r)` with `s = −q − r`.
The center cell is `(0, 0)` and the six corners sit at `(±(N−1), 0)`, `(±(N−1), ∓(N−1))`, `(0, ±(N−1))`.
The six Havannah win conditions are diagrammed on the optional rules page (see `--rules`):

- **Ring** — a closed loop around one or more cells
- **Bridge** — connect any two of the six corner cells
- **Fork** — connect any three of the six edges (corners are not part of an edge)

```bash
python generate_board.py 10 --game havannah                       # base-10 Havannah
python generate_board.py 10 --game havannah --pen-paper            # paper & pencil mode
python generate_board.py 8 --game havannah --theme dark           # dark theme
python generate_board.py 8 --game havannah --stone-size 19        # auto-pick paper
python generate_board.py 8 --game havannah --rules                # + rules page
python generate_board.py 8 --game havannah --n-up 4               # 4-up handout
python generate_board.py 8 --game havannah --format svg           # vector SVG
```

### Flags that differ for Havannah

- `--label-set` is ignored (no side bands). A warning is printed if set.
- `--corner-dots` is honored as for Hex (opt-in).
- `--cell-coords` renders the axial `(q, r)` label inside each cell when cells are large enough.
- `--no-coords` suppresses all coordinate labels.
- All other flags (`--theme`, `--paper`, `--stone-size`, `--pen-paper`, `--n-up`, `--pad`, `--sizes`, `--format`, `--rules`) work identically.

## Hex variants

Hex variants reuse the same hexhex-N rhombus geometry (and every flag above:
theme, paper, stone-size, n-up, pad, sizes, format, rules). Pick a variant with
`--variant <name>`, or use the convenience aliases `--game yavalath` and
`--game rex`, which are equivalent to `--game hex --variant yavalath` /
`--variant rex`.

### Yavalath (`--variant yavalath`, designer Cameron Browne, 2007)

| Base (N) | Total cells | Standard for |
|----------|-------------|--------------|
| 5        | 61          | Official nestorgames board, beginners |
| 6        | 91          | Intermediate |

- No perimeter bands. Stones sit on cells only.
- On your turn, place a stone of your color on any empty hex.
- **Win**: complete a line of **4** or more of your stones in any direction.
- **Lose**: complete a line of **exactly 3** of your stones (unless that line
  also forms part of a 4+ line; then the win still holds).
- The optional swap rule (White plays first; Black may take White's opening
  stone on Black's first turn) balances the first-move advantage and is
  described on the rules page. Pentalath and a three-player variant are also
  noted there for the same hex set.

```bash
python generate_board.py 5 --variant yavalath --rules                # hexhex-5 + rules page
python generate_board.py 5 --variant yavalath --pen-paper           # paper & pencil mode
python generate_board.py 5 --variant yavalath --n-up 4              # 4-up handout
python generate_board.py 6 --variant yavalath --sizes 4,5,6         # size reference
python generate_board.py 5 --variant yavalath --theme dark          # dark theme
python generate_board.py 5 --variant yavalath --format svg          # vector SVG
python generate_board.py 5 --game yavalath --rules                  # same board, alias
```

Variant-only flag notes:

- `--label-set` and `--corner-dots` are ignored (no side bands or marked corners). A warning is printed if either is set.

### Rex (`--variant rex`, misere Hex)

Same board as Hex, same bands, same coordinate labels. The variant flips the win
condition: the player who connects their two assigned sides LOSES. Win by
forcing the opponent to connect first. A draw is still impossible (Brouwer
fixed-point theorem); the loser is simply the player who moves into a winning
connection.

```bash
python generate_board.py 11 --variant rex --rules       # 11x11 Rex + rules page
python generate_board.py 9  --variant rex --pen-paper   # 9x9 paper & pencil
python generate_board.py 9  --game rex --rules          # alias works identically
```

Standard Hex flags (`--label-set`, `--corner-dots`, `--theme`, `--paper`,
`--stone-size`, `--pen-paper`, `--n-up`, `--pad`, `--sizes`, `--format`,
`--rules`) all behave exactly as for Hex. The footer and the rules page text
describe the misere win condition.

## Trike

Trike is a combinatorial abstract on a triangular hex-tessellated board, point-up.
Add `--game trike` to render a Trike board instead of Hex or Havannah. Size is the
**side length** — the number of hex cells along each edge of the triangle:

| Side | Total cells | Standard for |
|------|-------------|--------------|
| 7–10 | 28–55       | Learning |
| 13–15 | 91–120     | Standard competitive play |
| 19   | 190         | Largest tournament size |

Cells are addressed in **axial coordinates** `(q, r)` with the in-bounds
predicate `q ≥ 0 and r ≥ 0 and q + r < N`. The three vertex cells are
`(0, 0)`, `(N−1, 0)`, and `(0, N−1)`. The rules page (`--rules`) describes
the pawn-movement, scoring, and pie rule mechanics.

```bash
python generate_board.py 7 --game trike                  # side-7 Trike
python generate_board.py 13 --game trike --rules         # side-13 + rules page
python generate_board.py 13 --game trike --theme dark    # dark theme
python generate_board.py 13 --game trike --stone-size 19 # auto-pick paper
python generate_board.py 7 --game trike --n-up 4         # 4-up handout
python generate_board.py 7 --game trike --format svg     # vector SVG
```

### Flags that differ for Trike

- `--label-set` is ignored (no side bands). A warning is printed if set.
- `--corner-dots` is ignored (no marked corners). A warning is printed if set.
- `--cell-coords` renders the axial `(q, r)` label inside each cell when cells are large enough.
- `--no-coords` suppresses all coordinate labels.
- All other flags (`--theme`, `--paper`, `--stone-size`, `--pen-paper`, `--n-up`, `--pad`, `--sizes`, `--format`, `--rules`) work identically.

## Gallery

### Default

```bash
python generate_board.py 11
```

![Default board](docs/gallery/01_default.png)

### Dark theme

```bash
python generate_board.py 11 --theme dark --corner-dots
```

![Dark theme](docs/gallery/02_dark.png)

### Wood theme

```bash
python generate_board.py 11 --theme wood
```

![Wood theme](docs/gallery/03_wood.png)

### Paper & pencil

```bash
python generate_board.py 11 --pen-paper
```

![Paper & pencil](docs/gallery/04_penpaper.png)

### Red/Blue + corner dots

```bash
python generate_board.py 11 --label-set rb --corner-dots
```

![Red/Blue + dots](docs/gallery/05_rb_dots.png)

### N-up handout (4 boards per page)

```bash
python generate_board.py 11 --n-up 4
```

![N-up handout](docs/gallery/06_nup4.png)

### Reference booklet (9×9, 11×11, 13×13)

```bash
python generate_board.py 11 --sizes 9,11,13
```

| 9×9 | 11×11 | 13×13 |
|-----|-------|-------|
| ![9x9](docs/gallery/07_sizes_p1.png) | ![11x11](docs/gallery/07_sizes_p2.png) | ![13x13](docs/gallery/07_sizes_p3.png) |

### Stone play on ANSI-B (auto-picks paper)

```bash
python generate_board.py 11 --stone-size 19
```

Auto-selects ANSI-B (17×22) for 19mm stones with 63% comfortable fit.

![Stone play](docs/gallery/08_stone19.png)

### Stone play on Tabloid (11×17, tight fit)

```bash
python generate_board.py 11 --stone-size 19 --paper tabloid --makeitwork --pen-paper --rules
```

Tabloid 11×17 fits an 11×11 board with 19mm stones at 77% ratio (tight, but playable). Instructions auto-switch to stone-mode language.

![Stone play on tabloid](docs/gallery/10_tabloid_stone.png)

### Rules sheet (`--rules`)

```bash
python generate_board.py 11 --rules
```

Appends a one-page rules summary at the end of the PDF. Content is chosen from the selected `--game`/`--variant`.

![Rules page](docs/gallery/09_rules.png)

## Full flag reference

```
python generate_board.py <size> [options]

  size                Board size (e.g. 11 for 11x11 Hex). Optional; defaults to the most-played standard size for the selected --game/--variant (hex 11, rex 11, yavalath 5, havannah 10, trike 13).
  --game NAME         hex (default), havannah, trike, rex, or yavalath
                       (rex and yavalath are aliases for --game hex --variant <name>)
  -o, --output        Output PDF path (default: hex_board.pdf)
  -p, --paper         letter, legal, tabloid, a3, a4, ansi-b (auto-detected with --stone-size)
  --stone-size MM     Stone diameter in mm; auto-picks paper if -p omitted
  --margin PTS        Override page margin in points (1 inch = 72 pt)
  --pen-paper         Paper-and-pencil mode: thicker strokes, coords inside cells, footer
  --coords            Show coordinate labels (inside each cell when legible)
  --no-coords         Suppress coordinate labels
  --cell-coords       Alias for --coords (inside each cell)
  --stone-mode        Adapt instructions for stone play (auto-enabled by --stone-size)
  --theme NAME        classic, light, dark, wood
  --label-set NAME    wb (White/Black) or rb (Red/Blue) — Hex only (ignored for Havannah, Trike, Yavalath)
  --corner-dots       Mark corner hexes (Hex opt-in, Havannah opt-in, ignored for Trike/Yavalath)
  --variant NAME      rex (misère Hex) or yavalath; only valid with --game hex
  --n-up N            Pack N boards per page
  --pad N             Generate N copies (one per page)
  --sizes LIST        Comma-separated sizes, one page each
  --rules             Append a rules summary page (game/variant-aware: Hex, Havannah, Trike, Rex, Yavalath)
  --format FMT        pdf (default) or svg
  --safemode          Default. Stone ≤ 70% hex flat-to-flat.
  --makeitwork        Stone ≤ 85%. Shrinks margin to 4pt.
  --unsafe            Stone ≤ 100%. Flush fit.
```

## About Hex

Hex is a two-player connection game invented by Piet Hein in 1942 and
rediscovered by John Nash in the late 1940s. Players alternate placing
stones on hex cells; the first to form a connected chain linking their
two assigned sides wins. See [Wikipedia](https://en.wikipedia.org/wiki/Hex_(board_game))
for the full rules.

## About Havannah

Havannah is a two-player connection game invented by Christian Freeling in 1981.
Played on a regular hexagonal board (no side bands), the goal is to complete any
one of three structures: a **ring** (closed loop), a **bridge** (connect two
corner cells), or a **fork** (connect three edges). The pie rule is used to
balance the first-move advantage. See
[Wikipedia](https://en.wikipedia.org/wiki/Havannah_(board_game)) for the full rules.

## About Rex

Rex is the misère variant of Hex, played on the same hexhex-N rhombus with the
same perimeter bands. The win condition is flipped: the player who connects
their two assigned sides LOSES, and the other player wins. Both players are
therefore trying to *avoid* completing a chain while maneuvering the opponent
into having to. A draw is still impossible by the same Brouwer fixed-point
argument that guarantees a Hex winner exists; the loser is simply the player
who first moves into a winning connection. Optionally use the same swap rule
as Hex to balance the first-move advantage. See the Hex article on
[Wikipedia](https://en.wikipedia.org/wiki/Hex_(board_game)) under "Misere Hex"
for background.

## About Yavalath

Yavalath is a 2007 abstract designed by Cameron Browne's Ludi program (the
same system that later discovered Y and Pentalath). It is published as a
hexhex-5 set (61 cells) by Nestorgames. Players alternately place one of
their colored stones on any empty cell. The first to complete a line of four
or more stones in any direction wins; however, completing a line of exactly
three loses immediately, unless that line is also part of a longer winning
line. The same set plays Pentalath (5-in-a-row with Go-style enemy captures)
and a three-player elimination variant. An optional swap rule balances the
opening. See
[Yavalath rulebook (PDF)](https://nestorgames.com/rulebooks/YAVALATH_EN.pdf)
for the canonical rules.

## About Trike

Trike is a two-player combinatorial abstract designed by Alek Erickson in 2020.
Played on a triangular hex-tessellated board, players take turns moving a
single shared pawn any distance in a straight line, leaving a checker of their
color on the destination. The game ends when the pawn is trapped; each player
then scores 1 point per checker adjacent to (or under) the pawn, and the higher
score wins. The pie rule is used to balance the first-move advantage. See
[Trike on BoardGameGeek](https://boardgamegeek.com/boardgame/307379/trike) for the full rules.

## Requirements

- Python 3.8+
- `reportlab` (rendering)
- `pymupdf` *(optional, used by CI to validate PDFs — not needed for local use)*

Install runtime dependencies: `pip install reportlab`. To run the CI smoke tests locally: `pip install reportlab pymupdf`.