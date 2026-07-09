# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit subjects follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## [Unreleased]

### Maintenance
- Tailored framework docs to the hex-board-generator stack:
  - `AGENTS.md` — replaced boilerplate with project-specific file map,
    build/test commands, hard rules, and cross-references.
  - `CONTEXT.md` — replaced empty glossary with hex/Havannah/Trike
    domain terms (hexhex-N, base-N Havannah, side-N Trike, axial
    coords, themes, label sets, fit modes).
  - `FRAMEWORK_BOOTSTRAP.md` — set Python as Tier-2 addendum target,
    referenced the CLI smoke matrix as the PR regression gate.
  - `docs/agents/addenda/python.md` — new addendum covering
    reportlab boundary, pure-helper discipline, coordinate-system
    conventions per game, and the CLI dispatch + smoke-matrix
    workflow.

### Added
- <new user-visible capability>

### Changed
- <change in existing functionality>

### Fixed
- <bug fix>

### Removed
- <removed feature>

<!--
  Conventions:
  - One bullet per logical change
  - Reference the issue number if one exists
  - Reference the regression net (test name, smoke probe)
  - Internal refactors that don't change user-visible
    behavior go under Maintenance
-->