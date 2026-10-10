# PR10-ARCH — bounded recipe metadata-readiness audit

**Status:** reproducible source-manifest audit, **not** a kitchen-safety certification or Gate 2 acceptance.
**Audited repository:** `main@545c86b4dd39ba3b14e0c36fcbc4733da1137d14` (merged PR #190), 2026-10-10.
**Owning review:** Issue #191 / PR #192; companion to [PR10-ARCH contract](pr10-prep-freezer-implementation-contract.md).

## 1. Selection and reproducibility

The accepted [DC4 rerun evidence](../../data/curation/dc4-corpus-readiness/rerun-summary.json) identifies **51 currently verified/active recipe candidates** with `disposition=PASS` (Gate1 accepted evidence). We constructed a **bounded 30-recipe candidate set**, choosing all recipes from seven review-backed publication manifests whose canonical codes occur in those 51. This is a transparent candidate cohort of the Gate 2-required minimum of 30 recipes, **not a claim that the future Gate 2 fixture has already selected these exact recipes**. The actual fixed Gate 2 fixture must later be reaudited by its pinned RecipeVersion IDs and current published versions.

Source manifests (all paths repository-relative) and included code counts:

| Source manifest | Candidate recipes also in accepted DC4 |
| --- | ---: |
| [R1-G](../../data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json) | 2 |
| [R2 breakfast](../../data/curation/r2-breakfast-capacity/publication-specs.json) | 2 |
| [R2-B fish](../../data/curation/r2b-fish-main-diversity/publication-specs.json) | 2 |
| [R2-C grains](../../data/curation/r2c-breakfast-grain-diversity/publication-specs.json) | 3 |
| [R2-F sandwich](../../data/curation/r2f-sandwich-resilience/publication-specs.json) | 1 |
| [R3-A mains](../../data/curation/r3a-school2022-main-batch/publication-specs.json) | 10 |
| [R3-B breakfasts](../../data/curation/r3b-school2022-breakfast-batch/publication-specs.json) | 10 |
| **Total distinct canonical codes** | **30** |

Audit algorithm (can be reproduced with JSON reader, without production writes): parse `audit.catalogue.recipes[].canonical_code` from the DC4 rerun; for each listed manifest iterate `recipes`, derive `trusted_recipe_seed.canonical_code` and intersect with accepted DC4 codes; read `trusted_recipe_seed.version` fields and `steps`. Count null/non-null fields and visible numeric tokens; preserve `null` rather than converting to `false`, `0` or `safe`. These manifest receipts are an **audit of recorded publication specs**, not a live database query or a guarantee that every subsequent immutable RecipeVersion has identical process text.

The 30 audited codes, grouped by source:

- **R1-G (2):** `SCHOOL2022_54_29M_BEEF_MEATBALLS`, `SCHOOL2022_54_2M_BEEF_GOULASH`.
- **R2 (2):** `SCHOOL2022_54_1O_NATURAL_OMELET`, `SCHOOL2022_54_9K_MILK_OAT_PORRIDGE`.
- **R2-B (2):** `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK`, `SCHOOL2022_54_7R_POLLOCK_IN_MILK`.
- **R2-C (3):** `SCHOOL2022_54_13K_WHEAT_MILK_PORRIDGE`, `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE`, `SCHOOL2022_54_25_1K_RICE_MILK_PORRIDGE`.
- **R2-F (1):** `SAD28_SANDWICH_CHEESE_20_10`.
- **R3-A (10):** `SCHOOL2022_54_1R_COD_CUTLET`, `SCHOOL2022_54_2R_PINK_SALMON_CUTLET`, `SCHOOL2022_54_3R_POLLOCK_CUTLET`, `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES`, `SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS`, `SCHOOL2022_54_11M_BEEF_PILAF`, `SCHOOL2022_54_4M_BEEF_CUTLET`, `SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES`, `SCHOOL2022_54_6M_BEEF_BITOCHEK`, `SCHOOL2022_54_7M_BEEF_SCHNITZEL`.
- **R3-B (10):** `SCHOOL2022_54_2O_GREEN_PEA_OMELET`, `SCHOOL2022_54_3O_CARROT_OMELET`, `SCHOOL2022_54_4O_SEMI_HARD_CHEESE_OMELET`, `SCHOOL2022_54_2T_COTTAGE_CHEESE_CARROT_CASSEROLE`, `SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE`, `SCHOOL2022_54_2K_VISCOUS_CORN_MILK_PORRIDGE`, `SCHOOL2022_54_6K_MILLET_MILK_PORRIDGE`, `SCHOOL2022_54_16K_DRUZHBA_PORRIDGE`, `SCHOOL2022_54_23K_LIQUID_WHEAT_MILK_PORRIDGE`, `SCHOOL2022_54_24K_LIQUID_MILLET_MILK_PORRIDGE`.

## 2. FACT — exact field coverage in these 30 manifest versions

| RecipeVersion field | Non-null | Null | Safe consequence |
| --- | ---: | ---: | --- |
| `prep_time_minutes` | 0 | 30 | No source-backed prep duration for these recipes |
| `cook_time_minutes` | 1 | 29 | One recorded cook time is **20 min** on `SCHOOL2022_54_29M_BEEF_MEATBALLS`; not a reusable-work duration |
| `total_time_minutes` | 0 | 30 | No source-backed elapsed work/time-saving estimate |
| `batch_friendly` | 0 | 30 | **Zero confirmed batch-ready recipes** in audited manifests |
| `freezable` | 0 | 30 | **Zero confirmed freezer-ready recipes** in audited manifests |
| `storage_days_fridge` | 0 | 30 | No supported fridge hold interval |
| `storage_days_freezer` | 0 | 30 | No supported freezer hold interval |

These 30 manifest versions together contain **109 ordered RecipeStep text entries**. A *heuristic prefilter* scanning text for numeric tokens with mass/volume/piece words (e.g. `г`, `мл`, `л`, `штук`, `яйц`, `ложк`) identified **16 potentially quantitative steps in 12 recipes**. This is *not* a validated semantic classification; false positives and false negatives are possible, so no quantity-bearing step is automatically released based on a regex.

Concrete source examples:

- `SCHOOL2022_54_29M_BEEF_MEATBALLS` step 1: source has **75–100 г** cut-size; step 3 has **15–20 г** shaped-ball size. Those are *piece/process-size parameters*, not a command to buy 75–100 g of beef per scaled serving.
- `SCHOOL2022_54_1O_NATURAL_OMELET` step 1 says break eggs **по 2–3 штуки** at a time. This is a working batch size, not necessarily the ingredient quantity for the final household serving.
- `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES` step 3 includes **5,3 г масла total**, explicitly without a step-level allocation. Repeating this text when the ingredient totals have been scaled can **contradict** authoritative quantities.

RecipeStep process notes may retain fixed cooking times, temperatures and equipment dimensions; those are **not automatically scalable**, either. Their relevance for a changed batch size requires separately reviewed evidence.

## 3. DECISION PROPOSED — mandatory PR10-META readiness gate

**Current measured conclusion: BATCH/FREEZER READINESS NOT PROVEN.** The 30-recipe audit is enough to reject an unconditional automatic weekend batch, cross-day fridge storage or freezer recommendation. It does **not** prove that no recipe in the entire 51-recipe catalogue can ever support safe prep; that would require auditing every current pinned RecipeVersion and its evidence.

Before any PR10 batch/freezer capability can be accepted as product-ready, execute a **separately reviewed PR10-META evidence/readiness gate** (docs/evidence first; any needed data publication is a subsequent separately scoped approved operation). The gate must:

1. Freeze the *actual* Gate 2 MealPlan and at least its **30 current version-pinned verified recipes**, not just these 30 catalogue candidates; verify their current RecipeVersion and process/quantity bindings after any immutable corrections.
2. Report per-version source-backed storage states, batch_friendly, storage durations, preparation stages, safe holding and reheat/defrost requirements, explicit UNKNOWN and rights/provenance; independently resolve numeric instruction semantics into **rechecked immutable published steps** when needed.
3. Prove at least **one safe, source-backed reusable or advanced prep operation serving two or more meal events**, scheduled before a later use *only where storage/transition evidence supports it*, with traceable non-duplicated task count compared to event-by-event execution and no changed nutrition/purchase totals. No numeric minutes saved may be claimed without a trusted time basis.
4. Include a negative Gate 2 fixture where every candidate lacks reviewed storage/batch authority: the engine must return **INCOMPLETE / no unsafe advance preparation**, not present reprinted steps as a successful Prep benefit.
5. Freeze an honest decision: **READY** only when the measurable proof is achieved; otherwise **BLOCKED** with specific metadata/publication backlog. Do not lower thresholds or invent source data to flip status.

**Impact on sequence:** PR10-ARCH docs review → PR10-META readiness evidence (and reviewed publication if necessary) → PR10-A/B/C implementation of the validated deterministic slice → PR10-PDF → Gate 2 closure. The pure calculator can be designed without storage guesses, but a mere chronological rendering of RecipeSteps **does not** satisfy the PR10 product exit criterion.

## 4. Audit limits and what remains OPEN

- This is a GitHub source-manifest inspection joined by canonical recipe code to accepted DC4 evidence, not a live SQLite audit. If a later immutable RecipeVersion or accepted gate fixture differs, refresh the audit; do not silently reuse counts.
- No shelf-life, freezing, safety, saving-time, or cross-recipe shared-component conclusion follows from nullable metadata.
- Numeric-text matching above is a triage signal only. A curated field-level classification (ingredient total / cut-size / batch-size / time / temperature / cooking vessel size / ambiguous) is mandatory before scalable instructions are displayed as commands.
- Nothing here approves Prep runtime, migration `0044`, invented storage/defrost/reheat, new PreparedBatch inventory, Pantry writes or PR10-PDF.
