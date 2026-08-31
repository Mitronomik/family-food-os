# Current focus

Updated: `2026-08-31`

## Project

FamilyFoodOS is a separate product bootstrapped from the verified engineering baseline of CosmeticWorkshopOS.

Source baseline:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

## Current lifecycle

`PR0 — Frozen Fork — COMPLETE`

PR0 established:

- Git provenance;
- verified source baseline;
- canonical FamilyFoodOS product documents;
- FamilyFoodOS agent governance;
- FamilyFoodOS execution state;
- migration boundaries.

Verified baseline:

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- frontend build: passed
- frontend test scripts: `22 passed, 0 failed`
- startup smoke: `PASS`
- npm: `0 vulnerabilities`

## Current task

The next authorized milestone is:

`PR1 — Identity Detox`

PR1 implementation must begin only from an updated `main` on a new branch after PR0 is integrated.

## PR1 goal

Separate project/runtime identity from CosmeticWorkshopOS while preserving behavior.

Identity-only work may include:

- package/project names;
- product titles;
- environment-variable names;
- default database/user-data naming;
- launcher identity;
- repository-facing documentation;
- identity-only fixtures and tests.

## PR1 non-goals

Do not yet:

- introduce Household domain models;
- introduce food-domain migrations;
- change recipe business semantics;
- remove legacy bounded contexts;
- build Nutrition Engine;
- build Planner;
- add AI;
- add retail integrations;
- migrate persistence to PostgreSQL.

## Required reading

Before PR1 work:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/migration-plan.md`
5. `docs/migration-source.md`
6. relevant legacy identity code and tests

PR0 must be integrated before PR1 implementation starts.
