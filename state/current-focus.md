# Current focus

Updated: 2026-09-28.

## Accepted state

PR108 / R1-C production-proof prerequisite is merged into `main` at:

`b6973baa2f93ecfaded9c93cb7e5711300f247ee`.

R1-C remains blocked because the active Planner-eligible R1 RecipeVersion count
is zero.

## Current bounded operation

**R1 ACTIVATION-AUTHORITY PREREQUISITE — REVIEWED / DOCS-ONLY.**

Branch:

`docs/r1-activation-authority-prerequisite`.

Contract:

`docs/family-food/r1-activation-authority-prerequisite.md`.

## Reviewed disposition

USSR82-697:

- exact recipe/process branch — supported;
- source-branch 107 g chicken input → 75 g cooked output mass relation —
  corroborated by USSR82 Table 23;
- source baseline/Table 23 align the selected branch with semi-eviscerated
  category-II chicken;
- current CHICKEN_CATEGORY_1_RAW category-I binding conflicts with that source
  identity and is historical-only for this recipe;
- exact V2 nutrient retention / ENERGY_KCAL authority — not accepted;
- current Recipe Nutrition calculation cannot consume transformed Composition.

Therefore:

`USSR82-697 = INACTIVE / ROUTE_C`.

No activation runtime is authorized.

## Next allowed step

Remain inside R1.

Either:

1. first correct the exact category-II source-to-FoodIngredient authority for
   USSR82-697, then review exact consumed-Nutrition authority sufficient for
   Planner-safe exact ENERGY_KCAL. Do not preselect the implementation path:
   - applicability-aware transformed Composition with exact reviewed
     yield/retention is one permitted route when evidence supports it;
   - exact source-backed cooked/prepared-product Nutrition is a distinct permitted
     route if evidence exists;
   - any new calculation/publication seam requires its own versioned Recipe
     Nutrition Implementation Contract Gate; or
2. review another already selected R1 candidate under the same authority rules.

R2 is not authorized before successful R1-C without a separate sequencing
decision.

## Hard boundaries

Do not:

- activate USSR82-697;
- infer retention from 107→75 g mass change;
- use generalized nutrient-loss guidance as exact authority;
- change Recipe Nutrition runtime without a docs-only gate;
- start R2/R3;
- start Gate1-CLOSE;
- start Shopping/PR9;
- start Prep/Retail/API/UI/Auth/PostgreSQL/AI.
