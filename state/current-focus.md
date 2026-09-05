# Current focus

Updated: `2026-09-04`

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

## PR4-DATA closure

`PR4-DATA — Recipe Corpus FoodIngredient Coverage — COMPLETE`

- GitHub PR `#8`: **MERGED**;
- accepted head: `59cc1073ac1f951da5b172eb111ed162765b5eaf`;
- merge commit: `704c588387a28e18ac1aa947ded398f168875ea0`;
- final review: `PR4-DATA FINAL REVIEW: ACCEPT`.

## Current active repository task

`PR4 — Verified Recipe Catalogue — READY FOR REVIEW`

Branch: `migration/pr4-recipe-catalogue`

Base commit: `704c588387a28e18ac1aa947ded398f168875ea0`

Working-tree HEAD at verification: `704c588387a28e18ac1aa947ded398f168875ea0`

The corrected 30-card USDA FNS CACFP corpus and all 363 source ingredient rows
are frozen under `data/curation/pr4/`. Two minimal replacements reduce the
required union from 126 to 119 canonical FoodIngredient codes. The exact Gate 2
subset is durable in `mvp0-food-ingredient-codes.txt`; 36 codes resolve in the
accepted PR3 catalogue and the 83 missing corpus concepts have been added with
current USDA FDC provenance.

The global seed now contains 183 FoodIngredients and is no longer constrained
by PR3's historical 80–120 technical-slice range. The bounded MVP0 manifest,
not the production loader, enforces the unchanged `<=120` Gate 2 fixture limit.

PR4 now implements the platform-owned verified Recipe Catalogue from this
accepted frozen corpus. Migration `0024_food_recipe_catalogue` creates the five
new catalogue tables beside the legacy recipe schema. The trusted offline seed
contains exactly 30 active Recipes, 30 immutable source-verified v1 records,
365 ordered ingredient lines, 315 source-derived steps and 0 inferred equipment
rows. All ingredient lines resolve to the accepted 119-code subset without
adding a FoodIngredient.

Verification evidence:

- PR4-focused and affected migration suite: `80 passed`;
- backend suite within final regression: `2174 passed`;
- mandatory backend + launcher regression: `2819 passed`;
- checked-in seed rebuilt byte-for-byte from the exact 30 reviewed PDFs;
- fresh seed run inserted `30/30/365/315/0`; identical rerun inserted zero;
- Ruff format/check and `git diff --check`: passed.

PR4 is READY FOR REVIEW, not complete. PR5 remains unauthorized.

## Next action

Perform PR4 final review. Do not begin PR5.
