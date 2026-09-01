# Current focus

Updated: `2026-09-01`

## Project

FamilyFoodOS is a separate product bootstrapped from the verified engineering baseline of CosmeticWorkshopOS.

Source baseline:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

## Completed lifecycle

`PR0 — Frozen Fork — COMPLETE`

`PR1 — Identity Detox — COMPLETE`

`PR2-A — FamilyFoodOS Architecture & Persistence Contract — COMPLETE`

PR1 separated active FamilyFoodOS project, runtime, launcher, frontend and agent
identity from CosmeticWorkshopOS while preserving inherited runtime behavior.
Accepted source provenance, historical evidence, explicitly classified legacy
documentation and negative/legacy tests remain intentionally present.

PR2-A established the canonical `docs/family-food/architecture.md` contract and
accepted these decisions:

- dependency direction is `UI → API → application/domain → repository interfaces → persistence adapters → database`;
- new food persistence uses synchronous SQLAlchemy 2.x Core and a project-owned Unit of Work;
- the existing custom migration runner remains the sole SQLite schema authority;
- Alembic begins only at an explicit PostgreSQL cutover;
- SQLite remains local/vertical-slice persistence;
- PostgreSQL, Auth and tenant isolation are required before shared multi-family deployment;
- Billing remains later;
- `FoodIngredient` is the canonical name and `FoodIngredient != RetailSKU`;
- persisted derived state has source-revision and staleness rules;
- ShoppingList and PrepPlan generation do not mutate Pantry;
- UTC instants are distinct from household-local planning dates;
- the deterministic core works with `AI_ENABLED=false`.

## Next authorized task

`PR2-B — Persistence Foundation`

PR2-B is implementation infrastructure only. It proves the approved persistence
seam separately from the first FamilyFoodOS business bounded context.

PR2-B may:

- add the approved SQLAlchemy 2.x Core dependency;
- resolve physical ID representation, the exact SQLAlchemy dependency version,
  module/table organization, timestamp SQL types and SQLite conformance-test layout;
- introduce project-owned repository/Unit-of-Work infrastructure for new food contexts;
- implement the SQLite persistence-adapter foundation;
- add persistence/UoW transaction and portability/conformance tests;
- integrate with the existing custom migration authority without changing its authority.

PR2-B must not create `Household`, `HouseholdMember`, production food tables or
food migrations. It must not implement Nutrition, Planner, Shopping, Pantry,
Prep or Retail; add PostgreSQL, Alembic or Auth; refactor inherited
CosmeticWorkshopOS repositories to SQLAlchemy; or change consumer UI.

After PR2-B is accepted, the next intended milestone is:

`PR2-C — Household Foundation`
