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

`PR2-B — Persistence Foundation — COMPLETE`

PR2-B implemented and tested the accepted synchronous SQLAlchemy 2.x Core
persistence foundation with `SQLAlchemy>=2.0.52,<2.1`. The application-facing
Unit of Work is driver-independent, owns one explicit transaction, and makes
commit, rollback and failure terminal by revoking or discarding the active
connection. The custom migration runner remains the sole SQLite schema
authority. No production food tables, food migrations or runtime rewiring were
introduced.

Final evidence:

- adversarial review: `PR2-B FINAL REVIEW: ACCEPT`;
- readiness: `READY FOR HOUSEHOLD`;
- targeted persistence suite: `30 passed`;
- backend + launcher regression: `2603 passed`.

## Canonical reading order

Before continuing:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/architecture.md`
5. `docs/decisions/0032-family-food-persistence-portability-and-shared-deployment-tenancy-gate.md`
6. `docs/family-food/technical-spec.md`
7. `docs/family-food/migration-plan.md`
8. `backend/app/AGENTS.md`
9. `backend/app/persistence/AGENTS.md`
10. PR2-B persistence foundation code and tests:
    - `backend/app/services/unit_of_work.py`
    - `backend/app/persistence/sqlalchemy_core/engine.py`
    - `backend/app/persistence/sqlalchemy_core/uow.py`
    - `backend/app/persistence/sqlalchemy_core/types.py`
    - `backend/app/tests/persistence/`
11. existing custom migration runner:
    - `backend/app/db/migrations.py`
    - its migration-chain tests

## Next authorized milestone

`PR2-C — Household Foundation`

PR2-C is the first production FamilyFoodOS bounded-context implementation. Its
goal is to establish the Household aggregate and the persistence/API foundation
needed by later food-domain contexts.

## Persistence constraints

PR2-C must use:

`synchronous SQLAlchemy 2.x Core`

through this accepted dependency path:

`application/domain → repository contracts → Unit of Work → synchronous SQLAlchemy Core → SQLite`

Reuse, do not replace:

- `backend/app/services/unit_of_work.py`;
- `backend/app/persistence/sqlalchemy_core/engine.py`;
- `backend/app/persistence/sqlalchemy_core/uow.py`;
- `backend/app/persistence/sqlalchemy_core/types.py`.

If PR2-C discovers a genuine defect in these contracts, identify it explicitly
instead of silently creating a parallel persistence path.

New repository interfaces and the Unit of Work must not expose SQLAlchemy,
DBAPI or `sqlite3` connection types through domain/application APIs.

## Migration constraints

During the SQLite phase:

- the existing custom migration runner is the sole schema authority;
- do not introduce Alembic;
- do not use `MetaData.create_all()` as production schema management;
- do not create a second schema-version history.

PR2-C may add the first production food-domain migration after `0021`, using the
existing custom runner. New Household tables must coexist with inherited legacy
tables.

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

## PR2-C scope

PR2-C may implement, where justified by the canonical architecture:

- `Household` and `HouseholdMember`;
- household-local timezone;
- settings and constraints that genuinely belong to the Household foundation;
- the first production food-domain migration after `0021`;
- SQLAlchemy Core table definitions and repository adapters;
- Household-scoped application operations;
- minimal create/read/update API contracts and endpoints;
- deterministic validation;
- domain, application, repository and API tests.

## PR2-C non-goals

It must not:

- replace the custom SQLite migration runner or introduce Alembic;
- introduce PostgreSQL, Auth or pretend `household_id` is authorization;
- add a fake `owner_id` for the no-Auth vertical slice;
- use ORM or async SQLAlchemy;
- expose SQLAlchemy or DBAPI types to domain/application code;
- mechanically rename inherited `Client` to `HouseholdMember` or reuse inherited
  Client tables as Household tables;
- refactor unrelated inherited repositories;
- begin Nutrition, Planner, Shopping, Pantry, Prep, Retail or AI;
- begin consumer PWA redesign.

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

The new Household bounded context is distinct from inherited Client semantics.
Model and migrate it as new FamilyFoodOS behavior beside the legacy schema; do
not treat legacy Client code or tables as its domain contract.

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
