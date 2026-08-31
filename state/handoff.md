# Handoff

Updated: `2026-08-31`

## Project identity

This repository is **FamilyFoodOS**.

It was bootstrapped from CosmeticWorkshopOS to reuse a verified engineering foundation.

Source provenance:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

Do not continue CosmeticWorkshopOS product lifecycle work from this repository.

## Completed milestone

`PR0 — Frozen Fork — COMPLETE`

PR0 changed governance, canonical documentation and active project state only.

It intentionally did not introduce FamilyFoodOS runtime/domain behavior.

## Verified PR0 baseline

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- frontend test scripts: `22 passed, 0 failed`
- frontend build: passed
- startup smoke: `PASS`
- npm: `0 vulnerabilities`

Startup smoke verified the complete inherited local stack:

- backend `/health`: HTTP `200`
- frontend root: HTTP `200`
- frontend `/api/health`: HTTP `200`
- frontend API proxy payload matched backend payload

See:

- `docs/migration-source.md`

## Canonical reading order

Before continuing:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/technical-spec.md`
5. `docs/family-food/data-ingestion.md`
6. `docs/family-food/migration-plan.md`
7. relevant code and tests

## Legacy boundary

The repository still intentionally contains inherited CosmeticWorkshopOS:

- backend runtime;
- frontend runtime;
- SQLite schema;
- launcher/package infrastructure;
- tests;
- nested legacy `AGENTS.md` files;
- historical documentation.

This is not accidental technical debt introduced by PR0.

Do not mass-delete or mechanically rename these areas.

## Next milestone

`PR1 — Identity Detox`

## PR1 exact starting procedure

Before implementation:

1. update local `main` from `origin/main`;
2. create a new branch from that updated `main`;
3. read the PR1 section in `docs/family-food/migration-plan.md`;
4. inventory identity-only CosmeticWorkshopOS references;
5. separate identity references from true legacy-domain references;
6. define the bounded PR1 diff before editing runtime code.

Suggested branch:

`migration/pr1-identity-detox`

## PR1 boundary

PR1 may change product/runtime identity while preserving behavior.

Do not use PR1 to:

- add Household;
- add CanonicalIngredient;
- change recipe semantics;
- introduce food migrations;
- remove whole legacy bounded contexts;
- redesign consumer frontend;
- add AI;
- add retail;
- add PostgreSQL/Auth.

## Public repository safety

Never commit:

- API keys;
- tokens;
- passwords;
- `.env`;
- private credentials;
- real user personal data;
- real health-related data;
- local databases;
- local development environments.
