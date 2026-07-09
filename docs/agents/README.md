# core/

Stack-agnostic agent conventions. Every file in this directory
applies to any language or framework. Stack-specific patterns
live in `../addenda/`.

## Tier-0 — read at session start

These cross-cut every task. Load them once.

| Doc | When |
|---|---|
| [`session-protocol.md`](session-protocol.md) | Every agent session |
| [`laws.md`](laws.md) | Before any code lands |
| [`commit-and-branch.md`](commit-and-branch.md) | Before any commit |
| [`docs-index-scheme.md`](docs-index-scheme.md) | When adopting the framework |
| [`glossary-discipline.md`](glossary-discipline.md) | When adding domain terms |

## Tier-1 — load by task role

| Doc | Load when |
|---|---|
| [`rpci.md`](rpci.md) | Non-trivial work (3+ files or design questions) |
| [`complexity.md`](complexity.md) | Designing a new module, debating YAGNI vs broad interface, reviewing for strategic-programming correctness |
| [`tdd.md`](tdd.md) | Any feature or bug fix |
| [`feature-protocol.md`](feature-protocol.md) | Adding a feature |
| [`code-changes.md`](code-changes.md) | Cross-layer change (view + framework attrs + JS + backend or analogous) |
| [`bug-patterns.md`](bug-patterns.md) | Hunting a bug or reviewing a fix |
| [`subagent-pattern.md`](subagent-pattern.md) | Work that may benefit from delegated context (noisy research, parallel reads, restricted tool surface) |
| [`adr-discipline.md`](adr-discipline.md) | Recording a durable decision the next session needs |
| [`agent-memory.md`](agent-memory.md) | Working memory across sessions (compaction, checkpoint/rehydrate pattern) |

## Tier-2 — on demand

Per-addendum. Each `addenda/<stack>.md` file is its own tier-2
doc. Load only the one that matches the target stack.

## How to use

1. Read Tier-0 at session start. Stop.
2. Match the task to a Tier-1 doc. Load only that one.
3. If the task references a stack, load the matching addendum
   from `../addenda/`.
4. If a doc you'd expect to find isn't listed here, the
   framework is incomplete — open an issue.

## What stays out of core/

- Bug patterns that name a specific framework (HTMX, React,
  Django, Rails, etc.) → `../addenda/<stack>.md`
- Vendor-specific crash histories (specific host-runtime
  bugs, browser flags, etc.) → the addendum that owns the stack
- Project-specific terminology → the adopting repo's
  `CONTEXT.md`