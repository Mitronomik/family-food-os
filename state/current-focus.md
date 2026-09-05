# Current focus

Updated: `2026-09-05`

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

`PR2-C — Household Foundation — COMPLETE`

`PR2-DOCS — Canonical Roadmap & PR2-C Closure Sync — COMPLETE`

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

PR2-C implemented the first production FamilyFoodOS bounded context beside the
legacy schema. The real path now supports creating and updating a Household,
adding and updating HouseholdMembers, and reading complete Household state via:

`FastAPI → HouseholdService → repository contracts → Household Unit of Work → SQLAlchemy Core → SQLite`

Migration `0022_household_foundation` adds `households` and
`household_members` after `0021_family_food_identity`. Member access is always
Household-scoped; there is no `owner_id`, Auth shortcut or Client reuse.

Verification:

- PR2-C correction-pass targeted suite: `196 passed`;
- full backend + launcher regression: `2684 passed`;
- Ruff checks and formatting checks: passed;
- `git diff --check`: passed.

The correction pass preserves terminal Household UoW semantics after successful
and failed commit/rollback attempts, rejects non-finite or unquantizable Decimal
input through stable validation, and evaluates future birth dates against an
injected clock in the persisted Household timezone.

Closure:

- final review: `PR2-C FINAL REVIEW: ACCEPT`;
- GitHub PR `#5`: **MERGED**;
- accepted head: `13f7c7c480469853579912a7836680afc4734ad7`;
- merge commit: `48c72aeba19a1e6ece0dc729f0a80de930be88a8`.

PR2-DOCS closure:

- GitHub PR: `#6` — merged;
- accepted head: `351a0a7e374312d6dda4b7e0e746d6a54579de61`;
- merge commit: `a5b6ca5d210b2401a2fa7e4037a957ec7b846774`.

## PR3 closure

`PR3 — FoodIngredient Catalogue — COMPLETE`

- GitHub PR `#7`: **MERGED**;
- accepted head: `b4d886824989a67711fca0b28821e60934279e6b`;
- merge commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`;
- final review: `PR3 FINAL REVIEW: ACCEPT`;
- PR3-focused suite: `77 passed`;
- full backend + launcher regression: `2761 passed`;
- Ruff and `git diff --check`: passed.

## Current active repository task

`PR4-DATA2 — Russia/SPB Recipe Corpus Re-curation — IN PROGRESS`

Execution result: **BLOCKED — current regional market evidence**, not ready
for final review. Authorized by issue #12, on
`data/pr4-data2-russia-spb-recuration`, strictly from
`26af749be0f6446de1d88cad2e2e03158a9830a0` (main including merged policy PR #11).
Governance PR #9 and PR4-DATA PR #8 are already merged. The historical task
record below does not supersede this authorization.

Research covers the five specified retailer chains and ingredient-form
screening of all30 old recipes. Current SPB-qualified exact-form evidence was
not established; do not convert access failures into stock-absence claims.
See [DATA2 blocker and partial evidence](../data/curation/pr4-data2/README.md).

No successor corpus or replacements accepted; the two ICN sources are barred
from the future selection but the previous30-source artifact is unchanged.
Baseline remains30 recipes /363 coverage rows /119 fixture codes /183 global
FoodIngredients. No new FoodIngredient or runtime change. Baseline curation and
FoodIngredient regressions: **82 passed**. This is not DATA2 acceptance.
Research JSON/reference integrity and `git diff --check` passed; nine unique
observations remain UNCERTAIN. No current AVAILABLE record accepted.

Next allowed action: obtain permitted current SPB/LO catalogue access or
reviewable offline regional evidence, then resume the same supporting task.
The research PR is draft; no final ACCEPT or merge is claimed. PR #10 remains
unchanged on its own branch and must consume DATA2 only after ACCEPT+merge.
PR5 remains unauthorized.

## Historical PR4-DATA task record (status superseded)

`PR4-DATA — Recipe Corpus FoodIngredient Coverage — READY FOR REVIEW`

This is a supporting data operation, not a product milestone.

Branch: `data/pr4-recipe-ingredient-coverage`

Base commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`

The corrected 30-card USDA FNS CACFP corpus and all 363 source ingredient rows
are frozen under `data/curation/pr4/`. Two minimal replacements reduce the
required union from 126 to 119 canonical FoodIngredient codes. The exact Gate 2
subset is durable in `mvp0-food-ingredient-codes.txt`; 36 codes resolve in the
accepted PR3 catalogue and the 83 missing corpus concepts have been added with
current USDA FDC provenance.

The global seed now contains 183 FoodIngredients and is no longer constrained
by PR3's historical 80–120 technical-slice range. The bounded MVP0 manifest,
not the production loader, enforces the unchanged `<=120` Gate 2 fixture limit.

No Recipe schema, domain, persistence, migration, seed, scaling, API or frontend
implementation was started. PR5 remains unauthorized.

## Historical next action (superseded by current task above)

Complete PR4-DATA final review and merge it before starting the next product
milestone, `PR4 — Recipe Catalogue`. PR4 implementation is waiting for the
PR4-DATA merge. PR5 remains unauthorized.
