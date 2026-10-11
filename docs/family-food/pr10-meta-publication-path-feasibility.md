# PR10-META-PUBLICATION — immutable recipe-stage authority feasibility gate

**Status:** `BLOCKED_RECIPE_STAGE_PUBLICATION_AND_SHARED_COMPONENT_AUTHORITY` (docs-only **proposed decision**; not accepted as product authority until independent review/merge).
**Accepted main:** `506e4c9f6f493bf2c91ce698a2d6c2eee0a413cb`, merged PR #204, 2026-10-11.
**Issue:** #205.
**Owning contracts:** [accepted PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-META BLOCKED receipt](pr10-meta-readiness-decision.md), [PR #204 stage-source preflight](pr10-meta-reviewed-stage-authority.md), [DATA-CORPUS-V1](data-corpus-v1.md).
**Machine-readable receipt:** [publication-path feasibility matrix](pr10-meta-publication-path-feasibility.json).

This operation closes the **publication-path feasibility question**, not the PR10-META product gate. The real bottleneck is not whether JSON can be written to a repository, but whether a verified *source-backed cross-recipe executable stage* is represented, read and versioned through the accepted core while preserving immutable recipe/MealPlan and nutrition truth.

## 1. FACT — production publication interfaces and boundaries

Inspected the current accepted `main` interfaces:

| Existing owner | Exact current capability | Important absence |
| --- | --- | --- |
| [Recipe catalogue domain](../../backend/app/domain/food_recipes.py) | `RecipeVersion` stores immutable/versioned source identity, verified provenance and ingredient/step detail; `RecipeStep(id, recipe_version_id, position, instruction, stage_code, created_at)` | No typed `input_form`, `output_form`, `shared_component_identity`, process-stage batch compatibility, hold/safety evidence or explicit per-stage quantity allocation |
| [FoodRecipeCatalogueService](../../backend/app/services/food_recipes.py) | `append_trusted_version` and `append_trusted_version_in_scope` append a new version with `created_from_version_id` and monotonically advancing `version_number` inside UoW | An append-only **per-recipe** version does not create any source-backed **cross-recipe** shared-stage identity |
| [R3-D recipe seed publisher](../../backend/app/seed/r3d_final_dc3_batch.py) | `_recipe_seed` takes reviewed `consumer_steps_ru`, sets `TrustedRecipeVersionSeed.steps` to the source-reviewed tuple, and preserves card/document authority | No structured shared-stage/hold publisher, no separately queried PrepStage repository; R3-D currently sets batch/freezer/storage fields to null |
| [PR10-ARCH](pr10-prep-freezer-implementation-contract.md) | Exactly three planned Prep tables and optional reviewed `PrepTask.shared_work_group_key` | This key needs independently approved compatible staged-process truth **before** grouping; it is not permission to infer provenance from strings |

**Feasibility conclusion:** immutable *recipe text correction* through the existing append API is technically available. A `ReviewedPrepStageBindingV1` JSON/curation receipt, however, has **no currently accepted production retrieval, version validation, household-scoped consumption or source-fingerprint integration**. Adding a sidecar JSON under `docs/` or `data/curation/` is valuable as audit evidence but **cannot silently become authoritative Prep runtime data**. There is no justification for a fourth Prep table or migration in this docs-only operation.

## 2. FACT — source completeness for the exact Tuesday fixture pair

The accepted synthetic three-member fixture from PR #196, pinned by [PR #202 evidence](pr10-meta-same-day-pair-evidence.json), contains on Tuesday **2026-09-15**:

| Frozen truth | Lunch: beef/vegetable ragout | Dinner: potato split-pea soup |
| --- | --- | --- |
| MealEvent | `cf0e3fe3-4c59-4447-9fbd-7a9e19c6ff49` | `d000a213-d169-4f10-a2ad-08180f40aea6` |
| RecipeVersion | `063694fb-92cf-4731-adf6-041d36a532e4` | `116e25fa-12f3-4926-8a2a-7aa2cf99bb9c` |
| Published source step 2 SHA256 | `55519c2f9e26fbb12ea8abd237547f58d94361f17deff6005919d7a86c7ad128` | `a75d7d9fa0b0a77ab6eefd8a7b357c522dfc750662db99126efe89ea4447d850` |
| R3-D reviewed source card SHA256 | `89ef921166ece243277dc3f1106e340769f3a99a89195ff10028bd78f529a295` | `f4d70b7eb24de3fc10fd239ad6dcb2d7047c8e458541a0a1f8d6e15256ee8731` |
| Original source process | Prepared onion/carrot, finely chop, poach with water and butter | Vegetable **sort/peel/wash** in source preamble, then dish-specific potato, pea, carrot/onion processing |
| Present published RecipeStep | Fine chop onion/carrot and poach | “Prepare carrot/onion and poach”; no separately published source-pinned preamble |
| Independent source-backed `RAW_WASH_PEEL` stage for these exact vegetables | **NOT DEMONSTRATED** | **Explicit original generic vegetable preamble; precise ingredient-to-stage scope still requires review** |

Primary source cards: [МР 2.4.0162-19, № 2.11](https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/miasnye-bliuda/tekhnologicheskaia-karta-n-2.11/) and [№ 1.16](https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/supy/tekhnologicheskaia-karta-n-1.16/). Original source context is educational/special-diet meal preparation, already reviewed for **bounded factual recipe publication**, not a household cross-recipe batch-stage approval. Current frozen R3-D source data: [reviewed batch](../../data/curation/r3d-final-dc3-batch-gate/frozen-batch.json), including raw source document SHA256 `973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e`.

**Consequence:** even if the soup's source-supported vegetable preamble could be split into an independently reviewed Russian RecipeStep and published as **a new immutable version**, the ragout's source **does not independently identify an identical wash/peel operation with a verified input/output form**. Importing the soup preamble as authoritative ragout instructions would manufacture source evidence. Re-publishing one recipe does not meet the contract requiring one safe shared operation across **two actual MealEvents**.

The soup preamble also speaks of *vegetables* broadly; it does not assign step-level quantities or clarify source net-vs-raw cleaning/peeling loss. No source-backed yield, combined raw mass or quantization may be reconstructed from this text. Ingredient totals must stay in the authoritative `RecipeIngredient + Decimal Serving` path.

## 3. Proposed publication-path decision matrix — CHALLENGE BEFORE APPROVAL

| Option | What the current platform proves | Proposed disposition | Reconsideration trigger |
| --- | --- | --- | --- |
| **A. Immutable source-stage sidecar receipt** in repo | Can preserve provenance, original card SHA, reviewer notes and a typed proposed stage record | **Evidence-only; NOT runtime authority.** Current RecipeCatalogue/MealPlan services expose no accepted source-stage reader/version/fingerprint boundary | Independently accepted docs-only implementation contract for source owner, lifecycle, read path, idempotence, conflict/staleness, data/access isolation and policy/version fingerprints |
| **B. Append immutable RecipeVersion with revised source-backed steps** | Existing `append_trusted_version*` supports non-destructive new version history; original steps and source IDs stay untouched | **CONDITIONALLY viable for an actually documented process correction** (soup after stage/numeric/source review); cannot publish the ragout's missing wash/peel fact or authorize grouping | Source evidence for each distinct RecipeVersion; rights, Russian instructions, form and quantity treatment, nutrition/yield continuity and explicit source-approved step correction |
| **C. Versioned cross-recipe shared-component/stage authority** | Required by PR10-ARCH to allow the same non-null `shared_work_group_key` | **NOT PRESENT / NOT AUTHORIZED**; do not assume `RecipeStep.stage_code` can stand in for it | New separately reviewed pre-implementation contract if product evidence supports it: owner, data publication, retrieval, version pins/invalidations and any migration review; preserve three Prep tables |

**Proposed decision:** **do not choose an under-specified sidecar as the runtime system of record**; do not append fabricated ragout steps simply to pass PR10-META. Option B is the existing **mechanical recipe correction** path but is not, by itself, the approved full shared-stage publishing architecture. Option C is a potential **future authority contract**, not an automatic fourth table. Nothing here approves A/B/C implementation or changes a previously accepted architecture decision. Independent review must accept any consequential new publication boundary.

## 4. Contract for a future bounded immutable recipe-process publication (IF evidence becomes sufficient)

A future narrow DATA/recipe publication PR, **separately reviewed and authorized**, must freeze:

1. **Provenance identity:** exact R3-D source card, original document/row sha256 and rights basis, immutable source recipe identity, old RecipeVersion/RecipeStep identifiers and instruction/process SHA; approved reviewer and Russian rendering of every newly actionable instruction. Source card identity is not permission to borrow missing instructions from an adjacent recipe.
2. **Publication identity:** current existing RecipeVersion and `created_from_version_id`, next immutable `version_number`, new RecipeStep IDs/positions/text hashes, duplicate/replay/conflict behavior and exact fresh/upgrade/rollback transaction receipt. Do not update old version/step bytes in place or silently replace MealPlan version pins.
3. **Composition/nutrition invariants:** source-recognized FoodIngredient identities and raw/net state, unchanged authoritative ingredient totals, `base_servings`, source output mass, source-reviewed prepared-output nutrient calculation. No new numerical step instructions contradicted by Decimal serving scaling. An unknown prep yield remains UNKNOWN; never equate raw wash loss with net ingredient mass without evidence.
4. **Downstream compatibility:** existing pinned MealPlans remain legible/immutable and any Planner regenerate/replan explicitly selects new accepted versions; derived Shopping/Prep/PDF must use pinned source version and stale/revision rules. A new recipe version does not automatically rewrite prior MealEvent records. Exact fixture recipe/version/process hashes must be re-pinned and audited before a new positive Gate2 reuse claim.
5. **Source-correction acceptance:** Russian instructions, exact numeric-step classifications, source cards reviewed separately for each recipe, one verified intermediate output form and stage linkage per recipe, no unsafe borrowing of original card text, explicit non-approved hold/freezer states.
6. **Release value acceptance:** same actual two-event pair, source-backed operation and compatible food state, reviewed same-session or storage transition, exact per-member contributions and true **B less than A** physical operation count including splitting, equipment cleaning, additional holding/retrieval. No fabricated time savings or extra calories/cost.

**Stop rule:** if step curation requires a new durable shared-component identity or source adapter instead of plain RecipeStep correction, stop for a new docs-only implementation/source-authority contract. A migration number is **not reserved** by this research. No edit to previously accepted PR10 three-table schema is implied.

## 5. Adversarial release matrix and recovery decision

| Reviewer probe | Required result |
| --- | --- |
| Only soup source explicitly describes `SORT_PEEL_WASH`, ragout still vague | **BLOCKED** for this pair; must not accept a shared binding |
| Same FoodIngredient code but cut, raw/net form or post-prep state differs | **BLOCKED**; do not merge by ingredient name |
| Reviewed step hash changes, source card changes, or current RecipeVersion superseded | Re-review, invalidate binding and fresh source fingerprint |
| Batch quantity changes but source step includes fixed piece count, fixed temperature or ambiguous numeric | `STEP_QUANTITY_REVIEW_REQUIRED` / INCOMPLETE, no automatic scaling of numbers |
| Source ingredient mass or prepared-output nutrition changes unexpectedly | **BLOCKING**, not silent meal/Shopping change |
| Same-date events lack verified common prep-session or hold/reheat state | No authorized advance/shared execution |
| Same prep name but splitting/cleanup/storage adds as many physical actions as it removes | Do not claim `B<A` or Prep product readiness |
| Legacy MealPlan still pinned to prior immutable RecipeVersion | Preserve old history; no auto-mutation; mark derived stale only under accepted source-revision semantics |
| New sidecar not integrated with version-aware repository and UoW | Cannot publish as production calculation authority |
| Different Household/event/version/recipe identifier | No source grouping or cross-Household write |
| No recipe-process authority but LLM suggests a plausible household workflow | Suggestion is untrusted; **BLOCKED**, AI_ENABLED=false remains enough for product |

**FACT:** append-only RecipeVersion publication is a supported mechanism; structured shared-stage publication is not. Soup card has explicitly documented raw vegetable preparation; ragout card assumes “prepared” carrot/onion. Neither version currently has an approved structured shared task output, hold/same-session or net physical-action proof.

**ASSUMPTION:** other sources, a high-trust reviewed process policy or a different pair may provide the missing cross-recipe stage evidence.

**PROPOSED DECISION:** `BLOCKED_RECIPE_STAGE_PUBLICATION_AND_SHARED_COMPONENT_AUTHORITY`. Freeze this pair as **NOT PUBLISHABLE FOR SHARED PREP**, while retaining soup-only per-recipe step correction as an independently reviewable future candidate if it has its own product purpose. No one-off edits just to color a gate green.

**Next meaningful bounded task:** obtain **independent and explicit second-recipe process-stage evidence** for ragout, or select another pair of source-verified RecipeVersions with explicit compatible raw-prep stages. Only after that source completeness decision should an immutable publication PR and retrieval/contract gate be proposed. Do not start another generic string-similarity audit or manufacture a new source to satisfy a milestone.

**Non-goals:** RecipeVersion/RecipeStep production append, prepared inventory, new DB or migration, new runtime stage reader, Planner/Shopping/Pantry changes, AI, Retail, consumer UX, PR10-A/B/C, PR10-PDF or Gate2 closure.

**Verification:** docs/state and immutable source review only. Check links/whitespace, R3-D/source-card SHA consistency, task scope, and no false `PR10-META=READY`. Full backend+launcher regression is not triggered by byte-identical runtime.
