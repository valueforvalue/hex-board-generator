# ADR Discipline

How to maintain architecture decision records (ADRs) on a
repo that adopts agent-stack. Modelled on the
[Vercel ai ADR spec](https://github.com/vercel/ai/blob/main/skills/adr-skill/references/adr-conventions.md)
and the ["ADRs as executable constraints" pattern](https://blog.thestateofme.com/2025/07/10/using-architecture-decision-records-adrs-with-ai-coding-assistants/)
that's emerging as standard in 2025-2026. An ADR is
**durable prose that both humans and agents read before
changing shape in the area it covers**.

## When to write an ADR

Write an ADR when:

- The decision is durable enough that the next LLM session
  (or a human six months from now) needs to know it without
  reading the chat log.
- The decision touches multiple areas or files (cross-layer
  or cross-package), so the cost of re-discovering it is
  high.
- The decision was hotly contested or reversible — the
  contested history is exactly what future maintainers
  need to know not to repeat it.
- The decision's premise will eventually change. The ADR
  encodes the *why*, not just the *what*.

Skip an ADR when:

- The decision is local to one file and one commit (the
  commit message is enough).
- The decision is documented in code as a doc comment that
  survives at the declaration site.
- The decision is reversible in one commit (no future
  maintainer will wonder why it was the other way).

## The pattern

### Filename

`docs/agents/adr/0001-short-kebab.md` (zero-padded to four
digits; preserves lexical sort). Adopt the next number in
sequence; never reuse a number, even for a superseded ADR.

The directory lives at `docs/agents/adr/`, parallel to the
rest of the agent-stack install. Agent-stack templates the
location; adopters don't get to choose it.

### Required sections

Every ADR has these four headings. Adopt the Vercel
shape — it's the field-tested contract.

```markdown
# N. <Title>

## Status

<one of: proposed | accepted | deprecated | superseded
by [NNNN](NNNN-slug.md)>

## Context

<The forces at play. The constraints. The rejected
alternatives and why they were rejected. Cite the issue,
chat link, or commit that triggered the decision.>

## Decision

<The decision itself, one or two sentences. In declarative
present tense.>

## Consequences

<The trade-offs accepted. The follow-up work this decision
creates. The conditions under which this decision becomes
wrong (those conditions are the future Status changes).>
```

Optional but recommended: a **Rationale** subsection in
`## Decision` for non-obvious ties, and a **Followups**
section listing the work that becomes possible or required.

### Lifecycle states

The `Status` line is the contract. It is one of:

- `proposed` — under discussion; no ADR may be marked
  `accepted` without going through `proposed` first.
- `accepted` — current decision. The agents and humans
  follow it.
- `deprecated` — no longer the current decision, but no
  replacement yet. Agents should not introduce new code
  that follows the deprecated decision.
- `superseded by [NNNN](NNNN-slug.md)` — replaced by a
  newer ADR. The replacement link is mandatory. The
  superseded ADR is retained for traceability exactly
  as written — never edit it.

This is the
[Vercel "Living ADR" rule](https://github.com/vercel/ai/blob/main/skills/adr-skill/references/adr-conventions.md):
the file mutates by changing the Status line and adding
forward links, not by editing the body. The original
reasoning is preserved forever.

### Append-only discipline

**Never edit an accepted ADR's `Decision` or `Consequences`
sections.** The historical record is the point. If the
decision's content changes, write a new ADR that supersedes
the old one. If only the rationale deepens, link to a
follow-up document but leave the original body alone.

The temptation to retroactively clean up is the
["AGENTS.md is the New Architecture Decision Record"](https://ai.gopubby.com/agents-md-is-the-ew-architecture-decision-record)
anti-pattern: ADRs drift from immutable logs into living
documents, and the next agent reads a clean record that
no longer matches the code.

## When the agent encounters an ADR

When the agent considers a change in an area that has an
ADR:

1. Read the ADR's `Status`. If `proposed`, the decision is
   not yet authoritative — flag it to the human reviewer.
2. Read `Context` for the trade-offs the original
   maintainer considered.
3. Read `Decision` and check the proposed change against
   it. **No** means stop and discuss with the human.
4. Read `Consequences` for the work this decision creates.
   If the proposed change violates a `Consequences`
   clause, surface the violation explicitly in the slice
   plan.

If the change is consistent with the ADR, the slice plan
references the ADR number (`Refs ADR-0007`).

## ADRs vs laws

`core/laws.md` carries non-negotiable rules earned by real
bugs. ADRs carry decisions that *might* have been different.
The two files cross-reference each other:

- **A law has an ADR.** ADR explains the trade-off the law
  captured. The law itself is enforceable.
- **An ADR's decision is promoted to a law** when a bug
  ships that the ADR would have prevented ([`laws.md § Promoting
  a rule to a law`](laws.md)). The ADR is the historical
  anchor; the law is the enforceable rule.

## References

- [`laws.md`](laws.md) — when an ADR promotes to a law
- [`feature-protocol.md`](feature-protocol.md) — when an ADR
  is part of the locked-decisions block of a feature issue
- [`glossary-discipline.md`](glossary-discipline.md) — the
  ADR's vocabulary draws from the glossary
- [Vercel ai repo: adr-conventions](https://github.com/vercel/ai/blob/main/skills/adr-skill/references/adr-conventions.md)
- [SIGPLAN: Repositories as Knowledge Factories](https://blog.sigplan.org/2026/04/21/repositories-are-human-agent-knowledge-factories/)
- ["Using ADRs with AI coding assistants" (State of Me blog, Jul 2025)](https://blog.thestateofme.com/2025/07/10/using-architecture-decision-records-adrs-with-ai-coding-assistants/)