# R3-A School2022 MAIN batch Contract Gate

Issue: #144.

Accepted base: `da6d1e05fd44ecc2733e1a6f472eae3e54b60604` (merged PR #142).

This package freezes the first enlarged DC3 recipe batch: **10 MAIN RecipeVersions**
from one School2022 source family, using the existing
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` seam.

The batch is deliberately broader than the previous micro-PRs but remains bounded:

- 10 exact source cards;
- 3 new identity-only FoodIngredients;
- all other identities reused;
- no schema/migration/Planner change;
- ENERGY_KCAL only AVAILABLE; other 53 frozen nutrient codes UNKNOWN;
- no runtime publication in this gate.

The accepted durable source remains the existing private corpus archive and pinned
School2022 PDF. The public PDF was rechecked on 2026-10-03 only as corroboration.

See `docs/family-food/r3a-school2022-main-batch-gate.md`.

## Fail-closed source corrections

During gate review, School2022 `54-5м` and `54-12м` were removed from the selected batch because their ingredient tables name sunflower oil while their technology text names butter for the same cooking operation. No authority branch is inferred.

They were replaced by clean cards `54-4м` and `54-11р`. The gate also uses `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE` where process text proves stale wheat bread but not flour grade.


## Batch transaction semantics — accepted option B

R3-A does **not** require one giant publication transaction.

Future runtime must use:

1. per-recipe atomic publication of inactive RecipeVersion + prepared authority;
2. partial **inactive** publication is permitted after a failure;
3. exact replay is zero-write and rerun converges missing recipes;
4. activation cannot begin until all 10 publications reconcile exactly;
5. activation is a separate explicit batch command:
   - all 10 inactive -> activate all 10 in one caller-owned UoW;
   - all 10 active -> zero-write replay;
   - mixed active/inactive -> fail closed;
   - activation failure rolls back the entire activation transaction.

This keeps one runtime PR for the whole batch while preserving recovery and deliberate-deactivation semantics.

## Process-binding correction

Independent raw-PDF review rejected two previously selected cards:

- `54-9р` — two quantified fats; sunflower-oil placement unresolved;
- `54-18м` — two quantified fats; sunflower-oil placement unresolved.

They are replaced by source-clean `54-6м` and `54-7м`.

The accepted bounded rule is recorded in
`process-binding-review.json`: a single quantified cooking fat may bind to
otherwise unnamed same-card sautéing/tray-oiling operations, but the exact total
must remain authoritative and any internal per-step gram split stays UNKNOWN.
Multiple-fat ambiguity is not resolved by inference.

Durable archive and embedded School2022 PDF were independently re-read and
re-hashed on 2026-10-03; both pinned hashes and byte sizes match.
