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

`PR2-B — Persistence Foundation — COMPLETE`

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

PR2-B implemented the accepted synchronous SQLAlchemy 2.x Core persistence
foundation while preserving the custom migration runner as the sole SQLite
schema authority. The driver-independent Unit of Work owns one explicit
transaction; commit and rollback are terminal, revoke the active connection,
and prevent failed command state from contaminating later pooled commands.
New entity identifiers are application-generated `uuid.UUID` values using
UUIDv4 and generic SQLAlchemy `Uuid`; true instants use the UTC-normalizing
persistence type, while planning dates remain date-only and household-local.

## Next authorized task

`PR2-C — Household Foundation`

PR2-C is the first production FamilyFoodOS bounded-context implementation. It
may establish `Household`, `HouseholdMember`, household-local timezone and
genuine Household settings/constraints; add the first production food-domain
migration after `0021`; implement SQLAlchemy Core tables and repository
adapters; and add Household-scoped application operations, minimal create/read/
update API contracts, deterministic validation and tests across the domain,
application, repository and API layers.

PR2-C must reuse the accepted dependency path:

`application/domain → repository contracts → Unit of Work → synchronous SQLAlchemy Core → SQLite`

It must not replace the custom migration runner; add Alembic, PostgreSQL, Auth,
a fake `owner_id`, ORM or async persistence; expose database-driver types above
the adapter boundary; reuse or mechanically rename inherited Client semantics;
refactor unrelated repositories; begin later food contexts or AI; or redesign
the consumer PWA. New Household tables must coexist with inherited legacy tables.
