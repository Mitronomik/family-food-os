# Planner Serving Plausibility — source-backed feasibility contract proposal

**Status:** **PROPOSED / docs-only / awaiting owner decision and independent review**. No change to accepted Planner/Nutrition/Gate1/Gate2 runtime, schema, catalogue or release criteria takes effect from drafting this document. Merge of the proposal records a review decision **only if the owner explicitly accepts the proposed option and evidence prerequisites**. Until then, Planner behavior remains governed by its existing accepted versions and historical plans.

**Issue:** [#228](https://github.com/Mitronomik/family-food-os/issues/228). **Parent audit:** [#225](https://github.com/Mitronomik/family-food-os/issues/225).
**Accepted base:** `main@65c3aaeee8376a14a80af29c1a0fc6d0b5145c5b` ([#227](https://github.com/Mitronomik/family-food-os/pull/227) merged 2026-10-17).
**Read with:** [Operating Manual](project-operating-manual.md) §23, [Product Strategy](product-strategy.md), [Planner v0](planner-v0.md), [Planner Energy Allocation](planner-energy-allocation-contract.md), [Nutrition Core](nutrition-core.md), [MealPlan / Serving](pr7-mealplan-serving.md), [Recipe Nutrition V2 integration](recipe-v2-nutrition-planner-integration-contract.md), [Master Roadmap](master-roadmap.md) and [Finished-Dish-First](pr10-finished-dish-first-amendment-2026-10-12.md). The root `AGENTS.md` and state gates still apply.

## 1. Product goal and observed defect

A generated week must be **physically believable and usable**, not only mathematically energy-normalized. An energy-poor recipe must not be amplified to an impractically large finished-food serving merely to match a person's allocated energy for that meal.

**FACT — current code (`main@65c3aaee`):**

- `PlannerService.compose_authoritative_request()` builds an exhaustive, source-pinned active catalogue after #227, producing `PlannerCandidate` with recipe UUID, meal classification, FoodIngredient IDs, `kcal_per_serving`, nutrition status/readiness, cooking minutes and batch flag. It **does not carry a verified finished-food output mass or portion feasibility profile**.
- In `backend/app/domain/planner.py`, `generate_week()` scores candidates at ~692–759 by compatibility, preference, Pantry overlap, batch, cooking time and repetition, **before** individual portion calculations at ~816–855:
  `allocated_kcal = member_reference_energy_kcal × accepted_opportunity.energy_share`;
  `portion_servings = allocated_kcal ÷ recipe_kcal_per_base_serving`.
- The v0.4/v0.5 energy-share policy is stored in accepted `MemberMealPatternSelection` and intentionally may cover **less than an entire day**. `planner-v0.3` has an older distinct weekly factor, which must remain replayable; it cannot silently acquire a new constraint.
- `RecipeVersion.base_servings` is a recipe **scaling denominator**, not a universal physiologically suitable amount. The optional `RecipeVersion.source_output_g` is source output mass **only when its source form, original base and quality are independently verified**. It is not always present, and one source output does not itself prove that a multi-serving batch scales linearly or that a particular member should consume it.
- A `Serving.portion_servings` is an exact positive `Decimal` amount; existing Nutrition, Shopping and later Prep scale authoritative ingredient demand from it. Naively clipping a portion would change all those outputs and energy accounting.
- [#227](https://github.com/Mitronomik/family-food-os/pull/227) fixed the former 200-recipe cap and isolated unavailable Recipe/Nutrition authority. This proposal **must not undo that fix**.

**FACT — current product authority:** the [Operating Manual](project-operating-manual.md) requires reasonable portions; the [Product Strategy](product-strategy.md) requires individualized Servings; [Planner Energy Allocation](planner-energy-allocation-contract.md) forbids inventing or redistributing a person's allocated kcal to compensate for partial-at-home coverage.

**ASSUMPTION to test:** a source-reviewed combination of final dish mass/form, context-relevant portion bounds or user-confirmed portion preferences, and exact member MealPattern energy allocation can reject clearly implausible single-dish candidates *before* selection without arbitrary universal serving multipliers. This is not proven for the entire current catalogue.

## 2. External research: serving label != recommended meal

External primary-source **context**, not an accepted FamilyFoodOS numeric policy:

1. [NIDDK — Food Portions: Choosing Just Enough for You](https://www.niddk.nih.gov/health-information/weight-management/just-enough-food-portions) explicitly distinguishes a person's **portion** from the **serving size** on a food label. A standardized serving label is not inherently the recommended amount for that person. It also describes varying individual needs and practical portions.
2. [Роспотребнадзор — Советы по здоровому питанию](https://zpp.rospotrebnadzor.ru/advices/57827) gives illustrative *food-group-specific conditional servings* and activity-dependent daily patterns; e.g. the reference quantity of one food group is **not** a universal maximal mass of a whole cooked recipe.
3. [USDA Food Buying Guide for Child Nutrition Programs](https://foodbuyingguide.fns.usda.gov/Home/About) differentiates a planned serving size, required number of servings, as-purchased form and meal-component contribution. Its institutional programme thresholds are not automatically family/RecipeVersion/age-group policy.

**DECISION PROPOSED:** none of these materials alone authorizes hardcoding `max_portion_g`, `max_base_servings`, `minimum_kcal_per_serving` or one adult/child mass range. An external table becomes executable only through a versioned, scoped, independently reviewed FamilyFoodOS source/rights/applicability decision. Quantities supplied as examples in future tests must be explicitly *synthetic test inputs*, never presented as nutritional norms.

## 3. Proposed truth model and evidence boundaries

A portion's *energy feasibility* and its *physical plausibility* are different calculations:

```text
HouseholdMember accepted target + MealPatternSelection energy_share
     ↓  exact Decimal kcal allocated to this opportunity
RecipeVersion verified nutrition kcal/base serving
     ↓  hypothetical Decimal portion_servings
RecipeVersion source-reviewed final edible dish output / source base
+ reviewed applicability of batch scale, resulting form and capacity
+ applicable reviewed individual/context portion policy OR explicit
  Household-owned, user-confirmed portion-size preference (not medical advice)
     ↓
PASS / OUT_OF_BOUNDS / UNKNOWN_SOURCE_OR_POLICY / UNSUPPORTED_PERSON
     ↓  only PASS can substantiate a claim of plausible portion
candidate subset/group selection and trace
```

### Source-owned facts (not computed by LLM)

- Recipe identity: immutable `RecipeVersion.id`, `base_servings`, `source_original_servings`, `source_output_g` (optional), source document/card hash, source output *form* and state (cooked final dish vs raw/net input vs individual component).
- Nutrition: existing authoritative `kcal_per_base_serving`, `exact_energy_ready`, nutrient provenance and original food form. Never reconstruct cooked yield or calories from macros/ingredient names.
- Portion-policy input (future **conceptual** `PortionFeasibilityProfile`): versioned authority for applicable member age/context (if relevant), meal role, dish/output form/category, explicit valid edible-mass or number-of-portions interval, original external reference, review rationale, curator, revision and expiry/review status. **No such profile is currently accepted by this proposal.**
- A Household-owned explicit typical portion preference, where available, is a **user preference** (may be upper/lower bound on wanted quantity), not a claimed nutrition/medical suitability norm; it cannot override hard exclusions or safety data and must be versioned if used by automatic Planner generation.
- Batch scale feasibility, cooking vessel, food handling/hold safety and storage are **separate source-/policy-reviewed constraints**, owned by the recipe/prep policy. A feasible *individual amount* does not automatically prove that a combined 4-person batch can be executed safely.
- `UNKNOWN` is distinct from explicit, reviewed *out of bounds*. A missing final cooked yield or missing valid person-specific profile must never be replaced by `0 g`, a universal maximum, gross-to-net ratio, cooking-loss guess or a numeric warning labeled `SAFE`.

### Candidate feasibility math (conditional, not an accepted runtime formula yet)

Only when the source explicitly establishes that `source_output_g` is **final edible output for the same `base_servings` basis**, and validates applicability to target recipe scale, may a proposed Serving's mass be evaluated as:

```text
allocated_kcal = reference_energy × accepted_energy_share
portion_servings = allocated_kcal / authoritative_kcal_per_base_serving
estimated_planned_edible_mass_g
  = portion_servings × validated_final_output_mass_g_per_base_serving
```

The word **planned** matters: this is a **source-validated projection** if permitted by evidence, *not* the actual cooked output of a household. The source's `source_output_g` must **not** be assumed to map to current `base_servings` where published source bases differ. In particular, do not use sum of raw ingredient grams as finished food mass. All arithmetic is deterministic Decimal with the existing precision policy; no float or silent post-hoc rounding change.

**Proposed evaluated status per (event, candidate, member):**

| Code (proposed) | Meaning | Allowed consequence |
| --- | --- | --- |
| `PASS_REVIEWED_FEASIBILITY` | All required versioned sources and relevant bounds apply, computed Serving within bounds | Candidate is physically admissible for that member; still subject to existing exclusions, energy, cost and repeat filters |
| `REJECT_REVIEWED_PORTION_BOUNDS` | Applicable reviewed bound proves proposed Serving too small/large | Member excluded from candidate **before candidate selection**; trace identifies exact pinned policy and reason |
| `UNKNOWN_OUTPUT_OR_PORTION_POLICY` | Final edible output, actual source relation, candidate batch applicability or reviewed bounds missing/stale | Not a PASS; never claim physical realism. Next runtime must have a specifically accepted fail-closed or diagnostic-only handling mode |
| `UNSUPPORTED_MEMBER_CONTEXT` | Age/physiology/meal-role needed by a reviewed policy is unavailable/unsupported | No default adult bound, no inferred child bound, no medical substitution; early explicit unsupported evidence |

The current `MISSING_REFERENCE_ENERGY` failure is **not** changed by these codes. Incomplete Household profiles and age-under-3 cases need their own separately approved [Issue #225](https://github.com/Mitronomik/family-food-os/issues/225) decision. No `reference_energy_kcal` or `energy_share` fallback is authorized.

## 4. Candidate-selection and incomplete-week contract (proposed)

**Order after a future reviewed version increment:** source/role/recipe availability → all hard food exclusions → exact energy & accepted allocation → **member-specific physical feasibility** → shared compatible subset → deterministic scoring/repetition → trace → atomic MealPlan revision only for complete success.

1. Evaluate feasibility **for each member's actual opportunity** *before* committing an event choice, not after the shared recipe has been selected. Sharedness never overrides member exclusions or reviewed bounds.
2. It is possible for the same recipe to be feasible for one member but not another. Reconcile subsets by existing deterministic group/split logic; validate every chosen member's amount. An infeasible member must not be silently given the shared recipe or removed from the household plan.
3. A candidate with missing output/policy evidence cannot be promoted to `PASS` by high preference score or Pantry overlap. Preserve the reason in explainable generation evidence without misrepresenting the exact source as failed if **only** the policy is unknown.
4. When no physically supported recipe can satisfy all planned opportunities, return an explicit **bounded failure** identifying missing accepted source proof or checked infeasible cases. **No partial MealPlan write**, no opaque retry/LLM substitution and no auto-lowered calories.
5. Preserve the pinned opportunity's `allocated_kcal`. Never truncate an oversized portion to the upper bound while retaining the original kcal claim, never redistribute unfilled energy to other events or invent a second side dish/ready meal merely to make this single-recipe Planner succeed.
6. Changes to Planner scoring/selectability or new trace/failure values require a **new `planner-vX`** and persistence/trace compatibility review. Historical `planner-v0.3/v0.4/v0.5` traces/plans must be reproducible and unmodified.
7. Explicit plan-vs-execution boundary: no candidate profile implies cooked stock, same-recipe batch safety, a freezer guarantee or physical operations saving. [FD-ARCH](pr10-finished-dish-first-amendment-2026-10-12.md) and D3 still control those claims.

### Pending owner choice — no silent policy shortcut

**Option A (recommended for a future consumer-ready plan):** strict source-backed `PASS` is required for every recipe-based member Serving; `UNKNOWN` produces bounded `INSUFFICIENT_PORTION_EVIDENCE` / incomplete generation until the relevant policy data are reviewed.

**Option B (only if separately approved):** permit a *diagnostic-only provisional plan* showing `UNKNOWN` or `OUT_OF_BOUNDS` and explaining why it is not release-ready; do **not** allow that provisional result to masquerade as an accepted MealPlan revision or to become authoritative Shopping/Prep demand.

Both options require a revised accepted contract, a data readiness demonstration and versioning. This document **recommends A** but does not decide the consumer UX or switch current Planner behavior.

## 5. Source and policy data readiness gate **before** runtime

Before introducing any new `PlannerCandidate` field, hard mass limit or acceptance gate, audit an **explicit bounded cohort**:

- Pin the **current verified RecipeVersions** actually candidate-eligible for an accepted multi-member Gate1-like week (selected source/version/nutrition/review/rights, with output form/basis).
- For each, record: `source_output_g` known/unknown, source original vs current base servings relation, source output final cooked vs other form, validated linearity/batch applicability vs unknown, meal role, published rights and policy applicability. Distinguish **catalogue presence** from evidence sufficient to make an executable bound.
- For each intended household member/context and opportunity, record available authoritative or user-confirmed **applicable portion evidence**, not simply a number in a demo script. Identify any unsupported child/age/sex/activity combinations honestly.
- For at least **one** realistic pinned household/recipe/event scenario, show exact Decimal energy → Serving → supported cooked-output mass → bounds evaluation and a safe negative control. If no source-approved feasibility policy exists, classify the gate **NO_GO**, not `PASS` or a fallback.
- Keep the historical Gate1/Gate2 accepted test corpus and past MealPlans byte-identical. Research-only synthetic inputs are allowed **only** as clearly marked negative/probe fixtures and never establish production authority.

**Stop rule:** if no verified form/bounds combination exists, return a compact evidence gap to the owner. **Do not** open an indefinite sequence of arbitrary portion-threshold PRs or silently mark catalogue as consumer-ready. Source acquisition/curation and policy publication ownership must be separately approved before implementation.

## 6. Proposed later implementation boundaries (NOT authorized now)

| Layer | Possible bounded future change | Gate / cannot silently assume |
| --- | --- | --- |
| Research/Data | One accepted portion-feasibility source/policy payload, reviewed applicability and form/yield mapping, machine provenance | Separate curation decision; rights/language/quality, source pin, negative evidence |
| Recipe/metadata read | Add a strictly versioned final-edible-output/policy read to application composition; no derived hidden kcal/mass | **Docs-only Implementation Contract Gate required** before new authoritative publication/read path (D3 or context-specific owner), persisted identity or migration |
| Domain Planner | New versioned candidate member-feasibility evaluator applied before selection; positive/negative/UNKNOWN outcomes with deterministic explanation | Reviewed algorithm/trace/compatibility contract and unit tests; don't change v0.3/v0.4/v0.5 silently |
| Application Planner | Compose candidate from current accepted Recipe/Nutrition/Household/MealPattern and reviewed feasibility policy; reject stale or mismatched authority | Household scope, source revisions; source-snapshot integration requires separate contract |
| Persistence / migration | Only if truly needed for a new source/policy identity, member preference history or Planner trace | Preserve old versions; separate migration/fresh/replay/rollback preflight |
| API/consumer | Event/member-specific Russian message showing `невозможно подтвердить размер порции`, user confirmation where genuinely allowed | No product-facing false `норма` or medical claim; PWA after Gate2 |
| Shopping/Prep | Scale from **accepted exact Serving** once; aggregate without duplicate shopping, no Pantry mutation, batch execution still separately gated | Do not accept an UNKNOWN/diagnostic plan as authoritative demand; preserve staleness and FD-ARCH |

**Tests for later implementation:** one fixed-pinned low-energy recipe requiring implausibly large output (using **synthetic, explicitly reviewed test-only policy bounds**); high-energy tiny serving; correct under-bound case; raw vs cooked mismatch; source output unknown; source base mismatch; stale policy/version; mass conversion not source-authorized; member A fits/member B does not; hard allergen exclusion; high Pantry score cannot override rejection; heterogeneous meal patterns and duplicate meal roles; fixed `EAT_OUT` remains outside the recipe energy allocation; all candidates unsupported -> bounded failure/no write; repeated deterministic trace/fingerprint; old Planner version replay; source/MealPlan change marks derived Shopping stale; no inferred freezer safety.

## 7. Acceptance matrix and risks

**FACT:** accepted reference energy is Nutrition-owned; MealPattern share is policy/Household accepted state; source output mass may be incomplete.
**ASSUMPTION:** a bounded curated cohort can produce an executable, truthful member-context portion policy.
**DECISION PROPOSED:** choose Option A first; require per-member preselection feasibility, independent source and policy provenance, no hidden calorie clipping, explicit unsupported states.
**OPEN:** source owner, final-edible form coverage, age/context applicability, whether a user-confirmed range alone is sufficient for a UX preference (but never physiological validation), data storage and policy revision identity, how to represent diagnostic-only results, and the separate incomplete-member profile P1 decision.

**This PR's acceptance:** docs-only diff; accurate current references; no hardcoded universal grams/kcal/recipe multiplier, no acceptance/roadmap switch, no source-data or runtime change; reviews must challenge data sparsity, multi-member sharedness, Planner trace and MealPattern compatibility, history preservation and the distinction between *food preference* and *medical/physiological norm*. Source URLs are research context, not automatic regulatory claims. Run Docs CI on exact PR HEAD and stop for independent owner review.

**Next authorized only after owner acceptance:** one **bounded data-readiness receipt** for selected MealPlan/RecipeVersion/Household evidence. This docs-only proposal does **not** authorize Planner runtime, new tables or nutrition defaults. Incomplete profiles and under-3 support remain tracked separately in [#225](https://github.com/Mitronomik/family-food-os/issues/225). Finished-dish storage metadata remain `PR10-FD-META=BLOCKED / TIME_UNRESOLVED`.
