# Current focus

Updated: `2026-09-26`.

## Accepted state

PR92 / corrected Step 9 Contract Gate is merged into `main` at
`2c50782b17584a5708a946e497d6a628977420e9`.

Russian-data integration Steps 1–8 and the Step 9 Contract Gate are accepted.

## Current bounded task

**Step 9 runtime/data publication — one inactive School2022 RecipeVersion.**

Branch:
`feat/step9-school2022-recipe-runtime`.

Canonical contract:
`docs/family-food/russian-recipe-version-publication-contract.md`.

## Authorized runtime target

```text
School2022 53-19з — Масло сливочное (порциями)
→ inactive Recipe SCHOOL2022_53_19Z_BUTTER_PORTION
→ immutable SOURCE_VERIFIED RecipeVersion v1
→ one required 10 g BUTTER_PEASANT_72_5_UNSALTED row
→ two material RecipeSteps
→ deterministic 17-value V2 validation from Step 8 ATOMIC v1
```

Required source/context guards:

- seven exact source/process lineage hashes;
- institutional-only refrigerated holding remains source context;
- 14 °C remains institutional source context;
- `home_storage_status=not_granted`;
- no household storage/serving claim;
- source-declared nutrition remains reference-only;
- WATER and canonical carbohydrate remain unknown.

## Authorized shared seams

Only:
- additive default-preserving `TrustedRecipeSeed.initial_is_active: bool = true`;
- read-only exact Composition lookup by `food_ingredient_id + version`.

No schema/migration or calculation-semantic change.

## Planner boundary

Fresh Step 9 Recipe is inactive.

It must remain absent from current Planner `list_active()` candidate
enumeration/traces.

No activation belongs in Step 9.

## Hard stops

No:
- second Recipe/Food publication;
- source-corpus persistence expansion;
- current-profile switch;
- legacy NutritionService rewrite;
- Step 10 activation/Planner integration;
- API/UI/Retail/AI/Auth/PostgreSQL;
- migration 0033 or any new migration.

## Stop boundary

Deliver Step 9 runtime/data PR to review-ready state, then stop.

Do not merge autonomously and do not start Step 10.
