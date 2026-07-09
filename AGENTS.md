# AGENTS.md

<!-- Hand-curated — see docs/agents/laws.md. Target 20-30 lines; grow only
     from real agent mistakes. Codex hard-caps at 32 KiB and silently
     truncates past it.
-->

## Project at a glance

Python 3.8+ CLI (`generate_board.py`, reportlab) rendering PDF/SVG boards
for **Hex / Rex / Yavalath / Havannah / Trike**. Tests: `tests/test_*_geometry.py`
(unit) + `.github/workflows/test.yml` (CLI smoke matrix).

## File map

- `generate_board.py` — entry; CLI parser at bottom; `_generate_multi()`
  dispatches by `--game`.
- `tests/` — unit tests; import `generate_board` via `sys.path.insert`.
- `.github/workflows/test.yml` — smoke matrix (PR regression gate).

## Build + test

```bash
pip install reportlab                       # runtime
pip install reportlab pymupdf               # + CI (PDF validate)
python -m unittest tests.test_hex_variants  # unit
python generate_board.py 11                 # smoke
```

## Hard rules

- **Don't** add `--game X` without `_draw_X_rules_page` + smoke entries.
- **Don't** edit side-band drawing unless correct for hexhex-N (Rex
  shares it with Hex).
- **Do** read [CONTEXT.md](CONTEXT.md) before touching flags, geometry,
  or copy.
- **Do** add `tests/test_X_geometry.py` for new pure helpers + a smoke
  entry for new flag combos.
- **Do** update [CHANGELOG.md](CHANGELOG.md) `[Unreleased]` per change.

## Cross-references

- [CONTEXT.md](CONTEXT.md) · [`commit-and-branch.md`](docs/agents/commit-and-branch.md) ·
  [`feature-protocol.md`](docs/agents/feature-protocol.md) ·
  [`bug-patterns.md`](docs/agents/bug-patterns.md) ·
  [CHANGELOG.md](CHANGELOG.md)