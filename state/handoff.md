# Handoff

Updated: `2026-09-05`

## Current execution — PR4 DATA2 integration

PR4-DATA2 — COMPLETE. PR #13 merged after `PR4-DATA2 FINAL REVIEW: ACCEPT`.
Accepted head: `918bf81b5da306fc65a57643de515ca1b3fbd1e4`.
Merge commit / synchronized main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.
Final review submitted at `2026-09-05T16:06:13Z`; merged at
`2026-09-05T16:26:20Z`.

PR4 — IN PROGRESS on existing open PR #10, branch
`migration/pr4-recipe-catalogue`; starting head
`cd2285802c94735e0c9015042f9f4c0b52d68b85`.
Current main is being synchronized by normal merge, with accepted DATA2
preserved. No rebase, force-push, new PR or PR merge is authorized.

Existing PR4 Recipe/domain/application/persistence code and migration
`0024_food_recipe_catalogue` remain present. Production seed/compiler still
require DATA2 correction. The prior rights blocker is superseded by accepted
DATA2 source-specific review under the narrow direct-FNS project risk posture.
Source retrieval instants are under investigation before seed regeneration;
no date-only value may be converted into invented midnight provenance.

PR4 is neither COMPLETE nor ready for final review. PR5 remains unauthorized.
The accepted-main records below are retained as historical execution evidence;
their pre-merge DATA2 status/next-action sentences are superseded here.


## Immediate handoff — PR4-DATA2

PR4-DATA2 — READY FOR REVIEW, not ACCEPTED or COMPLETE (`2026-09-05`).

Issue #12; existing branch `data/pr4-data2-russia-spb-recuration` and
[PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Exact base: `26af749be0f6446de1d88cad2e2e03158a9830a0` (merged governance #9,
historical PR4-DATA #8 and localization #11). This direction-consumables
correction begins at reviewed head `66a30403e3463248bb9b66e5a40920ef3fb136b5`.
The delivered head is recorded exactly in PR #13 after push, not as a
self-referential commit hash in its own contents.

Final: **30 recipes**, **28 retained / 2 replaced in this correction pass**;
relative to historical PR4: **3 retained / 27 replaced**. Both forbidden ICN
cards remain absent. **225 source-audit rows / 189 selected rows** (185 required,
3 source-explicit optional, 1 conditional); exact **81 existing FoodIngredient**
union within **80..120**, zero new codes and zero unresolved required rows.
**86 source-backed equipment rows / 34 normalized codes**.

Canonical PR4 meal types: **breakfast 3 / main 5 / side 5 / salad 6 /
sandwich 1 / other 10**. Separate curation roles: **BREAKFAST 3 / MAIN_DISH 5 /
SIDE_DISH 11 / SOUP 2 / DESSERT 3 / SNACK 4 / CONDIMENT 1 / SANDWICH 1**.
**8 meal anchors**, **3 soups/substantial one-bowl meals**, **11 pure sides**;
six primary-protein families: **DAIRY 1 / EGG 2 / FISH 2 / LEGUME_TOFU 1 /
MEAT 1 / POULTRY 1** among anchors.

All 30 actual sources were audited beyond ingredient lists: **281 consumable
audit rows**. At the reviewed head, **9 recipes / 19 direction-only edible
rows** included two required unquantified pan-release sprays. Honey Lime
Chicken and Local Harvest Bake were replaced, not silently edited. The final
corpus has **9 recipes / 24 direction-only edible rows**, all explicitly
resolved; **zero unresolved required direction consumables**. Process water
discarded after preparation is excluded from those direction-only edible
counts; selected retained water is not.

**83 non-water purchase forms: 3 RU_MASS_MARKET / 80 RU_AVAILABLE /
0 SPECIALTY_OR_UNCLEAR**. Chain coverage: **70 one-chain / 10 two-chain /
3 three-chain** forms. All five baseline chains assessed; Lenta concentration
remains a limitation. Matrix: **187 raw / 179 unique observations,
142 AVAILABLE / 37 UNCERTAIN** (includes rejected research).
Compatibility is not momentary store stock.

All final sources have nine reviewed consistency dimensions, including
direction-only consumables; missing that ninth dimension fails closed. Exact
artifacts/hashes, attribution and notices remain under the approved narrow
direct-FNS project risk posture, including the ONIE-attributed deviled eggs.
No unresolved selected-source rights blocker; no blanket public-domain or
unrestricted commercial/derivative rights claim.

Verification: final DATA2 validator **PASS**; focused DATA2 **164 passed in
3.40s**; historical PR4-DATA/FoodIngredient affected suite **82 passed in 1.71s**;
Ruff format **2 files already formatted**, Ruff check **All checks passed!**;
`git diff --check` **PASS**. Five final artifacts reproduce byte-for-byte from
reviewed source/form/consumable inputs. Final staged scope audit **PASS**: 24
authorized text files, no runtime/database/binary or unrelated files. Full runtime suite
and PR4 production seed execution are excluded from this isolated curation operation.

Historical `data/curation/pr4/`, global seeds (183 ingredients / 172 aliases /
183 profiles), PR4 runtime, migrations/API/frontend and local development DB
remain unchanged. PR #10 remains at `cd2285802c94735e0c9015042f9f4c0b52d68b85`;
it may consume DATA2 only after ACCEPT + merge. No RetailSKU/retailer production,
Nutrition, Pantry, Planner, Shopping, Auth/PostgreSQL or AI work. PR5 unauthorized.
Next action: project final review, not autonomous merge.

See [final review evidence](../data/curation/pr4-data2/review-report.md) for sources, replacements and consumable resolutions.

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

## Historical work record (superseded by immediate handoff above)

`PR3 — FoodIngredient Catalogue — COMPLETE`

Closure evidence:

- GitHub PR `#7`: **MERGED**;
- accepted head: `b4d886824989a67711fca0b28821e60934279e6b`;
- merge commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`;
- final review: `PR3 FINAL REVIEW: ACCEPT`;
- PR3-focused suite: `77 passed`;
- full backend + launcher regression: `2761 passed`;
- Ruff and `git diff --check`: passed.

`PR4-DATA — Recipe Corpus FoodIngredient Coverage — READY FOR REVIEW`

This is a supporting data operation, not a product milestone.

Branch: `data/pr4-recipe-ingredient-coverage`

Base commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`

Review evidence:

- the initial 30-card union contained 126 concepts;
- Roasted Potato and Turkey Hash (marginal 6) and Brown Rice Pilaf (marginal 3)
  were replaced by Vegetable Frittata Bites (contribution 1) and Cauliflower
  Rice (contribution 1), the minimum two-card correction that passes the gate;
- `data/curation/pr4/ingredient-coverage.csv` retains all 363 source ingredient
  rows, including optional ingredients, alternatives and the explicit Bean
  Burrito Bowl subrecipe structure;
- the exact `mvp0-food-ingredient-codes.txt` manifest contains 119 codes, within
  the unchanged Gate 2 maximum of 120;
- all source rows resolve, with 36 PR3 codes and 83 corpus-required additions;
- the global seed contains 183 FoodIngredients, 172 aliases and 183 current
  nutrition profiles, with 102 Foundation and 81 SR Legacy profiles in total;
- the production loader validates a non-empty catalogue and all existing data
  rules but no longer hard-codes PR3's historical 80–120 milestone range;
- no Recipe implementation was made.

## Completed PR3 implementation

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

Complete PR4-DATA final review and merge. The next product milestone remains
`PR4 — Recipe Catalogue`, and its implementation waits for PR4-DATA merge. PR5
remains unauthorized.

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
