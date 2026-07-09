# Triage Workflow

The state machine for moving GitHub issues from "filed" to
"closed". Adopting repos run this workflow in their issue
tracker; the labels and the GitHub-side automation live in
the labels script and the issue templates.

## The flow

```
[filed]
   │
   ▼
[needs-triage] ────► [wontfix] (decision: no)
   │
   ▼
[needs-info] (waiting on reporter)
   │
   ▼
[ready-for-agent] OR [ready-for-human]
   │
   ▼
[PR opened]
   │
   ▼
[PR merged]
   │
   ▼
[closed]
```

## Step-by-step

1. **New issue lands** with no labels (or just `enhancement`).
2. **Maintainer applies the Type label** (`bug` /
   `enhancement` / `documentation`).
3. **Maintainer applies the Status label** based on what's
   missing:
   - `needs-triage` if Root cause / Locked decisions unknown
   - `needs-info` if the reporter owes detail
   - `ready-for-agent` when the template is complete
4. **Maintainer applies the Area label** based on the
   affected component.
5. **Maintainer applies the Priority label** based on
   impact.
6. **Agent picks up `ready-for-agent` issues**, drops the
   Status label, works the slice, applies the next Status
   label (`needs-info` if blocked on the user, no label on
   merge).

## When to apply `ready-for-agent`

**For bugs:** the template must be complete. Specifically:

- Symptom: filled
- Repro: numbered steps
- Root cause: file:line cited
- Proposed fix: paragraph
- Files: bulleted
- Regression net: test names or probe filenames

If any of those is missing, the issue stays at
`needs-triage`.

**For features:** the template must be complete.
Specifically:

- User story: filled
- Locked decisions: at least one cited
- Apply sites: at least one checkbox
- Acceptance criteria: at least one testable criterion
- Slice plan: at least one slice with files + success
  criteria + regression net

If any of those is missing, the issue stays at
`needs-triage`.

## Backfilling labels

Existing open issues often arrive at this framework without
any of the 6-axis labels. The `scripts/backfill-labels.sh`
script applies Area + Priority labels to existing issues by
parsing titles + bodies. Idempotent.

```bash
bash scripts/backfill-labels.sh
```

## Anti-patterns

- **Auto-applying `ready-for-agent` because the issue looks
  long.** The Status label reflects template completeness,
  not issue length.
- **Skipping the Status label on triage.** Every issue needs
  at least one Status label so the backlog can be filtered.
- **Applying two Area labels.** The agent can't load docs
  for two components at once. Pick the primary one.
- **Closing `wontfix` without a comment explaining the
  decision.** The reasoning is the durable record.