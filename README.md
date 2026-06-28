# HEX Board Generator

Generate printable HEX board PDFs sized for Go stones, paper-and-pencil play, or any custom layout.

11×11 is the classic Hex board size. This generator also supports 7×7, 9×9, 13×13, 14×14, 19×19, and any other N×N.

## Quick start

```bash
python generate_board.py 11                          # 11x11 on Letter (default)
python generate_board.py 11 --pen-paper              # paper & pencil mode
python generate_board.py 11 --stone-size 19          # auto-pick paper for 19mm stones
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
- Coordinate labels (a..k, 1..N) along edges
- Footer hint: notation, first player, win condition

### Coordinate labels (`--coords` / `--no-coords`)

Show or hide edge coordinate labels independently.

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

### Stone play (auto-picks paper)

```bash
python generate_board.py 11 --stone-size 19
```

Auto-selects ANSI-B (17×22) for 19mm stones with 63% comfortable fit.

![Stone play](docs/gallery/08_stone19.png)

## Full flag reference

```
python generate_board.py <size> [options]

  size                Board size (e.g. 11 for 11x11)
  -o, --output        Output PDF path (default: hex_board.pdf)
  -p, --paper         letter, legal, tabloid, a3, a4, ansi-b (auto-detected with --stone-size)
  --stone-size MM     Stone diameter in mm; auto-picks paper if -p omitted
  --margin PTS        Override page margin in points (1 inch = 72 pt)
  --pen-paper         Paper-and-pencil mode: thicker strokes, coords, footer
  --coords            Show coordinate labels
  --no-coords         Suppress coordinate labels
  --theme NAME        classic, light, dark, wood
  --label-set NAME    wb (White/Black) or rb (Red/Blue)
  --corner-dots       Mark the four corner hexes
  --n-up N            Pack N boards per page
  --pad N             Generate N copies (one per page)
  --sizes LIST        Comma-separated sizes, one page each
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

## Requirements

- Python 3.8+
- reportlab

Install: `pip install reportlab`