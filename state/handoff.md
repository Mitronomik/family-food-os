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

`PR2-A — FamilyFoodOS Architecture & Persistence Contract — COMPLETE`

PR2-A established the canonical FamilyFoodOS architecture, accepted ADR 0032,
aligned the migration plan, and resolved adversarial review blockers for
persistence technology, migration authority and derived-state invalidation. It
made no runtime, schema, migration or dependency changes.

## Canonical reading order

Before continuing:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/architecture.md`
5. `docs/decisions/0032-family-food-persistence-portability-and-shared-deployment-tenancy-gate.md`
6. `docs/family-food/technical-spec.md`
7. `docs/family-food/migration-plan.md`
8. current persistence implementation:
   - `backend/app/db/connection.py`
   - `backend/app/db/migrations.py`
   - representative inherited repositories and tests

## Next authorized milestone

`PR2-B — Persistence Foundation`

PR2-B builds implementation infrastructure only. It introduces and tests the
approved persistence seam before any FamilyFoodOS business bounded context.

After PR2-B is accepted, the intended next milestone is:

`PR2-C — Household Foundation`

## Persistence constraints

New food persistence uses:

`synchronous SQLAlchemy 2.x Core`

Do not substitute ORM, async SQLAlchemy or direct `sqlite3` repositories for new
food contexts. Changing this requires a future superseding architecture
decision. PR2-B may add the approved dependency and resolve its exact version,
physical ID representation, module/table organization, timestamp SQL types and
SQLite conformance-test layout.

New repository interfaces and the Unit of Work must not expose SQLAlchemy,
DBAPI or `sqlite3` connection types through domain/application APIs.

## Migration constraints

During the SQLite phase:

- the existing custom migration runner is the sole schema authority;
- do not introduce Alembic;
- do not use `MetaData.create_all()` as production schema management;
- do not create a second schema-version history.

PR2-B creates no production food tables or migrations. It integrates with the
existing migration authority without changing that authority.

## Unit of Work contract

```text
application operation
        ↓
one Unit of Work
        ↓
one connection / transaction scope
        ↓
participating repositories
        ↓
commit or rollback
```

All reads participating in a write command use that active Unit of Work.
Read-only operations use a consistent query scope and do not commit. Inherited
`backend/app/db/session()` is transitional implementation evidence and is not
the new food-domain Unit-of-Work contract.

## PR2-B scope boundary

PR2-B may introduce the project-owned repository/UoW infrastructure, SQLite
persistence-adapter foundation, transaction tests and portability/conformance
tests for new food contexts.

It must not:

- implement `Household` or `HouseholdMember`;
- create production food tables or food migrations;
- implement Nutrition, Planner, Shopping, Pantry, Prep or Retail;
- add PostgreSQL, Alembic, Auth or tenant infrastructure;
- refactor inherited bounded contexts merely to use SQLAlchemy;
- change consumer UI.

## Why PR2-B is separate from Household

The architecture changes persistence technology for new bounded contexts.
Introducing that dependency and Unit-of-Work infrastructure together with the
first Household aggregate would combine two independent failure surfaces.
PR2-B proves the persistence seam first; PR2-C then implements Household against
an already-tested contract.

## Preserved migration boundary

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
