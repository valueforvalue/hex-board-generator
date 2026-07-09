# Cross-Layer Working Contract

This document captures the patterns that prevent drift when a
change touches multiple layers. It exists because in every
codebase, the chi-router migrations and the framework
attribute strips shipped independently and silently broke
every click-driven button. Two halves of one system drifted
apart; the bug surfaced only at runtime.

The patterns below are the ones that prevent drift. Read
the section for the layer you're touching. If your change
crosses layers, read all the relevant sections in order.

## The drift bug class

Every codebase has a stack of layers that must agree:

- **View templates** declare framework attributes
  (`hx-get`, `hx-post`, `hx-target`, etc.) on `<form>` and
  `<button>` elements.
- **Attribute builder** validates and emits those
  attributes (typed builder preferred over raw strings).
- **URL builder** maps logical names to route paths.
- **Frontend JS** owns network round-trips. It reads the
  attributes and fires requests itself, instead of letting
  the framework fire.
- **Route table** registers each handler against a path +
  method.

The drift bug class happens when **two of these layers
change in isolation**. The fix is always the same: introduce
or update an assertion that mechanically catches the drift.

## When you change a route

You touch: the route table AND the view templates
referencing the URL AND the URL builder if it's a new URL.

Checklist:

1. **Choose the right HTTP method.** Read the handler's
   first non-comment statement. If it begins with `if
   r.Method != http.MethodPost { ... return }`, the route
   is POST-only.
2. **Specific paths before wildcards.** If your new route
   shares a prefix with an existing wildcard, register the
   specific one first.
3. **Add or update the URL builder.** If templates reference
   this URL via the typed builder, update the builder to
   return the new path. If templates still have a raw
   string, migrate it.
4. **Add a route integration test entry.**
5. **Run the route test suite.**

## When you change a view template

You touch: the view template files for the affected screen.

Checklist:

1. **Use the typed attribute builder and URL builder** for
   new elements. Don't write `hx-get="/foo"` directly. The
   guard test flags bare string literals.
2. **Trigger syntax.** Framework-specific; see the
   addendum for the target stack.
3. **Target selectors.** Use the registry (uiids or analog)
   for persistent targets. Ad-hoc selectors are allowed but
   emit a warning.
4. **Wrap inputs that need framework polling in a
   `<form>`.**
5. **Add `hx-sync` (or analog) on rapid-fire forms.** If a
   form submits on every keystroke, add the sync directive
   so the new request cancels the previous one.
6. **Run the view tests.**

## When you change frontend JS

You touch: `frontend/app.js` (or analog).

Many frameworks have a structural quirk: the JS strips
framework attributes at boot to prevent the framework's
auto-handler from double-firing alongside the JS's own
handlers. **Read the framework addendum for the stack
quirk before touching the boot sequence.**

Checklist:

1. **Use the helper for reading framework attributes**
   (`hxAttr(el, name)` or analog). Direct reads may return
   `null` / `false` because the original attrs were stripped
   at boot.
2. **Use `[hx-X], [data-hx-X]` in `closest()` selectors.**
   Same reason.
3. **Don't re-introduce the strip.** If you find yourself
   tempted to re-add `el.removeAttribute("hx-X")` somewhere,
   the right answer is to use `e.stopImmediatePropagation()`
   inside the handler instead.
4. **Parse-check after every edit.**

## When you add (or migrate) a fragment-swap action

You touch: view templates (add a helper that emits the
wrapper's innerHTML only) AND the handler (returns the
helper render, not a redirect + plain text) AND the route
table (a dedicated route BEFORE the catch-all wildcard when
extracting from a generic handler).

This is the architecture event that migrations move to.
Pre-migration the page used a redirect header on every
action, forcing a full-page reload. Post-migration the
handler returns a fragment, the framework swaps the
wrapper's innerHTML, the user never loses scroll position.

Checklist:

1. **Fragment helper is wrapper-inner-only.** The fragment
   helper renders the inner content only; the wrapper
   element lives in the page-level template.
2. **Per-card action forms carry the swap target.**
3. **Handler returns the fragment render, not a redirect.**
   Toast header carries the user-visible confirmation.
4. **Add a dedicated route BEFORE any catch-all.** The
   router walks the route table in registration order; the
   explicit path matches first when both patterns cover the
   same path.
5. **Pin the swap in tests + smoke.**

## When you add a new top-level page

You touch: the page template AND the page-snapshot test
file AND the route table (if a new route).

Checklist:

1. **Add a `TestPageSnapshot<Page>` test.** Render the page
   into a buffer, parse, assert shape invariants (heading
   present, primary action present, no debug overlay
   attributes).
2. **Register the route.** Specific before wildcards.
3. **Add a URL builder.**
4. **Add surface IDs to the registry.**
5. **Run the full test sweep.**

## What catches bugs at code-review time

The guard tests catch the following bug classes
automatically. Don't disable them. Don't add `[skip ci]`
for them.

| Guard | Catches |
|---|---|
| Boundary | Module accidentally importing the wrong layer |
| Architecture | Forgotten package added to architecture map |
| Routes-method | Wrong HTTP method on route registration |
| Routes-wildcard | Specific route registered after its sibling wildcard |
| Attribute URLs | Bare `hx-get="/foo"` string in any template |
| Attribute targets | Ad-hoc `hx-target="#foo"` selectors |
| Page snapshots | Top-level page missing required structural element |

When you add a new guard for a new bug class, **add it to
this table**. Future contributors will need the map.

## What catches bugs at runtime (not yet covered)

These bug classes currently have no automated guard. If you
hit one, add a test before fixing.

- **Background-task crashes.** No test fires an actual
  external invocation. Could be added as a smoke test
  that runs the binary against a fixture.
- **Framework runtime nil-guards.** No test mocks the
  runtime. Could be added by introducing a small interface
  that has a MockRuntime impl returning errors.
- **Swap target detach after swap.** No test renders a page,
  swaps a fragment, and re-queries for the target.

## When in doubt

The architecture intentionally has belt-and-braces guards at
every layer:

- AST-level guard (catches structural issues at compile time)
- Page-snapshot test (catches rendering drift)
- Integration test (catches runtime behavior)

If your change crosses a layer, **add a guard for the next
layer up**. The pattern is: every layer transition is a
place bugs hide. Add an assertion at each one.