# Current focus

Updated: 2026-10-04.

## Accepted state

PR #158 / R3-D final DC3 Contract Gate is MERGED into `main` at:

`a6c1a0bd203e0ec21fd73eb4107282c2b144ff9a`.

DATA-CORPUS-V1 / DC3 remains active until the separately reviewed R3-D runtime
publishes the final frozen batch.

Accepted pre-runtime usable Planner truth:

- 41 active exact-energy recipes;
- 17 `breakfast`;
- 23 `main`;
- 1 `sandwich`;
- hard exact `MILK_2_5` unaffected breakfast set = 3 / capacity 9;
- exact `BEEF_CATEGORY_1_RAW` = 12/23 MAIN.

## Current bounded operation

**R3-D runtime — final ten-recipe DC3 batch before DC4.**

Issue: `#159`.

Branch:

`feat/r3d-final-dc3-batch-runtime`.

Accepted base:

`a6c1a0bd203e0ec21fd73eb4107282c2b144ff9a`.

PR:

**not opened yet — implementation preflight is complete.**

Runtime/test preflight freeze:

`37b7696e40cc9d4192d6855047efa0d8012feaee`.

Pre-PR workflow #37233411877: **SUCCESS**.

Evidence:

- 24/24 focused/adversarial R3-D runtime tests PASS;
- merged R3-D gate validator PASS;
- Ruff check/format PASS;
- migration head 0042 / no 0043 PASS;
- `AI_ENABLED=false` PASS;
- scope/whitespace PASS.

## Runtime outcome under test

The implementation publishes exactly:

- 10 frozen identity-only FoodIngredients;
- 10 immutable SOURCE_VERIFIED MAIN RecipeVersions;
- 10 PREPARED_OUTPUT_V1 authorities with exact ENERGY_KCAL only;
- no FoodNutritionProfile/NutrientVector/Composition authority for new identities.

It preserves the merged gate's exact source-card URLs/hashes, 12+ ingredient
rows, source partition commitment, household review and medical-context
quarantine without adding schema.

Publication is per-recipe atomic/resumable. Activation reuses the merged
R3-A/R3-B/R3-C one-UoW batch seam.

Projected/verified seeded catalogue:

- exact-energy 41 -> 51;
- MAIN 23 -> 33;
- beef 12 -> 14;
- fish remains 9;
- chicken 2 -> 4;
- meat-free 0 -> 6;
- exact-beef unaffected MAIN = 19 / capacity 57;
- hard exact MILK_2_5 breakfast path remains 3 / capacity 9.

## Sequence decision

R3-D remains the last planned DC3 expansion.

After independent review and merge of the runtime PR:

```text
post-runtime reconciliation
→ DC4 corpus readiness audit + Gate1 consumption
→ Gate1-CLOSE
→ PR9 Shopping Engine
```

Do not create R3-E/R3-F for catalogue aesthetics.

## Scope boundaries

No schema/migration/Planner/API/UI/new-Nutrition-authority changes.
Do not start DC4 until this runtime PR is reviewed and merged.
