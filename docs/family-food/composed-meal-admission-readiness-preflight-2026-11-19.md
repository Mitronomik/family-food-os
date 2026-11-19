# Composed-meal admission — source, role and physical-readiness preflight

**Status:** PROPOSED / DOCS-ONLY / REQUEST INDEPENDENT REVIEW. **NO_GO for real-family or consumer activation.**
**Date:** 2026-11-19.
**Accepted starting point:** `main@af501e60911be3a393fa0eb3e2c611dc86b4fa28`, [#294 merged](https://github.com/Mitronomik/family-food-os/pull/294) on 2026-11-18.
**Scope owner:** cross-context readiness **assessment**, not runtime admission. The existing MealPlan/Recipe/Nutrition/Shopping/Prep owners retain their own source-of-truth responsibilities.
**Read with:** [root contract](../../AGENTS.md), [current focus](../../state/current-focus.md), [MealPlan 0044 contract](mealplan-multicourse-persistence-implementation-contract-2026-11-16.md), [Shopping v1b contract](shopping-composition-demand-implementation-contract-2026-11-18.md), [product strategy](product-strategy.md), [compatibility](architecture-addendum-2026-09-13.md), [source/portion feasibility proposal](planner-serving-plausibility-contract-2026-10-17.md), [PR10 stages](pr10-option-b-staged-delivery-gates-2026-10-17.md), [Finished-Dish-First](pr10-finished-dish-first-amendment-2026-10-12.md), [verification](verification-policy.md) and [Master Roadmap](master-roadmap.md) with its addenda.

## 1. Purpose and explicit decision boundary

**Goal:** choose the smallest evidence-first next step after #294: determine whether the **specific source-pinned multi-course MealPlan** can ever be promoted from internal diagnostic data to a family-facing plan, **without** conflating correct grocery arithmetic with complete nutrition, course/role suitability, feasible portions or safe executable Prep.

This is an **assessment gate proposal**. Its review may approve an evidence protocol, not a recipe, meal, physical norm, platform policy, production admission flag, PR10 executable task, Gate2 PASS or public Shopping V2 response. Any cross-context activation requiring a persisted identity, migration, public API or revised source authority needs a **separately merged docs-only Implementation Contract Gate**, followed by bounded implementation PRs. Do not treat approval of this assessment document as such activation approval.

## 2. FACT / ASSUMPTION / PROPOSED DECISION / OPEN

### FACT — what merged #294 actually proves

- [#292](https://github.com/Mitronomik/family-food-os/pull/292) introduced typed immutable `COOK_COMPOSITION` under `0044_meal_plan_components`: a full seven-day DRAFT revision with exact member-component `Serving`, source-pinned `RecipeVersion`, an ordered rule snapshot and a **diagnostic-only** admission status. There is no fabricated parent RecipeVersion or legacy event-level Serving.
- [#293](https://github.com/Mitronomik/family-food-os/pull/293) fixed the Shopping V2 provenance/legacy read-isolation implementation contract; [#294](https://github.com/Mitronomik/family-food-os/pull/294) implemented internal `shopping-v1b-composition`: per-component exact Decimal ingredient demand, per-event aggregation, dated read-only Pantry FEFO, immutable `0043` Shopping snapshots, V2 replay/provenance and fail-closed public V1a-only reads.
- #294's diagnostic readback independently reconciles source plan events, member-selection pins, legacy Servings and complete component/rule snapshots against the persisted `MealPlanDetail`. **This is data-integrity evidence, not evidence of physiological appropriateness or storage safety.**
- The [MealPlan contract](mealplan-multicourse-persistence-implementation-contract-2026-11-16.md) explicitly leaves recipe-to-course suitability, physical-portion feasibility, full Nutrition, consumer editing and production admission open. The three-course demonstration uses a prototype structure rule, not a published suitability/portion policy.
- The [portion feasibility proposal](planner-serving-plausibility-contract-2026-10-17.md) distinguishes energy-based scaling from verified **final edible output mass/form** and an applicable reviewed portion policy; it does not authorize universal numeric Serving limits.
- PR10 permits a **non-executable** pure diagnostic foundation. Executable actions, reviewed Step eligibility/D3, safe batch stock and source-backed holding/storage remain independently gated; `APPROVED_IMMEDIATE=0`, `SAFE_BATCH_READY=false` and `PORTION_RELEASE_READY=NOT_PROVEN` are not overturned by Shopping correctness.

### ASSUMPTION TO VERIFY

One complete, immutable composed-week source package **might** eventually support consumer admission if each actual recipe/course/member combination has independently reviewed source, role/coverage, physical and Nutrition evidence, and all downstream public lifecycle semantics are explicitly contracted. Existing synthetic structural/Shopping proofs do not establish those predicates.

### PROPOSED DECISION FOR REVIEW

**Next bounded operation:** create a **read-only source/role/physical evidence inventory for one actual seven-day composed DRAFT**, including one composed event and all at-home member allocations, without editing any canonical data. Evaluate the four independent readiness axes below. Record explicit `PROVEN / UNKNOWN / CONTRADICTED / NOT_APPLICABLE` **as audit labels only** (not new enums, persisted fields or service behavior). A missing required proof is `NO_GO` for consumer admission, not a substitute candidate, a zero quantity or permission to reinterpret an old dataset.

The inventory is an evidence artifact; any later runtime source validator/admission command requires a separate reviewed Implementation Contract Gate with exact preservation/replay/conflict semantics.

### OPEN — no decisions assumed

- Which **published**, source/rights-reviewed RecipeVersions are actually suitable for each proposed FIRST/SECOND/DESSERT role and for the members' meal roles, ages and exclusions?
- Which source records explicitly establish **final edible mass, output form, source/base-serving equivalence and batch-scale applicability** for each component and the intended exact member quantity?
- Which versioned, applicable **physical-portion/meal-combination policy** has independent authority? What must remain unsupported if none exists?
- Can the existing deterministic Nutrition pipeline calculate **complete** per-member multi-component energy/nutrient facts at the same immutable plan revision without inventing missing nutrients?
- Which explicit consumer activation API, stale/revision rule, Pantry/prepared-supply contract and rollback boundary would be required? These are **future contract decisions**, not defaults in this document.

## 3. Read-only evidence matrix for the next operation

| Axis | Facts to pin and independently check | If evidence is absent or inconsistent |
| --- | --- | --- |
| A. Source and rights | Actual MealPlan revision, member/selection pins, all course RecipeVersion IDs, source hash/version, active verification/rights status, complete RecipeIngredients, mandatory/optional input decisions and applicable allergen/exclusion review | `UNKNOWN` or `CONTRADICTED`; **no source eligibility**, no mutation or re-selection of an unreviewed recipe |
| B. Role and structure | Event MealRole vs RecipeVersion classification (not the same enum); full immutable rule coverage/version/ordered requirements and SHA; exact component order, kind and each attending member's allocations; authoritative course-suitability evidence and documented dessert optionality | Structural validator PASS is **not** role suitability PASS; no automatically approved multi-course menu |
| C. Individual physical feasibility | Each component's exact Decimal Serving factor; reviewed final edible output mass **in the same form and scaling basis**, cooking yield where source-authorized, total planned mass per actual member, an applicable reviewed feasibility profile and any contradictory physical/source constraints | `UNKNOWN`/unsupported; no invented default mass, universal cap, implicit split of a member's kcal or silent Serving clip |
| D. Nutrition and downstream authority | Source-pinned complete Nutrition per component/member and plan-wide coverage; hard exclusions; exact Shopping V2 provenance/replay and explicit `price_status=UNKNOWN`; Pantry read-only vs actual supply; revision/stale handling; absence of executable Prep authority | Grocery `COMPLETE` alone **cannot** close Nutrition, Pantry supply, physical, Prep or consumer admission gates |

The inventory must identify the **origin of every positive claim** (repository record/version, primary source or accepted reviewed policy), reviewer/date, applicable member/course and version, conflicts and missing information. User records must remain synthetic or appropriately non-sensitive; no personal health profiles in Git history. Source-identity equality is necessary but not sufficient for source suitability.

## 4. Admission order and fail-closed rules

1. **Source identity:** reread the same Household-scoped, immutable seven-day `MealPlanDetail`; compare all source, member and recipe pins to the diagnostic V2 evidence. A corrupted, missing or changed revision blocks assessment.
2. **Per-component eligibility:** verify the exact pinned published RecipeVersion, rights/validation, canonical ingredient units/forms and each actual participant's hard exclusions. A review status on a *different* recipe version does not transfer.
3. **Course/meal-role suitability:** apply an independently reviewed, versioned, explicitly scoped suitability rule; never infer FIRST/SECOND/DESSERT suitability from recipe display name, `meal_type_code`, prototype structural `RequiredCourseCoverage` or a general MealRole alone.
4. **Physical serving:** require applicable reviewed final-food form/mass and individual policy; report `UNKNOWN` if absent, regardless of energy/Shopping arithmetic. Source raw ingredient mass is not final cooked edible mass. Multi-course portions must be evaluated **per member and together**, without automatically reallocating calories.
5. **Nutrition completeness:** require deterministic aggregation of the actual member-component source with a verified nutrient profile and explicit partial/unknown semantics; do not mark the week nutritionally complete because a subset has energy data.
6. **Downstream lifecycle:** only after axes A–D have positive reviewed evidence may a **future separate** consumer-activation contract propose write/read, stale/history/replan, availability, use/Prep and rollback semantics. Public Shopping V1a continues to isolate diagnostics until that future approved contract is implemented.
7. **PR10 and release:** source-reviewed same-day actions, D3 live eligibility, technical Gate2 positive/negative fixture, and later safe-cooked-batch/physical release are separate non-negotiable approvals. Neither this assessment nor Shopping V2 substitutes for them.

**NO_GO remains the default** if any required axis is missing. An `INCOMPLETE` grocery list may truthfully coexist with more fundamental `NO_GO` for family admission; a `COMPLETE` grocery list is only a completed **grocery** calculation.

## 5. Preservation, transaction and rollback matrix

| Surface | This docs-only PR | Later runtime gate must preserve |
| --- | --- | --- |
| `0043` Shopping, `0044` MealPlan | No new schema/migration/SQL writes | All historical V1a/V2 immutable identities, order, fingerprint and Household scope; no fake parent Serving |
| `shopping-v1a` and public endpoints | No public exposure or projector change | Legacy generation/current/history/stale semantics, V1a response shape and diagnostic 404/409/503 isolation |
| `shopping-v1b-composition` | Still test/dev only | Exact Decimal per-component and aggregate math; V2 source/content and SQL-row readback; Pantry FEFO snapshot, never stock mutation |
| Planner/Serving/Nutrition | No scoring, Serving, energy-share or policy change | Historical replan/source provenance and hard exclusion; complete per-member semantics only with independently accepted data |
| Prep/Inventory/PDF/UI | No tasks, confirmed batches, stock, PDF or consumer feature | Proposed versus executed; safe source/Step/storage authority; no quantity/pricing/pantry readiness invented |
| Data/AI/Retail/shared deployment | No source publication, web parsing, AI activation, SKU or tenancy work | Existing `AI_ENABLED=false`, source rights, canonical FoodIngredient and future gates |

**Rollback for this PR:** documentation change only, revert the docs/state commits if review rejects it. **No persistent snapshot is rewritten.**

**Future runtime transaction preconditions:** any activation write/revision needs an explicit owning UoW, source/read consistency, idempotency/replay, optimistic conflict/stale semantics, fault rollback and exact Household authorization. A change in `0043`/`0044`, cross-context identity or new source policy must reopen a **new docs-only implementation gate** rather than silently extending this preflight.

## 6. Adversarial review and future acceptance evidence

The immediate **read-only inventory** must include, without modifying production truth:

1. **Positive control:** source-backed seven-day composed diagnostic revision with real pinned components, member/course/Serving mapping and valid Shopping V2 replay; report only the axes actually reviewed. If positive role/physical/Nutrition evidence does not exist, output is **NO_GO**, not an invented PASS.
2. **Source negatives:** wrong/revoked RecipeVersion, missing rights or allergen review, incompatible FoodIngredient/form/unit, duplicate/missing component, missing member Serving, mismatched rule snapshot. Existing strict source and Shopping replay failures stay observable.
3. **Role negatives:** a structurally valid first/second/dessert composition with no applicable **reviewed** suitability policy; conflicting requirement versus one member's actual meal opportunity; missing/unknown course coverage. Do not treat `PER_PARTICIPANT` structure as nutritional or medical proof.
4. **Physical negatives:** source mass missing/ambiguous raw-versus-final, mismatched source/base-serving denominator, unreviewed portion policy, implausible large energy-derived factors, lack of cookware/storage applicability. Do not introduce an arbitrary number to make a test PASS.
5. **Nutrition/downstream negatives:** energy-only source without full profile; missing member nutrient; legitimate non-recipe obligations; stale revision; unknown price/Pantry/water supply; Shopping V2 present but public V1 APIs must continue to withhold it.
6. **Source authority replay:** altered V2 JSON with recomputed fingerprints must still be rejected against immutable source; preserving the #294 negative-test family is mandatory when a later reader changes.
7. **Non-mutation:** all findings are reproducible from immutable read-only snapshots; no updates to MealPlan, Serving, RecipeVersion, Nutrition, Shopping, Pantry or source release statuses.

Each future case needs traceable evidence and exact checked revision. **Do not add positive test fixtures by fabricating reviewed external mass, meal suitability, source rights or food-safety policy.**

## 7. Verification tier and decision requested

**This PR:** docs/state-only tier from [verification policy](verification-policy.md): inspect exact links, scope/status consistency, whitespace and docs CI. No backend regression is claimed or required for byte-identical runtime.

**After independent review:** owner may accept this **read-only evidence-inventory scope** as the next separate bounded task. Runtime work, authoritative catalogue change, activation, PR10-A2/B/C or technical/consumer Gate2 are **not authorized by this PR**.

**Reviewer challenge questions:** Are the four axes independent and complete? Does any “positive” demand secretly borrow current diagnostic/energy-only evidence? Does this preflight accidentally define a physical norm, medical policy, public schema or source publisher without approval? Is the proposed follow-up truly read-only and auditably fail-closed?

**Required disposition:** `APPROVE AS ASSESSMENT PLAN` or `REQUEST CHANGES`, with any new authoritative data/model/release decision referred explicitly to the owner. Until a reviewed later decision changes it, the effective conclusion is **NO_GO_TO_CONSUMER_COMPOSED_MEALS**.
