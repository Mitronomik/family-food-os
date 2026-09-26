# Current focus

Updated: `2026-09-26`.

## Accepted state

PR91 / Step 8 runtime-data publication is merged into `main` at
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Russian-data integration Steps 1–8 are accepted.

## Current bounded state

**PR92 / Step 9 executable Russian RecipeVersion Contract Gate is review-ready.**

Branch:
`docs/step9-russian-recipe-version-contract`.

Verified semantic contract head:
`b0b5f890ce850075ea91d43e54bc8f93a6497c0d`.

Canonical gate:
`docs/family-food/russian-recipe-version-publication-contract.md`.

## Frozen Step 9 vertical slice

```text
School2022 53-19з — Масло сливочное (порциями)
→ BUTTER_PEASANT_72_5_UNSALTED
→ exact 10 g INPUT
→ SOURCE_VERIFIED RecipeVersion
→ deterministic 17-value V2 composition calculation
```

## Critical frozen decisions

- exact source card/variant/demand/process/selection/route hashes pinned;
- historical v0.3 publication blockers explicitly adjudicated;
- normative-card publication uses canonical factual-publication rights policy;
- Recipe identity frozen as `SCHOOL2022_53_19Z_BUTTER_PORTION`;
- fresh version = v1, one source portion, `meal_type=other`;
- unknown timing/difficulty/storage/freezer/batch facts remain null;
- one required 10 g Step 8 butter ingredient;
- four reviewed factual execution steps;
- zero equipment rows;
- source-declared School2022 nutrition remains reference-only;
- Step 8 profile remains non-current;
- legacy NutritionService is unchanged;
- Step 9 deterministic nutrition uses exact ATOMIC v1 / V2 Composition,
  scaled 10/100;
- carbohydrate and WATER remain unknown;
- narrow preflight forbids silent append to unexpected Recipe history;
- exact Composition lookup may be exposed read-only through the existing
  repository/reader boundary only;
- no source-corpus persistence expansion;
- no schema/migration; head remains 0038 and 0033 remains reserved;
- no Step 10 Planner integration.

## Verification

On semantic head `b0b5f890ce850075ea91d43e54bc8f93a6497c0d`:

- Docs #350 — SUCCESS;
- DC1 #212 — SUCCESS;
- semantic review #5324830015 — READY TO MERGE;
- mergeable=true;
- 0 behind main;
- unresolved review threads=0;
- changed scope = one canonical contract + three state files;
- whitespace/conflict audit clean.

## Hard boundary

PR92 is docs/state only.

No Step 9 runtime/data publication before PR92 is merged and separately
authorized.

No Step 10 work starts automatically.

## Stop boundary

PR92 is ready for final review/merge authorization.

Do not merge autonomously.
