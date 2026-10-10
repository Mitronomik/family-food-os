# PR10-META-SAFETY — source applicability for an overnight raw composite

**Status:** `CASE_BLOCKED_NOT_A_RECIPE_STORAGE_CLEARANCE` — source scope reviewed; no approved preparation/storage policy.
**Issue:** #199.
**Accepted main:** `326480f42aa5f3bada5398a369eb75003d6cceaa` (PR #198 merged 2026-10-10).
**Authority:** [PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-META BLOCKED](pr10-meta-readiness-decision.md), [accepted two-event shared-process research](pr10-meta-shared-process-preflight.md).
**Machine-readable review:** [safety source-scope receipt](pr10-meta-safety-source-scope.json).

## 1. FACT — exact tested scope

The accepted [PR #196 persisted synthetic fixture](pr10-meta-gate2-fixture-evidence.md) and [PR #198 source audit](pr10-meta-shared-process-preflight.md) identify two **different** MealEvents in one 3-member weekly MealPlan:

| MealEvent | 2026-09-18, LUNCH | 2026-09-19, LUNCH |
| --- | --- | --- |
| Source | `SCHOOL2022_54_7M_BEEF_SCHNITZEL` | `SCHOOL2022_54_6M_BEEF_BITOCHEK` |
| Event ID | `ece787f4-ac81-4390-b57f-211c220b02a9` | `63c2c701-ce68-4637-8a96-07252d32fde5` |
| RecipeVersion ID | `343a786b-3338-4d30-825e-486ce70dae54` | `34ec0fa8-c724-424c-819f-fa6823264d04` |
| Process step 1 | same reviewed original text and hash | same reviewed original text and hash |
| Recipe step 2 | form schnitzels | form bitochki |

The common first step, backed by reviewed [R3-A School2022 publication specs](../../data/curation/r3a-school2022-main-batch/publication-specs.json), **minces raw beef and combines it with bread soaked in milk**. Shared source-step SHA256: `2d5b8a370947b64df0b0526ab55caa970be93ee062438c066024d26ab8a689da`. PR #196 accepted JSON SHA256: `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`.

The MealPlan pins **meal dates, not household cooking or chilling clock times**, ingredient arrival/initial temperatures, thaw history or real refrigerator readings. These synthetic fixture dates also do not constitute observed consumer food handling.

**Research question:** may the raw mixed intermediate from the first event be prepared once on Friday, split, kept safely to Saturday and used to produce two different final dishes **without added unverified risk or enough extra work to invalidate the saved action**?

## 2. Source-by-source applicability, verified 2026-10-10

The following are primary government food-safety guidance or official publications, **not** a newly approved FamilyFoodOS storage-standard contract. Values in their original text are context and MUST NOT be copied into RecipeVersion `storage_days_*`, `freezable`, `batch_friendly` or executable consumer Prep instructions from this PR.

| Source and jurisdiction | Supports | Does **not** support |
| --- | --- | --- |
| [Роспотребнадзор, ГИС ЗПП, 2021-10-08 — «Рекомендации по выбору и хранению»](https://zpp.rospotrebnadzor.ru/news/federal/244173), RU | General selection and household packaging/refrigeration/freezing guidance for minced meat | No validated hold duration for **beef already mixed with milk-soaked bread** or a Friday→Saturday instance; no recipe-specific `freezable=true` |
| [Роспотребнадзор по Ингушетии, 2026-07-15 — «Как хранить продукты и готовые блюда в жаркую погоду»](https://06.rospotrebnadzor.ru/content/kak-hranit-produkty-i-gotovye-blyuda-v-zharkuyu-pogodu-0), RU | General separation of raw and cooked foods; timely use advice for **finished** chopped-meat dishes, including bitochki | Statements about cooked dishes do **not** authorize storing an uncooked composite intermediate |
| [Роспотребнадзор по Приморскому краю — домашняя готовка](https://25.rospotrebnadzor.ru/zdorovoe-pitanie/4353/), RU | Search-index description cautions against making minced meat too far in advance | **Direct page access unavailable** during this review; index alone is not a sufficient validated safety rule for the precise mixture |
| [USDA FSIS — Ground Beef and Food Safety](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/meat/ground-beef-and-food-safety), US | General fresh/raw ground-beef cold holding, hygiene, avoiding partial advance cooking and safe final cooking context | Different jurisdiction, no dish-/form-specific assessment of milk-soaked bread + raw beef composite; fresh vs thawed meat and continuous cold-chain not established here |
| [FoodSafety.gov — Cold Food Storage Chart](https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts), US | Category-level ground-meat household cold storage guidance | Not a source/validation receipt for this exact Russian recipe, different ingredient initial states or a specific overnight interval |

**Key distinction:** USDA's general ground-meat refrigerator guidance and the Russian minced-meat packaging guidance are not proof of an approved storage transition for the **prepared composite**. Equally, recommendations for **finished cooked** minced-meat dishes cannot be reinterpreted as a shelf-life for the **raw** bread/milk/beef mixture. The need for temperature control and separation is well supported generally, but the fixture **does not observe or pin** those controls.

The Russian original pages are the more relevant primary jurisdictional context for a Russian-family product; U.S. guidance can corroborate food-safety principles but cannot silently become Russian RecipeVersion authority. Do not turn advisory pages into a normative/legal promise or a recipe-specific shelf-life value.

## 3. State-transition review: block at the first unapproved hold

| Transition | Accepted fact | Decision for this pair |
| --- | --- | --- |
| Raw beef → ground beef | Recipe source includes mincing | Process exists; ingredient initial state still unknown |
| Ground beef + milk-soaked wheat bread → uncooked shared intermediate | Identical first source step in two versions | **Source process candidate only**; no approved common-batch identity |
| Friday uncooked intermediate → retained until Saturday | Only meal dates are pinned | **BLOCKED: exact safe holding transition not established** |
| Retained intermediate → separate schnitzel / bitochki forming | Step 2 differs across recipes | **BLOCKED** until prior hold and per-recipe form/split compatibility reviewed |
| Separate raw shaped portions → cooked final dishes | Source step 3 includes final baking | No automatic combined cooking, cook-time equivalence or safety extrapolation |
| Cooked dish → leftover → reheating | Not this source pair's proposed flow | Out of scope; no invented PreparedBatch/LEFTOVER supply |

The following evidence is **not** present in the accepted data: initial fresh/frozen/thawed beef status and supplier storage clock; milk/bread quality and prior hold; exactly when the mixture is prepared, cooled and used; verified raw composite storage rule; container and contamination controls; actual appliance temperature and food-form transition; approved aggregate portion split; safe final processing validated for the bigger batch; actual labor/action cost of putting away and taking out the mixture.

**Never transform an unknown field into a zero, an allowed temperature, a refrigerator expiration date, a freezer label or a Russian user instruction.**

## 4. Work saving and actual value remain conditional

The two immutable RecipeSteps share a single text/action candidate. Counting each first step once per event suggests a *baseline* of two first-step preparations; using one shared intermediate suggests **one** first-step preparation. This arithmetic would save one duplicated preparation action **only if** a reviewed common input/state and safe hold are established.

However, a new common batch also requires equipment handling, portion separation, container/label/cold-chain operations and later separate processing. The accepted roadmap metric measures **real physical operations across two MealEvents**, not simply repeated strings in `RecipeStep`, and provides no authority to claim minutes saved. On current data **net action reduction is not proven**.

## 5. DECISION, preservation and specific next evidence task

**DECISION: NO-GO for automatic Friday→Saturday raw-composite shared prep on current evidence. PR10-META remains BLOCKED.** This is an evidence decision about one synthetic pair, **not** a claim that the product can never support batching, that overnight storage of all minced meat is always unsafe, or that an individual refrigerator under real measured conditions is unsafe.

Before reconsidering this pair, a separately reviewed evidence package must establish:

1. An applicable, independently verified **source-backed rule or expert-reviewed project policy** for the raw beef + milk-soaked bread intermediate in the expected consumer environment, accounting for original ingredient state, storage temperature/cold-chain and exact elapsed interval.
2. Exact start/end prep/use times rather than meal date-only inference; safe household container/hygiene handling and separation; applicable cooking endpoint and food-form transition.
3. Proven, version-pinned shared component identity with exact Decimal Serving allocations across both MealEvents and distinct post-split shaping/cooking, no invented per-step numeric amounts or Pantry movement.
4. A conservative net **physical-action comparison** that includes storing/retrieving/splitting/cleaning operations. If the extra work eliminates the gain, select a **different actual pair**, ideally one requiring no overnight storage, through a separate bounded review.

**Recommended next bounded operation:** an **alternative two-event source-pair shortlist from the accepted full Gate2 fixture**, with priority for verifiably shared same-day preparatory operations or a separately evidenced cooked/batch state. This avoids the trap of repeatedly treating generic ground-meat storage pages as precise safety authority. Do not change the PR10-META READY threshold, Planner, recipe publication, shopping or Pantry invariants to make a candidate pass.

## 6. FACT / ASSUMPTION / DECISION / OPEN

**FACT:** #198 merged; the pair has a real identical source-step hash and differing second stage. Reviewed sources give broad raw-ground-meat and prepared-dish advice, not the exact composite state-transition receipt. The fixture records meal dates but not kitchen clock times.

**ASSUMPTION:** some appropriately reviewed intermediate/alternate MealEvent pair can reduce duplicated work; this has not been demonstrated by the current pair.

**DECISION:** case-level NO-GO; **PR10-META BLOCKED**, no Prep runtime or consumer refrigeration/freezer instruction, no source metadata publication.

**OPEN:** select another real event pair if this one's source-specific hold clearance cannot be established; only approve safe batch identity and numeric instructions under a separate accepted source-evidence contract.

**Scope and verification:** docs/evidence/state only; source link, source applicability, machine decision invariants and whitespace/diff scope. No runtime tests or full backend regression required for byte-identical production code. No PR10-A/B/C, Prep execution, PR10-PDF, PWA, Retail or AI.
