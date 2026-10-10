# PR10-META-SHARED — actual two-MealEvent preparation compatibility preflight

**Status:** SOURCE-PROCESS CANDIDATE IDENTIFIED; **SAFETY / STORAGE / SHARED EXECUTION BLOCKED**.
**Accepted main:** `c73f8a935a1c8ab39d1897310ed326005d0b68fd` (PR #196 merged 2026-10-10).
**Issue:** #197.
**Canonical gates:** [PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-META BLOCKED](pr10-meta-readiness-decision.md), [Gate2 fixture lineage](pr10-meta-gate2-fixture-evidence.md).
**Machine-readable frozen pair:** [PR10-META-SHARED source/pin evidence](pr10-meta-shared-process-evidence.json).

## 1. FACT — exact source of the two MealEvents

The actual **synthetic persisted** three-member fixture JSON came from PR #196's **final accepted** [workflow #38059374826](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826), artifact **11672432141**, JSON SHA256 **`6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`**, ZIP SHA256 `01ed6919e062ff7d97f11499fded7c22d413faa2490a26374a8198610f262d45`. The independent pure-Planner semantic baseline SHA256 is `2d6cb581649863b7edbd3c0efff2bae2934c6a512c99a45d10e92f92f514cb3d`. I examined the downloaded JSON and independently verified the **JSON** SHA256 before selecting the pair. The artifact is retained only temporarily; this PR freezes the minimum relevant two-event identifiers and process hashes so the research is reviewable after artifact expiry.

Both MealEvents belong to the same synthetic `MealPlan.id=589ef95a-2158-40a1-af91-0e13087d5744`, week 2026-09-14, source kind `COOK_RECIPE`, role `LUNCH`; each has the exact accepted `Serving.portion_servings=3.751136` for the same synthetic member. These are **fixture-only UUIDs**, not real people or identities stable across a new temporary DB build.

| Actual persisted fixture event | Friday, 2026-09-18 | Saturday, 2026-09-19 |
| --- | --- | --- |
| Meal / source code | Шницель из говядины, `SCHOOL2022_54_7M_BEEF_SCHNITZEL` | Биточки из говядины, `SCHOOL2022_54_6M_BEEF_BITOCHEK` |
| Event UUID | `ece787f4-ac81-4390-b57f-211c220b02a9` | `63c2c701-ce68-4637-8a96-07252d32fde5` |
| Current fixture RecipeVersion ID | `343a786b-3338-4d30-825e-486ce70dae54` | `34ec0fa8-c724-424c-819f-fa6823264d04` |
| Recipe source ID | `ru-school2022:recipe:54-7м` | `ru-school2022:recipe:54-6м` |
| Base servings | 1 | 1 |
| Source process hash | `df66b058337957720f8e0d88a3094fe439a2db29a363cf9ff7a61cb900a9299c` | `fb6cd597cc1511d048fe2d7396fcdd956a5522138a5120a6df6a395421903993` |

Provenance in accepted [R3-A School2022 publication specs](../../data/curation/r3a-school2022-main-batch/publication-specs.json): exact source variant cards **54-7м / 54-6м**, PDF pages 120/119, shared source document SHA256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`; `rights_review_status=REVIEWED`. **This investigation uses the accepted reviewed source manifest; it does not claim fresh inspection or independent safety approval of the upstream PDF.**

## 2. FACT — common source step, but distinct executable outcomes

Both source process manifests show exactly the same **first step**: grind prepared beef and combine it with stale wheat bread previously soaked in milk. The exact step-text SHA256 in **both** published RecipeVersions and in the persisted fixture receipt is:

`2d5b8a370947b64df0b0526ab55caa970be93ee062438c066024d26ab8a689da`.

The R3-A manifest ingredient rows also match across these two exact recipe variants (per **one source base serving**, NOT precomputed scaled Household quantities):

| FoodIngredient | Source input to each individual recipe |
| --- | ---: |
| `BEEF_CATEGORY_1_RAW` | 64.5 g |
| `MILK_2_5` | 17.3 g |
| `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE` | 14.3 g |
| `BREADCRUMBS` | 8.3 g |
| `BUTTER_PEASANT_72_5_UNSALTED` | 5.3 g |
| `SALT_IODIZED` | 0.2 g |

A plausible **review candidate** is to combine the first raw-beef and soaked-bread/milk preparation once for both events, but **not** to conflate their later recipe instructions or final cooked product forms.

Step 2 differs: the source instructs forming **шницели** for one RecipeVersion and **биточки** for the other. Step 3 has identical source words and equal text SHA256 `11bf546fb904bf8955a21d1f8ad2ec437aee81d39ad1a03f2ab2c2086505ac56`, but it involves breading and final baking **after different shaping**, on **different calendar days**. Identical prose does **not** confer identical prepared-food state, equipment capacity, safe holding or authority to cook both meals on Friday.

These source versions have **NULL** `batch_friendly`, `freezable`, `storage_days_fridge`, `storage_days_freezer`, `prep_time_minutes` and `total_time_minutes`. RecipeStep has no reviewed step-level active/passive time, storage transition or shared intermediate component entity. This is the **exact data blocker**; a string hash match is a useful identity candidate, not an executable batch instruction.

**Numeric authority:** the published source uses cooking temperatures/times in step 3, but it has no approved reviewed stage/equipment capacity at combined input scale; PR10 §4.1 numeric-step safety review is required. Do not invent two-day safe hold, a safe freezing stage, defrost/reheat instructions, nutrition, mass, energy or time savings from these source words.

## 3. EXTERNAL PRIMARY-SOURCE CONTEXT — not production storage truth

Official research references checked for this narrowed **ground beef** process:

1. **Роспотребнадзор**, [«Рекомендации по выбору и хранению» для фарша](https://zpp.rospotrebnadzor.ru/news/federal/244173): general consumer guidance discusses packaging, refrigerated containers and freezing meat mince. It does not approve an immutable `RecipeVersion` containing beef **already mixed with milk and soaked bread**, nor does it prove the exact Friday→Saturday transition for this fixture.
2. **USDA FSIS**, [«Ground Beef and Food Safety»](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/meat/ground-beef-and-food-safety): primary public food-safety guidance for ground beef refrigeration, hygienic handling, cooking and thawing. It is **US jurisdiction/context** and not a version-specific safety certification for this composite mixture, exact physical kitchen, cooling method, hold boundary, packaging, source ingredient status or form.

**Decision:** no temperature, storage duration or freezer shelf life from these pages is published into `RecipeVersion` or `PrepPlan` by PR #197. Specific recipe/form safety, cooling/holding at home, time spent preparing, physical storage and safe next-day use still require separate reviewed evidence. Recipe-specific process guidance remains **UNKNOWN**, not zero or automatically safe.

## 4. Measurable candidate versus accepted proof

One *source-supported potential* duplicated first-step action exists:

| Metric | Conditional comparison | Status |
| --- | --- | --- |
| MealEvents covered | Two actual persisted events, different dates | **FACT** |
| Repeated common source first step | Two references, identical instruction hash | **FACT** |
| Distinct first-step operations without batching | 2 | **BASELINE MODEL** |
| First-step operations if common raw intermediate safely prepared once | 1 | **ASSUMPTION, NOT EXECUTABLE** |
| Potential avoided duplicated first-step operation | 1 | **CONDITIONAL ONLY** |
| Source-backed safe storage across Friday→Saturday | None approved | **BLOCKER** |
| Source-backed shared component identity / splitting by exact Servings | No published authority | **BLOCKER** |
| Safe recipe-specific cooling, thaw/reheat/final cooking transition | No approved review | **BLOCKER** |
| Verified overall reduction in physical actions across the week | Not proven | **BLOCKER** |

**No claim of saved minutes.** A theoretical subtraction of two matching source steps is not the accepted PR10 metric until a validated common physical operation, intermediate form, exact Decimal Serving contributions, storage and endpoint recipe compatibility are independently accepted. Aggregating raw meat and bread mix cannot silently change nutrition/yield or negate the recipe-specific final cooking steps.

## 5. Required follow-up research/contract evidence (no runtime)

A separately scoped, independently reviewed **PR10-META-SAFETY** evidence operation should resolve only this real pair's state transition:

- **Data/research owner:** identify official source-backed safety advice applicable to mixed raw minced beef + milk-soaked bread in a home kitchen, including ingredient initial states, contamination controls, holding/storage container/temp/time, appliance verification, eventual shaping and separate cooking, and handling if already thawed. A generic 1–2 day rule for plain minced beef is *insufficient* to approve the composite mixture. If none exists, return **BLOCKED** for this pair, or propose another actual MealEvent pair.
- **Data/domain owner:** freeze an approved *intermediate shared-component identifier* attached to the two immutable RecipeVersion/step hashes, corresponding source ingredients and form, a deterministic allocation of two event-specific Decimal Serving contributions, recipe-specific later branches, source/provenance/rights and precise update/invalidation semantics. Do **not** invent a source process table, migration, revised RecipeVersion or storage field in this documentation PR.
- **QA/reviewer:** challenge whether combining the first step reduces one **actual physical prep action** at unchanged resulting recipes and source quantities without a hidden second mixing/holding/handling operation. Source text similarity is not proof of physical labor/time saved. Verify wrong Household, stale RecipeVersion, unreadable Russian/numeric process text and no Pantry writes in future implementation tests.
- **Orchestrator:** retain `PR10-META=BLOCKED` until a new independent gate receipt proves all accepted criteria. If verified safety/source publishing requires an immutable RecipeVersion correction or new metadata schema, create/review a new source-publication contract first. Do not open PR10-A/B/C or PR10-PDF.

## 6. FACT / ASSUMPTION / DECISION / OPEN

**FACT:** PR #196 merged and its exact fixture receipt is verifiable. The specific source variants in its week have identical first RecipeStep text and ingredient identity at base serving; their shaping steps differ; storage/batch/freezer metadata are NULL.

**ASSUMPTION:** performing one common preparation for the two source variants would reduce duplicated physical work. Neither reliable storage of the mixed intermediate nor resulting net work savings is proved.

**DECISION for this evidence PR:** **CANDIDATE_IDENTIFIED, NOT READY**. The accepted PR10-META gate remains **BLOCKED**, with recipe-specific source-storage and shared-component publication blockers now targeted to a concrete pair. This report does not edit authoritative recipe data or operationalize a household instruction.

**OPEN:** Is this exact mixture safe to retain from Friday until Saturday under reviewed conditions? Is holding/packaging itself extra work that negates the proposed action reduction? Do existing authoritative recipe/source contracts represent the shared intermediate without a schema change? Those need a separate reviewed resolution.

**Verification tier:** documentation + frozen compact JSON evidence + state only; whitespace, links/source pointers, synthetic receipt/artifact SHA and review gate consistency. No backend regression required when runtime is unchanged.
