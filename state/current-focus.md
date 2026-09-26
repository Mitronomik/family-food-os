# Current focus

Updated: `2026-09-26`.

## Accepted state

PR91 / Step 8 runtime-data publication is merged into `main` at
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Russian-data integration Steps 1–8 are accepted.

## Current bounded state

**PR92 / Step 9 Contract Gate blocker correction is under exact-head re-verification.**

Branch:
`docs/step9-russian-recipe-version-contract`.

Corrected contract head:
`1c8dc51c889c50713f0027efe0d31a31a9f66f7b`.

Canonical gate:
`docs/family-food/russian-recipe-version-publication-contract.md`.

## Corrected applicability boundary

Independent re-review #5324872702 found that one retained process evidence row
was explicitly institutional-only:

```text
ru-school2022:recipe:53-19з:process-evidence:40
applicability = institutional_school_catering_only
domestic_applicability = unestablished
not_executable_rule = true
SHA-256 = 5428e818127eceea1c69617e435666c6ce817666ba88bf7486b8c6ce4b60a6e4
```

The Gate now freezes:
- only “no thermal treatment” + “cut into portions” as RecipeStep material facts;
- refrigerated pre-service holding remains institutional source context only;
- 14 °C serving condition remains institutional source context only;
- `home_storage_status=not_granted` is preserved;
- no household storage/safety/serving rule is inferred.

## Corrected Planner / activation boundary

Current Planner automatically enumerates active + SOURCE_VERIFIED Recipes.

Therefore Step 9 now freezes:
- fresh Recipe starts **inactive**;
- Step 9 authorizes one additive
  `TrustedRecipeSeed.initial_is_active: bool = true` seam;
- existing trusted seeds keep current active behavior;
- Step 9 sets `initial_is_active=false`;
- exact replay never changes mutable activation state;
- inactive Step 9 Recipe is absent from Planner candidate enumeration/traces;
- Step 10 separately owns activation and V2 Planner/general-Nutrition integration.

## Preserved Step 9 decisions

- exact one-food School2022 53-19з vertical slice;
- exact seven source-lineage/process hashes;
- exact 10 g Step 8 butter dependency;
- SOURCE_VERIFIED immutable RecipeVersion;
- source-declared nutrition remains reference-only;
- deterministic 17-value V2 validation through Step 8 ATOMIC v1;
- WATER/carbohydrate remain unknown;
- legacy NutritionService stays unchanged;
- no source-corpus persistence expansion;
- no migration/schema; head remains 0038 and 0033 remains reserved.

## Hard boundary

PR92 remains docs/state only.

No Step 9 runtime/data publication before corrected Gate review/merge and separate
runtime authorization.

No Step 10 work starts automatically.

## Stop boundary

Reverify corrected semantic head, update review receipt, then stop before merge.
