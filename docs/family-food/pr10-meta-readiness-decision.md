# PR10-META — Prep/Freezer source-readiness decision

**Status: BLOCKED — honest evidence outcome, NOT runtime authorization.**
**Accepted base:** `main@6189fc634030a6d011ed930ed70690e196af3ba0` (#192 PR10-ARCH merged).
**Issue:** #193.
**Authority:** [accepted PR10 contract](pr10-prep-freezer-implementation-contract.md) §§4–5 and 8–9, [preceding 30-recipe audit](pr10-prep-metadata-readiness-audit.md).
**Machine receipt:** [30 accepted candidate RecipeVersion IDs + publication source evidence](pr10-meta-candidate-evidence.json).

## 1. FACT — what is actually frozen

The [accepted DC4 rerun receipt](../../data/curation/dc4-corpus-readiness/rerun-summary.json) records **51 eligible/active current-at-DC4 RecipeVersions**, each with a code and recipe_version_id. Its accepted Planner proof contains a **three-member, 7-day pattern with 21 MealEvents and 42 Servings**, with deterministic trace fingerprint. However, that public summary does **not** include the 21 individual MealEvent UUIDs, their recipe_version_id pins, the precise MealPlan UUID/revision and current recipe-process hashes. **It does not freeze an actual Gate 2 MealPlan for Prep**.

To avoid promoting guesses to facts, we joined the 30 recipe codes in the approved [earlier Prep audit](pr10-prep-metadata-readiness-audit.md) against DC4's 51 and seven reviewed source publication manifests. The machine receipt preserves **all 30 historical DC4 UUID pins**, manifest reference, source document hash, individual nullable metadata fields and step prefilter positions.

| Publication source | Matched accepted DC4 recipes |
| --- | ---: |
| [R1-G](../../data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json) | 2 |
| [R2](../../data/curation/r2-breakfast-capacity/publication-specs.json) | 2 |
| [R2-B](../../data/curation/r2b-fish-main-diversity/publication-specs.json) | 2 |
| [R2-C](../../data/curation/r2c-breakfast-grain-diversity/publication-specs.json) | 3 |
| [R2-F](../../data/curation/r2f-sandwich-resilience/publication-specs.json) | 1 |
| [R3-A](../../data/curation/r3a-school2022-main-batch/publication-specs.json) | 10 |
| [R3-B](../../data/curation/r3b-school2022-breakfast-batch/publication-specs.json) | 10 |
| **Total distinct accepted candidate codes** | **30** |

**Evidence limit:** code-to-UUID is a historical accepted DC4 receipt and source-publication-manifest match, not a read of current SQLite RecipeVersion/process bytes; these candidates are **not claimed to be the actual 30 verified recipes selected for the future Gate 2 fixture**, and all 30 need not appear in a 21-event week. No production data was changed.

## 2. FACT — readiness nulls and risky process text

| Source-backed RecipeVersion field | Non-null / 30 |
| --- | ---: |
| `prep_time_minutes` | 0 |
| `cook_time_minutes` | 1 |
| `total_time_minutes` | 0 |
| `batch_friendly` | 0 |
| `freezable` | 0 |
| `storage_days_fridge` | 0 |
| `storage_days_freezer` | 0 |

The single `cook_time_minutes=20` relates to `SCHOOL2022_54_29M_BEEF_MEATBALLS` and does **not** establish active-time saved or safe hold duration. The 30 manifest versions contain **109 RecipeSteps**. A heuristic prefilter flagged **16 potentially quantity-bearing steps in 12 recipes**; this is NOT approved semantic classification or proof of 16 conflicts.

Examples from accepted source manifests:
- `SCHOOL2022_54_29M_BEEF_MEATBALLS` contains 75–100 g cuts and 15–20 g ball size (potential process parameters, not ingredient totals).
- `SCHOOL2022_54_1O_NATURAL_OMELET` includes 2–3 eggs per working batch, not necessarily the RecipeIngredient total.
- `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES` refers to **5.3 g oil total** without a per-step split; it must not be shown as the actual scaled amount without reviewed mapping.

RecipeStep quantities remain **untrusted as scaled execution amounts** until accepted PR10 §4.1 classification: reviewed process-invariant, reviewed ingredient-amount mapping, no numbers, or ambiguous/review-required. Authoritative quantities come **only from structured pinned RecipeIngredient + Decimal Serving scaling**, displayed separately.

## 3. PR10-META acceptance matrix — decision

| Mandatory criterion | Evidence | Gate |
| --- | --- | --- |
| Actual Household-local 3-member MealPlan/21 MealEvents with full RecipeVersion + Serving pins frozen | DC4 summary confirms 21 events/42 Servings but omits complete event/recipe/revision identities | BLOCKED |
| At least 30 **current** verified version-pinned recipes belonging to the actual Gate 2 fixture catalogue | 30 historic DC4 recipe IDs matched; **live/current fixture not frozen** | BLOCKED |
| Validated stage/form transition, safe refrigeration/freezer hold and reheating/defrost evidence | Not supported in selected manifest metadata | BLOCKED |
| At least one reviewed, safe prep operation for **two or more real MealEvents** | No pinned pair/process/holding evidence | BLOCKED |
| Fewer unique physical operations than the same events performed separately | No reviewed shared-work identity or count proof | BLOCKED |
| Scale-consistent Russian directions with numeric-step review | 16 heuristic candidates, not reviewed classifications | BLOCKED |
| No invention or Pantry/PreparedBatch modification during investigation | Docs and evidence only | PASS (scope) |

**DECISION: BLOCKED.** This conclusion is not a claim that the entire 51-recipe catalogue is impossible to batch-cook. It means that current **reviewed evidence is insufficient** to claim the required safe and useful Prep result. It is also not permission to start PR10-A/B/C or to weaken PR10's measurable value requirement.

## 4. Required negative fixture contract — not yet executable

When PR10-A becomes authorized, its deterministic tests must include a **3-member/7-day fixture** with unknown batch/freezer/hold metadata and unreviewed numeric RecipeSteps. Expected: no scheduled advance/freezer actions or invented expiry; explicit `prep_unresolved_obligations`, source-event/step reasons and `INCOMPLETE` for required unsupported recipe steps; exact Decimal quantities remain in the separate structured ingredient block. PantryItems, PantryMovements and PreparedBatch remain unchanged on generation, conflict and failure. An all-out-of-home week may legitimately yield zero kitchen actions and no unresolved prep, without claiming any useful batch operation.

**This is a future test specification, not an executed runtime test**: PR10-A does not yet exist.

## 5. Source-evidence recovery sequence (separate reviewed work)

1. **Freeze actual Gate 2 fixture:** via existing repository-backed deterministic Planner (no production edits), record Household (fixture-only) and MealPlan UUID/revision/week/timezone, all 21 MealEvent IDs/date/role/source/recipe pins, all 42 Servings, and the **>=30 currently verified RecipeVersion IDs in its candidate catalogue** with recipe/process source hashes. Recheck unchanged deterministic trace, exclusions and all UUID joins. The DC4 summary alone is not enough.
2. **Review one realistic shared-prep candidate:** select two actual fixture MealEvents that might share process work, then inspect exact pinned recipe form, origin step, equipment, stage, resulting form, valid holding/storage duration and any defrost/reheat transition from reviewed sources. **Do not infer safety merely from recipe names, duplicate ingredients or general advice**.
3. **Classify numeric RecipeSteps:** review raw immutable instruction hashes and map fixed batch/cut sizes vs ingredient totals, equipment dimensions, times/temperatures; for ambiguous numbers withhold executable prose and emit `STEP_QUANTITY_REVIEW_REQUIRED`. Validate scaling factor !=1 and changes to RecipeVersion/process.
4. **Separately review a source-publication contract if data are missing:** preserve immutable RecipeVersion lineage, rights, original text, source/version/hash, migrations if necessary, rollback/error semantics. This evidence PR authorizes **no** such production change.
5. **Prove measurable value:** for actual pair of MealEvents, retain full event/serving/RecipeVersion contributions, show that approved shared operation reduces distinct physical actions by >=1 compared with ungrouped baseline, with independently reviewed safe holding and transition evidence. No invented time savings.
6. **Re-evaluate gate:** return READY only after the actual fixture, source metadata, instruction-classification and measurable usefulness proofs pass independent review. Otherwise retain BLOCKED with named source/owner backlog. PR10-A/B/C remain blocked.

### External primary safety research leads — not authoritative production recipe metadata

[Роспотребнадзор — рекомендации по хранению](https://zpp.rospotrebnadzor.ru/news/federal/546715) and [USDA FSIS — Leftovers and Food Safety](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/leftovers-and-food-safety) are primary information sources for a **later jurisdiction-aware safety review**, not automatic proof of safe freezer/holding values for any specific published RecipeVersion. This PR adopts **no temperature or number of storage days** as canonical data.

## 6. Architecture, scope and open questions

**FACT:** #192 PR10-ARCH merged and requires PR10-META first. The first 30 accepted candidates lack reviewed shared/batch/freezer source fields, and the full current Gate 2 event/revision fixture is not frozen.

**ASSUMPTION:** a narrow process-evidence or new reviewed immutable metadata publication can eventually enable one safe and genuinely reusable operation. This is unproven.

**DECISION:** no Prep runtime until meta gate READY. Evidence cannot be converted into execution authority by changing a status label. No AI, Retail, PDF, UI, new storage facts, service changes or Pantry writes.

**OPEN QUESTION:** which exact MealEvent/RecipeVersion pair, backed by safe food-state transitions and clear process provenance, can meet the accepted usefulness criterion? Resolve via the separately scoped evidence operation, not by guessing.

**Verification tier:** docs/evidence/state, repository-relative links, diff whitespace, scope and receipt integrity. Full backend/launcher is not required for byte-unchanged production code.
