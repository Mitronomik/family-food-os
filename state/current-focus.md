# Current focus

Updated: 2026-09-28.

## Accepted state

PR107 / #100 Planner v0.4 energy allocation is merged into `main` at:

`b27ab1e6338fd0ae76f25ce0040416fc15780891`.

Planner v0.4 is now the authoritative new-generation path. Historical v0.3 remains
replayable.

## Current bounded operation

**R1-C PRODUCTION PLANNER PROOF — AUTHORIZED / PREFLIGHT BLOCKED.**

Branch:

`docs/r1c-production-proof-prerequisite`.

Parent:

- #99 R1 Planner-capacity Russian recipe batch;
- #67 DATA-CORPUS-V1.

Canonical preflight contract:

`docs/family-food/r1c-production-planner-proof-prerequisite.md`.

## Preflight result

Current active Planner-eligible R1 RecipeVersion count is **0**.

R1-B published only USSR82-697 and intentionally kept it inactive:

`INACTIVE_PENDING_TRANSFORMATION_AUTHORITY`.

The other four reviewed R1-B candidates remain blocked.

USSR82-697 input-composition energy `255.892000 kcal` and source output `75 g`
do not authorize final cooked-dish Nutrition or output→yield inference.

Therefore R1-C cannot honestly prove a repository-backed production week yet.

## Next allowed step

Review/merge this docs-only prerequisite contract.

Then separately review the exact authority route needed to activate an R1
RecipeVersion. Numeric transformation/yield/retention publication is not
authorized by this preflight.

## Hard boundaries

Do not:

- activate USSR82-697 from input energy alone;
- infer yield/retention from source output;
- use synthetic Planner candidates to claim R1-C success;
- use non-R1 legacy recipes to substitute for the R1 success path;
- start R2/R3;
- start Gate1-CLOSE;
- start Shopping/PR9;
- start Prep/Retail/API/UI/Auth/PostgreSQL/AI.
