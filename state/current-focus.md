# Current focus

Updated: 2026-09-27.

## Accepted state

PR103 / R1-B source-output Contract Gate is merged into `main` at:

`fb89cfeb84f4052233f82daa7dcc2d1c07aa971a`.

Canonical contract:

`docs/family-food/r1b-source-output-contract.md`.

R1-A remains accepted from merged PR101:
5 recipes are food/form/Nutrition dependency-ready for R1-B; USSR82-364 and
USSR82-208 remain blocked and are outside this runtime batch.

## Current bounded operation

**R1-B RUNTIME — AUTHORIZED / ACTIVE.**

Branch:

`feat/r1b-recipe-versions`.

Parent:

- #102 — source-output contract gate;
- #99 — R1 Steps 7–10 product completion;
- #67 — DATA-CORPUS-V1.

Authorized scope:

1. migration `0040_recipe_version_source_output`;
2. RecipeVersion domain/persistence/replay support for:
   - `source_output_g: Decimal | None`;
   - `source_output_text: str | None`;
3. reviewed, hash-pinned publication package for exactly:
   - USSR82-453;
   - USSR82-467;
   - USSR82-492;
   - USSR82-1081 variant III — с маслом;
   - USSR82-697 exact chicken/main branch without garnish/sauce;
4. exact RecipeIngredient → FoodCompositionVersion bindings;
5. deterministic V2 Recipe Nutrition validation;
6. explicit activation disposition for each published RecipeVersion.

## Reviewed R1-B disposition in PR104

- `USSR82-697` is the sole `SOURCE_VERIFIED` publication, with two exact R1-A
  V2 Composition bindings. It remains inactive pending separately reviewed Step 7
  transformation authority. Its 255.892000 kcal is input-composition validation,
  not final cooked-dish Nutrition authority.
- `USSR82-453` and `USSR82-1081` are blocked because the accepted EGG and
  BUTTER_UNSALTED authorities use the historical nutrient registry and cannot be
  used for the required Step10 V2 binding.
- `USSR82-467` and `USSR82-492` are blocked because verified source process
  requires salt without a quantified source amount.

All five candidates retain exact source output and row receipts in the reviewed
package. No blocked candidate is published or activated.

## Hard contract boundaries

- exact source output is stored as RecipeVersion truth;
- output/input is not promoted to reusable yield;
- no implicit transformation/retention coefficient;
- Recipe Nutrition remains input-Composition authoritative;
- historical RecipeVersions retain null output fields;
- no inferred allergen truth;
- blocked USSR82-364 / USSR82-208 stay outside scope;
- no Planner/Serving behavior change;
- no #100 energy allocation implementation;
- no R1-C;
- no Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## Stop boundary

R1-B ends at a review-ready PR containing migration 0040 plus the bounded
five-candidate review and one-recipe publication/binding result.

Do not start #100 or R1-C merely because R1-B becomes review-ready.
