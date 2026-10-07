# DC4 — Corpus Readiness & Gate1 Consumption Audit

**Status:** BLOCKED — reproducible evidence, **not** Gate1 acceptance  
**Issue / PR:** #164 / #165  
**Accepted base:** `0ce316009eb6223d05756f175f388869ae8debd8` (merged #163)  
**Contract:** [dc4-corpus-readiness-contract.md](dc4-corpus-readiness-contract.md)  
**Machine-readable evidence:** [summary.json](../../data/curation/dc4-corpus-readiness/summary.json)  
**Evidence execution:** GitHub Actions `DC4 corpus readiness`, run `37569620771`, job `112625059401`, audited head `bc6c91b779fdd4c5d5c01b97e947a37ef049ca90`, 2026-10-07.

## Result

**DC4 = BLOCKED. Gate1-CLOSE and PR9 are NOT authorized.**

The standalone DC4 audit ran successfully and the focused tests passed (2/2) at the evidence head. The overall workflow was red at that head due to Ruff checks, corrected later in this same PR. A green workflow must be confirmed separately on the final head; a successful audit operation does not mean the product gate passed.

Two independent product-readiness blockers emerged:

1. `FULL_ACTIVE_CATALOGUE_READINESS`: seven active RecipeVersions are flagged `RUSSIAN_STEPS_NOT_READY` by the DC4 Cyrillic/Latin-text check. Each requires bounded Russian-display review/correction; do not silently change the published recipe or claim the validator proves the actual wording is wrong without inspecting it.
2. `GATE1_FIXTURE_FAILURE`: Fixture 3 produces a deterministic complete 21-event plan with selected hard exclusions respected, but authoritative MealPlan persistence rejects it with `Member event roles and order must match the accepted resolved schedule.` This is a distinct cross-context schedule/persistence defect. It is not permission for DC4 to redesign Planner or relax the accepted fixture.

## Layer A — dynamically enumerated full active catalogue

Inventory A was derived from `FoodRecipeCatalogueService.list_all()` filtered by `is_active`, **not** from the Planner admission subset or a hardcoded count.

| Metric | Observed |
|---|---:|
| Active current production RecipeVersions | **51** |
| PASS readiness rows | **44** |
| BLOCKED readiness rows | **7** |
| Active rows assessed for required FoodIngredient resolution | **51** |
| Prepared-output authority rows | **51** |
| Canonical nutrient values per prepared row | **54** |
| AVAILABLE per prepared row | **1 (ENERGY_KCAL)** |
| UNKNOWN per prepared row | **53** |

The current count **happens** to equal the Planner-eligible count. The two inventories remain logically separate and must be recalculated independently on future baselines.

The seven `RUSSIAN_STEPS_NOT_READY` findings are:

| Recipe code | Disposition / issue |
|---|---|
| `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES` | BLOCKED — Russian steps |
| `SCHOOL2022_54_11M_BEEF_PILAF` | BLOCKED — Russian steps |
| `SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES` | BLOCKED — Russian steps |
| `SCHOOL2022_54_1R_COD_CUTLET` | BLOCKED — Russian steps |
| `SCHOOL2022_54_2R_PINK_SALMON_CUTLET` | BLOCKED — Russian steps |
| `SCHOOL2022_54_3R_POLLOCK_CUTLET` | BLOCKED — Russian steps |
| `SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS` | BLOCKED — Russian steps |

The machine-readable summary records a disposition, ingredient identity and Nutrition authority for **each** enumerated active recipe. No new nutrition/provenance/food authority is manufactured in DC4.

### Nutrition uncertainty

Each of the 51 current prepared-output authority paths exposes only exact `ENERGY_KCAL`; the other **53 canonical nutrient codes remain UNKNOWN**, not numeric zero. The audit records actual `available_nutrient_count` and `unknown_nutrient_count` per recipe from `prepared_canonical_nutrition()`. This is a status/authority proof, **not** evidence that macros or micronutrients are complete.

## Inventory B — Planner-eligible exact-energy supply

Recomputed from `PlannerService.compose_candidate_admission()`, separately from Inventory A:

| Meal type | Expected | Actual |
|---|---:|---:|
| breakfast | 17 | 17 |
| main | 33 | 33 |
| sandwich | 1 | 1 |
| **Total** | **51** | **51** |

**Baseline reconciliation: PASS.** Planner version: `planner-v0.4`, max recipe repetitions: 3. A baseline match alone does not close the full-corpus or persisted-fixture gates.

## Layer B — frozen Gate1 fixtures

Week: 2026-09-14 … 2026-09-20; timezone: `Europe/Moscow`; patterns: `CUSTOM`; schedule identity: `GATE1_ROLE_SHAPES`.

| Fixture | Planned events | Persisted Servings | Planner result | Persistence result |
|---|---:|---:|---|---|
| 1 — 1 member DINNER | 7 / 7 | 7 / 7 | PASS | **PASS** |
| 2 — M1 BREAKFAST+DINNER; M2 DINNER; M1 excludes MILK_2_5 | 14 / 14 | 21 / 21 | PASS | **PASS** |
| 3 — M1 B+L+D; M2 B+D; M3 DINNER; M3 excludes BEEF_CATEGORY_1_RAW | 21 / 21 | 0 / 42 | PASS | **BLOCKED** |

All three pure Planner results were reproducible. In all three, selected recipe ingredient sets were checked against each constrained participating member; **zero selected hard-exclusion violations** were found. Fixture 2 also exposes 154 hard-exclusion candidate rejections. Fixture 3 does not expose that specific rejection code on its trace, but directly selected meals do not contain the excluded ingredient for Member 3. Do not equate candidate-rejection counters with proof of selected meal safety.

Fixture 3 failed in the existing `MealPlanService.create_plan_revision → validate_complete_plan` path. The harness records the exception as a **BLOCKED** fixture outcome rather than crashing or silently changing the schedule. The attempted fixture has no persisted Servings.

## Separate adversarial bounded-infeasibility case

Single member; all seven days BREAKFAST; hard excludes both `MILK_2_5` and `EGG`.

Observed: `PlannerFailure(NO_ELIGIBLE_CANDIDATE)`, 120 hard-exclusion rejections, one repetition-limit rejection, no returned persisted plan, no partial MealPlan in repository.

**Fail-closed proof: PASS.**

## Prior domain evidence reused (not new DC4 acceptance)

- 1/2/3/5/6 opportunities: `backend/app/tests/test_meal_plans.py::test_selection_snapshot_supports_initial_one_to_six_opportunities`.
- Reject 7 opportunities: `backend/app/tests/test_meal_plans.py::test_selection_snapshot_rejects_seven_opportunities_at_product_boundary`.
- Meal-pattern persistence/user acceptance: `backend/app/tests/test_meal_plan_application.py`.
- Prepared-source tamper: `backend/app/tests/test_r3d_final_dc3_batch.py::test_r3d_hash_pinned_gate_rejects_tampered_artifact`.
- Immutable process provenance: `backend/app/tests/test_r3d_final_dc3_batch.py::test_r3d_review_commitment_changes_on_process_binding_drift`.
- No gate-only authority: current audit reads the existing `seed_r3d_final_dc3_batch` production corpus through ordinary catalogue and Planner boundaries and publishes no DC4 recipe/food/nutrition data.

These test names identify accepted evidence paths. Actual pass/fail of reruns must be read from the exact final-head CI receipts; references do not assert unexecuted tests passed.

## Verification and preservation

- DC4 focused tests at audit evidence head: **2 passed**.
- DC4 standalone audit step at evidence head: **SUCCESS**; overall audit **BLOCKED**.
- Workflow at evidence head: **FAILURE** at Ruff only (later source-format correction in this PR).
- Schema/migration: no changes; expected migration head `0042_recipe_prepared_output_nutrition`; no `0043`.
- `AI_ENABLED=false`; no external AI/Retail dependency.
- No production RecipeVersion/FoodIngredient/Nutrition publication or Planner algorithm change.

## Required follow-up (separate bounded work)

**Do not merge a data or Planner fix into DC4.** Review/fix the seven specific Russian-step findings and the Fixture 3 Planner→MealPlan persistence mismatch in separately scoped work, then rerun affected DC4 checks. If a finding requires a schema/immutable contract change, apply the repository docs-only Implementation Contract Gate first. DC4 can then be re-evaluated; only a separate accepted **Gate1-CLOSE** decision may authorize PR9 Shopping Engine.
