# Contributing

## Filing issues

### Bugs

Use the [bug template](.github/ISSUE_TEMPLATE/bug.yml). The
template's Symptom, Repro, Root cause, Proposed fix, Files,
Regression net, and Related sections are all required.

The issue is the durable record of the Research phase. A bug
filed without research attached is incomplete and will be
bounced back for investigation.

### Features

Use the [feature template](.github/ISSUE_TEMPLATE/feature.yml).
The template's User story, Locked decisions, Apply sites,
Acceptance criteria, and Slice plan sections are all
required.

The apply-sites checklist is a contract: the feature is not
"shipped" until every box is checked.

## Working on issues

1. Pick up a `ready-for-agent` issue. Drop the Status label
   when you start.
2. Follow the [slice discipline](docs/agents/feature-protocol.md).
   The first slice is the only one that runs in this session.
3. Write the RED test before the slice code (TDD).
4. Commit per the [commit and branch policy](docs/agents/commit-and-branch.md).
5. Update [CHANGELOG.md](CHANGELOG.md) `[Unreleased]`.
6. Close the issue when the PR merges.

## Pull requests

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md). The
checklist covers the framework's regression gates.

## Triage labels

Issues carry labels from six axes (Type × Status × Area ×
Priority × Cohort × Meta). See
[`docs/agents/issues/label-taxonomy.md`](docs/agents/issues/label-taxonomy.md)
for the full taxonomy.

## Conventions

- **One commit = one reviewable unit.** Per the commit and
  branch policy.
- **Vertical slices, not horizontal layers.** Per the
  feature protocol.
- **Regression net required.** Every bug fix + every feature
  slice must land with a test that would have caught the
  bug if it had existed.