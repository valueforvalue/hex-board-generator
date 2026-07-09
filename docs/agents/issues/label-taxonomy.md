# Label Taxonomy (6-axis)

Every GitHub issue in a repo that adopts agent-stack carries
labels from six axes. Each axis answers a different question;
together they let maintainers filter the backlog by component,
urgency, and triage state without re-reading every issue
title.

## The six axes

### Type — what's the work?

| Label | When to apply |
|---|---|
| `bug` | Always. Every bug gets this. |
| `enhancement` | Always. Every feature gets this. |
| `documentation` | Doc-only change. |

### Status — where is it in triage?

| Label | Meaning |
|---|---|
| `needs-triage` | Maintainer needs to evaluate this issue |
| `needs-info` | Waiting on reporter for more information |
| `ready-for-agent` | Fully specified, ready for an AFK agent |
| `ready-for-human` | Requires human implementation |
| `wontfix` | Will not be actioned |

For **bugs**, `ready-for-agent` requires the bug template
(Symptom + Repro + Root cause + Files + Regression net)
filled in with a file:line cite for Root cause.

For **features**, `ready-for-agent` requires the feature
template (User story + Locked decisions + Apply sites +
Slice plan) filled in with at least one apply-site and one
testable slice.

### Area — which part of the system?

Adopting repos define their own area labels. The default set:

| Label | Signals |
|---|---|
| `area:backend` | Server code (handlers, services, middleware) |
| `area:frontend` | Frontend JS, CSS, framework attrs, view templates |
| `area:cli` | Headless subcommand surface |
| `area:db` | Schema, migrations, queries |
| `area:export` | Export surface (file outputs) |
| `area:import` | Import surface (file inputs) |
| `area:docs` | Glossary, ADRs, agent docs |
| `area:build` | Build, CI, packaging |

Each area label signals the agent to load specific docs. The
adopting repo's docs-index should list the mapping.

### Priority — how urgent is it?

| Label | When to apply |
|---|---|
| `priority:high` | Known regression, lost-data bug, active user blocker |
| `priority:medium` | Default. Bugs with workarounds, features on the backlog |
| `priority:low` | Speculative, nice-to-have, or research-only |

### Cohort — what batch does it belong to?

| Label | When to apply |
|---|---|
| `audit-fallout` | Issue discovered by a full audit sweep |

Cohort labels group issues that share a discovery context.
They let a maintainer filter the audit follow-up work
without re-reading every audit-finding issue. New cohort
labels are rare — created when a new sweep produces a
backlog of related issues.

### Meta — process state, not work state

| Label | When to apply |
|---|---|
| `blocked` | Held by another issue. Comment with a link. |
| `deferred` | Held until a future trigger. Issue body documents reopen conditions. |
| `duplicate` | This issue already exists. Comment with a link. |
| `good first issue` | Small enough for a newcomer to pick up. |
| `help wanted` | Maintainer is actively looking for someone to pick this up. |
| `invalid` | Not a real issue (test post, spam, off-topic). |
| `question` | Reporter is asking, not filing. |
| `wontfix` | Decision to not action. Must include reasoning in a comment. |

## One label per axis

An issue has **exactly one label from each axis** (where the
axis applies). Two `area:*` labels on one issue means the
agent doesn't know which component to load docs for. Zero
`area:*` labels means the issue hasn't been routed.

The exception is `Meta` — an issue can carry multiple `Meta`
labels (`duplicate` + `wontfix` for "this is a dup, also we
won't fix either"). Process labels compose.

## Adding a new area label

Add it to `scripts/sync-labels.sh` and run the script. The
label set is intentionally limited; new components should be
infrequent. If you find yourself wanting more than ~15 area
labels, the taxonomy probably needs to split by sub-area.

## References

- [`bug-template.md`](bug-template.md) — bug protocol
- [`feature-template.md`](feature-template.md) — feature
  protocol
- [`triage-workflow.md`](triage-workflow.md) — triage state
  machine
- `../scripts/sync-labels.sh` — canonical label spec
  (idempotent; safe to re-run)