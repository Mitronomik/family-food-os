# PR10-CORE — bounded two-step source, process, scale and eligibility review

**Status:** `NO_GO_TO_APPROVED_IMMEDIATE_ON_CURRENT_EVIDENCE` for **both** audited steps; `NO_GO_TO_PR10_CORE_RUNTIME` remains. This is a technical/source readiness disposition, **NOT an independent Domain/QA approval or a finding that the recipes cannot be cooked**.
**Owner scope:** 2026-10-23 explicit approval for **one** bounded inspection of the R3-C salmon and R2-B pollock first steps, exact GO/NO-GO evidence and necessary D3 publication/read follow-up; **no** recipe/runtime/schema/data changes or autonomous merge.
**Accepted base:** `main@22a7f2ab9d94fe395739f0691e5fff3ba3928594`; [PR #238](https://github.com/Mitronomik/family-food-os/pull/238) merged 2026-10-22.
**Issue:** [#239](https://github.com/Mitronomik/family-food-os/issues/239).
**Read with:** [D3 accepted contract](pr10-core-step-eligibility-d3-contract-2026-10-22.md), [prior preflight](pr10-core-positive-preflight-2026-10-20.md), [two-step queue](pr10-core-step-eligibility-review-queue-2026-10-22.json), [accepted PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [Option B Gate2](pr10-option-b-staged-delivery-gates-2026-10-17.md) and [bounded publisher/reader handoff](pr10-core-two-step-publisher-reader-acceptance-2026-10-23.md).
**Machine evidence:** [source/step/Decimal assessment](pr10-core-two-step-source-process-scale-decision-2026-10-23.json).

## 1. FACT — source and rights were checked at their proper trust levels

- The existing [R3-C publication manifest](../../data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json) and [R2-B publication spec](../../data/curation/r2b-fish-main-diversity/publication-specs.json) match the two **first-step Russian texts** in the [PR #236](pr10-core-positive-preflight-evidence-2026-10-20.json) / [PR #238](pr10-core-step-eligibility-review-queue-2026-10-22.json) historical fixture receipts. Machine evidence pins **Git blob SHA, historical RecipeVersion ID, Step ID/process and instruction SHA-256**, School2022 source PDF SHA-256, source-base ingredient grams, source original serving denominator and original member Decimal portion strings.
- The accepted school source is [Роспотребнадзор / ФБУЗ ФЦГиЭ, *Сборник рецептур блюд и типовых меню для организации питания обучающихся 1–4 классов* (2022)](https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf), specifically **recipe 54-17р, printed page 112 / PDF index 111**, and **recipe 54-7р, printed page 103 / PDF index 102**. Its primary-source **web-extracted text** was read this turn for input/output values and whole cooking method, corroborating repository source facts. The screenshot web endpoint reported a cache miss and the publicly served PDF bytes were **not independently re-downloaded/hashed** in this task; `c9264cf…` is a **previously accepted repository source pin**, **not a newly confirmed byte-level match** to the current website.
- School2022 original context is **institutional meals for ages 7–11**. Reviewed rights in existing curation are **limited factual recipe publication rights**; they are not automatic license or safe-application approval for a person's home procedure, family-scale equipment, refrigerated storage or an unchanged original institutional instruction. No new source rights were granted here.
- The original source contains longer preparatory hygiene/process descriptions than the consumer-published `RecipeStep`: the original salmon card specifies parsley-root washing, carrot/onion sorting, washing/peeling and industrial vegetable slicing before blanch/sauté; original pollock card similarly describes onion sorting/washing/peeling/shredding/blanching. **Do not silently augment the immutable abbreviated published instruction** with omitted originals. Source re-publication would be a different, separately reviewed data operation.
- **Additional source discrepancy requiring separate Data/Recipe-owner review:** the original pollock card's milk-level instruction uses **one-third of the baking tray's height**, while the accepted R2-B consumer Step 4 says **one-third of the fish's height**. These are different geometric reference dimensions. This was found by cross-reading the web-extracted primary PDF and the repo publication spec. It is a **potential original→published process inconsistency**, not permission for this PR to rewrite RecipeVersion or assert one interpretation is safe. This increases the review burden for the **whole recipe** even though the Step 1 text itself matches.

## 2. FACT — per-step numeric/food-form and exact historical Decimal projection

The following arithmetic is **source net grams × historically accepted Decimal `portion_servings`**, with **no floating point**, no rounding to a retail package and no raw-to-cooked conversion. All resulting grams are **RESEARCH PROJECTIONS**, not new approved executable quantities, cooked yield or physically suitable portion ceilings.

| Evidence | Salmon / R3-C lunch | Pollock / R2-B dinner |
| --- | --- | --- |
| Original `base_servings` | `1` | `1` |
| Historic source output per serving | `70 g` | `80 g` |
| Historical member `portion_servings` | `5.916796` | `5.631030 + 5.631030 + 6.546747 = 17.808807` |
| Source onion net per base | `9.8 g` | `16 g` |
| Onion exact source-scaled net projection | **`57.9846008 g`** | **`284.940912 g`** |
| Additional research-only input demand | Carrot `17.5 × 5.916796 = 103.5439300 g`; tomato purée `6.3 × 5.916796 = 37.2758148 g`; **total** sunflower oil `5.3 × 5.916796 = 31.3590188 g` | Pollock fillet `64 × 17.808807 = 1139.763648 g`; milk `25.6 × 17.808807 = 455.9054592 g`; sunflower oil `5.6 × 17.808807 = 99.7293192 g` |
| Current executable approval / physical batch applicability | **NONE / NOT REVIEWED** | **NONE / NOT REVIEWED** |

No approved final edible output mass at these household scales is proven; the 70/80 g published *source* outputs are not a source-reviewed linear **family batch capacity** or a person-specific physical suitability test. The magnitude of historical factors is an explicit **process/equipment/individual-Serving applicability question**, not justification for automatic calorie clipping or a fabricated gram limit. The separate measured Planner Serving release gate remains unmet.

The first-step Russian texts contain no **literal numeric tokens**, so both can be treated as **syntax candidates** for `NO_NUMERIC_DIRECTION`, but **not** as independently approved numeric classifications or `APPROVED_IMMEDIATE`. The **whole actual recipe** has numeric instructions, including salmon bake `40–45 minutes` and pollock `65 g` fish pieces, milk level and oven `20–25 minutes`; numeric/process rights/applicability in the rest of the RecipeVersion must still be validated where relevant.

## 3. Per-step bounded GO/NO-GO

| Step | Supported FACT | Missing before positive `APPROVED_IMMEDIATE` | Current decision |
| --- | --- | --- | --- |
| **R3-C salmon** `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES` Step 1 | Exact accepted text and source-pinned vegetables/Decimal input projection. Instruction describes *preparation → blanch → sauté → tomato purée*. | Independent reviewer has not certified **whole compound step** as a same-day actionable home procedure at actual scaled volumes/equipment; original institutional vegetable processing is abbreviated in consumer step; oil is **one source total** allocated between sauté and greasing a dish, and the step-level oil split is **UNKNOWN**. Can't extract only vegetable cutting as a new numbered step without approved source revision. | **`NO_GO_TO_APPROVED_IMMEDIATE`**; syntax observation only, `PENDING_INDEPENDENT_REVIEW` |
| **R2-B pollock** `SCHOOL2022_54_7R_POLLOCK_IN_MILK` Step 1 | Exact accepted text and source-pinned onion net input. Instruction describes *prepare → shred → blanch*. | No independently accepted same-day consumer process/equipment scale for blanching this onion amount; blanch processing-water/temperature/time/handling not source-pinned for this consumer path. The original-vs-published **milk-level reference** in subsequent process also needs separate Recipe/Data authority review before treating **the whole recipe** as a source-clean execution path. | **`NO_GO_TO_APPROVED_IMMEDIATE`**; syntax observation only, `PENDING_INDEPENDENT_REVIEW` |

**Negative answer scope:** the review does **not** declare either dish intrinsically unsafe or globally unusable, and does **not** claim the entire current catalogue fails PR10-CORE. The **bounded** two-candidate evidence does not satisfy independent positive-action eligibility. Zero approved executable steps is the truthful result.

## 4. ASSUMPTION, decision, blockers and exact next dependency

**ASSUMPTION:** a qualified independent Recipe/Domain QA reviewer with access to the retained source card(s), actual process and a re-pinned current three-member fixture could validate one or both same-day procedures under explicit source-backed scale/equipment restrictions **without inventing new cooking facts**. The available evidence does not prove that assumption.

**DECISION (evidence-only):**

- `SOURCE_INTEGRITY = PASS_REPO_MANIFEST_MATCH`; primary-source web text corroborated relevant facts but original binary re-hash/screenshot not passed in this run.
- `DECIMAL_SCALE_RESEARCH = PASS_ARITHMETIC_ONLY`, no runtime conversion/recipe cooking acceptance.
- `NUMERIC_CLASS = NO_DIGITS_OBSERVED_BUT_NOT_REVIEWER_APPROVED`.
- `R3C_STEP1_EXECUTABLE = NO_GO_ON_CURRENT_EVIDENCE`.
- `R2B_STEP1_EXECUTABLE = NO_GO_ON_CURRENT_EVIDENCE`.
- `PUBLISH_ELIGIBILITY = NO_GO`, `PR10_A_RUNTIME = NO_GO`, `GATE2 = NOT_EVALUATED`.

**OPEN — independent review, not silently decided:** an actual independent reviewer identity/date and signed rationale, current actual fixture and RecipeVersion/Step/scale re-pin, source-process completeness at family scale, exact trusted package reader + **rollback-independent** revocation status source (from #238), and adjudication of the pollock Step 4 original→published discrepancy. The [bounded publisher/reader acceptance addendum](pr10-core-two-step-publisher-reader-acceptance-2026-10-23.md) freezes how such a decision must be accepted; it does **not** implement or approve the result.

**Stop rule:** **do not initiate a third recipe candidate** in this operation, and do not turn reviewed source evidence into a nominal `APPROVED_IMMEDIATE` merely to unlock code. Once the independent reviewer resolves the two exact source/process/scale cases, the Product/Architecture owner may separately authorize *one* trusted publication/reader implementation, or accept a scoped `NO_GO` and reconsider PR10-CORE candidate strategy through a new explicit decision. No PR10-A, Prep migrations, API/PDF/PWA, Gate2 closure or real-family release follows from this document alone.

## 5. Verification and unchanged architecture

Checked repo manifest Git blob identities and exact first-step texts, source/original serving basis, complete 4-/5-step process strings, previous historical fixture pins, original PDF **web text** for process context, and reproducible exact base-10 multiplication using integer-scaled arithmetic. No updated RecipeVersion was published, no current live Household MealPlan generated and **no independent human Domain/QA sign-off was obtained**. The web PDF screenshot and independently rehashed public binary are unavailable, so the accepted archived source hash was **not reasserted as newly verified**.

`AI_ENABLED=false`; RecipeVersion immutable/source-backed; `Serving` and Shopping/Nutrition quantities remain backend authoritative; numeric prose not parsed into totals; no Pantry movement, hidden storage/freezer time, cross-event onion batch/Prep task creation or source/quantity policy bypass. D3 trusted publication/read/anti-rollback, three-table Prep, Gate2's two-positive-events rule and separate safe batch/serving-release gates unchanged. This is **docs + machine evidence only**; exact-head Docs CI, links/diff/scope review and independent review required before merge. Backend regression, runtime process/kitchen tests and trusted publisher execution **were not performed**.
