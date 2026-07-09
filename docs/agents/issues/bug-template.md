# Bug Template

Every bug in a repo that adopts agent-stack is filed as a
GitHub issue with this template. The issue is the durable
record; the chat is not. A bug filed without research
attached is incomplete and will be bounced back for
investigation.

This file documents the full template. The GitHub-side YAML
form lives in `../templates/.github/ISSUE_TEMPLATE/bug.yml`.

## Required sections

Use this template when filing a bug. Replace placeholders;
do not ship an issue with `<!-- ... -->` comments still in
the body.

```markdown
## Symptom
<What the user sees. Verbatim error text if any. One
paragraph, no solutions, no speculation about cause.>

## Repro
<Numbered steps a maintainer can follow to reproduce.
Include the URL, button name, expected vs actual. If the
bug requires seeded data, name the seed command.>

## Root cause
<One paragraph, max 5 sentences. File:line of the buggy
code. Why it produces the symptom. Link the spec / contract
the code violated, if any.>

## Call sites / blast radius
<List every place the same code path runs. For
`document.addEventListener("click", ...)` the blast radius
is every page that contains the matching selector.>

## Proposed fix
<One paragraph: the smallest change that resolves the root
cause. If the fix has more than one reasonable shape, list
the options and recommend one.>

## Files
<Bulleted list of every file that will be touched.>

## Regression net
<Bulleted list: unit test name(s), smoke probe filename(s),
or a manual smoke step.>

## Related
<Issue numbers, ADR numbers, or `docs/COMMON_BUGS.md`
section references that overlap with this bug.>
```

## What goes in each section

**Symptom** is what the user told you, not what you
diagnosed. If the user said "the buttons don't work", write
"the buttons don't work" — don't paraphrase to "the click
handler is detached from the DOM". The diagnosis lives in
Root cause.

**Repro** is for the next maintainer. If the bug is in
production, write the steps the user followed. If it's
caught by a probe, write the probe invocation.

**Root cause** must cite a file:line. If you can't, the
issue is not ready — you haven't done enough research. Label
it `needs-triage`.

**Call sites / blast radius** distinguishes "the bug" from
"the bug class". The Fix addresses both when the blast
radius is small; for big blast radius, the Fix may need a
refactor + the targeted fix.

**Proposed fix** is one paragraph, not a plan. The plan with
slices and success criteria lives in the PR description or
the design artifact — not in the issue body.

**Regression net** names the test or probe that will catch
the bug if it regresses. A regression net that just
"confirms the fix works" is not enough; it must catch the
same shape of bug from a different entry point.

## Labels

| Label | When to apply |
|---|---|
| `bug` | Always. Every bug gets this. |
| `needs-triage` | Root cause or files unknown. |
| `needs-info` | Symptom clear but the repro or root cause needs the reporter to clarify. |
| `ready-for-agent` | Full template filled in, root cause cited, fix proposed. An AFK agent can implement. |
| `ready-for-human` | Bug is straightforward but needs human judgment (UX decision). |
| `wontfix` | Decision to not fix. Must include reasoning in a comment. |

Apply `ready-for-agent` only when the R (Research) is
complete. If the issue has Symptom + Repro but no Root
cause, leave it at `needs-triage`.

## Anti-patterns

- **Filing a bug with just the title.** For a real bug,
  every section is required.
- **Filing the fix in the issue body.** The issue is the
  research, the PR is the fix. Don't paste code into the
  issue; reference the files it will touch.
- **Skipping Repro because "it's obvious".** The next
  maintainer is not you.
- **Filing during the chat session without writing it to the
  repo's actual issue tracker.** Issues live on GitHub.
- **Filing a "feature" as a "bug".** If the proposed fix is
  to add new behavior, label it `enhancement` and use the
  feature template.