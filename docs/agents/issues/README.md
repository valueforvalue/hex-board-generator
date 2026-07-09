# Issue Framework

GitHub issue framework: 6-axis label taxonomy, bug + feature
templates, triage workflow. Drop into a target repo via
`scripts/init.sh` (6th init question asks whether to include
issue scaffolding).

## Files

- [`label-taxonomy.md`](label-taxonomy.md) — the 6-axis
  taxonomy (Type × Status × Area × Priority × Cohort ×
  Meta). The canonical reference for what each label means
  and when to apply it.
- [`bug-template.md`](bug-template.md) — the full bug
  template (Symptom, Repro, Root cause, Call sites,
  Proposed fix, Files, Regression net, Related). Used by
  `.github/ISSUE_TEMPLATE/bug.yml`.
- [`feature-template.md`](feature-template.md) — the full
  feature template (User story, Locked decisions, Apply
  sites, Glossary changes, Acceptance criteria, Slice plan,
  Test plan, Files, Regression net, Related). Used by
  `.github/ISSUE_TEMPLATE/feature.yml`.
- [`triage-workflow.md`](triage-workflow.md) — the triage
  state machine. New issue lands unlabelled → maintainer
  applies Type + Status + Area + Priority → agent picks up
  `ready-for-agent`.

## Adopting this framework

1. Run `scripts/sync-labels.sh --dry-run` against the
   target repo to preview the label set.
2. Run `scripts/sync-labels.sh` to apply via the `gh` CLI.
3. Run `scripts/backfill-labels.sh` to apply Area + Priority
   labels to existing open issues by parsing titles + bodies.
4. Copy the template files to `.github/ISSUE_TEMPLATE/` and
   `.github/PULL_REQUEST_TEMPLATE.md`.
5. Update the repo's `CONTRIBUTING.md` to point at the
   bug + feature protocol.

## Why six axes

- **Type × Status** distinguishes bugs from features without
  losing triage routing. A bug and an enhancement can both
  be `ready-for-agent`; the agent reads the Type to know
  which template to apply.
- **Area** lets a maintainer filter by component without
  re-reading every issue title.
- **Priority** is the urgency signal. `priority:high` is
  reserved for known regressions, lost-data bugs, and
  active blockers.
- **Cohort** groups issues that share a discovery context
  (e.g. `audit-fallout`).
- **Meta** is process state, not work state. `blocked`,
  `deferred`, `duplicate` compose.

## References

- `../core/feature-protocol.md` — feature-specific
  procedural contract
- `../core/rpci.md` — Research → Plan → Critique →
  Implement flow (the issue body is the durable record of
  the Research phase)