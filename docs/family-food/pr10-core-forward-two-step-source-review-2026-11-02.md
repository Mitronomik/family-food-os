# PR10-CORE — bounded source/process/scale evidence review of two current Step 1 candidates

**Date:** 2026-11-02. **Issue:** [#275](https://github.com/Mitronomik/family-food-os/issues/275).
**Accepted base:** `main@1297393a86f020b86a8b3ddbf7b8754e68d99318` after [PR #274 merged](https://github.com/Mitronomik/family-food-os/pull/274).
**Review scope:** only two preselected Step 1 candidates from the owner-accepted `PR10_FF_FORWARD_3M_7D_V1` synthetic **energy-only** week. No third recipe may be substituted.
**Verdict:** `GO_TO_QUALIFIED_INDEPENDENT_SOURCE_PROCESS_REVIEW_ONLY`; `NO_GO_TO_APPROVED_IMMEDIATE_ON_CURRENT_EVIDENCE` for **both** candidates; `NO_GO_TO_PR10_A_RUNTIME`. This is an engineering **research/evidence assessment**, NOT a named qualified human culinary/Domain/QA source approval.
**Machine evidence:** [non-authoritative bounded two-step JSON](pr10-core-forward-two-step-review-evidence-2026-11-02.json). This file is **never** a `ReviewedRecipeStepEligibilityV1` publication, deployable allowlist, reviewer signature or source-of-truth eligibility reader.

## 1. FACT — actual fixture events, rights, source text and typed Step binding

Accepted source of Planner output: original [#269 final-head GitHub Actions run / raw artifact](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338/artifacts/13084512933), independently reviewed in [PR #270](pr10-ff-final-evidence-review-2026-11-02.md) and owner-accepted as technical-only by [#272](pr10-ff-owner-fixture-acceptance-2026-11-02.md). The [#274 current-week inventory](pr10-core-forward-positive-preflight-2026-11-02.md) covers all 21 selected events, 42 persisted Decimal Servings; this task changes neither the selected week nor the meal source.

For **each** Step 1 below, the original **frozen source A** [raw-pinned manifest](evidence/pr10-ff-forward-input-v1/publication-A-PROPOSED.json) contains the entire `TrustedRecipeVersionSeed` source version, ordered `steps`, structured recipe ingredient net quantities, reviewed factual-source rights (`REVIEWED`) and `SOURCE_VERIFIED` verification. `process_steps_sha256` is the canonical ordered-step-list hash, not an execution approval.

| Accepted real event | 2026-11-03 BREAKFAST | 2026-11-08 BREAKFAST |
| --- | --- | --- |
| RecipeVersion code | `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE@1` | `SCHOOL2022_54_2K_VISCOUS_CORN_MILK_PORRIDGE@1` |
| Persisted RecipeVersion UUID in both real Planner receipts | `025fc5c5-95f8-4e37-bffd-937f5630798b` | `31d36b91-3d2e-4aa6-9363-57d7c5aebbc6` |
| Actual MealEvent role/participation | `COOK_RECIPE`, BREAKFAST, member 1 + member 2 | `COOK_RECIPE`, BREAKFAST, member 1 + member 2 |
| Source card | `ru-school2022:recipe:54-20к` | `ru-school2022:recipe:54-2к` |
| Frozen ordered-process SHA256 | `d6340081a54597250753ef81de33af980212098c7e3a6ba292ac4710fe8af20b` | `2807cf22feb369bbe976c9ce75e1986cd595be7c48b7215397adb8971ff53b54` |
| Step ordinal | 1 of 4 | 1 of 3 |
| Exact Step 1 `instruction_sha256` | `fc78f3e59e588c116421a44824bfe0e77a53d36bdb64c38355cccceafae25afc` | `eb152a402c4347be0bd2aad22f277ed3999a851a05018f73bde4d9c269d55d0a` |
| **Expected** test-fixture Step UUID (deterministically derived, NOT persisted Step readback) | `11cb3e62-2f6c-4505-87be-cf162053c7d6` | `fd63a305-c919-40bf-be01-98783e8caa22` |

The frozen original Russian Step 1 texts are, respectively:

> Гречневую крупу перебрать и промыть, несколько раз меняя воду.

> Перебрать и промыть кукурузную крупу, несколько раз меняя воду.

They contain **no literal numeric instruction** and describe sorting/rinsing the corresponding grain. The later Steps of each RecipeVersion contain heating/time and ingredient-addition instructions. A proposed `NO_NUMERIC_DIRECTION` *syntax candidate* is **not** an independently accepted `numeric_direction_classification`, and definitely not `APPROVED_IMMEDIATE` or a guarantee that Step 1 is a separately meaningful, source-accurate home PrepTask.

### What the expected Step UUID does and does not prove

Both Step SHA256 values were independently recomputed over the **exact UTF-8 Russian instruction text** and matched the frozen `approved_ids` `RECIPE_STEP` keys (`position=1, stage_code=null`). Then the repository-approved `PR10_FF_TYPED_ID_POLICY_V1` (`backend/app/services/pr10_ff_typed_ids.py::derive_fixture_uuid`) was independently reproduced: SHA256 of the fixed typed-policy prefix and canonical envelope (kind, frozen version key, Step position/hash), followed by UUIDv4/variant masking. Its recomputed **RecipeVersion** UUIDs match the *actual persisted raw receipts*, supporting the correct fixture policy/seed lineage. The two Step IDs in the table are therefore **derived expected test fixture IDs**.

**P1 evidence boundary:** the #269/274 raw process receipts do **not** contain independently read-back persisted `RecipeStep.id` rows for these selected versions. We did **not** run a fresh SQLite Step read in this bounded assessment; the expected IDs are **not proof of a currently deployed independent Step FK reader**. Before granting any D3 positive, a separate authorized reader/reviewer must inspect actual current immutable `RecipeStep.id`, instruction SHA256 and source/process hashes *in the target accepted fixture context*, not rely solely on these calculated keys or old 2026-09 historical IDs. This task neither deploys nor publishes that reader.

### Original-source boundary

Both accepted cards reference the same School2022 source-document SHA256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d` and [source URL](https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf). This source SHA/rights is **previously accepted repository provenance**, not a newly authenticated public binary in this task. An independent attempt to fetch the public PDF for a new original-card comparison **timed out**; exact page scan/text and the currently hosted PDF bytes were not independently confirmed here. Therefore source-original vs published whole-recipe instruction completeness and applicability to a family household remain **review questions**, not newly established facts. Rights to publish bounded factual source records are **not** approval to author replacement culinary instructions or assert home process safety.

## 2. FACT — exact current-member Decimal projections

These are **source net ingredient grams × the real two members' existing `Serving.portion_servings`**, no float, rounding, guessed ingredient conversions, replacement of member portions or second Planner run.

| Research-only input | Buckwheat event | Corn event |
| --- | ---: | ---: |
| Member 1 `Serving.portion_servings` | `3.798916` | `2.472331` |
| Member 2 `Serving.portion_servings` | `4.416695` | `2.874382` |
| Sum, source-base servings | `8.215611` | `5.346713` |
| Source grain/net per base | `38 g BUCKWHEAT` | `57 g CORN_GROATS` |
| Member 1 projected grain | `144.358808 g` | `140.922867 g` |
| Member 2 projected grain | `167.834410 g` | `163.839774 g` |
| **Total source-scaled grain input** | **`312.193218 g`** | **`304.762641 g`** |
| Structured recipe **cooking** water per source base | `64 g` | `65 g` |
| Independent quantity of **washing/rinsing water** | **UNKNOWN** | **UNKNOWN** |

Both source cards also retain milk, butter, sugar and salt, and both have original source `base_servings=1` with source-labeled `source_output_g=200`. The source output is a recipe-card field, **not** a measured home batch yield, validated individual amount, safe process capacity, or entitlement to scale appliance/time assumptions. The family factors are materially larger than one source-card serving and require actual equipment/form/portion plausibility review. **The structured cooking-water quantity is for cooking**: do not appropriate it as washing water, equate it with extra water needed for repeated rinsing, or silently add an invented liter count to `RecipeIngredient`.

A purely mechanical reading supports **source-identified sorting and rinsing**. It does not demonstrate that the full step may be performed separately ahead of cooking, how wet groats should be handled, drained, stored, or safely held, nor whether the action offers meaningful independent *same-day* Prep value beyond a copied RecipeStep. No planned holding/freezer task, elapsed time, sink/equipment specification, wash temperature, safety interval or cost was inferred.

## 3. Independent review matrix — outstanding positive gates

| Review dimension | Evidence currently present | Unmet requirement before `APPROVED_IMMEDIATE` |
| --- | --- | --- |
| Selected current fixture / full Step text | **PASS for test-fixture provenance** via A/B/raw event and exact Step SHA | Actual independent persisted Step readback; no source/version/Step drift |
| RecipeVersion/rights/source card | **PASS for frozen reviewed seed** | Qualified reviewer reconciles original whole recipe/card and current home-use applicability, rights and grain form |
| Numeric-direction classification | Literal Step 1 has no digits (**research-only**) | Independent `NO_NUMERIC_DIRECTION` or other classification verdict from qualified reviewer, with signed rationale; no regex-based approval |
| Portion/source-scale | Exact source-grain Decimal arithmetic | Independent equipment/washing method/household batch feasibility and member portion plausibility. Unknown rinse water stays UNKNOWN |
| Genuine useful same-day Prep action | Grain sorting/rinsing occurs before cooking | Independently prove task is separable, nontrivial and honestly executable **same day without intermediate holding claims**; approve the original *whole* Step, no edited replacement text |
| D3 trusted publication/status | Accepted [D3 contract](pr10-core-step-eligibility-d3-contract-2026-10-22.md) plus [publisher/read handoff](pr10-core-two-step-publisher-reader-acceptance-2026-10-23.md) | Real signed independent review, immutable publication ID/revision and deploy pin; rollback-independent authenticated monotonic ACTIVE/REVOKED status authority checked before each task and across old-release rollbacks |
| Production runtime/persistence | Frozen recipe catalog, real Planner/MealPlan/Serving | Separate implementation contracts and review; no Prep tables/UoW, no source eligibility reader. Zero executable tasks |

No qualified named reviewer, independent signed reference, publication/review timestamps, current-status backend, rollback-proof deployment guard or separately approved family-quantity/method assessment was supplied. **Neither candidate receives a positive eligibility verdict**; no machine JSON from this PR may be promoted to a reader package.

### Adversarial/STOP requirements preserved

- Changed RecipeVersion, Step position/instruction SHA, source rights, structured grain amount or member Serving → reject/stale source binding; **do not** retain a positive grant on a stale copied code.
- Digit-free text, signed source rights, recipe source `SOURCE_VERIFIED` or matching expected *typed* Step UUID alone → **not sufficient** to approve `APPROVED_IMMEDIATE`.
- `ACTIVE → REVOKED → rollback to old release` must stay **DENIED**. Missing or unreachable rollback-independent current-status authority → **zero executable tasks**, not cached permission.
- Actual cooking-water quantity does not resolve rinse-water quantity. Unsupported equipment or family-scale assumptions → `REVIEW_REQUIRED`; do not invent facts or output a misleading user task.
- One qualifying MealEvent, two steps on the same event, or a week with zero positive tasks is NOT sufficient for the technical Gate2 **two genuinely distinct approved events** criterion. Neither of the current two candidates is yet a positive.
- No automatic substitution of a third recipe if one candidate fails; return a bounded `NO_GO` and owner decision.

## 4. Verdict, remaining gates, and next single operation

**FACT:** accepted technical Planner week remains `PR10_FF_FIXTURE_REPRODUCIBLE=PASS` for its exact energy-only 3/7/21/42 digest. The reviewed two candidate Step 1 texts, expected test-only Step UUIDs, source/version/Step SHA, member Decimal research quantities and current source records are traceable without modifying runtime.

**ASSUMPTION:** qualified source/process/Domain/QA personnel *might* approve one or both same-day grain washing procedures under explicit form/equipment/scale and process conditions. This is **not established**, and a negative conclusion is acceptable.

**DECISION (technical research only):** `GO_TO_QUALIFIED_INDEPENDENT_SOURCE_PROCESS_REVIEW_ONLY` with **two `NO_GO_TO_APPROVED_IMMEDIATE_ON_CURRENT_EVIDENCE`**. The current state stays `APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_A_RUNTIME`, `NO_GO_TO_PR10_CORE_RUNTIME`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`. This is **not** an accepted eligibility publication, a trusted reader or a completed D3/Prep/Gate2 gate.

**OPEN next authorized decision:** after independent review and owner merge of this docs-only evidence PR, separately authorize a named qualified Recipe/Data/Domain/QA source/process applicability review of precisely these two Step 1 procedures **and** a separate D3 publisher/reader/rollback-independent status implementation contract if any executable action is desired. Evidence of a possible process must not be replaced by arbitrary recipe hunting. No production source change, Reviewer identity invention, calendar planning, safer storage, nutrition, API, database, Prep, Shopping or PDF implementation is authorized here.

**Verification performed:** independently computed both source-text SHA-256, typed expected Step/RecipeVersion fixture UUIDs (and reconciled RecipeVersion UUIDs with actual raw #269 receipts), exact Decimal participant arithmetic, full frozen first-Step/other-Step process content and structured cooking-water origin; compared current GitHub `main` #274 merge and reviewed D3 trust/anti-rollback requirements. Public School2022 original PDF fetch was attempted but failed (timeout), so no independent PDF page review or current hosted PDF binary SHA is claimed. No new Planner/Prep runtime, person-in-kitchen trial, independent qualified source signoff, migration or publisher/reader check was run. Documentation-only CI and a separate reviewer/owner merge decision remain required.
