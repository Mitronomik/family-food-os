# Current focus

Updated: `2026-09-02`

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

## Current active repository task

`PR3 — FoodIngredient Catalogue — READY FOR REVIEW`

PR3 introduces the canonical platform-owned `FoodIngredient` catalogue through
the accepted application/domain → repository contracts → Unit of Work →
synchronous SQLAlchemy Core → SQLite path. It remains separate from legacy
cosmetic Ingredient, Household ownership, Pantry, recipes and RetailSKU.

Implementation evidence:

- migration: `0023_food_ingredient_catalogue`;
- trusted technical seed: `100` active FoodIngredients and `89` aliases;
- USDA FoodData Central sources: Foundation Foods `2026-04-30` (`87` rows)
  and final SR Legacy `2018-04` (`13` rows);
- every active seed item has one current provenance-bearing nutrition profile;
- direct PR3 focused suite: `75 passed`;
- expanded PR3 + affected migration/lineage suite: `154 passed`;
- full backend + launcher regression: `2759 passed`;
- Ruff format/check and `git diff --check`: passed.

Explicitly deferred: IngredientUnitProfile, regulatory allergen review,
storage-duration truth, Recipe, Pantry, Nutrition Engine calculations, Planner,
Shopping, Retail, Auth, PostgreSQL, AI, frontend and the full Data Program.

## Next action

Perform PR3 adversarial final review. Do not begin or authorize PR4 before PR3
final acceptance and merge.
