# PR10-EXT-PAIR — bounded external source-pair suitability gate

**Date:** 2026-10-12
**Issue:** [#218](https://github.com/Mitronomik/family-food-os/issues/218)
**Accepted base:** `main@162ce34e1b4e96099c51f6e547531d414b5414cf` ([PR #217](https://github.com/Mitronomik/family-food-os/pull/217) merged).
**Authority:** approved [D1/D2/D3](pr10-data-recovery-approved-decisions-2026-10-11.md), [PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-S1-PAIR negative result](pr10-s1-pair-review.md).
**Outcome:** `NO_GO_FOR_PR10_META_THIS_EXACT_EXTERNAL_PAIR`. **PR10-META stays BLOCKED.** No production source publication, stage/RecipeVersion authority, fixture, runtime, migration or source rights approval.

## Goal / bounded method

Test **one exact external pair**, rather than search the existing catalogue for another shared onion phrase. Evaluate whether two pinned, source-authored ForkRecipe records can form a verifiable reusable raw diced-onion stage that actually reduces preparation actions for two FamilyFoodOS MealEvents. Check the UniTools pinned `sample.json` *only* for competing dataset capabilities/provenance; it is not a third process/recipe pair.

This is an external **source-acquisition feasibility** check. No record becomes a published FamilyFoodOS RecipeVersion and no external process text becomes reviewed executable Russian instructions. Machine-readable [receipt](pr10-ext-pair-source-evidence.json) contains full SHA/line/field pins, not fabricated MealEvent identities.

## FACT — exact independent external records

ForkRecipe public repository [`futurechef/forkrecipe-recipes`](https://github.com/futurechef/forkrecipe-recipes), commit [`934319313379201f91ddccdd29abd054039a3ad6`](https://github.com/futurechef/forkrecipe-recipes/tree/934319313379201f91ddccdd29abd054039a3ad6). Both files declare author `ForkRecipe Kitchen`, `ratioSystem: "weight"`, and `servings: 6`. Source field `ratioValue` gives the **recipe record's** ingredient amount, not accepted FoodIngredient/RecipeVersion/Serving truth.

| Exact source file | Ingredient source field | Source amount | Downstream `processNodes` | Source Git blob SHA |
| --- | --- | --- | --- | --- |
| [`chicken-tortilla-soup.js`](https://github.com/futurechef/forkrecipe-recipes/blob/934319313379201f91ddccdd29abd054039a3ad6/recipes/chicken-tortilla-soup.js#L28) | `ing_03` — Yellow onion, diced (line 28) | 250 g / 6 source servings | `step_2` (line 62) mixes onion with peppers, aromatics and spices; output `chile_base` | `3e62c2802229701d7744e93696b289f73c99c469` |
| [`beef-and-barley-stew.js`](https://github.com/futurechef/forkrecipe-recipes/blob/934319313379201f91ddccdd29abd054039a3ad6/recipes/beef-and-barley-stew.js#L30) | `ing_05` — Yellow onions, diced (line 30) | 300 g / 6 source servings | `step_2` (line 61) mixes onion with celery/mushrooms/garlic and tomato; output `stew_base` | `b36222f6c29e462f2bab024ab64c150a4f873a0e` |

**Candidate only:** 250 + 300 = **550 g** of source-listed diced onion at those two source batch sizes. This is a simple arithmetic total, **not** a production shopping amount, net peeled mass, verified joint prep output or valid household Serving calculation. Both record names describe *diced* onion; **neither specifies exact cut dimensions** (including the 1/4-inch S1 guide cut), gross/net basis, an independent diced-raw `outputState`, a preserved cutting/packaging procedure or batch capacity. The actual described node outputs are **different mixed cooked bases**. Treating them as the same shared stage would be a false equality.

The records contain claims/instructions about storing or freezing **finished soup/stew**, but no source-specific safety authorization for making, storing and retrieving a **shared raw chopped-onion intermediate** between two separately timed MealEvents. Do not inherit dish-level freezing dates or cooling text as validated intermediate-stage rules. These source claims have **not** been independently validated for food safety.

### Source authorship, copyright and Russian-display boundary

The pinned [ForkRecipe README](https://github.com/futurechef/forkrecipe-recipes/blob/934319313379201f91ddccdd29abd054039a3ad6/README.md), [NOTICE](https://github.com/futurechef/forkrecipe-recipes/blob/934319313379201f91ddccdd29abd054039a3ad6/NOTICE) and [LICENSE](https://github.com/futurechef/forkrecipe-recipes/blob/934319313379201f91ddccdd29abd054039a3ad6/LICENSE) **declare** CC BY-SA 4.0 content rights and describe originally authored/public-domain-adapted recipe content. The two examined card objects do not give an individual external original recipe URL/document/edition or independent culinary validation trail. A public Git blob/CC declaration proves what the repository publishes, **not** that FamilyFoodOS has completed its per-record source/rights/review/publication process.

[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) permits commercial reuse under attribution/share-alike terms when applicable and the licensor has the necessary rights; it does **not** automatically satisfy our internal provenance acceptance, translation attribution, third-party material review, validated Russian step instructions or safety requirements. No text, images, weights or time/safety claims were imported into production.

### UniTools — bounded comparator, not candidate pair

Pinned [`farcrak/unitools-recipes` commit `2f554073f7e730b18d707fe1164d18308f6ec16c`](https://github.com/farcrak/unitools-recipes/tree/2f554073f7e730b18d707fe1164d18308f6ec16c): [`sample.json`](https://github.com/farcrak/unitools-recipes/blob/2f554073f7e730b18d707fe1164d18308f6ec16c/sample.json), Git blob `2d665107ddac2eec93d649d46129a2824dec187d`, version 2.0.0, contains **two** sample recipes (`spaghetti-carbonara` and `tom-yum-goong`). The sample offers Russian ingredient names, quantities and Russian steps/time fields; those sample records do **not** expose per-card original-source citations or typed `processNodes` dependencies. The README **claims 501 total recipes**, but the full collection was **not** audited here. It declares CC BY-SA 4.0; nutritional numbers are author-calculated rather than laboratory measurements. This does not supply a qualifying Prep pair or authoritative FamilyFoodOS nutrition/safety values.

## PR10-META readiness — falsifiable gate

| Required proof | Checked evidence | Result |
| --- | --- | --- |
| Two fixed external card identifiers and exact snapshot bytes | Source commit, paths and Git blob SHAs pinned | **YES — research records only** |
| Source-listed onion amount for both recipe batches | 250 g and 300 g at six source servings each | **YES — not accepted scaled Decimal Servings** |
| Equivalent exact ingredient/raw form | Both say diced yellow onion, but no cut dimension/net basis | **UNKNOWN** |
| Common *standalone* reusable process state | Neither source model defines one; `chile_base` differs from `stew_base` | **NO** |
| Independent card-level original provenance and suitable rights | Repository-level CC claim; original per-card sources and project rights review absent | **UNVERIFIED** |
| Two **accepted** distinct MealEvents / immutable RecipeVersion and step pins | Both external, not published or attached to accepted events | **NO** |
| Safe holding/packaging/retrieval over actual interval | Only finished-dish freezer text; raw-onion hold not established | **UNKNOWN** |
| Complete physical-operation graph with `B<A` | No verified cutting/cleaning/splitting/packaging/storage actions or session | **NOT PROVEN** |

For action accounting: baseline `A` would include both recipe-specific cutting/setup/cooking sequences; combined `B` would need verified combined cutting plus any portion splitting, extra handling, washing, packaging, holding, retrieval and their effect on individual cooking. **Neither A nor B is currently computable from the sources.** A claim such as “two cutting mentions become one action” omits physical work, so it cannot prove `B<A`, and minutes saved must not be asserted.

## FACT / ASSUMPTION / DECISION / OPEN QUESTION

**FACT:** Two exact public source cards provide weights and matching *descriptive ingredient names*, but not a source-defined shared raw-diced intermediate, independently accepted original card provenance, approved raw-onion storage/holding or an actual version-pinned two-event work graph.

**ASSUMPTION:** A separately curated pair with independently verified original recipes and preparable/holdable common intermediate might eventually satisfy PR10, but this pilot provides no such proof.

**DECISION (bounded research only):** `NO_GO_FOR_PR10_META_THIS_EXACT_EXTERNAL_PAIR`; `PR10-META=BLOCKED`, and PR10-A/B/C, PR10-PDF and Gate 2 remain NOT AUTHORIZED. **No more external keyword-pair hunting under this issue.** ForkRecipe's `processNodes` is useful as a modeling *reference*, not authorized domain truth. UniTools is a potential later ingredient/recipe acquisition source after independent provenance and quality review, not a Prep solution now.

**OPEN PRODUCT DECISION:** Stop repeat research and ask the owner to choose one of two separately scoped options: **(A)** commission/access an actually reviewed, rights-cleared two-recipe + food-safe prep-operation source package and then redo the gate; **(B)** propose a formal PR10 usefulness-gate/roadmap amendment that separates a truthful partial PrepPlan from cross-event batching optimization. Option B is a **change proposal only**; the accepted minimum usefulness criterion may **not** be weakened without explicit approval and a reviewed contract.

## Preservation / verification

No changes to verified RecipeVersion catalogues, provenance, FoodIngredient, nutrition, MealPlan/Serving, shopping or Pantry; no new schema, source data ingestion, AI, legacy migration, API, PWA, accepted fixture, PR10 runtime or Gate2. This docs-only negative proof calls for source-pin validation, link/scope checks, `git diff --check` and exact-head Docs CI; backend regression is not implied by unchanged bytes. Independent review before merge; no autonomous merge.
