# Current focus

Updated: 2026-10-03.

## Accepted state

PR #142 / R2-F runtime is merged into `main` at:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

R2-F delivered:

- active `breakfast` classification: 7;
- active MAIN classification: 5;
- active `sandwich` classification: 1;
- hard exact `MILK_2_5` unaffected BREAKFAST-compatible pool:
  egg + cottage casserole + cheese sandwich;
- capacity = 3 × repetition 3 = 9/week;
- persisted seven-BREAKFAST exact-MILK exclusion week succeeds.

## Current bounded operation

**R3-A — School2022 10-recipe DATA-CORPUS-V1 / DC3 Contract Gate.**

Issue: `#143`.

Branch:

`docs/r3a-school2022-10-recipe-batch-gate`.

Accepted base:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

Status:

`CONTRACT_GATE_ACTIVE`.

Canonical detail:

`docs/family-food/r3a-school2022-10-recipe-batch-gate.md`.

## Scope

Freeze one larger School2022 batch:

- 10 future RecipeVersions;
- 5 BREAKFAST + 5 MAIN;
- two new identity-only foods:
  `CHEESE_SEMI_HARD_UNSPECIFIED`, `PARSLEY_ROOT_FRESH`;
- reuse `PREPARED_OUTPUT_V1`;
- no schema/migration/Planner/new-Nutrition-authority change.

Do not start runtime, DC4/Gate1-CLOSE/PR9 or another R3 batch before this gate is
independently reviewed and merged.
