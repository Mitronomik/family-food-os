# Current focus

Updated: `2026-09-24`.

## Accepted state

PR89 / Step 7 transformation applicability runtime is merged into `main` at
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Russian-data integration Steps 1–7 are accepted.

## Current bounded state

**Step 8 recipe-dependency food batch Contract Gate is review-ready in PR90.**

Verified semantic head:
`49c291ab5e46a88e34a6f3ae897c32f4cccc6378`.

Canonical gate:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

## Frozen Step 8 decisions

- future Step 9 target: School2022 `53-19з — Масло сливочное (порциями)`;
- exactly one recipe-driven Step 8 food dependency;
- create `BUTTER_PEASANT_72_5_UNSALTED`, do not reuse generic
  `BUTTER_UNSALTED`;
- School2022 owns form/process evidence; FIC owns production numeric nutrition;
- FIC source = code 1417 / DB/533;
- exact raw record SHA-256:
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- FIC `water=null` remains unknown;
- expected sealed V2 vector = 17 values;
- source profile non-current, deterministic verified_at;
- ATOMIC v1 / INPUT;
- zero yield/retention/transformation/applicability rows;
- no schema/migration; migration head remains 0038 and reserved 0033 stays
  unconsumed.

## Contract verification

On `49c291ab5e46a88e34a6f3ae897c32f4cccc6378`:

- Docs #343 — SUCCESS;
- DC1 #205 — SUCCESS;
- semantic review #5303638521 — READY TO MERGE CONTRACT GATE;
- scope: one canonical Step 8 contract + three state files;
- patch whitespace/conflict audit clean;
- mergeable=true;
- 0 behind main;
- unresolved review threads=0.

## Hard boundaries

No Step 8 runtime/data publication before PR90 review/merge.

No Step 9 RecipeVersion, Step 10 Planner integration, extra FIC foods,
production retention/yield factors, API/UI/Retail/AI/Auth/PostgreSQL.

## Stop boundary

PR90 is ready for final review/merge authorization.

After merge: stop. Step 8 runtime/data publication requires separate explicit
authorization.
