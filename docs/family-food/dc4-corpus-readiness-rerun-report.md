# DC4 rerun — Corpus Readiness & Gate1 Consumption

**Status:** PASS — corrected-runtime rerun, **not** Gate1-CLOSE
**Issue / PR:** #178 / #179
**Accepted base:** `2482c52085d7ba9e530f650105a6664ed6d369a7` (merged #177)
**Contract:** [dc4-corpus-readiness-contract.md](dc4-corpus-readiness-contract.md)
**Historical blocked audit:** [dc4-corpus-readiness-report.md](dc4-corpus-readiness-report.md)
**Machine-readable rerun evidence:** [rerun-summary.json](../../data/curation/dc4-corpus-readiness/rerun-summary.json)
**Evidence execution:** GitHub Actions `DC4 corpus readiness rerun`, run `37771436384`, job `113291728664`, artifact `11548231670`, audited head `35cf1d154467ac4171979ea2943b600548c0fb27`, 2026-10-08.

## Result

**DC4 rerun = PASS.**

The two blockers recorded by historical PR #165 are no longer present on current accepted runtime truth:

- the seven Russian RecipeStep readiness defects were corrected through merged A3 / PR #177;
- the heterogeneous Fixture 3 ordering defect was corrected through merged B2 / `planner-v0.5`.

This result is evidence for a **separate Gate1-CLOSE decision**. It does not itself authorize PR9.

## Layer A — full active catalogue

The rerun uses the same dynamic Layer-A audit model as the accepted DC4 contract:
`FoodRecipeCatalogueService.list_all()` filtered by `is_active`, independently
from Planner admission.

| Metric | Rerun |
| --- | ---: |
| Active current production RecipeVersions | **51** |
| PASS readiness rows | **51** |
| BLOCKED readiness rows | **0** |
| `RUSSIAN_STEPS_NOT_READY` | **0** |
| Prepared-output authority rows | **51** |
| AVAILABLE per prepared row | **1 — ENERGY_KCAL** |
| UNKNOWN per prepared row | **53** |

No new FoodIngredient, RecipeVersion or Nutrition authority is published by the
rerun itself. The audit consumes current accepted A3 production truth.

## Inventory B — Planner exact-energy supply

Planner admission is recomputed independently from Layer A.

| Meal type | Expected | Actual |
| --- | ---: | ---: |
| breakfast | 17 | 17 |
| main | 33 | 33 |
| sandwich | 1 | 1 |
| **Total** | **51** | **51** |

Planner algorithm/config version: **`planner-v0.5`**.
Max recipe repetitions: **3**.

## Layer B — mandatory Gate1 fixtures

Week: `2026-09-14 .. 2026-09-20`; timezone: `Europe/Moscow`; accepted
schedule identity: `scripts/gate1a_fixture_spec.py::GATE1_ROLE_SHAPES`.

| Fixture | Events | Servings | Result |
| --- | ---: | ---: | --- |
| 1 — one member DINNER | 7 / 7 | 7 / 7 | **PASS** |
| 2 — M1 BREAKFAST+DINNER, M2 DINNER; M1 excludes `MILK_2_5` | 14 / 14 | 21 / 21 | **PASS** |
| 3 — M1 B+L+D, M2 B+D, M3 DINNER; M3 excludes `BEEF_CATEGORY_1_RAW` | 21 / 21 | 42 / 42 | **PASS** |

All fixtures:

- returned PlannerSuccess;
- persisted complete MealPlans;
- reproduced deterministic trace/request behavior;
- preserved accepted per-member role order;
- had zero selected hard-exclusion violations;
- recorded `planner-v0.5`.

Fixture 2 recorded 154 hard-exclusion candidate rejections. Fixture 3 selected
no beef-dependent DINNER for the constrained member; direct selected-ingredient
verification is the acceptance proof even though its trace does not need to
contain a specific hard-exclusion rejection count.

## Bounded infeasibility

Single member, seven BREAKFAST opportunities, hard excludes both `MILK_2_5`
and `EGG`.

Observed:

- `PlannerFailure(NO_ELIGIBLE_CANDIDATE)`;
- hard-exclusion rejections: **120**;
- repetition-limit rejections: **1**;
- returned persisted plan: **false**;
- partial MealPlan exists: **false**.

**Fail-closed proof: PASS.**

## Determinism and preservation

The focused rerun test suite ran the current full audit repeatedly and matched
gate-level catalogue, Planner supply, fixture outcomes and blockers.

Preserved invariants:

- migration head `0042_recipe_prepared_output_nutrition`;
- no migration `0043`;
- `AI_ENABLED=false`;
- UNKNOWN nutrients are not promoted to numeric zero;
- no gate-only authoritative data;
- historical PR #165 evidence remains intact and continues to describe the old
  `planner-v0.4` / pre-correction state.

## Prior/current domain evidence reused by the rerun

The frozen DC4 contract permits reuse of prior PR7/PR8/domain evidence only when
the rerun identifies it explicitly. The table below is the accepted proof map;
all listed tests were re-executed on exact verification head
`3e5139283c557f75e59f2dd23dd219902b0a4840`.

Primary full-backend receipt: `Nutrient registry V2` run `37772713432` —
**SUCCESS**, including all backend regression shards and launcher regression.
Secondary independent full-backend receipt: `Partial nutrition profiles` run
`37772713616` — **SUCCESS**, including all backend shards and launcher.

| Contract requirement | Current evidence | Why reusable/current |
| --- | --- | --- |
| Representative 1/2/3/5/6 meal opportunities | `backend/app/tests/test_meal_plans.py::test_selection_snapshot_supports_initial_one_to_six_opportunities` | Meal-pattern snapshot boundary is unchanged by A3/B2; exact-head full backend regression passed. |
| Seven-opportunity product boundary | `backend/app/tests/test_meal_plans.py::test_selection_snapshot_rejects_seven_opportunities_at_product_boundary` | Seven opportunities still fail closed; exact-head full backend regression passed. |
| MealPattern acceptance / persistence | `backend/app/tests/test_meal_plan_application.py::test_program_selection_expands_catalogue_template_to_seven_days`; `test_selection_versions_advance_and_preserve_superseded_history`; `test_manual_week_creates_revision_and_shared_event_servings`; `test_complete_manual_week_supports_three_member_household` | PROGRAM/CUSTOM acceptance, versioning and persisted shared Servings remain current application behavior. |
| Recipe classification is distinct from MealRole | `backend/app/tests/test_planner_application_boundary.py::test_candidate_admission_sees_blocked_catalogue_without_selecting_it`; supporting `backend/app/tests/test_planner.py::test_complete_heterogeneous_week_is_deterministic_and_weekly_normalized` and `test_exact_energy_readiness_is_narrow_and_legacy_incomplete_stays_rejected` | Planner consumes MealRole opportunities but separately admits RecipeVersion `MealTypeCode` through the versioned compatibility contract; unsupported `MealTypeCode.OTHER` is rejected as `ROLE_UNSUPPORTED`, not coerced into a role. |
| Meal source-kind boundaries / no fabricated unsupported source | `backend/app/tests/test_meal_plans.py::test_meal_source_requires_recipe_only_for_cook_recipe`; supporting `backend/app/tests/test_planner.py::test_incompatible_members_split_and_subset_fixed_event_is_preserved` | `COOK_RECIPE` requires RecipeVersion truth; non-recipe sources cannot carry recipe truth; fixed `EAT_OUT` remains user-supplied while Planner-generated remaining events use `COOK_RECIPE`. |
| Provenance / source tamper fails closed | `backend/app/tests/test_r3d_final_dc3_batch.py::test_r3d_hash_pinned_gate_rejects_tampered_artifact`; `test_r3d_hash_pinned_mr_bundle_rejects_tamper` | Exact source artifacts remain hash-pinned. R3-D runtime run `37772713549` and the full backend regression both passed on the verification freeze. |
| Immutable process provenance drift is detectable | `backend/app/tests/test_r3d_final_dc3_batch.py::test_r3d_review_commitment_changes_on_process_binding_drift` | Review commitment still changes when process-binding status/rule drifts; same exact-head receipts are green. |
| No gate-only authoritative data | current rerun execution path: `scripts/audit_dc4_corpus_readiness_rerun.py::audit → seed_dc4_a3_russian_step_corrections → ordinary catalogue/Nutrition/Planner services`; supporting `backend/app/tests/test_dc4_corpus_readiness_rerun.py::test_dc4_rerun_reproducible_corpus_and_gate1_evidence` | The rerun publishes no DC4-only Recipe/Food/Nutrition truth and creates no synthetic RecipeVersion. It consumes the merged A3 production catalogue through ordinary boundaries. Owning rerun run `37772713594` is SUCCESS. |

The same mapping is machine-readable under `reused_evidence` in
`data/curation/dc4-corpus-readiness/rerun-summary.json`.

## Verification receipt

Exact execution head: `35cf1d154467ac4171979ea2943b600548c0fb27`.

Dedicated rerun workflow:

- focused full DC4 rerun tests: **7 passed**;
- `--require-pass` audit: **SUCCESS**;
- `overall_status=PASS`;
- `blockers=[]`;
- evidence artifact upload: **SUCCESS**;
- Ruff/format: **PASS**;
- migration/AI invariants: **PASS**;
- scope/whitespace: **PASS**.

The machine-readable receipt includes exact current RecipeVersion UUIDs and all
fixture traces from this evidence database. Those UUIDs are execution-instance
evidence, not portable cross-database identifiers.

## Decision boundary

This PR may establish **DC4 rerun PASS** after independent review and merge.

It does **not** perform or silently imply Gate1-CLOSE.

Required next sequence:

```text
DC4 rerun PR #179 reviewed + merged
→ separate Gate1-CLOSE decision
→ PR9 Shopping Engine only if Gate1-CLOSE passes
```

No Shopping, Prep, UI, Retail, AI, Auth/PostgreSQL or unrelated catalogue work is
authorized by this rerun.
