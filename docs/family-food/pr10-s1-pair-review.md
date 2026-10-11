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
