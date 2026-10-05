# Current focus

Updated: 2026-10-05.

## Accepted state

PR #158 / R3-D final DC3 Contract Gate is MERGED into `main` at:

`a6c1a0bd203e0ec21fd73eb4107282c2b144ff9a`.

DATA-CORPUS-V1 / DC3 remains active until the separately reviewed R3-D runtime
is merged.

## Current bounded operation

**R3-D runtime — final ten-recipe DC3 batch before DC4.**

Issue: `#159`.

PR: **#160**

Branch:

`feat/r3d-final-dc3-batch-runtime`.

Accepted base:

`a6c1a0bd203e0ec21fd73eb4107282c2b144ff9a`.

Runtime/test freeze:

`50934bca489e4c87204b56032dde6a4d0d3d1862`.

Broad verification head:

`50934bca489e4c87204b56032dde6a4d0d3d1862`.

Status:

`READY_FOR_FINAL_REVIEW`.

Review unit:

https://github.com/Mitronomik/family-food-os/pull/160

## Delivered runtime

Exactly:

- 10 frozen identity-only FoodIngredients;
- 10 immutable SOURCE_VERIFIED MAIN RecipeVersions;
- 10 PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1 authorities;
- exact ENERGY_KCAL only, all other frozen nutrient codes UNKNOWN;
- no FoodNutritionProfile/NutrientVector/Composition authority for new identities.

Merged R3-D provenance is preserved:

- card-specific URL/hash;
- exact 12+ source ingredient rows;
- immutable `review_contract_sha256` over ingredients, process binding, source-row partition/branch, household context and prepared authority;
- intermediates/alternatives are not promoted to RecipeIngredients;
- household REVIEWED_PASS / specialized_medical_scope=false commitment;
- dietetic/institutional context remains provenance only.

Publication is per-recipe atomic/resumable and inactive.
Activation reuses the one-UoW / one-commit batch seam with replay,
mixed-state fail-closed and rollback semantics.

Seeded Planner proof:

- exact-energy 41 -> 51;
- breakfast 17;
- MAIN 23 -> 33;
- sandwich 1;
- beef 12 -> 14;
- fish 9 -> 9;
- chicken 2 -> 4;
- meat-free 0 -> 6;
- exact-beef unaffected MAIN 19 / capacity 57;
- hard exact MILK_2_5 breakfast unaffected remains 3 / capacity 9.

## Verification

Independent-review correction runtime freeze:
`50934bca489e4c87204b56032dde6a4d0d3d1862`.

Correction:

- `_review_commitment()` now includes frozen `ingredients` and `process_binding`;
- immutable marker renamed to `review_contract_sha256`;
- adversarial test proves changing only process-binding status/rule changes the commitment;
- runtime/test suite = **25 passed**.

Exact-head broad verification is fully green:

- R3-D runtime #37281889334 — SUCCESS;
- R3-D gate #37281889429 — SUCCESS;
- Docs #37281889396 — SUCCESS;
- DC1 #37281889497 — SUCCESS;
- R1-C #37281889551 — SUCCESS;
- R2 #37281889328 — SUCCESS;
- R2-B #37281889455 — SUCCESS;
- R2-C #37281889320 — SUCCESS;
- R2-E #37281889366 — SUCCESS;
- R2-F #37281889474 — SUCCESS;
- R3-A #37281889375 — SUCCESS;
- R3-B #37281889569 — SUCCESS;
- R3-C runtime #37281889390 — SUCCESS;
- R3-C gate #37281889436 — SUCCESS;
- Russian methodologies #37281889405 — SUCCESS;
- Nutrient registry V2 #37281889714 — SUCCESS including backend/launcher regression;
- Partial nutrition profiles #37281889327 — SUCCESS including backend/launcher regression.

Migration remains 0042; no 0043. `AI_ENABLED=false`.

The next commit is metadata/workflow/state only; runtime/test bytes remain frozen at
`50934bca...`.

## Sequence decision

Do not start DC4 before PR #160 is independently reviewed and merged.

After merge:

```text
post-runtime reconciliation
→ DC4 corpus readiness audit + Gate1 consumption
→ Gate1-CLOSE
→ PR9 Shopping Engine
```

Do not create R3-E/R3-F merely to increase catalogue size.
