# P1-PLANNER-SERVING-RESEARCH — bounded source/policy readiness receipt

**Status:** `NO_GO` **for this audited three-recipe research cohort on the available evidence**. **Not a catalogue-wide finding**, runtime defect fix, production policy, new numeric threshold or Gate2 change.
**Date:** 2026-10-17.
**Issue:** [#230](https://github.com/Mitronomik/family-food-os/issues/230). **Parent:** merged [PR #229](https://github.com/Mitronomik/family-food-os/pull/229), `main@3c5663b3b87f6f9f83b511d8a9e465a9bc85e60d`.
**Authoritative proposed research gate:** [Planner Serving Plausibility contract](planner-serving-plausibility-contract-2026-10-17.md) §5.
**Machine-readable receipt:** [bounded evidence JSON](planner-serving-research-evidence-2026-10-17.json).

## 1. Goal, facts and audited boundary

This receipt asks whether **one** real, pinned `(Household, RecipeVersion, MealEvent, member)` opportunity can attain `PASS_REVIEWED_FEASIBILITY`, backed by (a) verified finished edible output and scale relation, (b) an **applicable reviewed physical portion policy**, and (c) the exact accepted member/MealPattern energy allocation. The negative control must distinguish Household-owned preferences from independent physical evidence. This is the **RESEARCH_READY** level only; seven-day **RUNTIME_READY** is a separate future gate.

**FACT:** [Historical DC4 rerun receipt](../../data/curation/dc4-corpus-readiness/rerun-summary.json) reports 51 active exact-energy-eligible recipes and a deterministic `planner-v0.5` **three-member** seven-day case with 21 MealEvents and 42 Servings. The three member opportunity-role patterns are `BREAKFAST/LUNCH/DINNER`, `BREAKFAST/DINNER`, and `DINNER`, respectively. This was a **historical normal Planner proof**, not a strict physical-serving proof. The receipt does not supply member reference-energy/accepted allocation and each member/event/Serving source pin in the material audited **here**. We do not reconstruct or invent them.

**FACT:** Merged #229 explicitly describes the prospective `PortionFeasibilityProfile` as conceptual and **not accepted**, and treats NIDDK, Rospotrebnadzor and USDA portions context as research references **not executable numeric policy**. Neither the recipe manifests nor this contract provide a reviewed, versioned person/context/dish-form interval authorizing a physical PASS. No broader claim is made about every possible outside publication or future policy.

**Evidence method:** read immutable reviewed publication manifests and historical DC4 receipt on the exact accepted main SHA. No fresh SQLite, live current-main RecipeVersion query, raw private corpus fetch, independent external source byte verification or new household fixture were executed. Version IDs below are **historical DC4 snapshot IDs**, not claimed to identify newly materialized production rows.

## 2. Three bounded source-backed RecipeVersion candidates

| Source identity and role | Historical DC4 RecipeVersion ID | Published original/base / source output | Manifest expected energy per base Serving | Physical-policy evidence |
| --- | --- | --- | --- | --- |
| `SCHOOL2022_54_2M_BEEF_GOULASH` — MAIN | `4e6eac51-384e-40d5-8f89-24943cbfc38e` | `1 / 1` / `80 g` | `185.6 kcal` | No accepted applicable reviewed bound in audited inputs |
| `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK` — MAIN | `ab8d55dc-ce6f-4072-a6bf-e4f68f1f3977` | `1 / 1` / `80 g` | `144.8 kcal` | No accepted applicable reviewed bound in audited inputs |
| `SCHOOL2022_54_2O_GREEN_PEA_OMELET` — BREAKFAST | `43e34739-aff2-4954-a5e4-2e476f54d614` | `1 / 1` / `150 g` | `153.5 kcal` | No accepted applicable reviewed bound in audited inputs |

Manifest sources, respectively:

- [R1-G verified publication specs](../../data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json), blob `394b35d3d02c0498a681584a37d36b1d98faf40d`, School2022 card `ru-school2022:recipe:54-2м` and card SHA-256 `d48a9461e98d4d2df0056c379722dc9e6ed248dc74ce65a4a118a1165565209d`.
- [R2-B verified publication specs](../../data/curation/r2b-fish-main-diversity/publication-specs.json), blob `b4ad353c4c9e955b64fb8b155cc98a1530aeb3a8`, card `ru-school2022:recipe:54-6р`, card SHA-256 `507b25f2bb485cb9e151773b06feb82b948df46c1cb2be53298ad41c50ce95ab`.
- [R3-B verified publication specs](../../data/curation/r3b-school2022-breakfast-batch/publication-specs.json), blob `96d134265a8c256e34ad985670feed8ca56c295d`, card `ru-school2022:recipe:54-2о`; no independent exact-card SHA is asserted in this receipt.

All three inherit School2022 source-document SHA-256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d` and their manifests record `rights_review_status=REVIEWED` for **bounded factual recipe data**. Their publication inputs mark `initial_is_active=false` before the curation/runtime publish operation; eligibility above comes **from historical DC4 rerun**, not from asserting those seed flags represent current runtime state.

The source output amounts refer to the reviewed **source recipe's prepared-output basis**, not a universally physiologically appropriate portion and not a proof of **linear finished-yield scaling** to another household batch. In particular, input/raw ingredient sums and `RecipeVersion.base_servings` are **not** acceptable substitutes for those missing facts. The energy figures here are publication-manifest **expected** `ENERGY_KCAL` values, not new live Nutrition recalculations.

## 3. Research readiness evaluation

| Required proof | Audited evidence | Verdict |
| --- | --- | --- |
| Source identity, rights and original output/basis | Pinned School2022 manifests plus accepted historical DC4 RecipeVersion UUIDs and exact energy-readiness | **Available for these three identities**, with stated historical limits |
| Verified applicability of cooked output to arbitrary target portion/batch scale | Original source output is known; independently approved extrapolation to the hypothetical Planner-selected member portion is **not demonstrated** | `UNKNOWN` |
| Reviewed physical portion interval applicable to actual member age/context, meal role and dish form | #229 identifies this policy as conceptual and non-accepted; none supplied in audited input manifests | `UNKNOWN` |
| Exact pinned real member/opportunity, accepted energy share and planned candidate serving | Historical three-member fixture exists, but no such individual event/target pin is reproduced in **this** audit | `NOT_EVALUATED` |
| Positive case with physical `PASS_REVIEWED_FEASIBILITY` | Cannot be supported without the above authority and context | **Not demonstrated** |
| Safe negative control | See §4: a preference match cannot make a physical PASS | **Logical negative control only**, not a complete experimental pair |
| Whole-week strict gate | Prohibited to infer from normal 21-event/42-Serving `planner-v0.5` success | `RUNTIME_READY = NOT_EVALUATED` |

The permitted exact Decimal *conditional* math remains:

```text
allocated_kcal = accepted_member_reference_energy_kcal × accepted_opportunity_energy_share
portion_servings = allocated_kcal / authoritative_recipe_kcal_per_base_serving
planned_final_edible_g = portion_servings × validated_final_output_g_per_base_serving
```

No numeric `allocated_kcal`, proposed member portion, validated arbitrary-scale mass or policy-bounds verdict is fabricated here. A source `80 g` or `150 g` line is **not** an adult/child serving bound.

## 4. Research-only negative control

**Synthetic preference-only scenario:** suppose a user confirms that they *prefer* the amount printed as the source output of a recipe. The preference comparator can return `MATCHES_USER_PORTION_PREFERENCE`. Without independently reviewed person/context/meal-role physical bounds and verified scale applicability, the **separate** physical evaluator must still return `UNKNOWN_OUTPUT_OR_PORTION_POLICY`, **never** `PASS_REVIEWED_FEASIBILITY`.

This is a logical contract control, **not** an experimentally exercised Planner call, not real Household data, not a medical recommendation and not enough to satisfy the required paired positive/negative `RESEARCH_READY` gate.

## 5. Decision and one required owner action

**DECISION (evidence status, not new architecture): `NO_GO_FOR_THIS_BOUNDED_RESEARCH_COHORT_ON_CURRENT_EVIDENCE`.** These three source-backed recipes cannot yet establish one positive *member/event-specific* physical feasibility result. Thus `RESEARCH_READY=false`; `RUNTIME_READY` is **not evaluated**, not assumed failed over the entire catalogue. The historical accepted Planner and Shopping remain unchanged. No new Planner/Serving authority is created.

**OPEN QUESTION / next user decision:** identify/approve a *single* independently reviewable **physical portion-policy source and policy owner** with clear authority, rights, version, member age/context, meal role, finished-dish category/form, explicit bounds and applicability rules. Separately review whether the recipe's final cooked yield can be projected to a particular target scale. After that, authorize one pinned **Household/MealEvent/member** positive and negative research proof. If it fails, return `NO_GO` again rather than inventing adult/child gram caps.

A successful `RESEARCH_READY` still would **not** authorize strict Planner activation: a separate complete seven-day, three-member `RUNTIME_READY` proof, reviewed Planner version/trace and explicit owner Option A/B choice are required first.

**Non-goals/unchanged:** no production code, numerical standards, profiles, migrations, API/UI, recipe publication, historical PlannerVersion/MealPlan changes, Pantry/Shopping/Prep execution, safety/hold/storage claims or Goal/roadmap reorder. `PR10-FD-META=BLOCKED`, `TIME_UNRESOLVED` and Gate2 remain gated. `AI_ENABLED=false` preserved.

## 6. Verification scope and caveats

Evidence fields were transcribed from the exact three pinned publication manifests and `dc4-corpus-readiness/rerun-summary.json` into [machine receipt](planner-serving-research-evidence-2026-10-17.json). The evidence claims only reviewed manifest/source facts and **historical** Planner readiness, not actual current-plan simulations. This is docs/data-evidence only, so full backend regression is not required by [verification policy](verification-policy.md). Exact-head docs CI and human independent review are required before merge; no external physical policy/source has been approved by this PR.
