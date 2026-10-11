# PR10-META-ONION — two source-backed onion-blanch instructions, one unverified shared operation

**Status:** `REVIEW_REQUIRED_SHARED_BLANCH_STAGE_NOT_PROVEN` (bounded evidence research, not product-ready).
**Accepted main:** `f30a756476067ca99f66c71610aa80347286be7b`, PR #206 MERGED 2026-10-11.
**Issue:** #207. **Gate:** `PR10-META=BLOCKED`.
**Authority:** [PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-META-PUBLICATION](pr10-meta-publication-path-feasibility.md), [previous same-day source audit](pr10-meta-same-day-pair-audit.md), [DATA-CORPUS-V1](data-corpus-v1.md).
**Machine-readable trace:** [Wednesday onion stage evidence](pr10-meta-onion-blanch-evidence.json).

## 1. FACT — a stronger pair than the blocked Tuesday wash/peel hypothesis

The validated *synthetic*, repository-persisted PR #196 weekly fixture includes two different meal events on **2026-09-16**, grounded in JSON sha256 `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec` from [accepted workflow #38059374826](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826), artifact #11672432141. These are traceable **temporary-fixture UUIDs**, not real-user data and not stable across new DB seeds.

| Pin | Wednesday LUNCH | Wednesday DINNER |
| --- | --- | --- |
| Recipe | `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES` (сёмга в томате с овощами) | `SCHOOL2022_54_7R_POLLOCK_IN_MILK` (минтай в молоке) |
| MealEvent UUID | `a3bd9a18-5ed6-4447-8a13-1b7b9416c45f` | `bf60e784-bd3e-4d62-96dd-54318fd5920c` |
| RecipeVersion UUID | `155f5283-2f2a-4487-83ac-895877197b45` | `16a04325-d532-45f6-82ca-2f30630467a6` |
| Process hash | `4fb058b03530ab54136e4bdf2d3b233681b10454629f03774aae5f9ba449028c` | `74e02d9c88421665f35e2f07c8cf54adfcad62200fe857de27bda87e0f36be71` |
| First RecipeStep SHA256 | `46ca78ea057058c50cb6d76417bdd01d08b05f7a7e6259848a12b98a548b5258` | `b6b9e45dc7afdf48d30247f33bc7fd71b154af29fe4a8075da53edb2e89affde` |
| Canonical common food | `ONION_BULB_FRESH` | `ONION_BULB_FRESH` |
| Accepted source net/gross onion g per base serving | 9.8 / 12.2 | 16 / 20 |

Actual servings: lunch has one member with Decimal `5.916796`; dinner three members with `5.631030`, `5.631030` and `6.546747`. These values are **pins**, not approval to multiply process-text numbers or invent source yield/holding. Only structured RecipeIngredient + exact backend Decimal Serving/food form semantics may compute production amounts.

Both **reviewed source process descriptions contain the operation `бланшировать лук`**:
- **Lunch:** accepted [R3-C frozen publication](../../data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json) for `54-17р` says prepare parsley root, carrot and bulb onion, *blanch the onion*, then **sauté it** with carrot/parsley and add tomato purée. This source does **not specify an exact onion cutting form before blanching**.
- **Dinner:** accepted [R2-B fish publication](../../data/curation/r2b-fish-main-diversity/publication-specs.json) for `54-7р` says prepare, **shred** and blanch the onion, then put it with pollock before hot milk and subsequent cooking. This is a different downstream process and form requirement.

Both reviewed recipe cards cite the **same** School2022 source PDF SHA256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`. They are two independently version-pinned recipe-card entries, **NOT two independent external source authorities**. This task uses their already reviewed **publication manifests** and frozen process evidence; it has **not** approved a new interpretation of the original PDF or any changed normative source text. Actual Card/Step IDs are frozen in the [JSON receipt](pr10-meta-onion-blanch-evidence.json).

**Why this is materially different from Tuesday:** both Wednesday recipes separately **name the exact same type of physical operation** (onion blanching), whereas the Tuesday ragout source only says vegetables are already prepared, and no equally explicit common wash/peel stage was reviewed. Zero identical *whole step hashes* in the [PR #202 same-day audit](pr10-meta-same-day-pair-audit.md) does not contradict overlapping suboperations inside different multi-action RecipeSteps.

## 2. SOURCE-COMPATIBILITY — a shared verb is not a verified shared component

| Required binding | Lunch salmon | Dinner pollock | Deterministic verdict |
| --- | --- | --- | --- |
| Exact raw FoodIngredient identity | `ONION_BULB_FRESH` | `ONION_BULB_FRESH` | MATCH |
| Operation named in original-reviewed *published* RecipeStep | Blanch onion, then sauté | Shred onion, then blanch | MATCH on verb; process fragments differ |
| Onion cut/input shape **before** blanch | Not specified in published step | Shredded | **UNRESOLVED form compatibility** |
| Output form/stage composition | Blanched onion passes into vegetable sauté | Blanched onion used separately with fish and milk | **NOT AN APPROVED COMMON OUTPUT** |
| Water, temperature, blanch duration, vessel and capacity for one batch | Not separately pinned | Not separately pinned | **UNKNOWN** |
| Meal preparation session/time and safe interim holding | Not in MealPlan | Not in MealPlan | **UNVERIFIED**, same day does not mean same session |
| Exact combined quantity and per-event provenance | Source-base net/gross and exact Serving pins available | Source-base net/gross and exact Serving pins available | Must use backend; **no shared-stage allocation published** |
| Step numeric instructions | No quantity in the first onion instruction | No quantity in the first onion instruction; **later fish-size/milk/cook** numbers exist | Later stages remain recipe-specific; PR10 §4.1 review still required |
| Physical workload reduction after washing/shredding/splitting/cleanup | Unknown | Unknown | **NOT PROVEN** |

A source-blanching instruction from one card **cannot be copied into the other with an invented cut form**, nor can two separately cooked fish dishes be treated as one physical cooking operation just because both blanch onions. The current `RecipeStep` model lacks source-verified stage input/output and any accepted cross-recipe retrieval or reviewer binding. `shared_work_group_key` cannot be set on this evidence alone.

## 3. Measurable conditional benefit and stop criteria

**Hypothetical baseline:** blanch the correctly prepared onion separately for each MealEvent = **two** physical blanching actions. **Hypothetical combined stage:** blanch a sufficiently compatible single batch once = **one** blanching action. The apparent saving of one operation is a *candidate estimate only*; it excludes possibly different chopping requirements, splitting the batch, washing equipment, safe handling, storage and recovery before different meal times. Therefore **no reviewed net `B < A`** and no measured minutes saved.

**Release requirements before any accepted shared stage:**

1. Independently review the exact two **source card process variants**, confirming whether salmon's pre-blanch onion form is compatible with pollock's shredded form. If the salmon source does not establish this, **BLOCK**; no inferred text amendment or source copying.
2. Verify the same input/output food form, reviewed pre-blanch conditions, batch capacity, physical process, exact stage identity and **separate** later sauté/assembly paths; source/rights/step hashes must remain pinned.
3. Confirm an actual simultaneous preparation session **without holding**, or independently review a stage-specific safe cold-chain/storage transition across lunch → dinner. Fixture has meal dates only; no Prep clock/holding state.
4. Produce exact RecipeIngredient + Decimal Serving allocation through accepted backend authority, not an LLM estimate or source prose; preserve all individual MealEvent contributions, RecipeVersion IDs, unit/form/basis and source fingerprints.
5. Observe or rigorously substantiate the **net** physical action count including mixing/splitting/cleanup/retrieval. Require at least one fewer action across two events without changing meal composition/nutrition, food safety or later process.
6. Under [merged PR #206 publication-path review](pr10-meta-publication-path-feasibility.md), freeze a **new source/data publication implementation contract** before any immutable recipe step correction or cross-recipe source reader. A source-curation JSON review is evidence only, not production authority. If either source lacks explicit required form/state evidence, return **BLOCKED for this pair** rather than invent.

## 4. Decision and bounded next move

**FACT:** two real synthetic MealEvents each have a reviewed, version-pinned recipe step expressly including blanching `ONION_BULB_FRESH`. The steps are not text-identical, require different post-blanch uses, and salmon's pre-blanch onion form is not stated in the current reviewed version.

**ASSUMPTION:** a sufficiently reviewed common blanching batch might save one operation when both meals' ingredient forms and preparation session are compatible. Neither form nor safe interval is yet evidenced.

**DECISION:** `REVIEW_REQUIRED_SHARED_BLANCH_STAGE_NOT_PROVEN`. The Wednesday pair is a stronger **source-research candidate** than Tuesday's wash/peel, **not an accepted safe/executable shared Prep stage**. **PR10-META remains BLOCKED**; no PR10-A/B/C, PrepPlan runtime, Pantry mutation, freezer/holding duration publication, PR10-PDF or Gate2 completion.

**NEXT:** a single **bounded original-card source/form validation** for `School2022:54-17р` and `54-7р` with a YES/NO output-form equivalence decision. Do **not** start an open-ended series of string-similarity audits. If form equivalence fails, stop and explicitly request authorization to source/review recipes with published batch-friendly stages or update Gate2 fixture selection through a separate approved change.

**Verification:** docs/source JSON receipt only; exact event/version/hash provenance, internal references, whitespace, scope and Docs CI. No production runtime/schema changes or broad backend regression.
