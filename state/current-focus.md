# Current focus

Updated: `2026-09-24`.

## Accepted state

PR89 / Step 7 transformation applicability runtime is merged into `main` at
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Russian-data integration Steps 1–7 are accepted.

## Current bounded state

**Step 8 recipe-dependency food batch Contract Gate is active.**

Branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Canonical gate:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

## Frozen preflight direction

- future Step 9 target: School2022 recipe `53-19з`,
  `Масло сливочное (порциями)`;
- exactly one Step 8 food dependency;
- create source-faithful
  `BUTTER_PEASANT_72_5_UNSALTED`, not reuse generic `BUTTER_UNSALTED`;
- School2022 owns recipe/form/process evidence only;
- licensed FIC RU-NUT-DB code 1417 / DB/533 owns production numeric nutrition;
- exact FIC raw record SHA-256
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- reuse accepted Step 4 source-field semantics;
- FIC `water = null` remains unknown, so expected V2 vector has exactly 17 values;
- source profile is non-current;
- expected ATOMIC composition is v1 / INPUT;
- no yield/retention/transformation/applicability publication;
- no new migration/schema expected.

## Source-artifact verification

Durable private corpus artifact was independently retrieved:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`.

Verified:

- bytes: `206692075`;
- SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- School2022 PDF SHA-256:
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- FIC RU-NUT-DB raw HTML SHA-256:
  `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`.

## Hard boundaries

No Step 8 runtime/data publication before this gate is reviewed/merged.

No Step 9 RecipeVersion, Step 10 Planner integration, extra FIC foods,
production retention/yield factors, API/UI/Retail/AI/Auth/PostgreSQL.

Reserved `0033_recipe_template_catalogue` remains unconsumed.

## Stop boundary

Deliver this docs-only Contract Gate for review.

After gate merge: stop. Step 8 runtime/data publication requires separate
explicit authorization.
