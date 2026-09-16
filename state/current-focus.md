# Current focus

Updated: `2026-09-16`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34–#43 = MERGED.
- Exact accepted `main` after PR #43: `c428899e703f2bf5addd5f910d53ad40617244c5`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- Assembly A remains BLOCKED; Assembly B, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` and PR7+ remain NOT STARTED.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.

## Current authorized operation

`RECIPE-ASSEMBLY-A-RECOVERY-B` — bounded recovery decision after PR #43 reached
the source-only boundary for `USSR82-267`.

Goal:

1. compare the strongest retained recovery paths without relaxing any Assembly-A gate;
2. determine whether switching away from `USSR82-267` removes the evidence-type blocker;
3. stop source-only churn when the remaining evidence requires physical kitchen execution.

Current delivery:

- Branch: `research/recipe-assembly-a-recovery-b`.
- Base: accepted `main` after PR #43, `c428899e703f2bf5addd5f910d53ad40617244c5`.
- [PR #44](https://github.com/Mitronomik/family-food-os/pull/44) — `research: decide Assembly A recovery boundary` — OPEN / READY FOR HUMAN REVIEW.

Scope is research/data-curation + state only. No runtime/domain code, schema/migration,
production seed, FoodIngredient/Nutrition/Composition promotion, RecipeVersion,
RecipeTemplate or RecipeAssembly publication is authorized.

## Recovery decision

Accepted ready families remain `R1-21` and `R1-23`.

The bounded comparison covers:

- `USSR82-267` — preferred recovery path;
- `R1-05 — Local Harvest Bake` — first fallback;
- `USSR82-369 — Грибы в сметанном соусе` — second fallback;
- the remaining MAP-A optional/substitution shortlists at screening level.

No retained alternate eliminates the accepted complete-variant kitchen evidence
requirement. Candidate switching would add food/composition/process debt without
closing `verified_substitution`.

Assembly A is therefore described more precisely as:

`HUMAN_EVIDENCE_BLOCKED__2_OF_3`.

This does not change architecture or acceptance criteria. It records the kind of
evidence still missing.

## Next-step rule

No additional source-only recovery PR is recommended.

- If measured PR #43 protocol evidence is supplied, a separately authorized
  `V22-13-267-KITCHEN-B` may validate and retain it.
- If measured 267 execution fails, a separately authorized `R1-05-RECOVERY`
  may activate the first fallback.
- If measured execution is unavailable, Assembly A remains BLOCKED.

`V22-13-267-PROFILE-B` remains deferred until the kitchen decision. No automatic
Assembly B, Meal Pattern Catalogue support, PR7, Retail, AI, Auth or bulk data
promotion is authorized.
