# PR10-CORE — one-pass action-class triage of the accepted historical 21-event fixture

**Status:** source-manifest audit `COMPLETE_FOR_HISTORICAL_CODES_AND_TEXT`; **`GO_TO_INDEPENDENT_REVIEW_OF_TWO_CANDIDATES_ONLY`**; zero approved executable PrepTasks, `NO_GO_TO_PR10_A_RUNTIME`.
**Owner's 2026-10-23 approved change:** replace the *previous narrow R3-C/R2-B candidate-only search strategy* with **one bounded pass across the 21 MealEvents of the already accepted seven-day synthetic household fixture**, identify one **minimal** two-event candidate pair and describe reusable **review classes**. This is **not** approval of a new Gate2 fixture, taxonomy as authoritative data, automatic eligibility, or any reduction of Option B two-event acceptance.
**Base:** `main@5e5ee82f90a5f0f3103f96b09ac7a6d166565e3b` (#240 merged); [Issue #243](https://github.com/Mitronomik/family-food-os/issues/243); concurrent [PR #242](https://github.com/Mitronomik/family-food-os/pull/242) remains **OPEN/unmerged** and is not treated as accepted authority.
**Machine evidence:** [all 21 events, 87 source steps and exact two candidate descriptors](pr10-fixture21-action-class-triage-2026-10-23.json).
**Read with:** [Option B technical Gate2](pr10-option-b-staged-delivery-gates-2026-10-17.md), [accepted D3 trusted step eligibility/anti-rollback](pr10-core-step-eligibility-d3-contract-2026-10-22.md), [PR10-ARCH §4.1 and three tables](pr10-prep-freezer-implementation-contract.md), [prior #240 source/process negative receipts](pr10-core-two-step-source-process-scale-review-2026-10-23.md), [DC4 historic verified catalogue](../../data/curation/dc4-corpus-readiness/rerun-summary.json), [historical 21-event day/recipe mapping](pr10-meta-same-day-pair-evidence.json).

## 1. FACT — bounded coverage and evidence boundaries

The accepted 2026-09-14 → 2026-09-20 **synthetic** MealPlan fixture records three distinct `COOK_RECIPE` codes per day, **21 distinct recipe codes in 21 MealEvents** and a three-member Household. Its earlier [PR #196 receipt](pr10-meta-gate2-fixture-evidence.md) describes **42 individual Servings** and immutable event/step provenance. It is **not** a newly run production/actual Gate2 acceptance. The accepted DC4 catalogue has **51** verified active candidates; this operation audits **only 21 distinct recipes selected by that historical week**, not all current published recipes.

Reconciled each of the **21** codes to a verified historic RecipeVersion ID in DC4, and to the exact repo **publication manifest blob SHA**, original ordered Russian RecipeStep text and source structured ingredient identity. Resolved all recipe input formats: R2-/R3- `recipes{}` maps, R3-C/R3-D `selected[]`, and the special **R2-E singular `recipe`** payload (cottage-cheese casserole). No recipe with missing source steps was silently dropped. **87 ordered source steps** were inventoried; their literal texts are preserved in the accompanying non-authoritative JSON for independent audit.

**Important gaps:** the weekly code/day manifest alone does **not** give source MealEvent UUID and each Member's exact Decimal `Serving.portion_servings` for every event. It cannot certify the *current* fixture's live RecipeVersion/RecipeStep UUID/hash or 3-member end-to-end correctness. DC4's RecipeVersion UUIDs are **historical**, not stable lookup keys on freshly generated disposable databases. **No approved executable instruction may be published from this receipt alone**; independent current exact fixture / step / member re-pin is a mandatory next gate. The original source PDFs were not newly fetched/rehashed for this pass: accepted repo manifest provenance is the evidence basis, not a new external source validation.

### Deterministic triage (NOT validation or authoritative classification)

Applied a reproducible **text prefilter** to the immutable published instructions, with mutually exclusive priority: literal digit → `NUMERIC_TEXT_REVIEW`; otherwise an explicit heat/hot-state verb → `HEAT_PROCESS_REVIEW`; otherwise broad ambiguous/compound context → `CONTEXT_OR_COMPOUND_REVIEW`; remaining strings → `NON_HEAT_TEXT_CANDIDATE`. These are **research-only flags**, not automatically selected `NO_NUMERIC_DIRECTION`, `APPROVED_IMMEDIATE`, an accepted `PrepActionType` platform enum, or a safety/physical-batch judgement. A text-only prefilter can both miss requirements and over-flag harmless processes.

| Research-only group | Count of the 87 published steps | Handling |
| --- | ---: | --- |
| `NUMERIC_TEXT_REVIEW` | **31** | Full source/process/mass/time/temperature context review; **never** scale or suppress numeric prose via regex |
| `HEAT_PROCESS_REVIEW` | **34** | Source/food-form/process/equipment/time applicability required regardless of literal digits |
| `CONTEXT_OR_COMPOUND_REVIEW` | **17** | Object/action identity, missing substep and input/output conditions require reviewer |
| `NON_HEAT_TEXT_CANDIDATE` | **5** | **Still unreviewed**; no positive task until source, process, actual scale and eligibility reviewer approves |
| **Total** | **87** | Exactly 21 code/event inputs accounted for |

A group count is **not** a count of usable PrepTasks. A non-heat instruction may still omit equipment, implicitly depend on unsafe conditions, or merely repeat a recipe. An unclassified numeric instruction must be withheld as executable source guidance. `SAFE_BATCH_READY`, storage and nutrition/portion quality remain **separate**.

## 2. DECISION PROPOSED — exactly two lower-complexity source candidates for independent review

| Historical MealEvent | Source and immutable publication text | Structured RecipeIngredient amount at source base | Why consider / what remains open |
| --- | --- | --- | --- |
| **2026-09-18** — `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`, step 1 | [R2-E published `recipe.version.steps[0]`](../../data/curation/r2e-cottage-casserole/publication-specs.json): **«Творог протереть.»** | `TVOROG_5`, **139.5 g** at `base_servings=1` | Specific raw/source-form action, no numeric or thermal command in this step. Need independently validate whole action, actual household scale, equipment/process output, current step hash and member amounts. Do not guess sieve, task time or actual consumed/stored output |
| **2026-09-19** — `SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE`, step 1 | [R3-B published `recipes[code].trusted_recipe_seed.version.steps[0]`](../../data/curation/r3b-school2022-breakfast-batch/publication-specs.json): **«Перебрать и промыть кукурузную крупу, несколько раз меняя воду.»** | `CORN_GROATS`, **40 g** at `base_servings=1` | Concrete nonthermal sorting/rinsing before cooking. Need confirm entire instruction, correct product form, amount and suitable immediate process; **rinsing water is NOT automatically the separate structured 68 g recipe cooking water**. Do not invent rinse-water grams, equipment, storage/shelf life or scale-independent capability |

**Why these rather than salmon/pollock:** neither proposed first step itself involves cooking the fish, thermal blanching, unreviewed vegetable-oil split or the R2-B original-vs-published milk-level discrepancy; that reduces *the number of visible preflight questions*, but does **not** make either approved, risk-free or eligible before review. Both are in the **existing historical accepted week's recipe set**, different dates/MealEvents, with source version and exact original text. They are **not** newly invented recipes and do **not** replace the original fixed MealPlan/MealEvent fixture. The earlier R3-C/R2-B `NO_GO` remains intact.

**Test of meaningful Prep value:** independently reviewed action must be an actual separately useful, source-bound preparation of an exact product amount for its event on its **same meal day**, not a UI list that simply reprints RecipeSteps. If the reviewers cannot demonstrate that the action is executable as a useful PrepTask under the accepted D3 and Option B conditions (including required ingredient amounts and status), then **reject it**, even if the string looks simple.

**NO `APPROVED_IMMEDIATE` granted:** two chosen candidates only narrow subsequent human/Domain QA work. Both remain `PENDING_INDEPENDENT_REVIEW`; `independent_reviewed_count=0`, `approved_immediate_count=0`, `PR10_A_RUNTIME_READY=false`, `Gate2_PASS=false`.

## 3. Proposed scalable review-class process (scope suggestion, not new domain policy)

The goal is to stop searching the web for every RecipeVersion **without weakening verification**. Separate:

1. **Source validation** of all published recipes: retain exact immutable RecipeVersion, source URL/version/hash, rights, structured RecipeIngredients (including form/unit), ordered Russian Step texts and version history. Missing values remain UNKNOWN/blocked. This is largely reproducible through existing DATA-CORPUS-V1 validations.
2. **Research candidate families:** group *potentially analogous processes* by identifiable food form/action (e.g. `MECHANICAL_FOOD_PREP_NONHEAT` for source-form cottage cheese, or `RAW_GROATS_SORT_RINSE_NONHEAT`). Group names in this receipt are **not new authoritative table columns or enum values**. Numeric text and thermal/holding/freezer operations remain separately constrained. One source-backed review of an action/process applicability **policy** can be reusable **as a criterion**, but cannot automatically grant every recipe/version an eligibility permit.
3. **Per-RecipeVersion/Step binding:** independently reviewed `numeric_direction_classification` and `immediate_same_day_eligibility` must still match **current** exact Step UUID/text hash, process/source identity, equipment, food form, family scale and accepted member Servings. The D3 versioned publisher/read policy is the **only** future trusted grant source, with live rollback-independent revocation and explicit reason on UNKNOWN. Merely matching a policy class, heuristic regex, verb, similar ingredient or source family never yields `APPROVED_IMMEDIATE`.
4. **Exception review** for amount/process discrepancies, source loss, numeric steps, unreviewed heating and stored-food instructions. Explicit `NO_GO` for failing candidates. Later broader catalogues reuse the same validation machinery; do not do an uncontrolled mass approval.
5. **Adversarial coverage:** absent/stale package, unsupported context/source, conflicting hash or form, all-UNKNOWN week, only 1 approved event, misleading process steps, altered RecipeVersion, high portion factor, missing reviewer/rights, `approved → revoked → rollback → no executable task`, and no Pantry writes.

**Compatibility:** retain approved `prep_plans` / `prep_tasks` / `prep_unresolved_obligations` three-table contract, `AI_ENABLED=false`, backend-owned Decimal/Shopping truth, Household isolation and versioned source fingerprints. No new source-publisher deployment choice, DB/service or migration is approved in this docs-only PR; the existing D3 anti-rollback and actual accepted fixture review must be satisfied before **any** PR10-A runtime.

## 4. Validation and stop

**FACT:** a reproducible accepted historical source map has 21 distinct COOK_RECIPE events, 87 published source steps and two lower-complexity candidates. This is a source-input audit, **not** a simulation of current live application services or independent culinary validation.

**ASSUMPTION:** a qualified independent Domain/QA reviewer can find at least one fully source-justified, scalable same-day useful action in each of the two chosen RecipeVersions. Missing source data, review scope or current fixture/Serving evidence may make this impossible.

**PROPOSED DECISION:** **`GO_TO_INDEPENDENT_REVIEW`** for these two event-specific candidates, **not** `GO_TO_RUNTIME` or Gate2. If either fails, emit bounded **`NO_GO`**, return to owner and request a separately authorized candidate/contract change. This approved audit **closes the search pass**: no third, fourth or endless replacement candidate within this task.

**Separate pending branch:** PR #242 is not merged at this base; do not reinterpret its source/RecipeVersion claims as current main or overwrite its state. The prior R3-C/R2-B case remains an independent bounded issue pending review.

**Required before the next production step:** independently re-pin actual current accepted Gate2 MealPlan and both MealEvent/RecipeVersion/RecipeStep UUID + SHA256 + every member's Decimal `Serving`; perform two independent process/source/scale reviews with recorded reviewer identity, dates and source proof; independently review D3 trusted publisher/reader + rollback-proof revocation mechanism; prove negative all-UNKNOWN/one-approved-event cases and stable fingerprints. Then obtain explicit PR10-A authorization. **Without both source-approved positive tasks, technical Gate2 and runtime stay blocked.**

**Current release state:** `NO_GO_TO_PR10_CORE_RUNTIME`, `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`, `SAFE_BATCH_READY` and `PORTION_RELEASE_READY=PASS` unmet. No Pantry/Shopping inventory mutation, early cooking, frozen stock, reuse savings, meal-clock, recipe re-publication, PDF or PWA created. **Docs-only** evidence and review; no backend regression claimed, no autonomous merge.
