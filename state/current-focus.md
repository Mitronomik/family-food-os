# Current focus

Updated: `2026-08-31`

## Project

FamilyFoodOS is a separate product bootstrapped from the verified engineering baseline of CosmeticWorkshopOS.

Source baseline:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

## Historical bootstrap baseline

`PR0 — Frozen Fork — COMPLETE`

PR0 established:

- Git provenance;
- verified source baseline;
- canonical FamilyFoodOS product documents;
- FamilyFoodOS agent governance;
- FamilyFoodOS execution state;
- migration boundaries.

Historical verified baseline:

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- frontend build: passed
- frontend test scripts: `22 passed, 0 failed`
- startup smoke: `PASS`
- npm: `0 vulnerabilities`

## Current task

Current branch/workstream:

`PR1 — Identity Detox`

FamilyFoodOS targets a hosted Web/PWA under ADR 0030. The inherited macOS
consumer package and its D5 / CR-017 forward path are retired under ADR 0031;
they are historical source-product evidence, not current implementation work.

Source-run backend, launcher, SQLite and Restore remain transitional migration
scaffolding. PR1-G retires the consumer package but does not authorize hosted
infrastructure implementation.

PR1-H aligns the retained Restore smoke tools with current FamilyFoodOS
launcher-owned temporary and probe identity.

PR1-I resolves the report-document reconciliation fixture debt by deriving the
current user-mode test database from the canonical FamilyFoodOS path resolver;
the inherited hard-coded `cosmetic_workshop.sqlite` fixture is no longer used.

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

For current PR1 work:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/migration-plan.md`
5. `docs/decisions/0030-family-food-hosted-product-target.md`
6. `docs/decisions/0031-retire-inherited-macos-packaging.md`
7. `docs/migration-source.md`
8. relevant legacy identity code and tests
