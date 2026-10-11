# PR10-S1-PAIR — source-backed raw diced-onion compatibility check

**Issue:** [#216](https://github.com/Mitronomik/family-food-os/issues/216)
**Accepted base:** `main@35d0787709d175fd11b8dece044854aa2a0b56f9` (merged [#215](https://github.com/Mitronomik/family-food-os/pull/215)).
**Authority:** [approved D1–D3](pr10-data-recovery-approved-decisions-2026-10-11.md), [shortlist](pr10-source-shortlist.md), [PR10-ARCH](pr10-prep-freezer-implementation-contract.md).
**Result:** `NO_GO_NO_VERIFIED_TWO_RECIPE_DICED_RAW_ONION_STAGE`. `PR10-META=BLOCKED`.

## FACT: inspected accepted production publication records

The immutable publication evidence files inspected were:

- [R3-D frozen batch](../../data/curation/r3d-final-dc3-batch-gate/frozen-batch.json), which contains instructions to *finely cut* onion with carrot and then **poach/sweat in water with fat** in more than one recipe process. It does not establish a reviewed, stand-alone reusable **raw diced-onion output stage** or approved batch form and holding state shared across those RecipeVersions.
- [R3-C frozen batch](../../data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json), containing onion preparation including **shredding, blanching, sautéing** in recipe-dependent combinations; these are not interchangeable with unheated diced onion.
- [R2-B fish publication](../../data/curation/r2b-fish-main-diversity/publication-specs.json), requiring **shredded and blanched** onion before its fish stage, not the unblanched S1 stage.

The [NCHFP onion-freezing process](https://nchfp.uga.edu/how/freeze/vegetable/freezing-onions/) describes a method for **prepared diced raw onion** for freezing. It is an external process guide, **not a published FamilyFoodOS RecipeVersion or recipe-step binding**. Its availability does not prove publication/retranslation rights, actual storage/execution, or compatibility with a poached/blanched process.

This check is limited to these three accepted publication records and the previously shortlisted S1 process source. It does **not** claim to exhaust every active recipe in the current database. No exact two-event receipt or source-stage output fingerprint can be established from this bounded evidence.

## Reproducible source-card and step registry (review correction)

The [machine registry](pr10-s1-pair-evidence.json) now pins **all 13 publication-record recipes containing `ONION_BULB_FRESH`** in the **three scoped accepted JSON files** (5 R3-D, 6 R3-C, 2 R2-B). For each recipe it records the exact publication file **Git blob SHA** (not a SHA-256), JSON Pointer to the record and onion ingredient, recipe/card identity, source document SHA-256, **card SHA-256 with explicit hash kind**, process SHA-256 where published, and **1-based reviewed consumer step positions with literal Russian step text and JSON Pointers**.

| Source | Published recipe code | Source card ID | Onion-related step positions (1-based) | Card SHA-256 (prefix) | Why it cannot prove S1 raw-diced reuse |
| --- | --- | --- | --- | --- | --- |
| R3-D | `MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP` | 1.2а | 1, 2 | raw card `b20917235791…` | Fine cutting and poaching together; source does not specify a separately verified raw 1/4-inch diced output. |
| R3-D | `MR2019_1_3_LENINGRAD_RASSOLNIK_SOUR_CREAM` | 1.3 | 2 | raw card `7ec1683c8889…` | Onion appears among cooked vegetables; specific raw cut/output is not source-pinned. |
| R3-D | `MR2019_1_4_OAT_VEGETABLE_SOUP_SOUR_CREAM` | 1.4 | 1 | raw card `40606e0739c6…` | Prepared/poached onion, with no source-pinned raw diced cut or separate stage. |
| R3-D | `MR2019_1_16_POTATO_SPLIT_PEA_SOUP` | 1.16 | 2 | raw card `f4d70b7eb24d…` | Prepared/poached onion, with no source-pinned raw diced cut or separate stage. |
| R3-D | `MR2019_2_11_BEEF_VEGETABLE_RAGOUT` | 2.11 | 2, 4 | raw card `89ef921166ec…` | Fine cutting and poaching together; matching words in cabbage soup do not prove an identical standalone diced-raw stage. |
| R3-C | `SCHOOL2022_54_21M_BOILED_CHICKEN` | ru-school2022:recipe:54-21м | 1, 2 | canonical card `576eb87d0edb…` | Onion is shredded and used in broth, not an explicitly diced freezer-stage output. |
| R3-C | `SCHOOL2022_54_3M_LAZY_CABBAGE_ROLLS` | ru-school2022:recipe:54-3м | 2, 3, 4 | canonical card `a474209834d4…` | Onion is shredded, blanched and sautéed; cooked form differs from unheated diced onion. |
| R3-C | `SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF` | ru-school2022:recipe:54-1м | 1, 5 | canonical card `ec8b76061f70…` | Onion is shredded, blanched and sautéed; cooked form differs from unheated diced onion. |
| R3-C | `SCHOOL2022_54_20M_BOILED_BEEF` | ru-school2022:recipe:54-20м | 1, 2 | canonical card `e4b7a3846b34…` | Onion is only prepared; the source does not pin a raw diced form. |
| R3-C | `SCHOOL2022_54_15R_SALMON_IN_MILK` | ru-school2022:recipe:54-15р | 1, 2 | canonical card `8aecc6f4b811…` | Onion is shredded and blanched; not a raw diced output. |
| R3-C | `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES` | ru-school2022:recipe:54-17р | 1, 3 | canonical card `72bceb85840f…` | Onion is blanched and sautéed, and its pre-blanch cut is not independently pinned. |
| R2-B | `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK` | ru-school2022:recipe:54-6р | 1, 3 | exact card `507b25f2bb48…` | Onion is shredded and blanched; not a raw diced output. |
| R2-B | `SCHOOL2022_54_7R_POLLOCK_IN_MILK` | ru-school2022:recipe:54-7р | 1, 3 | exact card `79d9d346f7dc…` | Onion is shredded and blanched; not a raw diced output. |

The abbreviated card hashes above are **display aids only**; the JSON contains complete hash strings, source locators, step text and exact pointers. For R3-D the manifest provides a **raw card** hash but not a separate process-text hash. For R3-C it provides **canonical card JSON** and **process-text** hashes; R2-B provides **exact source card/process** hashes. None is silently treated as a hash of the displayed consumer step itself. School2022 source PDF SHA-256 and R3-D source document bytes SHA-256 are recorded at file/card level.

**Boundary:** these are accepted source-publication *records*, not an independently verified full enumeration of current active database RecipeVersions or a complete MealEvent-to-RecipeVersion fixture. Positions index the reviewed `consumer_steps_ru` (R3-D/R3-C) or `trusted_recipe_seed.version.steps` (R2-B), not unknown positions in original PDFs. No matching keyword, partial `мелко нарезать` instruction, or shared ingredient amount is promoted into an accepted standalone raw diced output, cross-event binding or holding permission. This correction adds *reproducibility of the negative observation*, not a new source-safety finding.

## Compatibility / rejection matrix

| Required evidence | Observed | Decision |
| --- | --- | --- |
| Common FoodIngredient identity `ONION_BULB_FRESH` | Appears in multiple published recipe records | Food identity alone insufficient |
| Two distinct immutable source-approved RecipeVersions explicitly requiring **the same raw diced cut/output** | **Not established**; some say *finely cut*, other cards say *shred* and/or *blanch* | BLOCKED |
| Their common standalone intermediate stage before divergent downstream recipe work | **Not published** in a verified cross-recipe stage reader | BLOCKED |
| Verified two MealEvents and exact Decimal portions for that proposed shared stage | No accepted S1-specific event/RecipeVersion pair pinned | BLOCKED |
| Same physical session or source-specific safe hold/storage/retrieval | Not established | BLOCKED |
| Full physical-operation graph proves net `B < A` incl. split/cleanup/handling | Not established | BLOCKED |
| Source rights, reviewed Russian process instructions, immutable publication binding | Not established for S1 as production stage | BLOCKED |

**Negative cases:** Do not equate finely chopped with measured 1/4-inch dice; do not equate poached, sautéed or blanched onion with raw diced freezer output; do not reuse a freezing guide as permission to hold a prepared food between lunch/dinner; do not identify physical savings by repeated onion names, text verbs or a naive hypothetical 2→1.

## FACT / ASSUMPTION / DECISION / OPEN QUESTION

**FACT:** R3-D/R3-C/R2-B publication records contain onion work, but do not collectively prove an exact source-backed shared S1 output in two version-pinned recipe processes. NCHFP is independent evidence for a preservation process, not verified recipe demand.

**ASSUMPTION:** a purpose-curated, licensed pair of ordinary food recipes might provide sufficient compatible intermediate processing, but the current evidence does not demonstrate it.

**DECISION:** `NO_GO_NO_VERIFIED_TWO_RECIPE_DICED_RAW_ONION_STAGE`. Stop expanding the S1 match-by-words search under this issue; this is a valid negative research result. No new RecipeVersion, stage metadata publication, fixture replacement, migration or PR10 runtime is authorized.

**OPEN QUESTION:** whether an independently source-curated recipe pair with complete form, process, quantity and safety evidence can be acquired without building a broad ingestion pipeline. This requires a separately approved bounded source-acquisition/rights task, not continued random string matching.

## Verification / non-goals

Docs-only comparisons of existing reviewed manifests; no code, SQL migration, repository seed, API or test fixture changed. Correctness of an actual shared-stage engine cannot be claimed from this source review. Follow [verification policy](verification-policy.md) for docs diff, links, scope and exact-head CI. No full backend regression triggered for byte-identical runtime. Independent review before merge.
