# PR10-CORE — current forward fixture positive-data / D3 / schema preflight

> **Later proposed sequencing exception (2026-11-02):** [PR10-A1 pure diagnostic calculation amendment](pr10-pure-calculation-sequencing-amendment-2026-11-02.md) would allow the **separate future pure, non-executable** domain calculation substep to proceed after review/merge and explicit owner authorization **without** the positive step eligibility currently missing from this preflight. The source-readiness `NO_GO`, `APPROVED_IMMEDIATE=0`, D3 and positive Gate2 conditions recorded here **remain true for executable/persistent/user-actionable Prep**. This note does not retroactively turn the audited steps into approved instructions or authorize implementation.

**Date:** 2026-11-02
**Tracking:** [Issue #273](https://github.com/Mitronomik/family-food-os/issues/273).
**Base:** accepted `main@418756bfc16af4b6786226725438d075f7ddd609`, after [PR #272 merged](https://github.com/Mitronomik/family-food-os/pull/272).
**Status:** `GO_TO_INDEPENDENT_SOURCE_STEP_REVIEW_ONLY`; `NO_GO_TO_PR10_A_RUNTIME`, `APPROVED_IMMEDIATE=0`.
**Scope:** test-only / docs-and-source-evidence preflight on *the actual newly accepted* `PR10_FF_FORWARD_3M_7D_V1`. This is NOT PR10-A/B/C implementation, eligibility publication or a completed Gate2.

## 1. FACT — input truth and reproducible weekly evidence

Owner acceptance: [PR10-FF exact-fixture decision](pr10-ff-owner-fixture-acceptance-2026-11-02.md). The independent [review report](pr10-ff-final-evidence-review-2026-11-02.md) pins synthetic three-member household, `Europe/Moscow`, 2026-11-02..08, **21 real persisted COOK_RECIPE MealEvents and 42 six-place Decimal Servings**, source A/B and semantic hash. `PR10_FF_FIXTURE_REPRODUCIBLE=PASS` for this *specific synthetic energy-only technical week*, and for no other week.

Raw evidence for this preflight was freshly obtained from the original [#269 final-head Actions run #41309700338, artifact #13084512933](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338/artifacts/13084512933). Independently rehashed ZIP SHA256: `6a9943ed1819231ac6bb52005b9b8b8af8e912749efa98d4260b46f2a9bb7fb2`. Its two persisted readback receipts independently match semantic-week SHA256 `45c8773b6bd51fdb9f69f8c887dc2c66ae8a7674756b4787e72995a6d84df5e2`, normalized actual input SHA256 `5f812e41de2d3f2b11526503e72a1bc1b1371345b9ea68a64f55e21d7aa27966`, and provenance SHA256 `6e03e03865ce95bcca5d61d77652b4b1c4af4243bdfca966dae4d88902c0558c`. No other Planner run, week or output selection was performed.

Frozen source A: [publication-A-PROPOSED.json](evidence/pr10-ff-forward-input-v1/publication-A-PROPOSED.json), Git blob `27f6ea8284b30785fe3c0fd512b3963b1166efb9`; frozen B: [planner-B-PROPOSED.json](evidence/pr10-ff-forward-input-v1/planner-B-PROPOSED.json), blob `d2dd93987ec48109a73cbf1c7efe0ac0a56d9bbe`. All 51 current candidates are `exact_energy_ready=true` but `nutrition_status=INCOMPLETE`, so the evidence is **not** nutritionally complete and does not validate meal-size plausibility, human dietary suitability or actual equipment capacity.

### Complete selected event identity inventory (from persisted source-provenance receipt)

Every row is a **distinct current** RecipeVersion event; the UUIDs are *fixture-specific* and must not be reused as global production/consumer identifiers. Process SHA256 is the reviewed ordered-step publication digest. No row has published executable `APPROVED_IMMEDIATE` eligibility.

| Local date | Role | Source code @ version | RecipeVersion UUID | Ordered-process SHA256 |
| --- | --- | --- | --- | --- |
| 11-02 | BREAKFAST | `SCHOOL2022_54_6K_MILLET_MILK_PORRIDGE@1` | `00b6db61-8739-48dd-8d3a-d56483fa35d5` | `cfbf43bd843b539970474f98b6ca16daa82f3b3fb0c2f96d67e4b63b963f7ce1` |
| 11-02 | LUNCH | `MR2019_6_9_VERMICELLI_HARD_CHEESE@1` | `03f48fc3-afa0-4d10-bccc-6ed66f86b1aa` | `c11bd2b629be499885772fc4442a36650dcdd7cd932e1fa733c2f97852de8216` |
| 11-02 | DINNER | `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES@1` | `0a5bef8a-2ca6-4940-a894-16ad78bcfea3` | `14186123f8c63516d8793cb186a482a80ae5eacb1b957bedf6d99affeb8e71a3` |
| 11-03 | BREAKFAST | `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE@1` | `025fc5c5-95f8-4e37-bffd-937f5630798b` | `d6340081a54597250753ef81de33af980212098c7e3a6ba292ac4710fe8af20b` |
| 11-03 | LUNCH | `SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE@1` | `0ae60b54-02ad-4a18-89c3-126229d84571` | `4213cad92430e538e14b256f8282fab4c4d5d03e4eb97de57f76caca98f95f91` |
| 11-03 | DINNER | `MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP@1` | `26c44181-5ed7-4ad3-b984-7800a7685b1b` | `4ffa3cc1fa81cfb1a235782ff2eb9e489f8ddeaeeb5fce42d05e6defa8072741` |
| 11-04 | BREAKFAST | `SCHOOL2022_54_23K_LIQUID_WHEAT_MILK_PORRIDGE@1` | `0bf11207-ead0-464d-a802-84f97a4f0249` | `e092d47b47d3f14ab2f11453cd0d428ca8c007fd1846419bc1e7105cf63526a6` |
| 11-04 | LUNCH | `SCHOOL2022_54_7M_BEEF_SCHNITZEL@1` | `0c4cfd6b-2b7a-4338-879f-f10fe7fe126a` | `1ad7e9f0a45f4174d8891bb0fd8a9a6d68669383b63d50d300342b89eefe447e` |
| 11-04 | DINNER | `SCHOOL2022_54_15R_SALMON_IN_MILK@1` | `34485bc2-59df-4c1b-9a24-86e1479eaf8a` | `03882bef1d41e7c9e616587c351248646338bca7da2bb9623497bde12244c12a` |
| 11-05 | BREAKFAST | `SCHOOL2022_54_1O_NATURAL_OMELET@1` | `113e3ed3-9ed2-43dc-9134-0e1da5b69c93` | `76d08d815ef143cd62d9148679af6a9c7bc199b1b9857b34dc869e0cb7aea73c` |
| 11-05 | LUNCH | `SCHOOL2022_54_29M_BEEF_MEATBALLS@1` | `24122a63-b080-497f-85de-db698556f750` | `0f872d9f691358b6388617d0890a6280a2c9f6ec055b1da54b77bc15224adf69` |
| 11-05 | DINNER | `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK@1` | `47c61e6e-6c16-4e24-abc0-f14901a25452` | `fec67a464e9ffe6641f68bc4463a722cb837b3a06e433e0641ddfd00636d2f27` |
| 11-06 | BREAKFAST | `SCHOOL2022_54_3O_CARROT_OMELET@1` | `13813b98-e92e-49fb-a123-6d7b3fec31cf` | `a13184806c7e6136e05a538268e3f5b3b7c6b25b5dae829fdef7d0db9e6227b0` |
| 11-06 | LUNCH | `SCHOOL2022_54_11M_BEEF_PILAF@2` | `2889a305-4d0f-46ff-afca-2f5c449072ac` | `7844357799d5800cf6e5884191d07d0a361ed8778cdec845a60ed71af4deb5f3` |
| 11-06 | DINNER | `SCHOOL2022_54_21M_BOILED_CHICKEN@1` | `6136dfe9-4902-4603-8c0e-1983de0e587a` | `1a9dab09def084abc199f314616f92e1db96f5028333a1fd4c8bef1128a29138` |
| 11-07 | BREAKFAST | `SCHOOL2022_54_24K_LIQUID_MILLET_MILK_PORRIDGE@1` | `1f37cff2-795e-4e0b-a21d-6667970f0576` | `2267ffa613a08b9204e792af8a129bf05d9ec72e6f295a513f086dffef1785de` |
| 11-07 | LUNCH | `SCHOOL2022_54_2M_BEEF_GOULASH@1` | `361f12ea-2144-4876-a5f8-6f798a92a26e` | `424af2245fa79c102258bff27d3c54b391fd33450b91818133b03116d2416ffe` |
| 11-07 | DINNER | `SCHOOL2022_54_1R_COD_CUTLET@2` | `656dbe12-f2d4-4b9f-ba78-d9850b0c1905` | `c130109bcc881a545f17007c17108d05612e44c2297dcaec78c77870d75f98b9` |
| 11-08 | BREAKFAST | `SCHOOL2022_54_2K_VISCOUS_CORN_MILK_PORRIDGE@1` | `31d36b91-3d2e-4aa6-9363-57d7c5aebbc6` | `2807cf22feb369bbe976c9ce75e1986cd595be7c48b7215397adb8971ff53b54` |
| 11-08 | LUNCH | `SCHOOL2022_54_20M_BOILED_BEEF@1` | `37bba0b5-2440-48dc-8469-6f77bc13f351` | `d17ea14ab638836601ab4a668847b7d8a277b3bd2e600f63447b62c7b07a12a9` |
| 11-08 | DINNER | `MR2019_1_3_LENINGRAD_RASSOLNIK_SOUR_CREAM@1` | `6794ea52-7ca6-4766-82c4-6f262c14cfa8` | `fce997552bb14f77306b8b61589f818dcf56c3c33def6ecb2aabc737b084aa16` |

**Important:** this inventory ties MealEvent to *current selected RecipeVersion/process*, NOT the per-Step persisted UUID, a reviewed `ReviewedRecipeStepEligibilityV1` grant, physical safety or full nutritional authority. A/Step publication permits inspection only. Distinct 21 events and 42 servings do **not** imply 21 approved Prep actions.

## 2. EXACTLY TWO source-backed nonthermal Step 1 review candidates

These are an explicit **bounded research choice**, not a change to the accepted Planner week, not a substitute for the [historic 21-event triage](pr10-fixture21-action-class-review-2026-10-23.md) or a production allowlist. They are at different MealEvents/dates.

| Current accepted event | `RecipeVersion`/source pinned | Original Step 1, exact published Russian source text | Status |
| --- | --- | --- | --- |
| **2026-11-03 BREAKFAST**, members **1+2**, `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE@1` | UUID `025fc5c5-95f8-4e37-bffd-937f5630798b`; source `ru-school2022:recipe:54-20к`; ordered-process SHA `d6340081a54597250753ef81de33af980212098c7e3a6ba292ac4710fe8af20b` | «Гречневую крупу перебрать и промыть, несколько раз меняя воду.» | `PENDING_INDEPENDENT_REVIEW` |
| **2026-11-08 BREAKFAST**, members **1+2**, `SCHOOL2022_54_2K_VISCOUS_CORN_MILK_PORRIDGE@1` | UUID `31d36b91-3d2e-4aa6-9363-57d7c5aebbc6`; source `ru-school2022:recipe:54-2к`; ordered-process SHA `2807cf22feb369bbe976c9ce75e1986cd595be7c48b7215397adb8971ff53b54` | «Перебрать и промыть кукурузную крупу, несколько раз меняя воду.» | `PENDING_INDEPENDENT_REVIEW` |

Both initial source instructions were fetched from **A's original frozen `seed_projection.steps[0]`**, `base_servings=1` and `rights_review_status=REVIEWED`, `verification_status=SOURCE_VERIFIED`. Their shared School2022 source-document SHA256 is `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`, from previously accepted source authority; its public PDF binary was **not newly retrieved/re-hashed** in this preflight.

**Exact Decimal research only** — structured net-ingredient base quantity × exact persisted member `Serving.portion_servings`, without floats, rounding to package, cooked-yield inference or assumed water conversion:

| Pin | Buckwheat, 11-03 | Corn groats, 11-08 |
| --- | --- | --- |
| Member 1 Serving | `3.798916` | `2.472331` |
| Member 2 Serving | `4.416695` | `2.874382` |
| Total base Servings | `8.215611` | `5.346713` |
| Source net grain per base | `38 g BUCKWHEAT` | `57 g CORN_GROATS` |
| Exact research grain input | **`312.193218 g`** | **`304.762641 g`** |
| Source recipe *cooking* water per base | `64 g WATER` | `65 g WATER` |
| Additional rinse water | **UNKNOWN / NOT SCALABLE FROM THE STRUCTURED COOKING WATER** | **UNKNOWN / NOT SCALABLE FROM THE STRUCTURED COOKING WATER** |
| Source Step 1 numeric direction / thermal verb | None literal in the *first Step 1 text only* | None literal in the *first Step 1 text only* |
| Independently approved numeric classification | **0** | **0** |
| `APPROVED_IMMEDIATE` and scale/equipment/food-form verdict | **NO_GO / NOT REVIEWED** | **NO_GO / NOT REVIEWED** |

These are source-based **input projections**, not approved human portions or executable quantities. The following steps of both recipes do contain thermal/numeric cook processes. Whole-Step 1 review, current *persisted Step UUID/instruction hash*, source-original vs current published process completeness, member scale feasibility, food form and rinse-water/equipment applicability are not independently approved. A nonthermal or digit-free line can still be unhelpful or inapplicable as a separately useful PrepTask. **Do not** split/edit the RecipeStep, silently infer washing duration, sieve or water quantity, or assert source-backed cooking safety from a single sentence.

### Historical carry-over is explicitly prohibited

The 2026-09 historical positive-data [salmon / pollock first-step review](pr10-core-two-step-source-process-scale-review-2026-10-23.md) remains `NO_GO_TO_APPROVED_IMMEDIATE`. Current 2026-11 fixture has a salmon dish on **11-02 DINNER**, not the 2026-09 salmon MealEvent, and **no selected `SCHOOL2022_54_7R_POLLOCK_IN_MILK`**. The source-uncertainty/oil-split and published-vs-original pollock process conflicts are not resolved by the new week. The historic [cottage-cheese/corn review class](pr10-fixture21-action-class-review-2026-10-23.md) does **not** automatically approve the current buckwheat or distinct `VISCOUS_CORN` recipe. A new source/RecipeVersion/Step/Serving applicability decision is required.

## 3. Prep schema / Unit of Work / D3 trust preflight

- Current `main` GitHub migration directory `backend/app/migrations/versions/` contains migration history through **`0043_shopping_engine.py`**, with no registered `prep_plans`, `prep_tasks` or `prep_unresolved_obligations` migration. The concrete SQL/UoW/transaction implementation for those three prospective tables is **NOT IMPLEMENTED/NOT VERIFIED**. This report reserves no migration ID and creates no schema.
- [PR10-ARCH](pr10-prep-freezer-implementation-contract.md) retains the default immutable three-table design and Household-scoped authoritative read → atomic write, failure/rollback/idempotence, revision staleness and tenant isolation requirements. Source-only preflight says **conceptually compatible for ungrouped same-day tasks**, not proven compatible with an implemented Prep repository.
- [Option B](pr10-option-b-staged-delivery-gates-2026-10-17.md) requires one accepted **current** Household fixture, at least two separate approved positive task-bearing events, a genuine unresolved case, and technical Shopping→Prep→PDF full proof, with `AI_ENABLED=false` and no Retail; it does **not** waive D3 source/reader prerequisites.
- [Accepted D3 contract](pr10-core-step-eligibility-d3-contract-2026-10-22.md) and [two-step publisher/reader decision](pr10-core-two-step-publisher-reader-acceptance-2026-10-23.md) require a separate current `ReviewedRecipeStepEligibilityV1` publication identity, independent reviewer and source-/Step-/version-/process-/scale-pinned whole-action approval, plus a **rollback-independent monotonic revocation/current-status authority** with fail-closed reader (including `ACTIVE → REVOKED → old deployment rollback` remains denied). No such authority, signed approval or runtime reader is established by this report. Research JSON and this doc must **never** be treated as an executable allowlist.
- A successful independently signed source/scale review of **both** Step 1 candidates would still **not** establish `APPROVED_IMMEDIATE` until a separately accepted release/read trust package exists. Any discovery requiring new persisted identity, release status authority or repository/transaction schema change must trigger a separate docs-only high-coupling implementation gate **before** PR10-A code.
- Source/Prep planning may not mutate Pantry/Shopping inventory, confirm cooking, grant storage/freezer expiry or assert physical work savings. The separate portion-quality release gate remains unmet.

## 4. Decision and next bounded step

**FACT:** the technical Planner fixture is reproducible and contains two **source-text and structured-ingredient-traceable** nonthermal preparation candidates in two distinct genuine MealEvents. This preflight only observed source text, current RecipeVersion/Step process SHA and exact Decimal grain inputs; it did not certify physical performance, whole-Step eligibility or active authority.

**DECISION (scope limited to this preflight):** `GO_TO_INDEPENDENT_SOURCE_STEP_REVIEW_ONLY` for exactly the 11-03 buckwheat and 11-08 corn Step 1 at their actual member scale. **Runtime determination:** `NO_GO_TO_PR10_A_RUNTIME`, `NO_GO_TO_PR10_CORE_RUNTIME`, `APPROVED_IMMEDIATE=0`; no entitlement to a Prep calculator, publisher, migration, API, PDF or Gate2. Source candidate observations are not a policy/status publication.

**OPEN / explicit next owner choice:** authorize a separately bounded independent Recipe/Data/Domain/QA review of the **two named actual Step 1** candidates with whole-step origin/process, ingredient form, independently pinned Step ID/hash, exact aggregate Decimal factors and household equipment/water/meaningful separate Prep-action applicability. If either fails, retain `NO_GO` and return for an explicit different source/contract decision: **do not silently pick a third recipe or tune Planner selections**. Before any executable publication, independently review the D3 publisher/reader and rollback-independent anti-revocation infrastructure contract.

**Hard gates unchanged**: `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`, `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`, `APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_CORE_RUNTIME`. Historical PR #196/#254 evidence immutable. This task does not authorize PR10-A/B/C, Gate2, real-family use or release.

**Verification performed:** re-read current `main` merge, owner-accepted A/B source projections, original #269 real persisted two-process raw artifact and exact 21-event/42-serving provenance, Step 1 texts/rights/version/process, and actual migration directory. No new Planner runtime, production tests, culinary validation, original PDF binary download or eligibility publication performed. Docs-only CI / independent review required before accepting this document.
