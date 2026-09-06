# Handoff

Updated: `2026-09-06`

## Current status

`PR4 — Recipe Catalogue — COMPLETE`

- PR [#10](https://github.com/Mitronomik/family-food-os/pull/10): MERGED;
- merge commit / verified main: `e7a2e00615c8ef1f5bdb4634089e821542ba50dc`;
- accepted/merged head: `0ac6c9d34a3cc54052c8fd01af3acfc49786242f`;
- final project review: `PR4 FINAL REVIEW: ACCEPT — READY TO MERGE`;
- final regression gate: PASS.

No PR currently carries unfinished PR4 work.

`PR5 — Pantry — AUTHORIZED / NOT STARTED` is the next bounded product milestone.
PR4-CLOSE is documentation/state closure only; Pantry is not implemented here.

## PR5 startup

After this closure PR is reviewed and merged, start a feature branch from current
merged `main`. Follow the required reading order in [AGENTS.md](../AGENTS.md),
the [PR5 Pantry contract](../docs/family-food/master-roadmap.md#pr5--pantry) and
the [architecture contract](../docs/family-food/architecture.md).

PR5 owns Household-scoped PantryItem and immutable PantryMovement, transactional
add/consume/adjust/waste operations and available/expiring-stock queries. Preserve
FoodIngredient references, unit validation, non-negative stock, Household
isolation and rollback. Use the canonical PR5 contract for full acceptance
criteria; this handoff changes no architecture or milestone scope.

Canonical sequence remains:

`PR4 Recipe Catalogue → PR5 Pantry → PR6 Nutrition Core → PR7 MealPlan/Serving → PR8 Planner`.

PR6 Nutrition, MealPlan/Serving, Planner, Shopping, Prep, Retail, AI,
Auth/PostgreSQL and PWA remain unauthorized by this closure task.

## Accepted foundations for Pantry

- Household and FoodIngredient contexts are complete. Recipe Catalogue is
  platform-owned; Pantry state is Household-owned.
- RecipeVersion and its ordered ingredient/step/equipment children are immutable.
  RecipeIngredient references canonical FoodIngredient; Recipe is not Serving.
- New food persistence uses repository contracts, synchronous SQLAlchemy Core
  and a project-owned UoW. The custom SQLite migration chain currently ends at
  `0024_food_recipe_catalogue`; preserve legacy coexistence and migration authority.
- Accepted production recipe truth comes from PR4-DATA2 plus reviewed steps in
  `data/curation/pr4-runtime/recipe-steps.json`. Historical `data/curation/pr4`
  is not the active production corpus. Do not re-curate it for Pantry.
- The accepted slice is 30 Recipe, 30 SOURCE_VERIFIED RecipeVersion,
  189 RecipeIngredient, 169 RecipeStep, 86 RecipeEquipment, 34 equipment codes
  and 81 referenced FoodIngredient codes. Required ingredients and required
  direction-consumables both have zero unresolved entries.
- Provenance/rights remain accepted; unknown `source_retrieved_at` stays `NULL`.
  The compiler/seed is deterministic and offline with `AI_ENABLED=false`.
- ShoppingList and PrepPlan generation must not mutate Pantry when those later
  milestones are authorized.

## Accepted verification baseline

Latest fully tested implementation: `173b0f5479c7af2dd7095bf54f9393b2ff68ba55`.
Final full backend + launcher evidence: `2986 passed, 2 skipped` in run
`34002182325`; the recorded warning and timings remain in
[progress](progress.md#verification).

Deterministic byte-identical compilation, first/second seed idempotency and
fail-closed curation-drift validation remain accepted. Detailed PR4 verification
and closure evidence is in [progress](progress.md#pr4-closure).

The closure PR stops at `READY FOR PR4-CLOSE FINAL REVIEW`; it must not be merged
autonomously or used to start later milestones.
