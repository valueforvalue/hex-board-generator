# Agent Session Protocol

Procedural rules that govern how an LLM agent behaves in a
session on a repo that adopts agent-stack. These are the
procedural complement to the architectural boundaries in
`CONTEXT.md` and the repo's own agent docs (usually
`AGENTS.md` or `CLAUDE.md`).

Adopting repos should copy this file (with project-specific
edits) to their own `docs/agents/session-protocol.md` or
inline it into their `AGENTS.md`.

## The five rules

### 1. No implementation before direction approved

Recon (read, grep, find, list) is always fine. Implementation
(edit, write, scaffolding new files, running build targets
that mutate state) waits for explicit approval of a proposed
direction. LLM agents default to writing more than
necessary; the gate keeps that in check.

### 2. Batched discovery

Up to 4 focused questions per turn, batched in a single
ask. One-at-a-time questioning breaks flow. Skip discovery
entirely if the request is already clear.

### 3. YAGNI — features only, not interfaces

Do not introduce *features* (methods nobody calls, branches
nobody exercises, parameters nobody passes) for requirements
that do not exist yet. Speculative behavior creates more
problems than it solves.

Interface shape is a separate question. Apply the
net-complexity-gain test in
[`complexity.md`](complexity.md) §1: a slightly broader
interface that costs the implementer an hour but saves every
caller from relearning the module earns its keep. The
[`feature-protocol.md`](feature-protocol.md) two-adapter rule
and the deep-module discipline are the operational form.

### 4. Bias toward action

When two options are close in quality, pick one and go.
Movement creates clarity. The cost of a wrong choice that
is easily reversible is lower than the cost of a long
deliberation.

### 5. Proportional depth

Match the weight of the process to the weight of the task.
A small bug fix may need zero questions; a new subsystem
deserves a more thorough exploration. Let task complexity
guide conversation complexity.

## Capturing decisions

- **Default:** capture in the conversation. The user is the chat.
- **Default flow for non-trivial work:** the user invokes RPCI
  (Research → Plan → Critique → Implement). Full procedure in
  [`rpci.md`](rpci.md). The Critique phase is the gate — no
  implementation before the user signs off.
- **Promote to ADR:** if a decision is durable enough that the
  next LLM session (or a human six months from now) needs to
  know it without reading the chat log, write
  `docs/adr/000N-<slug>.md`. Match the existing ADR shape.
- **Never inline in source.** Source-file comments are
  reserved for non-obvious code, not session breadcrumbs.
  Inline comments about "we discussed this" rot.

## Tool usage

- Use specialized subagents when the task matches an agent
  type's description. Subagents are valuable for parallelizing
  independent queries or for protecting the main context window
  from excessive results.
- Trust but verify: a subagent's summary describes intent, not
  outcome. When a subagent writes or edits code, check the
  actual changes before reporting work as done.
- Use `ask_user_question` whenever the user's request is
  underspecified and you cannot proceed without concrete
  decisions. Batch up to 4 questions per invocation.
- Use a task list for any work with 3+ steps or whenever the
  user gives a list of tasks. Skip it for single trivial tasks
  and purely conversational requests.
- Mark a task in_progress BEFORE beginning work and completed
  IMMEDIATELY when done. Never batch completions.
- One task in_progress at a time. Use blockedBy to express
  dependencies.

## References

- [`rpci.md`](rpci.md) — Research → Plan → Critique → Implement
- [`commit-and-branch.md`](commit-and-branch.md) — commit shape +
  branch policy
- [`laws.md`](laws.md) — non-negotiable laws