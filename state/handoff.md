# Handoff

Updated: `2026-08-31`

## Project identity

This repository is now **FamilyFoodOS**.

It was bootstrapped from CosmeticWorkshopOS only to reuse its verified engineering foundation.

Source provenance:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

The source repository is retained only as read-only reference/provenance.

Do not continue CosmeticWorkshopOS lifecycle work from this repository.

## Current branch

`migration/pr0-frozen-fork`

## Current milestone

**PR0 — Frozen Fork**

Status: **IN PROGRESS**

The purpose of PR0 is governance, provenance and documentation only.

No FamilyFoodOS runtime implementation is authorized in PR0.

## Verified baseline

Before FamilyFoodOS-specific changes, the inherited runtime was verified:

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- frontend build: passed
- npm install/audit: `0 vulnerabilities`
- no baseline test failures

See:

`docs/migration-source.md`

## Canonical reading order

Before continuing work:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/technical-spec.md`
5. `docs/family-food/data-ingestion.md`
6. `docs/family-food/migration-plan.md`
7. relevant code/tests

## Files already established in PR0

Created:

- `docs/migration-source.md`
- `docs/family-food/project-operating-manual.md`
- `docs/family-food/technical-spec.md`
- `docs/family-food/data-ingestion.md`
- `docs/family-food/migration-plan.md`

Replaced for FamilyFoodOS:

- root `AGENTS.md`
- `state/current-focus.md`
- `state/progress.md`
- `state/handoff.md`

## Important legacy boundary

The repository still contains CosmeticWorkshopOS:

- backend runtime;
- frontend runtime;
- database schema;
- nested `AGENTS.md` files;
- legacy documentation;
- launcher/package infrastructure;
- tests.

This is intentional at PR0.

Do not remove or rewrite legacy runtime in PR0.

Nested legacy `AGENTS.md` files may contain cosmetic-specific rules. Root `AGENTS.md` defines how to interpret them during migration.

## PR0 non-goals

Do not:

- rename runtime packages;
- rename environment variables;
- change database schema;
- implement Household;
- implement food ingredients;
- implement Nutrition Engine;
- implement Planner;
- implement Shopping Engine;
- redesign frontend;
- add AI;
- add retailer parsers;
- add PostgreSQL/Auth;
- begin PR1.

## Exact next actions

Complete PR0 only:

1. review the complete Git diff;
2. verify only governance/docs/state files changed;
3. check for accidental secrets or personal data;
4. run `git diff --check`;
5. run appropriate lightweight verification;
6. update PR0 progress state if needed;
7. commit;
8. push branch;
9. open PR0 against `main`;
10. review PR;
11. merge only after acceptance criteria pass.

## After PR0

The next milestone is:

**PR1 — Identity Detox**

PR1 is responsible for beginning runtime/project identity separation while preserving behavior.

Do not start PR1 until PR0 is merged and a new branch is created from updated `main`.

## Safety note

The GitHub repository is public.

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
