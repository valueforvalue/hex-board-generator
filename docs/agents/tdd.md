# Test-Driven Development

The truth anchor for every slice that lands on a repo that
adopts agent-stack. It does not replace the vertical-slice
discipline in [`feature-protocol.md`](feature-protocol.md);
it sits *inside* it, in the gap between "the slice is
well-shaped" and "the slice ships what we said it would."

This doc is the agent-stack port of the TDD skill. The
generic red-green-refactor loop lives in the skill; this
doc captures the per-layer recipes and anti-patterns that
recur across stacks.

## The failure modes TDD prevents

Three classes of bug recur across every codebase. Each is
preventable by a single test written *before* the slice
lands.

### 1. Invoker wiring (most common)

**Symptom:** UI button calls a helper that queries the DOM
for a target element, gets `null`, and silently early-returns.
The feature is fully implemented server-side (handler +
route + state) but the user sees no feedback.

**RED test:** drive the live binary (or a smoke harness),
click the button, assert the target element is in the DOM
AND not in a hidden state. This test fails BEFORE the slice
because the target doesn't exist.

### 2. Adjacent race / state-machine collision

**Symptom:** The slice's own click handler does the right
thing, but a different handler attached to a higher-priority
event (document, window, ancestor element) reacts to the same
event and undoes the work. The slice passes its own smoke
probe because the probe only checks the slice's own outcome.

**RED test:** smoke probe that clicks the trigger, waits
50–200ms, then asserts the panel is still in the expected
state. For native-host runtimes (webview hosts, Electron,
Tauri, etc.) the 50ms window is the
right delay — the event loop is slower than headless Chromium.

### 3. Orphan handler / response-shape mismatch

**Symptom:** A handler is registered (Go route, Express
endpoint, Django URL) but the response shape doesn't match
what the client expects. The client follows a redirect to
raw HTML, or parses JSON as a navigation, or vice versa.

**RED test:** handler test that asserts the response status,
content-type, and key body fields. Plus: an orphan-handler
probe that walks the route table against the client
invokers, flags any handler with no caller.

## The loop

This is the slice-internal protocol. It runs *inside* one
slice, not across the whole feature.

### Step 0 — Read the slice's acceptance criterion

The slice plan states "the user can X" or "the user sees Y
when Z." That criterion is what the test will pin. If the
slice plan doesn't have one, the plan is incomplete — go
back and add it. An implementation criterion ("the service
exposes method `Foo(int64)`") is not an acceptance criterion;
it's an implementation step.

### Step 1 — RED: write the failing test first

Write the test that **pins the acceptance criterion.** Do
not write the slice code yet. Do not write other tests yet.

The test fails for the **right reason.** If the test fails
for an unrelated reason (missing import, test setup
mistake), fix the test, not the code. A passing test that
wasn't actually pinning the criterion is worse than no test.

### Step 2 — GREEN: write the minimum slice code

Implement the smallest diff that satisfies the RED test. No
drive-by refactors. No "while I'm here" cleanup. No
speculative surface.

- Package test suite green.
- Smoke probe green.
- Full short suite green.

If a slice makes another test in the same package turn red,
**stop.** The slice is touching code outside its seam.

### Step 3 — Adjacent behavior sweep

Before the commit, run the smoke probes and tests for
**adjacent surfaces** — anything in the same screen family,
anything that shares a JS dispatcher, anything that the
slice's render touches.

If any turn red, the slice has crossed a seam it shouldn't
have. **Fix or escalate; do not silence.**

### Step 4 — REFACTOR (only after green)

Extract duplication the slice revealed. Deepen modules.
Two-adapter check before adding any new public method.

**Never refactor while RED.** Get to GREEN first.

### Step 5 — Commit the RED test + GREEN slice together

The RED test lives in the same commit as the slice code it
pins. Inline, atomic, reviewable.

## What's the seam?

Per [`feature-protocol.md`](feature-protocol.md) §"Module
discipline", the seam is the **service interface + DTO**.
Tests cross the seam. The persistence layer is private to
the service; the test does not import it.

For slices that don't add a service, the seam is the **DOM
surface ID** (or its stack-equivalent — schema name, route
name, etc.). The render test asserts the surface ID is
present (or absent) in the rendered output; the smoke probe
asserts the same ID is reachable from a click.

If a test needs to mock the service, the test is testing
the wrong thing. The service is the seam; mocking it hides
the failure mode where the JS calls a real method that
quietly early-returns.

Exception: when the service itself depends on a hard-to-
fake boundary (native dialog, host runtime, native
API), mock
the boundary, not the service.

## Per-layer recipes

### Backend (handler + service)

- **Handler test:** asserts status code, response shape,
  headers (especially any redirect / toast / content-type
  contract).
- **Service test:** uses a real DB (or in-memory fixture).
  No mocks. Reach for property-test patterns when the input
  domain is interesting.
- **Migration test:** if the slice ships a schema change,
  the RED step extends the existing reversibility catalogue.

### View template

- **Render test:** calls `Render` (or equivalent) into a
  buffer, asserts the rendered output contains (or doesn't
  contain) specific surface IDs.
- **Attribute test:** if the slice introduces a new
  framework-specific attribute (hx-target, react-router path,
  etc.), the validator fails fast in dev builds.

### Frontend (JS / interaction)

- **Smoke probe:** Playwright (or equivalent) driving the live
  binary, asserting response shape AND `page.url()` AND the
  relevant DOM state. The response-only assertion is
  insufficient (that is how the silent-swallow bug class
  ships).

## Anti-patterns

- **Horizontal slicing.** Writing all the tests first, then
  all the implementation. AI-slop failure mode. Right move:
  one test → one impl → repeat, even within one slice
  commit.
- **Test-after-the-slice-is-done.** Catches future
  regressions but not the slice's own drift. TDD adds the
  test that pins the acceptance criterion *before* the slice
  lands.
- **Mocking the seam.** Writing a test that mocks the
  service to assert "the handler called `Foo(int64)` with
  X." This pins the implementation, not the behavior.
- **Pinning the response shape but not the post-click URL.**
  Smoke probes MUST assert `page.url()` after every click
  that expects navigation.
- **Speculative tests.** Writing a test for behavior the
  acceptance criterion doesn't mention.

## When NOT to TDD

- One-line bug fix with clear repro — bug protocol applies.
- Pure doc change.
- Pure build / CI change.
- Refactor with characterization tests — when the slice
  preserves behavior but rearranges code, the RED step is a
  characterization test.

## References

- [`feature-protocol.md`](feature-protocol.md) — slice
  discipline this protocol sits inside
- [`rpci.md`](rpci.md) §I — Implement phase wiring
- [`bug-patterns.md`](bug-patterns.md) — per-layer bug
  patterns to read alongside