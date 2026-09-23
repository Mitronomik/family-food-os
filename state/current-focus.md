# Current focus

Updated: `2026-09-23`.

## Accepted state

PR83 is merged into `main` at
`f12a3f58279eb07c710d1ff889cc70d933da3310`.

Russian-data integration Steps 1–4 are accepted, and the Step 5
Implementation Contract Gate is accepted.

Current bounded work is **Step 5 runtime publication — reviewed Russian adult
micronutrient population reference table**.

## Frozen runtime contract

Canonical contract:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

Methodology version:

`RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`.

Runtime V1 must publish exactly:

- source tables 11/12 for men and 16/17 for women;
- source header `Старше 18 лет` → completed age 19+;
- male/female only;
- KFA-independent rows only;
- 24 reviewed canonical definitions × 2 sexes = 48 rows;
- scalar `ready_source_group_lookup` claims only;
- exact Decimal source values and source/reference units;
- exact source claim/page/table/row/column provenance;
- explicit compatibility against the pinned `RU_NUTRIENT_REGISTRY_V2`;
- existing `ReviewedRussianReferenceTable` / provider / selector boundary;
- deterministic fail-closed load/replay behavior.

Explicitly deferred remain tables 9/10/13/14/15/18, Vitamin D, Calcium, folate,
Vitamin K, fluoride, cobalt/silicon/vanadium, children and pregnancy/lactation.

## Current authorization

The user explicitly authorized Step 5 runtime continuation on 2026-09-23 after
merging PR83.

Authorized:
- hash-pinned 48-row curation package;
- loader/provider runtime wiring through the existing explicit Russian path;
- focused/adversarial tests required by the merged contract;
- state/docs updates required for delivery.

Not authorized:
- schema or migration;
- persisted methodology selection (Step 6);
- Planner/API/UI default switch;
- NASEM behavior change;
- reference-kind extension;
- Step 6+.

If implementation discovers that any authorized row cannot preserve the merged
source/mapping/applicability contract without a new schema/domain decision, stop
rather than widening scope.

## Stop boundary

Deliver Step 5 runtime through exact-head verification and final review. Do not
merge autonomously and do not start persisted methodology selection automatically.
