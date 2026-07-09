# Agent Memory Conventions

How an LLM agent carries state across sessions on a repo
that adopts agent-stack. Modelled on
[Anthropic's long-horizon techniques](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
(Sept 2025): compaction, structured note-taking, sub-agent
isolation; and the
[Claude memory tool](https://www.anthropic.com/news/context-management)
(Sonnet 4.5 launch).

The tier system in [`docs-index-scheme.md`](docs-index-scheme.md)
covers what the agent loads from the repo. This document
covers what the agent *produces* in the working tree,
surviving the session boundary.

## Two directories, two purposes

### `agent-notes/`

**Working memory the agent writes for its future self.**
Short-lived, often session-scoped, frequently rewritten.

Typical contents:

- `current-task.md` — what the agent is trying to do right
  now, the slice plan, the open questions.
- `open-questions.md` — surfaced decisions the user owes a
  call on.
- `investigation-log.md` — recent file paths opened, tests
  run, commands tried.

The directory is **gitignored by default.** Its purpose is
to outlive the agent's working memory between compaction
events within a long session, and to rehydrate context on
resume. Committing it pollutes the diff. Per Anthropic's
compaction pattern, the agent reads back the most recent
5 files it touched when rehydrating.

### `agent-checkpoints/`

**Durable state across sessions.** Survives a full session
boundary; intended to be read at session start.

Typical contents:

- `state.md` — what was in flight when the previous session
  ended. What's green, what's broken, what's blocked.
- `decisions.md` — decisions locked during the previous
  session, with source citations.
- `experiences.md` — bugs the agent hit that the next
  agent must not re-discover.

The directory **may be committed** at the maintainer's
discretion, or gitignored and synced via another channel.
A committed checkpoint is the most reliable form of
agent-to-agent transfer; a gitignored checkpoint is
session-local only.

Both directories are created at the repo root by convention,
so the agent's tooling can find them deterministically.

## The CHECKPOINT / REHydrate pattern

The pattern Anthropic's long-horizon techniques document
as "Compaction" and "Structured note-taking" is renamed
here for clarity. Each corresponds to a directory:

- **CHECKPOINT**: at a natural boundary (end of slice,
  end of session, before context fill), the agent writes
  the current state to `agent-checkpoints/state.md`.
  Includes: files touched, decisions locked, blockers
  raised, next actions.
- **REHydrate**: at session start (or after a compaction
  event), the agent reads `agent-checkpoints/state.md`
  before beginning work. Verifies the checkpoint is
  current; if stale, archives the old one and writes a
  fresh "session start" state.

The discipline prevents two failure modes the literature
calls out:
- "Lost in the middle" — context-window attention drifts
  away from earlier-in-the-session decisions.
- "Compaction drop" — Claude Code's auto-compact drops
  structured decisions silently; a checkpoint before
  compaction is the only way to ensure persistence.

## Sub-agent delegation alignment

When a subagent delegates to the parent
([`subagent-pattern.md`](subagent-pattern.md)), the
parent's working memory is the constraint. Subagents
**must**:

- Return a structured summary, not raw output
  (`output-format: <json|md>`, default md, <2K tokens).
- Append a "decisions made" line to `agent-notes/` if
  they locked any decision that the parent didn't ask
  for.
- Never write to `agent-checkpoints/` directly — that's
  the parent's responsibility.

The parent **must**:

- Update `agent-checkpoints/state.md` if the subagent's
  decisions change the in-flight slice.
- Cite the subagent's source in the slice plan or commit
  body.

## Anti-patterns

- **Auto-committing `agent-notes/`.** The notes are
  working memory; they belong in session scope, not in the
  code-review surface. Commit them and they become a
  source of churn.
- **Single mega-file.** A `state.md` with 50 sections is
  unreadable. Split by concern (state, decisions,
  experiences) and only-load what matches the task.
- **Notes that survive in the agent's context but not on
  disk.** If the next session needs it, write it down.
  The LLM's working memory does not persist.
- **Checkpoint without timestamp.** A checkpoint without
  `Last updated: <date>` is a stale-by-default checkpoint
  the next agent will trust too much.

## References

- [`subagent-pattern.md`](subagent-pattern.md) — how
  subagent delegation interacts with this directory
  layout
- [`docs-index-scheme.md`](docs-index-scheme.md) — the
  tier system covers what the agent reads; this covers
  what it writes
- [`session-protocol.md`](session-protocol.md) — when
  to checkpoint (end of slice, end of session, before
  context fill)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic memory tool](https://www.anthropic.com/news/context-management)
- [Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)