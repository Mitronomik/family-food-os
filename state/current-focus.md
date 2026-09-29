# Current focus

Updated: 2026-09-29.

## Accepted state

PR110 / R1 cross-corpus consumed-Nutrition feasibility review is merged into
`main` at:

`076de7026a48809d68f314189455b29f35e32a04`.

The user has now explicitly approved widening the R1 candidate universe beyond the
narrow USSR82 set.

Canonical decision:

`docs/family-food/r1-cross-corpus-candidate-universe-decision.md`.

## Current bounded operation

**R1 CROSS-CORPUS CANDIDATE-UNIVERSE DECISION — DOCS/STATE ONLY.**

R1 candidate selection may now draw from all retained, reviewable recipe source
families under DATA-CORPUS-V1, including USSR82, School2022 and RU-MR-2019.

This does not grant blanket publication authority. Every selected recipe still
requires exact source/variant, FoodIngredient/form, Nutrition/Composition,
consumed-Nutrition, immutable RecipeVersion and activation authority.

## Immediate next bounded operation after this decision

Create the docs-only Recipe Nutrition Consumed-Authority Implementation Contract
Gate identified by PR110.

The gate must distinguish:

1. identity-preserving/no-thermal preparation;
2. applicability-aware transformed Composition;
3. exact source-backed prepared-output Nutrition.

After that gate is reviewed/merged, select a small production batch from the
widened cross-corpus candidate universe for Planner capacity and authority
readiness. The batch may come from one or multiple source families; source
diversity is not itself an acceptance criterion.

## Hard boundaries

Do not:

- activate recipes from source-corpus presence alone;
- promote source-declared Nutrition without an accepted authority contract;
- infer raw→cooked Nutrition or implicit retention;
- start runtime/schema/data publication from this decision alone;
- start R2/R3 before successful R1-C;
- start DC4/Gate1-CLOSE/Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.
