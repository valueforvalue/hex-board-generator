# Glossary Discipline

How to maintain a project's domain glossary (typically
`CONTEXT.md` or `docs/GLOSSARY.md`) so future features, docs,
and discussions use the same vocabulary.

## When to maintain a glossary

A glossary is worth maintaining when:

- The project has domain concepts that aren't obvious from
  their names (e.g. "archive" meaning three different things
  in a research app).
- Multiple features share concepts that need to align across
  UI copy, ADRs, and database schema.
- New contributors (human or LLM) consistently reach for the
  wrong word because they don't know the project's vocabulary.

If your project is a small utility with self-evident
vocabulary, skip this doc.

## The pattern

### Single glossary file

One file at a known location (typically `CONTEXT.md` at the
repo root, or `docs/GLOSSARY.md`). Multiple glossary files
drift apart; one file is the contract.

### Term + definition + avoid-list

Each entry has three parts:

- **Term** — the canonical name (header or bold)
- **Definition** — what it means, in one or two sentences
- **Avoid-list** — synonyms or near-synonyms that drift the
  vocabulary, with the disambiguation ("use X instead")

The avoid-list is the highest-leverage part. It catches
contributors who reach for the wrong word because the
intended meaning isn't obvious from the term alone.

### Relationships section

A separate section enumerates how terms relate to each
other ("A Person Record has zero or more Source Records").
This makes the glossary a mini-domain-model that survives
feature additions.

### Example dialogue section

A short section showing domain experts using the terms in
conversation. This anchors the glossary to real usage and
catches edge cases ("Is X a Source Record or a Person
Record?") that the formal definitions gloss over.

### Historical section for resolved ambiguities

A section listing every past term-confusion and how it was
resolved ("`record` was used to mean both X and Y — resolved:
use X for one and Y for the other"). This prevents the same
drift from recurring when a new contributor (or a returning
LLM session) reaches for the old term.

## Adding a new term

When a feature introduces a new domain concept:

1. Open the feature issue with a `## Glossary changes`
   section that quotes the new entry exactly as it should
   appear.
2. The PR that lands the feature updates the glossary in
   the same commit (or in a paired glossary-only commit if
   the feature commit is too large).
3. The CHANGELOG bullet for the feature references the
   glossary update.

If the feature ships without the glossary update, the issue
isn't closed.

## Renaming a term

Term renames are high-blast-radius changes. Process:

1. File an issue with `## Rename` section listing every
   call site (UI copy, ADRs, database columns, schema
   files, tests).
2. Add the new term to the glossary with the old term in
   its avoid-list.
3. Ship the rename as a single PR (or a sequenced set of
   PRs if the blast radius is too large for one).
4. Keep the old term in the avoid-list for at least one
   release cycle so anyone searching the old word finds
   the new one.

## Flagged ambiguities section

When you discover that two existing terms are being confused,
add an entry to the "Flagged ambiguities" section rather
than silently picking a winner. The section should include
the resolution date and the rationale.

## References

- [`laws.md`](laws.md) §"Glossary is a contract" — why
  glossary drift is treated as a bug
- [`feature-protocol.md`](feature-protocol.md) — glossary
  changes are part of every feature