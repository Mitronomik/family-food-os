# Handoff

Updated: `2026-09-06`

## Current status

`PR4 — Recipe Catalogue — READY FOR REVIEW`

- PR: `https://github.com/Mitronomik/family-food-os/pull/10`
- branch: `migration/pr4-recipe-catalogue`
- base/main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`
- latest fully tested implementation commit: `173b0f5479c7af2dd7095bf54f9393b2ff68ba55`
- PR4-DATA2: COMPLETE; PR #13 merged accepted head `918bf81b5da306fc65a57643de515ca1b3fbd1e4`
- PR5: UNAUTHORIZED

Do not merge PR #10 without explicit user authorization after final review.

## Authoritative decisions

1. PR #13 is the accepted recipe-corpus/data handoff; it did not replace PR4 runtime.
2. Keep the useful PR #10 Recipe Catalogue domain/application/persistence layer.
3. Historical `data/curation/pr4` and the old 119-FI/all-servings-6 seed are not production truth.
4. Exact historical retrieval instant is not a PR4 publication hard gate. `source_retrieved_at` is nullable; never invent an instant.
5. Accepted DATA2 source ID/URL/hash/servings/rights/ingredient/equipment truth remains authoritative for v1 production recipes.
6. Fresh network acquisition is not a runtime/publication dependency for PR4 after the user-approved scope reset.
7. Ordered source-derived directions are durably reviewed in `data/curation/pr4-runtime/recipe-steps.json`; extraction hash/comparison lineage is retained in the source manifest.
8. Recipe Catalogue remains deterministic/offline and works with `AI_ENABLED=false`.

## Implemented bounded context

The PR adds the platform-owned Recipe Catalogue beside legacy recipe tables:

- `Recipe`;
- immutable/versioned `RecipeVersion`;
- ordered `RecipeIngredient → FoodIngredient`;
- ordered `RecipeStep`;
- ordered source-backed `RecipeEquipment`;
- verification and reviewed-rights metadata;
- exact Decimal serving scaling;
- deactivate/archive behavior;
- append-version/current-verified history;
- driver-independent repository contracts;
- synchronous SQLAlchemy Core repositories and UoW/read scope;
- custom SQLite migration `0024_food_recipe_catalogue` after `0023`;
- SQLite UPDATE/DELETE guards for version-owned immutable rows;
- deterministic offline seed compiler and idempotent reconciliation.

No Planner, MealPlan, Serving, Nutrition Engine, Pantry, Shopping, Retail, Auth/PostgreSQL, frontend or AI scope is introduced.

## Accepted production corpus

Compiler inputs:

- accepted `data/curation/pr4-data2/**`;
- reviewed ordered steps in `data/curation/pr4-runtime/recipe-steps.json`.

Exact output:

- Recipe: 30;
- initial RecipeVersion: 30 SOURCE_VERIFIED;
- RecipeIngredient: 189 = 185 required + 3 optional + 1 conditional;
- RecipeStep: 169;
- RecipeEquipment: 86;
- distinct equipment codes: 34;
- distinct FoodIngredient: 81;
- new FoodIngredient: 0;
- unresolved required ingredients: 0;
- unresolved required direction-consumables: 0.

`SNAP3-GRILLED-FRUIT` has three active selected steps; wooden-skewer soaking is conditional guidance and is excluded because DATA2 selected a non-wood skewer.

The single selected conditional ingredient is Spring Vegetable Saute water: stored as optional 30 ml upper bound with source condition preserved in `prep_note` (`only if vegetables start to brown; source permits 1–2 tablespoons`).

## Provenance boundary

Production RecipeVersion v1 keeps:

- accepted source identity/URL;
- accepted document SHA-256 and source version;
- source original/base servings;
- verification status + `verified_at`;
- source-specific reviewed rights basis;
- true `source_retrieved_at` only when actually known (3 records), otherwise `NULL`.

The source manifest separately keeps step-extraction source SHA-256 and comparison result. This preserves reviewable lineage when ordered directions were transcribed from a current official representation whose bytes differ from the accepted DATA2 artifact while recipe-relevant selected facts remain matched.

## Verification evidence

Run `34001179713` — scope-reset/seed acceptance:

- DATA2 validator PASS; DATA2 `164 passed`;
- PR4 focused `55 passed`;
- fresh seed inserts exactly `30/30/189/169/86`, conflicts 0;
- second identical seed inserts 0 and sees `30/30/189/169/86`, conflicts 0;
- deterministic compiler regeneration byte-identical;
- full backend+launcher `2983 passed, 2 skipped`;
- Ruff + diff checks PASS;
- no final workflow diff.

Run `34002182325` — adversarial fail-closed hardening:

- DATA2 validator PASS; DATA2 `164 passed in 3.56s`;
- PR4 focused `58 passed in 15.56s`;
- full backend+launcher `2986 passed, 2 skipped, 1 warning in 626.61s`;
- Ruff PASS;
- `git diff --check` and staged diff PASS;
- temporary workflow removed before final push;
- loader rejects per-recipe same-count ingredient mapping drift, equipment-order drift, step-text drift and source-manifest step-lineage drift.

## Next action

Final project review of the current PR #10 head. If ACCEPT, wait for explicit user merge authorization. After merge, verify new main and mark PR4 COMPLETE before authorizing PR5.
