# Python Addendum — `hex-board-generator`

Stack-specific patterns for the Python 3.8+ / reportlab codebase. Load
this doc when editing `generate_board.py`, `tests/test_*.py`, or any
helper that runs in this repo's Python runtime.

## Universal Python laws (this repo)

### Type hints on the public surface

Every **module-level** `def` in `generate_board.py` is effectively the
public surface — the file is imported by `tests/test_*_geometry.py` and
also executed as a script. Per
[`docs/agents/laws.md § Doc comments on exported identifiers`](../laws.md),
every such function must carry a docstring starting with the function
name and explaining the contract (not the implementation).

Private helpers prefixed `_` (e.g. `_draw_hex_cell`, `_go_col_letter`)
follow the same rule but their docstrings may be terser — contract only.

### No mutable default arguments

Python's late-binding closure captures default args once at `def` time,
not per call. Every helper in `generate_board.py` that takes a list/dict
default uses `None` + an internal rebuild, e.g.:

```python
def f(theme="classic", stones=None):
    if stones is None:
        stones = []
```

**Do not** introduce `def f(stones=[])` even in new helpers.

### Geometry helpers are pure

`havannah_*`, `trike_*`, and `hex_vertices` / `axial_to_pixel` /
`grid_extent_r_units` are **pure functions** — no I/O, no canvas, no
globals. Keep new geometry helpers pure so they stay unit-testable
without spinning up reportlab.

### `reportlab` is the rendering boundary

Everything that draws lives behind `draw_*_board_into_region()` or a
`_draw_*` helper. Geometry functions must not import `reportlab`. This
separation is what makes the geometry tests fast (no canvas, no PDF).

## Project-specific patterns

### CLI dispatch

`argparse` lives at the bottom of `generate_board.py` in
`if __name__ == "__main__":`. Dispatch funnels through `_generate_multi()`,
which must handle every flag (or warn + skip if the flag is
incompatible with the chosen `--game`).

**When adding a flag:**

1. Add the `parser.add_argument` in the `__main__` block.
2. Update `_generate_multi()` to thread the new value through every
   game-dispatch path (`hex`, `rex`, `yavalath`, `havannah`, `trike`).
3. Add a smoke-matrix entry in `.github/workflows/test.yml` covering
   each `--game` combination where the flag is meaningful.
4. Add a unit test if the flag affects any pure helper.

### PDF vs SVG dispatch

`--format pdf` (default) calls `draw_*_board(...)`. `--format svg`
calls `write_*_svg(...)`. SVG paths mirror the PDF draw paths but
operate on a string buffer instead of a `reportlab` canvas. **Both
paths must produce equivalent geometry** — verify by running both
formats on the same args.

### Per-game rules page

Each game has its own `_draw_<game>_rules_page` or `draw_<game>_rules_page`
function in `generate_board.py`. The `argparse` `--rules` flag toggles
appending it. When porting a rule description across games, copy the
text-shape but re-derive the diagram coordinates from that game's
geometry helpers — do not reuse Hex axial→pixel math for Havannah.

### Coordinate systems

- **Hex / Rex / Yavalath**: odd-r offset layout. `_go_col_letter(col)`
  maps column index → letter, skipping `i` per Go convention.
- **Havannah**: axial `(q, r)` with `s = −q − r`. Use `havannah_cells(N)`
  to enumerate and `havannah_in_bounds(q, r, N)` for the predicate.
- **Trike**: axial `(q, r)` with predicate `q ≥ 0 and r ≥ 0 and q + r < N`.
  Use `trike_cells(N)` / `trike_in_bounds(q, r, N)`.

Mixing coordinate systems is the #1 source of off-by-one bugs. Always
state the system at the top of any new helper.

## Python testing conventions

- Tests live in `tests/test_*.py`, run via `python -m unittest
  tests.test_<name>` or `python -m unittest discover tests`.
- Each test module imports `generate_board` via:
  ```python
  import os, sys
  sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
  import generate_board as gb
  ```
- Pure-helper tests are self-contained — no fixture files, no temp
  directories.
- CLI smoke is **not** in `tests/`; it lives in
  `.github/workflows/test.yml` as a shell matrix and is the PR gate.

## Anti-patterns (avoid)

- Introducing a config file or env var in place of a CLI flag — the
  UX contract is the `argparse` surface documented in `README.md`.
- `try/except: pass` around `reportlab` calls — surface the error, the
  smoke matrix will catch it.
- Computing geometry inline inside a draw function. Extract to a
  `_pure()` helper so it can be tested.
- Adding `--game foo` without a complete dispatch path. Smoke matrix
  will fail.

## References

- [`docs/agents/laws.md § Doc comments on exported identifiers`](../laws.md)
  — the universal doc-comment law.
- `generate_board.py` — read the function map (every `def` is in
  alphabetical-ish order; new helpers go near related ones).
- `tests/test_*_geometry.py` — copy the test shape (`unittest.TestCase`,
  `self.assertEqual`, no fixtures) for new helpers.