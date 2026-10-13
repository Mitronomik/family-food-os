# PR10-FD-META — one source-backed fully cooked goulash batch candidate

**Issue:** [#223](https://github.com/Mitronomik/family-food-os/issues/223)
**Base:** `main@89b13a61fbfb8bb6246b7fb39ad8b3a1a3acf352` ([#222](https://github.com/Mitronomik/family-food-os/pull/222) merged).
**Authority:** [accepted Finished-Dish-First amendment](pr10-finished-dish-first-amendment-2026-10-12.md) §§3.1/4.1, [D1–D3](pr10-data-recovery-approved-decisions-2026-10-11.md), [R1-G source provenance](../../data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json).
**Scope:** exactly **one** currently reviewed Russian recipe and one isolated persisted research-only repeated-recipe MealPlan; no other food source hunt, no real household inventory, no runtime or accepted Gate 2 fixture change.

## 1. FACT — precise cooked-dish RecipeVersion candidate

**Selected:** `SCHOOL2022_54_2M_BEEF_GOULASH` — «Гуляш из говядины», source card `ru-school2022:recipe:54-2м` from the already accepted School2022 recipe source. The [R1-G immutable publication manifest](../../data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json) has Git blob SHA `394b35d3d02c0498a681584a37d36b1d98faf40d`, original source document SHA-256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`, and exact card SHA-256 `d48a9461e98d4d2df0056c379722dc9e6ed248dc74ce65a4a118a1165565209d`. Original PDF: [School2022 collection](https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf), which this PR does **not** re-download or claim to have freshly independently verified byte-for-byte. Accepted R1-G rights basis is `REVIEWED` for bounded factual normative recipe records, not blanket permission to republish external safety prose.

The published immutable seed specifies one base serving, **80 g source output** (meat 46.6 g plus sauce 33.4 g) and seven structured ingredient records: beef 74 g, onion 9.3 g, tomato puree 7.3 g, butter 4.3 g, flour 2.5 g, iodized salt 0.2 g and water 107 g. This is the **source base recipe**; total raw ingredient mass is not cooked mass, and the published 80 g output does **not** justify assuming linear kitchen yield at an increased batch size. The process has five Russian steps, including thawed/raw beef, chopped/blanched/sautéed onion, braising, a flour sauce, and a final cooked meat-with-sauce dish.

**Accepted metadata is deliberately incomplete:** `batch_friendly=null`, `freezable=null`, `storage_days_fridge=null`, `storage_days_freezer=null`, `prep_time_minutes=null` and `total_time_minutes=null`. Source step text contains cooking timing, piece-size and sauce temperature numbers that require PR10-ARCH §4.1 reviewed numeric-instruction classification before any scaled executable kitchen direction. The original source document proves a finished dish recipe, **not** a validated home-frozen ready-meal procedure.

The exact author/source, process text, amounts, rights and nulls are frozen without reinterpretation in [source evidence JSON](pr10-fd-meta-goulash-source-evidence.json).

## 2. Official primary-source research — applicable category ≠ accepted recipe policy

| External source | What it actually supports | What it does **not** yet prove |
| --- | --- | --- |
| [NCHFP / University of Georgia — Freezing Soups and Stews](https://nchfp.uga.edu/blog/freezing-soups-and-stews-a-good-wintertime-activity) | General **already cooked** soups/stews portion-packaging, rapid cooling, freezing, later reheating and quality limitations; article published 2019-02-18 | No independently reviewed specific School2022 goulash freezer-quality result, batch vessel capacity, source-card stage mapping or Russian household policy approval |
| [USDA FSIS — Leftovers and Food Safety](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/leftovers-and-food-safety) | Generic cooked leftover safe handling, rapid cooling in small/shallow containers, cold storage, methods of thaw and reheat | No actual initial thaw/cooking/holding history for a particular family, or reviewed source-specific multi-event plan |
| [FoodSafety.gov — Cold Food Storage Chart](https://www.foodsafety.gov/food-safety-charts/cold-food-storage-charts) | Published category for **soups and stews with meat/vegetables**, distinguishes refrigerator safe limits from freezer-duration **quality** guidance | No reviewed legal/jurisdiction transfer of US rules to Russia or proof of good texture after reheating this exact dish |
| [Роспотребнадзор — Правила хранения продуктов и готовых блюд](https://09.rospotrebnadzor.ru/node/12724) | Official Russian regional consumer storage discussion, including **soup** and **fried beef** categories | Neither category is independently established as exactly this finished **beef goulash with sauce**, and it does not approve our end-to-end freezing, cooling and reheating workflow |

The U.S. official references contain **quantitative food-handling advice**, but it is **research-only information** here. Different jurisdictions/categories are not interchangeable. No third-party web page is pinned as a byte-identical immutable policy snapshot or accepted into the FamilyFoodOS **policy owner, versioned publisher/read path, Russian instructions, applicability matrix and revocation** boundary required by D3. The [external guidance references](pr10-fd-meta-goulash-source-evidence.json) are attributable research links, not production authority. The source cookbook's School2022 PDF and its card SHA-256 remain the accepted recipe truth, not the safety-policy authority.

**Quality must be reviewed separately from safety:** the described finished goulash is meat plus sauce, which fits a broad stew category, but the original card has no accepted `freezable=true` nor a reviewed verdict on thaw/reheat texture and scaled equipment capacity. `UNKNOWN` does not mean `UNSAFE`, but it forbids an executable freezer-plan claim.

## 3. Research-only proof without changing Gate 2

Added [`scripts/audit_pr10_fd_meta_goulash.py`](../../scripts/audit_pr10_fd_meta_goulash.py), focused [adversarial tests](../../backend/app/tests/test_pr10_fd_meta_goulash.py) and [dedicated CI](../../.github/workflows/pr10-fd-meta-research.yml). This **evidence script is not production runtime**:

1. Initialize **fresh disposable SQLite** from existing A3/DC4 reviewed seed; never connect to live/user data.
2. Create one synthetic Household and one verified seven-day dinner-only meal pattern with the existing service helpers. Persist a normal deterministic Planner baseline.
3. Construct a **second immutable MealPlan revision** through real `MealPlanService.create_plan_revision` / `MealEventDraft` where **two distinct** Monday/Thursday `COOK_RECIPE` MealEvents point to **the same actual currently verified goulash RecipeVersion ID**. Preserve the other five event source pins. Re-read the exact current revision, validating Household/member schedule and positive Decimal Servings.
4. Compare a semantic digest computed independently from intended `MealEventDraft` inputs with the persisted events and member servings; freeze actual synthetic `MealPlan`/Event/Serving IDs and immutable RecipeVersion/RecipeStep hashes. UUIDs are **ephemeral and different on every fresh run**. The externally logged JSON file SHA-256 provides the independent artifact integrity anchor.
5. Run backend-owned `scale_recipe` on the combined exact Decimal target servings and separately per event. Check `combined RecipeIngredient demand == per-event sum` for all seven inputs. This prevents *research planning quantity double count* but does **not** change the existing Shopping Engine or claim its production integration.
6. Emit an explicitly `BLOCKED`, `TIME_UNRESOLVED`, `UNAPPROVED_RESEARCH_ONLY` research receipt. Do **not** create a PreparedBatch, freezer portion stock, synthetic production customer data, source-authorized time windows, temperature measurements or safe-through date.

**Receipt status:** The JSON artifact, actual fixture UUIDs, semantic digest and separate JSON SHA-256 are valid **only after the exact-head research CI successfully emits them**. This documentation does not invent identifiers, reuse an older acceptance fixture artifact or assert a local run. If CI fails, the persisted two-event proof remains **NOT VERIFIED**, not automatically PASS.

This is a constrained manual `MealPlan` revision validated by the accepted **domain/application service**, **not** an assertion that deterministic Planner would have selected the same repeat by default or that the repeated meals satisfy a full personalized nutrition target. That requires a distinct product gate. It also does not change the accepted historic three-member Gate 2 fixture, whose 21 selected recipe codes remain different.

## 4. FD-META GO/NO-GO against approved Finished-Dish-First contract

| Required assertion | Present proof / pending requirement | Verdict |
| --- | --- | --- |
| Exact RecipeVersion and original verified Russian source, rights | R1-G source/card hashes and accepted rights; runtime version verified in disposable seed by script | **CANDIDATE / PASS subject to CI** |
| Two persisted MealEvents with same RecipeVersion, exact Decimal member Servings | Isolated manual revision, independent planned-vs-readback digest; CI artifact required | **PENDING research CI** |
| One combined ingredient demand, no double count | Backend `scale_recipe` combined equals exact per-event sums | **PENDING research CI** |
| Source-approved method and equipment for full batch | Unknown; old seed `batch_friendly=null`; kitchen batch capacity not reviewed | **BLOCKED** |
| Final dish freezer-quality applicability | Finished stew category guidance, but no accepted dish-specific quality/process review | **BLOCKED** |
| Time authority for cooking → cooling → freezer entry → retrieval → reheating | Existing MealEvent only carries date. No actual or independently approved proposed cooking/hold time windows for this use case | **`TIME_UNRESOLVED` / BLOCKED** |
| Applicable versioned safety policy / Russian executable steps | US public general advice and RU category context; policy not adopted or byte pinned; numeric RecipeSteps not cleared for scaling | **BLOCKED** |
| D3 metadata publication/read owner and separate Gate 2 fixture D2-FD | Not executed or authorized by this research PR | **BLOCKED** |
| Actual frozen food ready to consume | No user confirmation, no PreparedBatch, no physical stock by design | **NOT CLAIMED** |

**DECISION:** `PR10-FD-META=BLOCKED` for the exact goulash candidate **until** independent acceptance of a suitable source/jurisdiction/time/cooling/freezer/quality/batch policy and its publication/read path. The receipt may successfully prove two MealEvents and exact ingredient scaling, but cannot turn the source's null storage fields into `freezable=true` or authorize a user-facing frozen meal instruction. No net physical actions/minutes savings are claimed; **proposed independent cooking sessions 2 → 1** is a research hypothesis contingent on the safety gate.

## 5. FACT / ASSUMPTION / DECISION / OPEN QUESTION; delivery

**FACT:** R1-G accepts a full cooked Russian beef goulash recipe with exact numeric ingredient basis and source/card identity. Official NCHFP/FSIS/FoodSafety resources explain *general cooked stews*, not accepted RecipeVersion-specific storage policy. Current MealPlan date-only time and null freezer metadata remain limitations.

**ASSUMPTION:** safe batch scale and correctly cooled/stored/used cooked goulash *may* be supported after independently reviewed consumer safety/quality authority. Category similarity or repeated recipe name is not approval.

**DECISION (this scoped research):** one precise fixed candidate. Stop on NO-GO rather than create more recipe-pair sourcing PRs. Do not auto change D2, accepted fixture, D3, recipes, runtime or Pantry.

**OPEN PRODUCT/DATA QUESTION:** who owns the jurisdictional finished-dish safety policy, can a specific original goulash process and scaled batch be reviewed against it, and how will a future runtime obtain authoritative cooling/usage time windows under FD-ARCH §4.1? This requires **one targeted food-safety/policy-owner and D3 review decision**, not another arbitrary ingredient matching cycle.

**Verification:** CI runs an isolated persisted research fixture, adversarial tamper/negative policy tests, recipe source pin validation, Decimal reconciliation, Ruff, docs links/scope and independent SHA of temporary JSON. Real user data not used. `AI_ENABLED=false`. Historic Gate 2 baseline and RecipeVersion publication remain byte-unchanged.

**Post-review stop:** the current PR may merge a well-supported `BLOCKED` evidence report. **PR10-FD-META READY, PR10-FD-A/B/C, PR10-PDF and Gate 2 are NOT authorized by that merge.** Any next scope requires a separate explicit owner decision and D3 contract.
