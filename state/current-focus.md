# Current focus

Updated: `2026-09-26`.

## Accepted state

PR91 / Step 8 runtime-data publication is merged into `main` at
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Russian-data integration Steps 1–8 are accepted.

## Current bounded state

**PR92 / corrected Step 9 executable Russian RecipeVersion Contract Gate is review-ready.**

Branch:
`docs/step9-russian-recipe-version-contract`.

Verified corrected semantic head:
`3f7a4276ca623c23b61cb344c75e3751f2f83f54`.

Canonical gate:
`docs/family-food/russian-recipe-version-publication-contract.md`.

## Corrected applicability boundary

Review #5324872702 is closed.

Pinned institutional process evidence:

```text
ru-school2022:recipe:53-19з:process-evidence:40
SHA-256 = 5428e818127eceea1c69617e435666c6ce817666ba88bf7486b8c6ce4b60a6e4
applicability = institutional_school_catering_only
domestic_applicability = unestablished
not_executable_rule = true
```

Step 9 RecipeSteps are now exactly:
1. no thermal treatment;
2. cut butter into portion pieces.

Refrigerated pre-service holding and 14 °C serving remain institutional
source-context evidence only.

`home_storage_status=not_granted` remains preserved.

## Corrected Planner / activation boundary

Fresh Step 9 Recipe is inactive.

The gate authorizes one additive application seam:
`TrustedRecipeSeed.initial_is_active: bool = true`.

- existing trusted seeds keep active behavior;
- Step 9 sets false for fresh creation;
- exact replay never mutates activation;
- inactive Step 9 Recipe is absent from current Planner `list_active()` candidate
  enumeration/traces;
- Step 10 separately owns activation + V2 Planner/general-Nutrition integration.

## Preserved Step 9 contract

- exact School2022 53-19з vertical slice;
- seven exact source-lineage/process hashes;
- exact 10 g `BUTTER_PEASANT_72_5_UNSALTED` dependency;
- immutable SOURCE_VERIFIED RecipeVersion;
- source-declared nutrition reference-only;
- deterministic 17-value V2 validation from Step 8 ATOMIC v1;
- WATER/carbohydrate remain unknown;
- Step 8 profile non-current;
- legacy NutritionService unchanged;
- strict fresh/replay/conflict semantics;
- read-only Composition lookup seam only;
- no source-corpus persistence expansion;
- no schema/migration; 0033 reserved, head 0038.

## Corrected semantic verification

On `3f7a4276ca623c23b61cb344c75e3751f2f83f54`:

- Docs #353 — SUCCESS;
- DC1 #215 — SUCCESS;
- corrected semantic review #5324890694 — READY TO MERGE;
- mergeable=true;
- 0 behind main;
- unresolved review threads=0;
- changed scope = one canonical contract + three state files;
- whitespace/conflict audit clean.

## Hard boundary

PR92 is docs/state only.

No Step 9 runtime before PR92 merge + separate runtime authorization.
No Step 10 work starts automatically.

## Stop boundary

PR92 is ready for final review/merge authorization.

Do not merge autonomously.
