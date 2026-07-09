# Bug Patterns — Stack-Agnostic Catalog

This document captures recurring bug patterns at a high
level. The per-layer specifics live in the addendum for the
target stack.

The patterns are grouped by where the bug lives in the
stack: **frontend wiring** (view + framework attributes),
**view markup**, **frontend JS**, **backend handlers**, and
**build / CI**. A final section covers debugging workflow.

Adopting repos should extend this catalog with their own
stack-specific patterns in their addendum.

## Authoritative cross-references

Where an agent-stack pattern overlaps with a known
classification scheme, the cross-reference is recorded
inline. Adopters working in regulated environments (SOC2,
HIPAA, PCI) can map their required controls to these
sources.

- **[MITRE CWE Top 25 (2025)](https://cwe.mitre.org/top25/)** —
  industry-weakness enumeration. CWE-79 (XSS) still leads.
- **[OWASP Top 10:2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/)** —
  web application risk categories. A10 "Mishandling of
  Exceptional Conditions" is new in 2025 and aligns with
  the *invoker wiring gap / silent early return* pattern
  below.
- **[OWASP Top 10 for LLM Applications (2025)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)** —
  agent-specific risks. Excessive Agency, Improper Output
  Handling, Prompt Injection are the ones a coding agent
  can self-introduce.
- **[Tambon et al. (2024)](https://arxiv.org/abs/2403.08937)** —
  canonical empirical taxonomy of bugs in LLM-generated
  code: 333 bugs across 10 categories, LLM bugs 50% more
  logic-heavy than human bugs, 2.25× slower to fix. Source
  for many of the AI-amplified categories below.
- **[DAPLab 9 Critical Failure Patterns (Jan 2026)](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html)** —
  field reports from 5 leading agents (Claude, Cline,
  Cursor, v0, Replit) across 15+ vibe-coded apps.
  Source for *intent mismatch*, *hallucinated APIs*,
  *re-implementing stdlib*, *repeated code*.
- **[CodeRabbit AI vs Human report (Dec 2025)](https://coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)** —
  470 PRs, AI produces 1.7× more issues overall, 2× more
  concurrency/dependency issues, 2.74× more security issues.

### Pattern → authority cross-reference

| Agent-stack pattern | CWE | OWASP 2025 | OWASP LLM |
|---|---|---|---|
| Invoker wiring gap (silent early return) | CWE-754, CWE-1188 | A10:2025 (Mishandling of Exceptional Conditions) | LLM05 (Improper Output Handling) |
| Drift between layers | CWE-704 (Incorrect Type Conversion) | A03:2025 (Supply Chain) | — |
| Response-shape mismatch | CWE-20 (Improper Input Validation) | A04:2025 (Cryptographic — by analogy, signature drift) | LLM05 |
| Authorization / intent gap | CWE-862 (Missing Authorization) | A01:2025 (Broken Access Control) | LLM06 (Excessive Agency) |
| Hardcoded paths / secrets | CWE-798 (Hardcoded Credentials), CWE-22 (Path Traversal) | A02:2025 (Cryptographic Failures), A05:2025 (Misconfiguration) | — |
| Concurrency / dependency correctness | CWE-362 (Race Condition), CWE-676 (Use of Risky API) | A08:2025 (Software/Data Integrity) | — |
| Nil-guard gap | CWE-476 (NULL Pointer Dereference) | A10:2025 | LLM05 |
| Hallucinated API / fake key | CWE-1188 (Insecure Default) | A06:2025 (Vulnerable Components) | LLM09 (Misinformation) |
| Silent error suppression (logging-only) | CWE-778 (Insufficient Logging), CWE-209 (Info Exposure via Error) | A09:2025 (Logging Failures), A10:2025 | — |
| Re-implementing stdlib / reinventing wheels | CWE-1076 (Insufficient Prefabricated Components) | A03:2025 (Supply Chain) | — |
| Repeated code (AI amplification) | CWE-1041 (Use of Redundant Code) | — | — |
| Date / timezone handling | CWE-682 (Incorrect Calculation) | — | — |
| UI re-entrant call | CWE-662 (Improper Synchronization) | A04:2025 | — |

If your fix contract maps to a CWE or OWASP category that
isn't listed here, open an issue. The table grows by
adoption.


## The meta-patterns (every stack)

### Drift between layers

Two halves of one system drifted apart; the bug surfaced
only at runtime. See [`code-changes.md`](code-changes.md)
for the working contract that prevents this.

### Invoker wiring gap

UI button calls a helper that queries the DOM for a target
element, gets `null`, and silently early-returns. The
feature is fully implemented server-side but the user sees
no feedback. The fix is always: a smoke probe that asserts
the target element is in the DOM AND not in a hidden state.

### Response-shape mismatch

Handler is registered but the response shape doesn't match
what the client expects. The client follows a redirect to
raw HTML, or parses JSON as a navigation, or vice versa.
The fix is always: a handler test that asserts response
status, content-type, and key body fields.

### Orphan handler / fragment-as-redirect

A handler ships with no caller, OR a fragment endpoint's
HTML is followed as a navigation because a header told the
client to redirect. The fix is always: an orphan-handler
probe that walks the route table against client invokers.

### Adjacent race / state-machine collision

The slice's own click handler does the right thing, but a
different handler attached to a higher-priority event
reacts to the same event and undoes the work. The fix is
always: a smoke probe that asserts the state 50–200ms
after the click, after the event has fully bubbled.

### Unguarded re-entrant UI call

If a UI operation opens a native dialog, modal, file
picker, or any other re-entrant surface, a second
invocation while the first is still open must be rejected
before it reaches the host. See [`laws.md`](laws.md) §"No
unguarded re-entrant UI calls".

### Date / timezone handling

Anniversary shows on the wrong day, or birthday shows a
day early/late. Date construction without explicit
timezone; the formatter defaults to UTC. The fix is
always: pass the user's stored timezone offset.

### Goroutine / subscription / handle leak

Over time, background work accumulates. Memory grows.
Eventually OOM. The fix is always: a `defer cleanup()` at
the top of the goroutine / handler.

### Nil-guard gap

Panic on a path that's rare in dev but common in prod.
Code path that "always works in dev" because the test setup
pre-populates state. The fix is always: add the nil check,
or restructure so the call site guarantees non-nil.

### Hardcoded paths

Production build fails to find files that work in dev.
Hardcoded paths from dev environment leak into release
code. The fix is always: use `runtime.Caller` /
`os.Executable()` to anchor the path.

### Authorization / intent gap (CWE-862, OWASP LLM06)

A structurally perfect endpoint with no authorization
check. The bug compiles, the test passes, the user sees
the right response. The bug only surfaces when an
unauthorised actor hits the same path — and the
[Stellman analysis](https://www.oreilly.com/radar/ai-code-review-only-catches-half-of-your-bugs/)
calls out that ~50% of LLM-introduced security defects
are *intent violations* invisible to structural analysis.
[CWE-862](https://cwe.mitre.org/data/definitions/862.html)
(Missing Authorization) is #9 on the 2024 CWE Top 25.
Aligns with [OWASP LLM06 (Excessive Agency)](https://owasp.org/www-project-top-10-for-large-language-model-applications/).

The fix is always: derive a per-handler requirement list
from the ticket + chat history, and assert that each
requirement has a corresponding authorization check. The
guard test is the spec, not the code.

### Hallucinated APIs and fake environment keys

The agent imports `library.io.Magic.DoThing`, calls it,
and the build succeeds because some unrelated package
happens to expose that symbol in this version. Or the
agent reads an env var that no deployment ever sets and
silently defaults to dev. Field-reported by
[DAPLab #5](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html)
across Claude, Cursor, and v0. Also covers
pre-existing-API drift: the agent imports the v1 API but
v2 has been out for two releases.

The fix is always: pin the dependency version in the
manifest, run the test against the real environment, and
assert the env var is set (`if !ok { return ErrMissingConfig }`,
not `if !ok { return devDefault }`).

### Re-implementing stdlib instead of importing

The agent writes `formatTimestamp(t)` instead of importing
the existing `time.Format` helper, or inlines a CSV parser
when the project already ships one. Output looks identical;
future maintenance doubles the surface. Field-reported by
[DAPLab #8](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html)
in production codebases.

The fix is always: before writing any helper, run a
project-wide `grep -r <concept>` and read the
glossary entry for that concept. Add a guard test that
flags stdlib re-implementations when detected.

### Repeated code (AI amplification)

The agent produces two near-identical implementations of
the same handler because the prompt scrolled and lost
context, or because parallel branches of a planning
session converged on the same answer. [CodeRabbit's
2025 audit](https://coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)
measured this as 1.7× more issues overall in AI PRs, with
*repeat code* being a top-3 category.

The fix is always: a post-Implement diff review that
groups edits by concept, not by file. Two functions with
matching signatures and matching call sites are one
function.

### Silent error suppression (logging-only)

An error happens, gets logged to dev console, the user
sees a generic "Something went wrong" toast. DAPLab #9
calls this the highest-frequency AI failure mode;
[OWASP A10:2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/)
(Mishandling of Exceptional Conditions) formalised it as
a category covering 24 CWEs (improper error handling,
logical errors, failing open).

The fix is always: every error handler either (a) reports
the failure to the user with an actionable message, (b)
escalates to a retry/recovery path, or (c) explicitly
documents why dropping is correct. The guard test
asserts: every `catch` / `if err != nil` either bubbles
up or hits one of those three.

### Concurrency / dependency correctness (AI amplification)

Race conditions in goroutines / async / event listeners
that pass single-threaded tests. The CodeRabbit report
measured AI PRs at **2× more concurrency/dependency
issues** than human PRs, because AI code typically
single-threads mentally and only the human reviewer
spotted the missing lock.

The fix is always: run the project's race detector under
load (Go: `go test -race ./...`. JS: concurrent
test runner. Python: thread + asyncio concurrency tests).
Pair with the meta-pattern table above.

### Intent / business-logic mismatch

The agent implements what was asked, not what was meant.
The bug compiles, tests pass, the user complains. The
intent is in chat history or ticket comments but was not
in the spec the agent worked from. DAPLab #3 lists this
as the #1 failure pattern across every agent they
observed.

The fix is always: the slice plan captures the user
story, not the implementation step. The acceptance
criterion is the test. The Implement phase runs the
*deletion test*: would removing this code break the
acceptance criterion? If no, the implementation does not
match the spec.

## Debugging workflow

When you see a regression, work this checklist in order:

### 1. Identify the layer

Before reading code, name the layer:

- Did the user click something? → frontend wiring.
- Did a page render wrong? → view markup.
- Did a button or toggle stop working after navigation? →
  framework-swap destroyed a listener.
- Is it slow / hangs? → backend. Check for leaks, race
  conditions, lock timeouts.
- Is it an export / file output? → output formatter.
- Screen reader broken? → accessibility.
- Build / CI failure? → build / CI.

### 2. The four diagnostic commands

```bash
# What's currently in this template?
grep -n 'framework-attr\|@\|render ' <view files>

# What template renders a URL? (catches wrong-selector class)
go test <view-package> -run TestAttributeURLsUseBuilders -v

# Is the boundary intact? (catches architectural drift)
go test <architecture-package> -v

# Are there races?
go test -race ./...
```

### 3. Three files to read first when a regression appears

1. The attribute-URL guard test — is the URL going through
   a builder?
2. The architecture-boundary test — is the import
   boundary still intact?
3. The recent commits touching the affected file.

### 4. When to add a regression test

If a bug was found by accident (manual testing, code
review, prod report) and the fix is non-obvious, **add a
snapshot or behavioral test that would have caught it.**
This is what codifies "we already burned fingers on this."

## Bug class → first place to look

Quick reference table for "the page does X wrong, where's
the bug":

| Symptom | First place to look |
|---|---|
| Click does nothing | Frontend wiring: button type / form wrap |
| Click fires but nothing changes | Frontend wiring: target missing |
| Worked before, broken after navigation | Framework-swap destroyed listener |
| Stale results | Sync directive missing |
| Progress keeps polling | Terminal-state trigger missing |
| Handler runs, toast shows, page doesn't navigate | Redirect header missing |
| Form submits, server runs, JS post-response ignored | Dispatcher opt-in attribute missing |
| Double-click produces duplicate work | Dedup helper / in-flight slot |
| Toast shows mojibake | HTTP header charset |
| 405 from a clickable form | Wrong HTTP method on route |
| Floating overlay covers content | Overlay height + padding drift |
| Panic on rare path | Nil guard |
| Background work leak | Missing cleanup |
| Date wrong by 1 day | Timezone |
| Output missing references | Data-dir resolution |
| Search returns ghost | Index sync |
| Screen reader silent | ARIA missing |
| Mobile layout broken | Viewport test |
| Memory grows over time | Leak / race |
| Works in dev, fails in release | Hardcoded paths |

For stack-specific patterns and copy-paste greps, see
the addendum for the target stack.

## References

- [`code-changes.md`](code-changes.md) — cross-layer working
  contract
- [`laws.md`](laws.md) — non-negotiable laws
- The addendum for the target stack (`addenda/<stack>.md`)