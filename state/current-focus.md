# Current focus

Updated: 2026-09-29.

## Accepted state

PR109 / R1 activation-authority prerequisite is merged into `main` at:

`03984aae526ddcd7765f6df6f43608bd4ef0e3fa`.

Accepted PR109 disposition:

- `USSR82-697` remains inactive / Route C;
- the current category-I binding is historical-only for that recipe;
- activation requires exact consumed-Nutrition authority;
- retention/transformed Composition is one possible path, not the only preselected path;
- no activation/runtime/schema/data work was authorized.

R1-C remains blocked because the active Planner-eligible R1 RecipeVersion count
is zero.

## Current bounded operation

**R1 CROSS-CORPUS CONSUMED-NUTRITION FEASIBILITY REVIEW — DOCS-ONLY.**

Branch:

`docs/r1-cross-corpus-consumed-nutrition-review`.

Review document:

`docs/family-food/r1-cross-corpus-consumed-nutrition-review.md`.

Parent:

- #99 R1 Planner-capacity Russian recipe batch;
- #109 activation-authority prerequisite;
- #67 DATA-CORPUS-V1.

## Reviewed scope

Compare retained authority paths across:

- current selected USSR82 R1 candidates;
- School2022 retained routes;
- RU-MR-2019 retained routes;
- licensed FIC RU-NUT-DB input Nutrition authority.

The review may identify a better reusable authority path, but it does not change
the authorized R1 candidate set or publish runtime/data truth.

## Current finding

Retained evidence shows the recurring blocker is reusable consumed Recipe
Nutrition authority, not a chicken-specific loss-factor problem.

School2022 has hundreds of materially executable non-clinical routes and
source-published nutrient reconciliation, but current contracts still treat
source-declared recipe Nutrition as reference-only.

RU-MR-2019 is not currently the short household path under the retained
applicability interpretation.

## Next decision after review

After this docs-only review is reviewed/merged:

1. explicitly decide whether R1 remains the exact current USSR82 set or is widened
   to a bounded cross-corpus pilot;
2. create the Recipe Nutrition consumed-authority Implementation Contract Gate
   required by the accepted path;
3. do not begin runtime/data publication automatically.

## Hard boundaries

Do not:

- activate any RecipeVersion;
- change the R1 candidate set implicitly;
- infer raw→cooked Nutrition;
- promote source-declared recipe totals to production authority without a gate;
- publish yield/retention/transformation authority;
- start R2/R3;
- start Gate1-CLOSE;
- start Shopping/PR9;
- start Prep/Retail/API/UI/Auth/PostgreSQL/AI.
