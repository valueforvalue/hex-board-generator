# Subagent Delegation

When to dispatch work to a subagent instead of doing it
inline, and how to structure the delegation. The pattern
is now standard across production agent harnesses
([Claude Code subagents](https://code.claude.com/docs/en/sub-agents),
Cursor, Roo Code, GitHub Copilot); this doc is the
agent-stack shape.

## The rule

Delegate to a subagent when **any** of the following
holds. If none holds, do the work inline — subagent setup
has its own cost.

1. **Output would pollute the parent context.** A 200KB
   grep result, a 30-step web research trace, an audit log
   output — anything that would crowd out the agent's
   working memory but is critical to one decision.
2. **Different model needed.** Subagents can run on a
   cheaper model for cheap work and an expensive model for
   the slice's core reasoning. The savings are real even
   on small workloads.
3. **Restricted tool surface needed.** A subagent that
   only needs read-only tools shouldn't have access to
   `bash`. Skill manifests already do this for skills
   (`allowed-tools` / `disallowed-tools`); the same
   mechanism applies to subagents.
4. **Parallel work is possible.** Two independent reads
   that the parent will synthesise. Background agents the
   parent polls.

When **none** of these holds, dispatching a subagent is
AI-slop ceremony. Inline the work.

## Subagent manifest

Each subagent carries a manifest modelled on the SKILL.md
frontmatter (Anthropic Skills) plus a
[`context: fork`](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
flag that says "isolated context window — do not bleed back."

```yaml
---
name: <short-kebab>
description: |
  <One sentence including both *when this subagent applies*
  and *when it doesn't* — vague descriptions = unused
  subagent. Anthropic truncates descriptions at ~1,536
  chars; stay under that.
context: fork             # run in fresh context window
allowed-tools:            # narrow the tool surface; default-deny
  - read_file
  - grep
disallowed-tools:
  - bash
  - write_file
  - edit_file
model: <alias-or-name>    # cheaper for cheap work
output-format: <json|md>  # default: md summary, <2K tokens
---
```

The `output-format` line is the most under-appreciated
constraint. A subagent that returns a 30-page free-form
report has defeated the point of context isolation.
Default to a 1,000-2,000 token structured summary; the
parent reads only what's relevant.

## The three-questions brief

When delegating, the prompt answers three questions
explicitly:

1. **What does success look like?** One-sentence acceptance
   criterion the subagent can verify itself before
   returning. Skip this and the subagent returns 90%-done.
2. **What's in scope? What's out?** Explicit allow-list
   and deny-list. A subagent with an open scope drifts
   into adjacent problems; the drift is invisible until
   the parent synthesises the result.
3. **What's the output shape?** The structured
   "success / partial / failure with reason" envelope.
   The parent pattern-matches on envelope tags, not on
   prose.

## When NOT to subagent

- Sequential work where the parent needs every intermediate
  state in its own reasoning.
- Work that requires more of the codebase than the
  subagent's context window can hold (the parent context
  is no bigger; the same constraint applies).
- "Just to be safe" — the AI-slop ceremony case. Default
  to inline; promote to subagent when the rule above
  triggers.

## Verifier subagent pattern

A separate, read-only verifier subagent is often the
single highest-leverage subagent pattern. The verifier
runs after the main agent's slice and asks: "would
removing this code break the acceptance criterion?" If
no, the implementation does not match the spec (intent
mismatch, DAPLab #3). The verifier returns
pass/fail + a quoted acceptance criterion, not a
narrative.

Pair the verifier with the *deletion test* in
[`rpci.md § Critique sub-step`](rpci.md). The verifier
subagent is the automated version of the critique step.

## References

- [`session-protocol.md`](session-protocol.md) — when to
  load subagents
- [`rpci.md`](rpci.md) §I — the critique sub-step that the
  verifier subagent automates
- [`bug-patterns.md`](bug-patterns.md) — categories the
  verifier subagent should know
- [Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents)
- [Anthropic Skills (context: fork + frontmatter schema)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)