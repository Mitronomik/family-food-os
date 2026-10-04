# Current focus

Updated: 2026-10-04.

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

`37b7696e40cc9d4192d6855047efa0d8012feaee`.

Broad verification head:

`74c7188aca47d1b5f5335f8a9d3696a9bcbf1196`.

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
- gate-reviewed full source-row partition commitment;
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

Pre-PR freeze:
R3-D #37233411877 — SUCCESS, 24 passed.

Broad exact runtime verification head `74c7188...`:

- R3-D runtime #37233906070 — SUCCESS;
- R3-D gate #37233906129 — SUCCESS;
- Docs #37233906088 — SUCCESS;
- DC1 #37233906260 — SUCCESS;
- R1-C #37233906123 — SUCCESS;
- R2 #37233906152 — SUCCESS;
- R2-B #37233906041 — SUCCESS;
- R2-C #37233906077 — SUCCESS;
- R2-E #37233906172 — SUCCESS;
- R2-F #37233906090 — SUCCESS;
- R3-A #37233906113 — SUCCESS;
- R3-B #37233906086 — SUCCESS;
- R3-C runtime #37233906052 — SUCCESS;
- R3-C gate #37233906054 — SUCCESS;
- Russian methodologies #37233906124 — SUCCESS;
- Nutrient registry V2 #37233906064 — SUCCESS including backend/launcher regression;
- Partial nutrition profiles #37233906111 — SUCCESS including backend/launcher regression.

Migration remains 0042; no 0043. `AI_ENABLED=false`.

Post-freeze repository changes are verification workflows/state only; runtime/test
bytes remain identical to `37b7696...`.

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
