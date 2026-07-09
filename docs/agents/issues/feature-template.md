# Feature Template

Enhancements use a parallel template that mirrors the bug
template's rigor. The full procedure — 3-tier commit rule,
module discipline, pipeline phasing, slice plan template —
lives in `../core/feature-protocol.md`. This file is the
issue-filing companion.

The GitHub-side YAML form lives in
`../templates/.github/ISSUE_TEMPLATE/feature.yml`.

## Required sections

Every section is required unless marked optional:

```markdown
## Summary
<One sentence: what the feature does and who it serves.>

## User story
<As a <role>, I want <capability>, so that <outcome>.>

## Locked decisions
<Numbered list of decisions settled during recon. Each cites
the source: "Decided in <PR/issue/chat on YYYY-MM-DD>". Locked
decisions are NOT re-opened during the Critique phase unless
the user explicitly says so.>

## Proposed UX
<Per apply-site, what the user sees. References the screen by
name and surface by ID.>

## Apply sites (v1 checklist)
- [ ] <Surface 1>
- [ ] <Surface 2>

The feature is not "shipped" until every box is checked.

## Glossary changes (if any)
<Quote the new entry exactly as it should appear in
CONTEXT.md. If the feature uses existing terms only, write
"None.">

## Schema sketch (if any)
<Migration SQL + version bump + seed data.>

## Acceptance criteria
- [ ] <Observable, testable in 5 min>

## Slice plan
### Slice 1: <name>
- Files: <paths>
- Success criteria: <observable>
- Regression net: <test / probe / manual step>

## Test plan
- Unit: <file: TestXxx>
- Handler: <file: TestXxx>
- Migration: <file: TestXxx>
- Smoke probe: audit/smoke_<feature>.mjs (per UI apply-site)

## Files
- <bulleted list of every file that will be touched>

## Regression net
- <unit test names + audit/smoke probe filenames>

## Related
- <issue numbers, ADR numbers, docs/COMMON_BUGS.md refs>
```

## What shifts vs the bug template

| Bug section | Feature section | Why |
|---|---|---|
| Symptom | User story | Bug has a wrong-behavior; feature has a missing-capability |
| Repro | (skip — UI walk is in the apply-sites list) | Features don't repro; they get exercised by the user story |
| Root cause | Locked decisions | Bug has a why-broken; feature has a why-this-shape |
| Proposed fix | Proposed UX | Bug fixes are scoped to code; features span code + UI |
| Files | Apply sites + Files | Bug touches specific files; feature touches a surface area |
| Regression net | Test plan | Bug needs one net; feature needs per-apply-site nets |

## Labels

| Label | When to apply |
|---|---|
| `enhancement` | Always. Every feature gets this. |
| `needs-triage` | Locked decisions unknown or apply-sites list empty. |
| `needs-info` | User story clear but the locked decisions or apply-sites need the reporter to clarify. |
| `ready-for-agent` | Full template filled in, locked decisions cited, apply-sites checklist complete, slice plan testable. |
| `ready-for-human` | Feature is straightforward but needs human judgment. |
| `wontfix` | Decision to not implement. Must include reasoning. |

Apply `ready-for-agent` only when the P (Plan) phase is
complete. If the issue has User story + Apply sites but no
Locked decisions or Slice plan, leave it at `needs-triage`.

## Anti-patterns

- **Filing a feature without apply-sites.** The checklist
  is the contract; an empty list signals "I haven't thought
  about where this lives in the UI."
- **One mega-slice.** A slice plan with a single "Slice 1:
  ship the whole thing" line is no plan. Decompose until
  each slice is Tier 1 / Tier 2 / Tier 3.
- **Filing the design in the issue body.** The issue is the
  research + acceptance + slice plan. Architecture decisions
  live in `docs/designs/<slug>.md`.
- **Locking decisions the user hasn't settled.** Locked
  decisions cite their source. If a decision is "I think we
  should X", it isn't locked — list it under "Open
  questions" instead.
- **Skipping the smoke probe.** Every UI apply-site needs a
  smoke probe that checks both response shape AND
  `page.url()` after the click.

## References

- `../core/feature-protocol.md` — slice discipline + 3-tier
  commit rule
- `../core/rpci.md` — Research → Plan → Critique → Implement
- [`triage-workflow.md`](triage-workflow.md) — triage state
  machine