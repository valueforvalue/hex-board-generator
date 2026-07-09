# Commits and Branches

Procedural contract for how changes land in a repo that adopts
agent-stack. Adopting repos should copy this file (with
project-specific edits) into their own `docs/agents/` or
inline it into `AGENTS.md`.

## Commit shape

### One commit = one reviewable unit

Default: one user-visible capability or one well-scoped bug
fix, including its tests + docs + slice-internal refactors.

A multi-layer feature can be a single commit when the layers
only make sense together. Slice decomposition into multiple
reviewable commits is a separate decision — see
[`feature-protocol.md`](feature-protocol.md) for the
decomposition rules.

### Commit message shape

`<area>: <imperative summary>` for the subject (≤72 chars),
blank line, then 1–3 bullets explaining *why* and what the
regression net is. Reference the issue number if one exists.

Look at recent commits with `git log --oneline -20` for the
in-repo house style before writing your first commit.

### Conventional Commits prefix

The subject prefix follows Conventional Commits:

- `feat:` — new user-visible capability
- `fix:` — bug fix
- `refactor:` — internal change, no user-visible effect
- `docs:` — documentation only
- `test:` — test-only change
- `chore:` — build / tooling / non-code

Adopting repos may add project-specific prefixes (`audit:`,
`ux:`, `perf:`) when the project's commit log benefits from
finer-grained categorization.

### Anti-patterns

- **Mega-commit** that bundles view + handler + audit test +
  regression net + CHANGELOG for one feature with no slice
  plan. The fix: slice the plan first, ship the slices.
- **Per-layer micro-commit** (schema alone, service alone,
  handler alone). Three commits each uncompilable. Bundle
  into a vertical slice instead.
- **Drive-by refactor** committed alongside a feature
  without a slice plan. Open a separate PR.
- **"WIP" commit** pushed to a shared branch. Use a draft
  PR or hold locally.

## Branch policy

The default flow is to **commit and push directly to the
integration branch**. Feature branches are reserved for
work that meets at least one of these criteria:

- The work will land across multiple commits and benefits
  from review or rollback granularity that doesn't fit on
  the integration branch.
- The user explicitly asks for a branch.
- The work is a significant new surface (a new screen, a new
  sub-system, a new external integration) that warrants a
  PR for review.

### Single-branch model (default)

- One integration branch (e.g. `main` or `dev`).
- Direct commits for slice-shaped work.
- Feature branches for multi-commit or new-surface work.
- Production releases tag the merge commit on the integration
  branch.

### Three-branch model (advanced)

For repos that need a frozen production-history anchor plus
a released-code home plus an integration branch:

- **`integration`** (e.g. `dev`) — direct commits for slice-
  shaped work.
- **`release`** (e.g. `stable`) — released-code home. Promotion
  requires a passing full suite + visual sweep on integration.
  No direct commits.
- **`legacy`** (e.g. `main`) — frozen legacy production record.
  Sits at the production anchor commit, accepts no new
  commits.

Promotion flow: integration → release via PR (CI green, gate
chain documented in `docs/adr/`).

### Branch hygiene

- **No dangling branches.** A `feature/<short-kebab>` branch
  exists to land ONE feature. Once merged into integration,
  delete the branch in the same merge step.
- **No `wip`, no `temp`, no `agent-scratch`.** Branch names
  that signal indecision are noise. If a branch isn't worth
  naming, the work belongs on integration directly.
- **Large feature branches need a PR opened early.** When a
  feature branch is used, open the PR the moment the first
  green commit lands, even if the work is WIP. Don't let a
  branch accumulate commits in isolation for days.

### Push verification

Before pushing:

- Run the project's short test suite.
- Run any per-layer guards (lint, format, snapshot tests).
- Update CHANGELOG `[Unreleased]` block under the right
  heading (`### Added`, `### Changed`, `### Fixed`,
  `### Removed`, `### Maintenance`).
- Update CHANGELOG bullet for every user-visible change in
  the same commit that lands the change.

## References

- [`feature-protocol.md`](feature-protocol.md) — slice
  decomposition + the 3-tier commit rule
- [`laws.md`](laws.md) — non-negotiable laws that gate
  merge