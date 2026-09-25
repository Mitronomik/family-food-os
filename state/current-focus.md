# Current focus

Updated: `2026-09-25`.

## Accepted state

PR89 / Step 7 transformation applicability runtime is merged into `main` at
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Russian-data integration Steps 1–7 are accepted.

## Current bounded state

**PR90 / corrected Step 8 recipe-dependency food batch Contract Gate is review-ready.**

Verified corrected semantic head:
`f0b2fa24403589de8b6c16a20b3cc326772c0fbe`.

Canonical gate:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

## Corrected form-authority closure

Re-review blocker #5312850815 is closed:

- School2022 requires 72.5% unsalted butter;
- exact FIC DB/533 / code 1417 supplies the selected 72.5% peasant-butter
  numeric profile;
- exact DB/533 source field `salt_ad = 0.0`;
- frozen source label `Добавленная соль`;
- Step 4 disposition remains `SOURCE_ONLY_NO_V2_TARGET`;
- the literal is used only as source-owned form-compatibility evidence for
  **no added salt**;
- it does not become V2 nutrition or a zero-sodium claim;
- sodium never infers salinity;
- non-zero/null/missing `salt_ad` fails closed.

The frozen identity remains:
`BUTTER_PEASANT_72_5_UNSALTED`.

## Preserved Step 8 decisions

- future Step 9 target: School2022 `53-19з`;
- exactly one Step 8 food dependency;
- FIC raw record SHA-256:
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- `water=null` remains unknown;
- V2 vector remains exactly 17 values;
- profile non-current;
- ATOMIC v1 / INPUT;
- no yield/retention/transformation/applicability publication;
- no migration/schema; head remains 0038 and 0033 remains reserved.

## Corrected semantic verification

On `f0b2fa24403589de8b6c16a20b3cc326772c0fbe`:

- Docs #345 — SUCCESS;
- DC1 #207 — SUCCESS;
- corrected semantic review #5314905510 — READY TO MERGE;
- mergeable=true;
- 0 behind main;
- unresolved review threads=0;
- patch whitespace/conflict audit clean.

## Hard boundaries

No Step 8 runtime/data publication before PR90 merge.

No Step 9 RecipeVersion, Step 10 Planner integration, extra FIC foods,
production retention/yield factors, API/UI/Retail/AI/Auth/PostgreSQL.

## Stop boundary

PR90 is ready for final review/merge authorization.

After merge: stop. Step 8 runtime/data publication requires separate explicit
authorization.
