# PR10 two-step analogue research — source corroboration ≠ execution approval

**Status:** bounded `GO_CULINARY_TECHNIQUE_CORROBORATED` / **`NO_GO_APPROVED_IMMEDIATE` for both exact existing steps** / `NO_GO_PR10_A_RUNTIME`. This is a **research decision**, not a qualified independent Domain/QA approval or permission to alter the production RecipeVersion.
**Date/base:** 2026-10-23; `main@5e5ee82f90a5f0f3103f96b09ac7a6d166565e3b` (merged [PR #240](https://github.com/Mitronomik/family-food-os/pull/240)).
**Issue:** [#241](https://github.com/Mitronomik/family-food-os/issues/241). **Machine comparison:** [JSON matrix](pr10-two-step-recipe-analogue-comparison-2026-10-23.json).
**Existing controls:** [R3-C/R2-B exact NO-GO](pr10-core-two-step-source-process-scale-review-2026-10-23.md), [D3 trusted publication/reader + anti-rollback](pr10-core-step-eligibility-d3-contract-2026-10-22.md), [two-step bounded acceptance](pr10-core-two-step-publisher-reader-acceptance-2026-10-23.md), [Option B roadmap](pr10-option-b-staged-delivery-gates-2026-10-17.md).

## 1. Evidence hierarchy and comparison method

**Primary original source 2022:** [Роспотребнадзор — «Сборник рецептур блюд и типовых меню для организации питания обучающихся 1–4-х классов»](https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf). Exact target recipes: salmon/tomato `54-17р`, printed p. 112 (PDF page index 111); pollock/milk `54-7р`, printed p. 103 (PDF index 102). Same-volume analogues: tomato/vegetables pink salmon `54-10р`, printed p. 105 (PDF index 104), and pollock `54-11р`, printed p. 106 (PDF index 105); milk pink salmon `54-6р`, printed p. 102 (PDF index 101), and salmon `54-15р`, printed p. 110 (PDF index 109).

**Earlier corroboration 2020:** [Роспотребнадзор / Новосибирский НИИ гигиены — «Сборник рецептур блюд и кулинарных изделий для организации горячих завтраков и обедов обучающимся 1–4-х классов»](https://pervomayskaya-shkola.ru/wp-content/uploads/2020/07/Sbornik_receptur_blyud_i_kulinarnyh_izdelij_dlya_organizacii_goryachih_zavtrakov_i_obedov_obuchayushchimsya.pdf); milk `54-6р-2020` PDF p.74 (index 73), pollock `54-7р-2020` PDF p.75 (index 74), tomato/vegetables pink salmon `54-10р-2020` PDF p.78 (index 77), pollock `54-11р-2020` PDF p.79 (index 78). **Separate earlier publication but overlapping Rospotrebnadzor/institutional lineage**: corroborates a recipe *family*, not independent home cooking trials.

**Other primary contextual sources, not recipe authority:** [FoodSafety.gov — fish safe minimum cooking temperature](https://www.foodsafety.gov/food-safety-charts/safe-minimum-internal-temperatures) and [NCHFP — freezing onions](https://nchfp.uga.edu/how/freeze/vegetable/freezing-onions/). US fish safety chart provides an independently documented fish temperature, **not an accepted Russian consumer procedure** for either RecipeVersion. NCHFP's *freezing* sliced/diced/whole onion practices differ with food form; it must **not** be used to replace source blanch instructions for *immediate cooking*, authorize held onion between meals or create a freezer plan.

**Verification limit:** primary and earlier-edition PDF **web-extracted source text** was read and exact relevant recipes/lines matched to source manifests. The web PDF screenshot endpoint returned errors on both PDFs; the currently public binary PDF was **not independently downloaded and SHA256 checked**. The 2022 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d` is the **previously reviewed repository archive pin**, not proof that current web bytes hash identically. The 2020 source was **not previously published as FamilyFoodOS source authority**, has no independently accepted local archive/hash/rights receipt and remains **external corroboration only**, never added to the production catalogue.

## 2. Target salmon `54-17р` and four comparable tomato-fish processes

| Comparison | What is source-corroborated | What must NOT be imported |
| --- | --- | --- |
| **2022 54-10р** (pink salmon, same book) | Vegetables carrot **17.5g net**, onion **9.8g net**, tomato purée **6.3g**, parsley root **2.8g**, sunflower oil **5.3g total**, water **17.5g** per card, matching salmon `54-17р` non-fish rows; trim/wash/shred onion, blanch and sauté with carrot/parsley, then tomato | Distinct fish card/RecipeVersion; similar recipe does not independently review the household portion factor |
| **2022 54-11р** (pollock, same book) | Same basic vegetable category, source ingredient rows and sequence | Fish ingredient/form/base yield differs; no new combined stage identity or output safety policy |
| **2020 54-10р-2020** (pink salmon) | Same blanch onion → sauté with carrot/parsley → tomato purée and fish baking pattern | The **2020** description additionally scalds parsley root/carrot; old process text is **not identical** to published 2022 salmon step |
| **2020 54-11р-2020** (pollock) | Same main vegetable process and cooking objective | Earlier edition/source-specific prep operations and species variant not a reviewed amended RecipeStep |

**Decision on culinary provenance:** **GO**: the source technique itself is real and independently locatable within two related institutional publications. **NO-GO for executable eligibility:** the currently published salmon *first step combines preparatory and heating actions*. The original source contains additional wash/peel/machine cutting detail; the published consumer Step omits it. One source sunflower oil total `5.3g` is used for **both** sauté and tray greasing, with **no accepted step-level split**; similar cards repeat the total but **do not supply that missing split**. A reviewer cannot fabricate a split, create a new shortened cutting-only step, or authorize a kitchen/equipment procedure at `5.916796` historical base portions from similarity alone.

## 3. Target pollock `54-7р` and four comparable fish-in-milk processes

| Comparison | What is source-corroborated | Difference relevant to data integrity |
| --- | --- | --- |
| **2022 54-6р** (pink salmon, same book) | Onion sort/wash/peel/shred/blanch; fish fillet net **64g**, milk **25.6g**, onion net **16g**, oil **5.6g**, finished card **80g**; hot milk + baking | Explicit milk level referenced to **one-third of tray height** |
| **2022 54-15р** (salmon, same book) | Same onion/fish/milk preparation family with species variant | Milk instruction says one-third **of height** without identifying its referent; it cannot prove the referent is fish rather than tray |
| **2020 54-6р-2020** (pink salmon) | Same onion blanch and hot milk + fish method | Earlier edition describes fish **85g pieces**, vs 2022 **65g pieces**; milk relative height lacks a specified referent |
| **2020 54-7р-2020** (pollock) | Exact same named fish dish with onion preparation/blanch and milk treatment | 2020 text has **unspecified height referent**, not a source-correct replacement for the explicitly different 2022 instruction |

**Important source conflict:** the primary **2022 target pollock 54-7р** explicitly refers to **one-third of the baking tray's height**. The accepted R2-B FamilyFoodOS consumer Step 4 refers to **one-third of the fish's height**. These are not equal units of reference and may produce different liquid levels. The **2020 same-name** version and **2022 salmon/milk** say one-third *of height* without a specific noun, which offers a plausible lineage for the ambiguous phrasing but **does not overrule the chosen 2022 target source**. Do not mark the currently published recipe as source-identical throughout, overwrite Step 4 in place, or guess a home tray/milk-volume conversion.

**Decision on culinary provenance:** **GO** for the fish-with-onion-and-milk *general method*. **NO-GO** for asserting the target's complete production RecipeVersion matches its own chosen source, and **NO-GO** for auto-executable Step 1 at the historical family scale: there is no independently accepted home blanch technique, water/time/temperature/equipment capacity or current-fixture review, and a downstream step has an unresolved source discrepancy.

## 4. Source mass, actual household applicability, and no automatic safety promotion

Prior [bounded exact Decimal evidence](pr10-core-two-step-source-process-scale-decision-2026-10-23.json) calculated **research-only** net onion totals from historic three-member `Serving.portion_servings`:
- Salmon `9.8 × 5.916796 = 57.9846008 g` onion; source total sunflower oil `5.3 × 5.916796 = 31.3590188 g`. No split.
- Pollock `16 × 17.808807 = 284.940912 g` onion; `64 × 17.808807 = 1139.763648 g` fillet; milk `25.6 × 17.808807 = 455.9054592 g`.

These are **exact ingredient-demand projections**, *not* source-authenticated final prepared output masses, validated vessel capacity, safe oven time, physiological adult/child portion bounds, or sufficient process duration for a family-sized batch. The original books are school/catering recipe cards. Consumer-executable Prep eligibility additionally needs independent Recipe/Data + Domain/QA source/form/scale and accepted current fixture proof. The product-owner-approved Option B gate still requires two distinct `COOK_RECIPE` MealEvents with reviewed positive immediate actions and a negative unresolved case; neither criterion is waived because analogues exist.

**Food safety context is strictly separate:** the US official fish food-safety chart provides a current external generic context standard. FamilyFoodOS must not silently adopt it as a Russian `RecipeStep` temperature/process instruction or substitute it for an independently reviewed jurisdiction/source/recipe-specific policy; no new freezer/holding source numbers are introduced.

## 5. FACT / ASSUMPTION / DECISION / OPEN — final research decision

**FACT:** eight located **closely related published recipe cards** across the 2022 and 2020 Rospotrebnadzor collections corroborate both target *culinary sequences*. They are **four same-book species variants** plus **four earlier-edition variants**, not eight independent culinary trials. 2020 recipes are a related institutional publication, not authority for rewriting 2022. The 2022 original target pollock-versus-current R2-B consumer Step 4 has a **material unadjudicated tray-height-versus-fish-height discrepancy**.

**ASSUMPTION:** A qualified independent Recipe/Domain reviewer may be able to validate a suitable home process for one or both steps with explicit source-specific scale/equipment applicability, or decide that a separately reviewed immutable recipe/process correction is needed. Current evidence cannot prove this.

**RESEARCH DECISION** (this PR, **not an authorized runtime/data publication decision**):

| Scope | Outcome |
| --- | --- |
| General culinary technique is source-backed | **GO** for corroboration of source families only |
| New analogues as drop-in replacement for target source | **NO-GO**; variant and edition data identities differ |
| Salmon Step 1 as `APPROVED_IMMEDIATE` | **NO-GO** on available evidence |
| Pollock Step 1 as `APPROVED_IMMEDIATE` | **NO-GO** on available evidence |
| Pollock R2-B RecipeVersion full process matching exact 2022 source | **NO-GO pending Data owner adjudication** of Step 4 |
| Production step-eligibility/reader publication | **NO-GO**; independent human review and trusted anti-rollback status mechanism unimplemented |
| Starting PR10-A or declaring technical Gate2 ready | **NO-GO** |

**NEXT concrete decision for the owner:** explicitly route the **pollock `54-7р` Step 4 discrepancy** to Recipe/Data provenance adjudication and appoint an independent qualified Domain/QA reviewer for the full R3-C/R2-B steps in the actual accepted Gate2 fixture. After that independent finding, the owner can authorize **one immutable corrected RecipeVersion publication (only if proved necessary)** and/or **one D3 trusted eligibility publisher/reader implementation**, with source/version/anti-rollback/negative controls. No arbitrary further recipe hunt, invented recipe text, immediate action approval, automatic Gate2 reduction, or autonomous merge. If reviewers cannot justify either step, retain the scoped NO-GO and request a **new explicit product candidate strategy**, rather than repeating research forever.

## 6. Verification and limitations

This is a docs/evidence comparison only. Original current public PDF pages were inspected through web textual extraction; the screenshot endpoint failed and public PDF binary hashes could not be revalidated here. Existing Git blobs/accepted SourceVersion and first-step texts were independently checked against repository manifests on `main@5e5ee82f`. No human Domain/QA signed decision, home kitchen experiment, source publication, current live MealPlan/RecipeVersion pin, Planner serving feasibility, new deterministic Prep service, migration, API or PDF was executed. No `APPROVED_IMMEDIATE` was issued. Static JSON/diff/links/Docs CI and human review are required on the PR head before merge.
