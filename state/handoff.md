# Handoff

Updated: `2026-09-06`

## Current status

`PR4 — Recipe Catalogue — READY FOR REVIEW`

- PR: `https://github.com/Mitronomik/family-food-os/pull/10`
- branch: `migration/pr4-recipe-catalogue`
- base/main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`
- PR4-DATA2: COMPLETE; PR #13 merged accepted head
  `918bf81b5da306fc65a57643de515ca1b3fbd1e4`
- PR5: UNAUTHORIZED

Do not merge PR #10 without explicit user authorization after final review.

## Authoritative PR4 decisions

1. PR #13 is the accepted recipe-corpus/data handoff; it did not replace PR4
   runtime.
2. Keep the useful PR #10 Recipe Catalogue runtime/domain/persistence layer.
3. Historical `data/curation/pr4` and the old 119-FI/all-servings-6 seed are not
   production truth.
4. Exact historical retrieval instant is not a PR4 publication hard gate.
   `source_retrieved_at` is nullable; never invent an instant.
5. Accepted DATA2 source ID/URL/hash/servings/rights/ingredient/equipment truth
   remains authoritative for v1 production recipes.
6. Fresh network acquisition and changed-current-page hash comparison belong to
   later ingestion/data maintenance unless a real source-truth problem is found.
7. The Recipe Catalogue remains deterministic/offline and works with
   `AI_ENABLED=false`.

## Implemented bounded context

The PR adds the new platform-owned food context beside legacy recipe tables:

- `Recipe`;
- immutable/versioned `RecipeVersion`;
- ordered `RecipeIngredient → FoodIngredient`;
- ordered `RecipeStep`;
- ordered source-backed `RecipeEquipment`;
- verification and reviewed-rights metadata;
- exact Decimal serving scaling;
- deactivate/archive behavior;
- append-version history;
- driver-independent repository contracts;
- synchronous SQLAlchemy Core repositories and UoW;
- custom SQLite migration `0024_food_recipe_catalogue` after `0023`;
- SQLite UPDATE/DELETE guards for version-owned immutable rows;
- deterministic offline seed compiler and idempotent reconciliation.

No Planner, MealPlan, Serving, Nutrition Engine, Pantry, Shopping, Retail,
Auth/PostgreSQL, frontend or AI scope is introduced.

## Accepted production corpus

The generated seed is compiled from accepted `data/curation/pr4-data2/**` plus
reviewed ordered steps in `data/curation/pr4-runtime/recipe-steps.json`.

Exact acceptance counts:

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

The step count is 169, not 170. `SNAP3-GRILLED-FRUIT` has three active selected
steps; the source wooden-skewer soaking note is conditional and omitted because
accepted DATA2 explicitly selected a non-wood skewer.

## Provenance boundary

Required/reviewable production truth remains source-specific:

- source identity and URL;
- accepted source/document SHA-256;
- source version;
- original/base servings;
- verification status and `verified_at`;
- reviewed rights basis and attribution;
- accepted source limitations.

`source_retrieved_at` is an optional true UTC instant. Unknown remains `NULL`.
The earlier TLS/403/ZIP acquisition work is historical execution evidence and
is no longer a PR4 hard gate; temporary acquisition/reset files were removed
from the final PR tree.

## Verification evidence

GitHub Actions run `34001179713` completed successfully.

- DATA2 validator: `PASS: final DATA2 gates`;
- DATA2 focused: `164 passed in 2.80s`;
- focused PR4 suite: `55 passed in 21.93s`;
- fresh first seed:
  - recipes_inserted 30;
  - versions_inserted 30;
  - ingredients_inserted 189;
  - steps_inserted 169;
  - equipment_inserted 86;
  - conflicts 0;
- second identical seed:
  - all inserted counts 0;
  - recipes_existing 30;
  - versions_existing 30;
  - ingredients_existing 189;
  - steps_existing 169;
  - equipment_existing 86;
  - conflicts 0;
- full backend + launcher: `2983 passed, 2 skipped, 1 warning`;
- Ruff: PASS after deterministic formatting/fixes;
- compiler output regenerated twice byte-for-byte identically;
- `git diff --check`: PASS;
- exact final count gate: `30 189 169 86 81`;
- final `.github/workflows` diff against main: empty.

## Final-review checklist

Before accepting PR4, adversarially verify the current PR head against main:

1. final changed-file list contains no temporary workflow, payload, acquisition
   bundle or reset patch;
2. migration `0024` keeps `source_retrieved_at` nullable while source hash/URL/
   source version remain required;
3. final 30 source IDs exactly equal accepted DATA2;
4. 189/169/86/81 counts match seed and loader invariants;
5. conditional source semantics are preserved in existing fields without schema
   expansion;
6. immutability, UoW terminality and rollback behavior remain intact;
7. no future bounded context leaked into PR4;
8. PR body/state say READY FOR REVIEW, not COMPLETE.

If final review accepts, wait for explicit merge authorization. Only after merge
may PR5 Pantry begin.
