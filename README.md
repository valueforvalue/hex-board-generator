# HEX Board Generator

Generates printable HEX board PDFs sized for Go stones.

## Usage

```bash
python generate_board.py <size> [--paper letter|legal|tabloid|a3|a4|ansi-b] [-o output.pdf]
```

Paper auto-rotates to landscape when wider fits better (always for N >= 3).

### Examples

```bash
python generate_board.py 11                            # Letter landscape
python generate_board.py 11 --paper tabloid            # 17x11 in, big hexes
python generate_board.py 11 --paper ansi-b -o big.pdf  # 22x17 in
```

## Board sizing notes

- Letter (11x8.5 in): hex flat-to-flat ~16 mm -- only fits mini stones
- Tabloid (17x11 in): hex flat-to-flat ~25 mm -- fits 19 mm Go stones
- ANSI-B (22x17 in): hex flat-to-flat ~32 mm -- generous fit for 22-24 mm stones

Stone diameter should be <= 70% of hex flat-to-flat for comfortable play.

## Requirements

- reportlab