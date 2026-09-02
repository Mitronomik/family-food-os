# Handoff

Updated: `2026-09-02`

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

`PR2-C — Household Foundation — COMPLETE`

PR2-C implemented the first production FamilyFoodOS bounded context. Household
and HouseholdMember now work through the real FastAPI → application service →
repository contracts → Household-specific Unit of Work → synchronous
SQLAlchemy Core → SQLite path. Migration `0022_household_foundation` adds the
new tables beside every inherited table and leaves the custom migration runner
as the sole SQLite schema authority.

Closure evidence:

- targeted Household/domain/persistence/API/migration suite: `196 passed`;
- backend + launcher regression: `2684 passed`;
- Ruff checks and formatting checks: passed;
- `git diff --check`: passed;
- final project review: `PR2-C FINAL REVIEW: ACCEPT`;
- GitHub PR `#5`: **MERGED**;
- accepted head: `13f7c7c480469853579912a7836680afc4734ad7`;
- merge commit: `48c72aeba19a1e6ece0dc729f0a80de930be88a8`;
- merged at: `2026-09-01T21:23:23Z`;
- no remaining PR2-C blocker.

The correction pass revokes Household repositories after every terminal UoW
attempt, maps expected commit-time database failures to stable Household
persistence errors, makes Decimal validation total for hostile numeric input,
and validates future birth dates from an injected aware clock in the persisted
Household timezone.

`PR2-DOCS — Canonical Roadmap & PR2-C Closure Sync — COMPLETE`

- GitHub PR `#6`: merged;
- accepted head: `351a0a7e374312d6dda4b7e0e746d6a54579de61`;
- merge commit: `a5b6ca5d210b2401a2fa7e4037a957ec7b846774`.

## Canonical reading order

Before continuing:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `state/current-focus.md`
4. `docs/family-food/master-roadmap.md`
5. relevant architecture/domain documents, including:
   - `docs/family-food/architecture.md`
   - `docs/decisions/0032-family-food-persistence-portability-and-shared-deployment-tenancy-gate.md`
   - `docs/family-food/technical-spec.md`
   - `docs/family-food/data-ingestion.md`
   - `docs/family-food/migration-plan.md`
6. `state/handoff.md`
7. applicable scoped `AGENTS.md`, code and tests, including:
   - `backend/app/AGENTS.md`
   - `backend/app/persistence/AGENTS.md`
8. PR2-B persistence foundation code and PR2-C Household code/tests:
    - `backend/app/services/unit_of_work.py`
    - `backend/app/persistence/sqlalchemy_core/engine.py`
    - `backend/app/persistence/sqlalchemy_core/uow.py`
    - `backend/app/persistence/sqlalchemy_core/types.py`
    - `backend/app/tests/persistence/`
    - `backend/app/domain/households.py`
    - `backend/app/services/household_contracts.py`
    - `backend/app/services/households.py`
    - `backend/app/persistence/sqlalchemy_core/household_*.py`
    - `backend/app/api/households.py`
    - `backend/app/tests/test_household_*.py`
9. existing custom migration runner:
    - `backend/app/db/migrations.py`
    - its migration-chain tests

## Current work

`PR3 — FoodIngredient Catalogue — READY FOR REVIEW`

Branch: `migration/pr3-food-ingredient-catalogue`

Base commit:

`a5b6ca5d210b2401a2fa7e4037a957ec7b846774`

PR3 implements the canonical platform Food Catalogue only. It must remain
`READY FOR REVIEW`, not COMPLETE, until adversarial acceptance and merge.

## PR3 implementation

Domain/application:

- `FoodIngredient`, `IngredientAlias` and `FoodNutritionProfile` use UUIDv4,
  UTC instants, exact Decimal validation and Python-generated Unicode keys;
- search supports exact canonical code/name/alias and bounded prefix/contains
  matching with deterministic ordering and deduplication;
- deactivation preserves aliases and nutrition provenance and is not reversed
  by seed reruns;
- nutrition source/version snapshots are immutable: identical snapshots are
  idempotent, new versions become current and conflicts are explicit.

Persistence:

- migration `0023_food_ingredient_catalogue` follows
  `0022_household_foundation`;
- new tables are `food_ingredients`, `food_ingredient_aliases`,
  `food_nutrition_profiles` and `food_ingredient_allergens`;
- driver-independent contracts compose a Food Catalogue UoW/read scope over the
  accepted synchronous SQLAlchemy Core foundation;
- repository access is revoked after every terminal commit/rollback attempt;
- legacy `ingredients`, catalogue and Household schemas remain unchanged.

Seed/data:

- `data/seed/food_ingredients/` contains `100` FoodIngredients, `89` aliases and
  one current nutrition profile per ingredient;
- authoritative sources are USDA FDC Foundation Foods `2026-04-30` (`87`
  records) and final SR Legacy `2018-04` (`13` records);
- first run inserts `100/89/100`; the second inserts `0/0/0` and reports every
  row existing;
- `греч` returns `BUCKWHEAT` first; `СВЕКЛА` resolves `BEET` through NFKC,
  casefold and `ё → е` normalization;
- allergen review, density, edible fraction and storage truth remain unknown
  rather than receiving invented defaults.

Verification:

- direct PR3 focused suite: `75 passed`;
- expanded PR3 + affected migration/lineage suite: `154 passed`;
- full backend + launcher regression: `2759 passed`;
- Ruff format/check and `git diff --check`: passed.

## Immediate next action

Run PR3 adversarial final review. Do not start or authorize PR4 until PR3 is
accepted and merged.

## Persistence constraints

PR3 must continue to use:

`synchronous SQLAlchemy 2.x Core`

through this accepted dependency path:

`application/domain → repository contracts → Unit of Work → synchronous SQLAlchemy Core → SQLite`

Reuse, do not replace:

- `backend/app/services/unit_of_work.py`;
- `backend/app/persistence/sqlalchemy_core/engine.py`;
- `backend/app/persistence/sqlalchemy_core/uow.py`;
- `backend/app/persistence/sqlalchemy_core/types.py`.

If PR3 discovers a genuine defect in these contracts, identify it explicitly
instead of silently creating a parallel persistence path.

New repository interfaces and the Unit of Work must not expose SQLAlchemy,
DBAPI or `sqlite3` connection types through domain/application APIs.

PR3 must not introduce ORM or async persistence. PostgreSQL remains deferred to
`SHARED-1`; Auth and `HouseholdMembership` remain deferred to `SHARED-2`;
Retail and AI remain later roadmap programs.

## Migration constraints

During the SQLite phase:

- the existing custom migration runner is the sole schema authority;
- do not introduce Alembic;
- do not use `MetaData.create_all()` as production schema management;
- do not create a second schema-version history.

PR2-C added `0022_household_foundation` through the existing runner. PR3 must
append its migration after `0022`; historical migrations remain immutable and
new tables continue to coexist with inherited legacy tables.

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

## PR2-C implementation and scope audit

Implemented:

- `Household` and `HouseholdMember`;
- household-local timezone;
- settings and constraints that genuinely belong to the Household foundation;
- the first production food-domain migration after `0021`;
- SQLAlchemy Core table definitions and repository adapters;
- Household-scoped application operations;
- minimal create/read/update API contracts and endpoints;
- deterministic validation;
- domain, application, repository and API tests.

PR2-C did not:

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

Also deliberately deferred are FoodPreference/excluded-ingredient entities,
member roles, meals-at-home scheduling, portion adjustment, and controlled
Nutrition/Planner vocabularies for activity level and goal.

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
