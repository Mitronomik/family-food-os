# Current focus

Updated: 2026-09-30.

## Accepted state

PR113 / R1-D corpus-wide Planner admission and source closure inventory is merged
into `main` at:

`48707e1e84eff260726609c4508f05407e9f9448`.

R1-D established:

- exhaustive Planner admission for the published Recipe Catalogue;
- fail-closed Planner eligibility;
- deterministic retained-source inventory of 547 identities:
  - USSR82: 68;
  - School2022: 265;
  - RU-MR-2019: 214;
- source visibility remains distinct from production authority.

## Current bounded operation

**R1-E — CORPUS BLOCKER CLUSTERING AND PLANNER-CAPACITY BATCH SELECTION.**

Issue:

`#114`.

Branch:

`data/r1e-corpus-blocker-clustering`.

Goal:

Turn the 547-row retained inventory into an evidence-backed blocker map with one
deterministic next action per recipe, then select the highest-leverage production
batch for current Planner capacity.

## Important product boundary

"All recipes reach Planner" means every retained/published recipe has a visible,
deterministic closure/admission disposition.

It does not mean every RecipeVersion is a valid standalone meal.

Current Planner can truthfully use standalone BREAKFAST / MAIN and compatible
SANDWICH candidates. SIDE / SALAD / OTHER must not be silently relabelled as MAIN;
their future use as meal components requires a separate meal-composition/bundle
seam.

## Current evidence direction

Repository receipts already identify a high-value Planner-capacity set:

- USSR82-453 — breakfast;
- USSR82-467 — breakfast;
- USSR82-492 — breakfast;
- USSR82-1081 — breakfast;
- USSR82-697 — main.

These five were previously selected for Planner capacity. Current retained reviews
show that their remaining blockers are not one common food-catalogue problem:

- 453 / 1081 retained reviews include missing exact V2 Composition/form authority;
- 467 / 492 retain required-quantity/process blockers;
- 697 retains exact source identity + consumed-Nutrition authority blockers;
- cooked/transformed consumed Nutrition remains the recurring reusable seam.

R1-E must verify current main before selecting any production batch; historical
R1-A "ready" status is not sufficient by itself.

## Next operation inside R1-E

1. classify all 547 rows using repository-backed evidence only;
2. keep unsupported recipe-level facts unknown rather than infer them;
3. summarize blocker counts by source family and blocker class;
4. identify the first batch that maximizes BREAKFAST/MAIN Planner capacity;
5. if no material batch fits current Recipe Nutrition V1, identify the single
   demonstrated reusable architecture seam with the highest capacity payoff.

## Hard boundaries

Do not:

- bulk-activate source recipes;
- treat route count or source presence as production readiness;
- infer raw→cooked Nutrition or implicit retention;
- promote source-declared Nutrition without accepted authority;
- relabel SIDE/SALAD/OTHER as MAIN;
- start meal-bundle runtime in this classification operation;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3 before successful R1-C.
