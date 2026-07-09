# Framework Bootstrap — Session-Start Checklist

This repo adopted the [agent-stack](https://github.com/jmorris/agent-stack)
framework on 2026-07-09. Read these docs at session start.

## Tier-0 — always loaded

These cross-cut every task. Load them once.

- [ ] [`docs/agents/session-protocol.md`](docs/agents/session-protocol.md) — agent session rules
- [ ] [`docs/agents/laws.md`](docs/agents/laws.md) — non-negotiable laws
- [ ] [`docs/agents/commit-and-branch.md`](docs/agents/commit-and-branch.md) — commit shape + branch policy
- [ ] [`docs/agents/docs-index-scheme.md`](docs/agents/docs-index-scheme.md) — 3-tier progressive disclosure
- [ ] [`docs/agents/glossary-discipline.md`](docs/agents/glossary-discipline.md) — glossary maintenance
- [ ] [`AGENTS.md`](AGENTS.md) — project-specific session notes (hex-board-generator)
- [ ] [`CONTEXT.md`](CONTEXT.md) — project glossary (Hex / Havannah / Trike / etc.)

## Tier-1 — load by task role

Load only the ones that match your task.

- [ ] [`docs/agents/rpci.md`](docs/agents/rpci.md) — non-trivial work (3+ files or design questions)
- [ ] [`docs/agents/tdd.md`](docs/agents/tdd.md) — any feature or bug fix
- [ ] [`docs/agents/feature-protocol.md`](docs/agents/feature-protocol.md) — adding a feature
- [ ] [`docs/agents/code-changes.md`](docs/agents/code-changes.md) — cross-layer change
- [ ] [`docs/agents/bug-patterns.md`](docs/agents/bug-patterns.md) — hunting a bug or reviewing a fix
- [ ] [`docs/agents/complexity.md`](docs/agents/complexity.md) — designing a new module or reviewing interface shape

## Tier-2 — on demand

Per addendum. Load only the one that matches the target stack.

- [ ] [`docs/agents/addenda/python.md`](docs/agents/addenda/python.md) — Python stack patterns (reportlab, geometry helpers)

## Issue framework

Adopted. See [`docs/agents/issues/`](docs/agents/issues/) for the templates
and triage workflow. CLI smoke matrix lives in
[`.github/workflows/test.yml`](../../.github/workflows/test.yml) and is the
canonical regression gate for any flag-changing PR.

## Bundled skills

None selected. See `skills/SKILLS.md` (or the bundled copy if applicable)
and pick what you need.

## Branch model

single-branch (`main`).

## Conventions in this repo

- Commit subjects follow Conventional Commits (`feat:`, `fix:`, etc.)
- CHANGELOG.md `[Unreleased]` block updated per slice
- Glossary ([CONTEXT.md](CONTEXT.md)) updated whenever a new term is introduced
- Issue tracker uses 6-axis label taxonomy (see
  [`docs/agents/issues/label-taxonomy.md`](docs/agents/issues/label-taxonomy.md))
- Smoke matrix in `.github/workflows/test.yml` is the PR regression gate
  for any flag change