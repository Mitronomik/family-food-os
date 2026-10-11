# PR10-SOURCE-SHORTLIST — bounded source/rights preflight

**Date:** 2026-10-11
**Issue:** [#213](https://github.com/Mitronomik/family-food-os/issues/213)
**Baseline:** `main@1b928b6583688e73f5933e702a30ebf6ffb12824` (PR #214 merged).
**Authority:** [approved D1–D3 decision record](pr10-data-recovery-approved-decisions-2026-10-11.md), [recovery strategy](pr10-data-recovery-proposal.md), [PR10-ARCH](pr10-prep-freezer-implementation-contract.md).
**Outcome:** **DISCOVERY_CANDIDATES_ONLY; PR10-META=BLOCKED**. No two-event approved shared stage; no Gate2 fixture change.

## Scope and method

Reviewed **exactly three** vegetable-preparation stage families using public university extension/USDA-associated National Center for Home Food Preservation (NCHFP) technical instructions. This is a **process-source scouting pass**, not a discovery of two source-backed production recipes or an execution/safety approval for any MealEvent. Sources were inspected as online pages, **not downloaded byte-identical production snapshots**; independent record hashes and redistribution/translation licenses were not established. Link-based attribution and factual evaluation do not imply the right to copy publisher prose into the catalogue. Reuse/rights review required before publication.

The approved D1 path A (existing recipes) remains blocked by the existing [School2022 exact-card identity finding](pr10-meta-form-source-review.md). The three entries below explore path B without manufacturing new verified RecipeVersions.

## Candidate matrix

| Stage family | Primary source and source-backed form | Potential value | Important missing evidence | Outcome |
| --- | --- | --- | --- | --- |
| **S1 — diced raw bulb onion** | [NCHFP Freezing Onions](https://nchfp.uga.edu/how/freeze/vegetable/freezing-onions/): peel/trim/clean, dice approximately 1/4 inch, freeze without blanching; guidance distinguishes whole bulbs and onion rings | Exact typed form and separately prepared freezer ingredient may be applicable to multiple cooked recipes | No two published FamilyFoodOS recipes pinned to same diced form; no approved recipe-stage binding, freezer inventory/execution authority or measured net actions; unrelated School2022 salmon/pollock *blanched* onion is **NOT** equivalent | **REVIEW_CANDIDATE**, not runtime approved |
| **S2 — diced/sliced blanched carrot** | [NCHFP Freezing Carrots](https://nchfp.uga.edu/how/freeze/vegetables/freezing-carrots/): wash, peel, cut thin slices or 1/4-inch cubes or lengthwise strips; water blanch cut forms for two minutes then rapidly cool/drain/pack | Well-defined input and frozen output form may be useful in a reviewed multi-recipe vegetable-prep corpus | No verified pair of RecipeVersions requiring precisely the same *blanched* carrot output; cannot equate an unblanched recipe carrot to this stage. Batch capacity and per-event work saving not evidenced | **REVIEW_CANDIDATE**, not runtime approved |
| **S3 — sliced sweet pepper, heated vs unheated** | [NCHFP Freezing Bell or Sweet Peppers](https://nchfp.uga.edu/how/freeze/vegetable/freezing-bell-or-sweet-peppers/): wash/trim/deseed; cut 1/2-inch strips/rings. Heated strips/rings have distinct water-blanch treatment; unheated peppers freeze separately | Source explicitly distinguishes heated/unheated states; useful negative control for preventing unsafe matching by ingredient name | No exact published recipe pair or required state mapping. Heated and unheated forms **cannot** be grouped as one operation; recipe-specific use and total labor proof missing | **REVIEW_CANDIDATE**, not runtime approved |

The [NCHFP general blanching guide](https://nchfp.uga.edu/how/freeze/freeze-general-information/blanching-vegetables/) stresses that treatment is dependent on vegetable and size. [USDA FSIS food-handling guidance](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/steps-keep-food-safe) provides general cooling/cross-contamination principles, **not** dish-specific permission to hold a prepped component between two FamilyFoodOS meal events. No generic food safety rule here is adopted as a universal RecipeVersion storage field.

## Source authority and rights assessment

| Criterion | Finding |
| --- | --- |
| Publisher identity | NCHFP/University of Georgia extension pages, attributed to *So Easy to Preserve*, 6th ed. |
| Availability | Public web pages, URLs included above; live at time of review |
| Exact snapshot/version SHA | **UNKNOWN** — web pages not byte-pinned into accepted corpus |
| License allowing recipe/prose copying and Russian translation | **UNVERIFIED**; public readability != reproduction rights |
| Technical preparation/process evidence | **YES, bounded to the specified vegetable forms and preservation context** |
| Source-backed complete RecipeVersion pair | **NO** for all three |
| Net physical-operation savings B<A | **UNVERIFIED** for all three |
| Household timing, storage and inventory transition | **UNVERIFIED** for FamilyFoodOS fixture |
| Production data approval | **NO** |

## Adversarial comparison — source procedure is not shared recipe execution

For any candidate S1/S2/S3, the hypothesis is a common preparation performed for two dishes. The baseline graph would contain per-event washing/cutting/treatment. A shared graph needs common setup, a verified compatible combined batch, precise splits, extra cleaning/packaging/retrieval and any hold/defrost. Without two independently pinned dish processes, `A` and `B` are **not comparable empirical/verified graphs**. Do not claim 2→1 is net `B<A`, or invent saved minutes.

Negative tests before publication:
1. Same FoodIngredient but different sliced/diced or heated/raw form → **NO SHARE**.
2. Freezer-prep source used to infer fresh same-day dish stages → **NO SHARE** until source/recipe bridge approved.
3. Different source or revised RecipeStep hash → invalidate binding.
4. Unverified hold across meals, insufficient quantity basis or unknown packaging → block executable shared task.
5. Source terms unclear for re-publication or process text translation → review required, do not copy prose.
6. Any purported action savings excluding washing, cutting, split, setup or cleaning → reject B<A proof.

## FACT / ASSUMPTION / DECISION / OPEN QUESTION

**FACT:** Three credible, public technical process guides establish distinct vegetable forms and preparation methods. They do **not** bind two authoritative FamilyFoodOS recipes, approve stage retrieval or demonstrate net household work savings.

**ASSUMPTION:** These families may be candidates for a *future* independently curated pair of executable recipes; no specific pair is verified.

**DECISION:** **NO-GO FOR PR10-META RELEASE** on this research pass. **S1 diced onion** is the recommended *next research target only*, because it has a simple explicit food form and avoids a blanching operation; do not conflate it with the blocked blanched-onion pair. S2 and S3 are retained as negative/control candidates. This is a discovery preference, not authorization to change Gate 2 or publish recipes.

**OPEN QUESTION:** Which licensed/reviewable two actual recipe cards independently require exactly the same diced-onion stage, with complete quantity, timing and compatibility facts? If none are found in a bounded follow-up, stop and request a new decision, not indefinite pair searches.

## Follow-up gate

The next independently reviewed bounded research action may evaluate **one exact recipe pair** for S1, with verifiable source identity/rights, immutable RecipeVersion/RecipeStep and MealEvent applicability, input/output form, exact structured Decimal portions, no unreviewed hold, and a falsifiable physical work-count trace. Only after evidence and user approval may a changed Gate2 fixture be *proposed*. D3 still requires a separately merged publication/read-path implementation contract before runtime.

**No** RecipeVersion append, schema/migration, Pantry movement, Prep implementation, Gate2 rewrite, Retail/AI or PDF. PR10-META, PR10-A/B/C and PR10-PDF remain **BLOCKED/NOT AUTHORIZED**.
