# Handoff

Updated: `2026-09-01`

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

`PR1 — Identity Detox — COMPLETE`

PR1 established active FamilyFoodOS identity while preserving inherited runtime
behavior. Acceptance closed with `2573` backend/launcher tests passing, frontend
build and all 25 frontend test scripts passing, the isolated source-runtime
smoke passing, zero active static-identity blockers and a clean worktree.

## Canonical reading order

Before continuing:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/technical-spec.md`
5. `docs/family-food/data-ingestion.md`
6. `docs/family-food/migration-plan.md`
7. relevant current ADRs
8. current repository architecture and persistence code only as implementation
   evidence, not as the target food-domain specification

## Next authorized milestone

`PR2-A — FamilyFoodOS Architecture & Persistence Contract`

PR2-A must produce a reviewable documentation/architecture contract before any
production food-domain implementation. It should define bounded contexts,
dependency direction, repository and unit-of-work seams, household ownership,
food/catalog/retail separation, deterministic engines, recipe provenance and the
future persistence boundary while retaining SQLite for MVP/local execution.

## Migration boundary

The repository still intentionally contains inherited CosmeticWorkshopOS:

- backend runtime;
- frontend runtime;
- SQLite schema;
- source-run launcher, SQLite and Restore scaffolding;
- tests;
- nested legacy `AGENTS.md` files;
- historical documentation and packaging evidence.

This is preserved migration scaffolding, not the FamilyFoodOS food-domain
specification. Do not mass-delete it and never mechanically rename legacy
entities such as `Client → HouseholdMember`, `Order → MealPlan` or
`ProductionBatch → PrepBatch`.

## PR2-A constraints

- Do not implement `Household` or any other production food-domain entity in PR2-A.
- Do not migrate the database to PostgreSQL yet.
- Define new repository contracts so food-domain services are not coupled to
  `sqlite3` or another concrete database technology.
- Keep SQLite as the MVP/local implementation and define an explicit future
  SQLite → PostgreSQL seam.
- Reconsider PostgreSQL and Auth before shared multi-family deployment; billing
  remains a later milestone.
- Keep the deterministic core usable with `AI_ENABLED=false`.
- The generic Shopping Engine precedes retailer connectors; do not add retailer
  parsers or integrations in PR2-A.
- Do not start the consumer PWA or other production implementation in this
  documentation/architecture milestone.

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
