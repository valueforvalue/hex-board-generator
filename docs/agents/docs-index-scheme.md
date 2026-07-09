# Docs Index Scheme — 3-Tier Progressive Disclosure

A repo that adopts agent-stack should maintain a
`docs/agents/INDEX.md` (or equivalent) that organises its
agent-facing docs by tier. This file documents the pattern.

The 3-tier model formalised here is the open pattern used
by [Anthropic Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
and adapted from
[Will Larson's "Progressive disclosure and large files"](https://lethain.com/agents-large-files/).
The empirical justification comes from
[Liu et al.'s "Lost in the Middle"](https://aclanthology.org/2024.tacl-1.9/):
information in the middle of long contexts gets missed.
The agent's working memory has a finite budget. Tiering
protects the budget.

## The three tiers, with token budgets

### Tier-0 — always loaded

Cross-cuts every task. Load at session start. The agent
should not start work without these in context.

**Budget: <2K tokens total.** Every doc in this tier must
declare a `Token cost: ~N` line so the maintainer and the
agent can audit the budget on every PR.

Examples: glossary + laws, session protocol, commit shape,
RPCI flow, TDD discipline, bug catalog, cross-layer
contract.

Cross-reference these from the repo's main `AGENTS.md` so
they're pulled into the agent's context automatically.
Claude Code supports `@imports` up to 4 hops deep; use them
sparingly, since the empirical ceiling for `AGENTS.md` is
[20-30 lines to start](https://www.morphllm.com/agents-md-guide)
(Codex enforces a
[**32 KiB hard cap**](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)).

### Tier-1 — task-role loaded

Loaded only when the task matches the role. Don't pre-load
all of them; load only the ones that match. The
description (one-sentence load-when) is the only signal
the agent uses to decide whether to load the doc body —
the same model as
[Anthropic Skills' YAML frontmatter](https://agentskills.io/home).
Write descriptions that say both when the doc applies AND
when it doesn't. Vague descriptions = doc never loaded.

**Budget: ~500 lines per doc, ~5K tokens total per role.**

Examples:

- Bug work → bug-pattern catalog + manual audit playbook
- Feature work → feature protocol + slice plan template
- UI hunt / redesign → UI map + wireframes for the affected
  screen
- Schema / database → migration history (latest two)
- Process / meta → ADR + research + services

### Tier-2 — on-demand

Lives under `docs/historical/` (or similar) and is NOT
loaded by default. Load only when the issue, PR, ADR, or
explicit user direction names the doc. The "always loaded"
counterpart to this tier is the agent's own file-read
tools; content budget is effectively unbounded because the
model reads what it needs, when it needs it (Anthropic
Skills calls this the
[filesystem-as-context-window pattern](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)).

**Budget: unbounded. Per-file, declare `Token cost: ~N`
in the doc's frontmatter so the agent can decide whether
to load the full body or skim.**

Examples: historical handoffs, resolved audits, past
per-surface rendering reviews, old design discussions.

## Retention

Tier-2 docs are retained for traceability but not loaded
by default. The retention rule typically caps at the latest
3 rounds in the working tree; older rounds move to
`docs/historical/`.

## How to use

1. Read Tier-0 at session start. Stop. Do not load Tier-1 yet.
2. Read the task. Identify which Tier-1 doc(s) match.
3. Load only those Tier-1 docs.
4. If the task references a specific historical artifact by
   name or number, load it from Tier-2. Otherwise, ignore the
   Tier-2 docs entirely.

If a doc you'd expect to find isn't listed in the index, it's
either in the wrong tier (open an issue) or it doesn't exist
yet (open an issue with a "missing doc" label).

## Prompt-cache alignment

Anthropic and OpenAI prompt caches both gate on exact
prefix match — any change between sessions invalidates the
cache ([KVFlow, NeurIPS 2025](https://arxiv.org/html/2507.07400v1)).
The 3-tier model exploits this: pin Tier-0 at the prefix
boundary so it caches maximally across sessions; let Tier-1
vary per role behind a `cache_control` breakpoint; leave
Tier-2 in the dynamic tail where it's not part of the
cacheable prefix.

If your harness supports per-doc cache markers, mark every
Tier-0 doc with `cache_control: ephemeral`. Tier-1 docs
that the maintainer updates frequently should NOT be
cache-pinned; the cache-hit ratio drops to zero on any
edit.

## Adopting this pattern

1. Create `docs/agents/INDEX.md` with the three tier
   sections, each doc annotated with `Token cost: ~N` and
   `Load when:`.
2. Move existing agent-facing docs to their tier-appropriate
   category.
3. Cross-reference Tier-0 docs from `AGENTS.md` at the repo
   root so they auto-load.
4. Mark any Tier-2 doc with a clear retention timestamp.
5. Re-evaluate tier placement every quarter — a Tier-2 doc
   that gets referenced repeatedly probably belongs at Tier-1.

## References

- [`session-protocol.md`](session-protocol.md) — what the
  agent reads at session start
- [`glossary-discipline.md`](glossary-discipline.md) —
  Tier-0 glossary maintenance
- [`laws.md § Tier-0 docs have a size ceiling`](laws.md) —
  the enforced budget for this tier
- [Anthropic: Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Lost in the Middle (Liu et al., 2024)](https://aclanthology.org/2024.tacl-1.9/)
- [Chroma: Context Rot](https://www.trychroma.com/research/context-rot)
- [Will Larson: Progressive disclosure and large files](https://lethain.com/agents-large-files/)