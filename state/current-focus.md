# Current focus

Updated: `2026-09-26`.

## Accepted state

PR91 / Step 8 runtime-data publication is merged into `main` at
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Russian-data integration Steps 1–8 are accepted.

## Current bounded task

**Step 9 — executable Russian RecipeVersion Implementation Contract Gate.**

Branch:
`docs/step9-russian-recipe-version-contract`.

Canonical gate:
`docs/family-food/russian-recipe-version-publication-contract.md`.

## Selected vertical slice

```text
School2022 53-19з — Масло сливочное (порциями)
→ BUTTER_PEASANT_72_5_UNSALTED
→ exact 10 g INPUT
→ SOURCE_VERIFIED RecipeVersion
→ deterministic 17-value V2 composition calculation
```

## Critical preflight decisions

- no new schema/migration; head remains 0038 and 0033 remains reserved;
- existing Recipe Catalogue transaction/replay seams are reused;
- Step 9 wrapper must fail closed instead of appending to unexpected Recipe history;
- normative-card rights use the later canonical factual-publication decision in
  `ru-normative-recipe-corpus.md`;
- source PDF/layout/photos are not published;
- source-declared nutrition remains reference-only;
- exact Step 8 FIC profile stays non-current;
- legacy `NutritionService.recipe_version()` is not changed;
- deterministic Step 9 nutrition is validated through exact ATOMIC v1 /
  `RU_NUTRIENT_REGISTRY_V2`, scaled from 100 g to exact 10 g;
- missing carbohydrate/WATER remain unknown;
- `meal_type=other` is technical classification only, not Planner eligibility;
- no equipment code is invented for refrigerated holding.

## Hard boundaries

No Step 9 runtime before this gate is reviewed/merged.

No Step 10 Planner integration, additional Recipe/Food publication, source-corpus
bulk ingestion, current-profile switch, API/UI/Retail/AI/Auth/PostgreSQL.

## Stop boundary

Deliver the Step 9 docs-only Contract Gate to review-ready state, then stop.

Do not merge autonomously and do not begin Step 9 runtime until separately
authorized after gate merge.
