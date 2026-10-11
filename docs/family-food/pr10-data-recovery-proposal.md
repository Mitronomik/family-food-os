# PR10-DATA-RECOVERY — source-backed prep metadata and Gate 2 strategy proposal

**Status:** PROPOSED / review only; NOT an accepted roadmap or runtime contract  
**Issue:** [#211](https://github.com/Mitronomik/family-food-os/issues/211)  
**Accepted baseline:** `main@42b76adaed10a3a9b10e8600f71a5d1084b8fbbe` (PR #210 merged, 2026-10-11)  
**Current authorization:** docs-only proposal. `PR10-META=BLOCKED`; PR10-A/B/C, PR10-PDF, Gate 2 remain unauthorized.

## 1. Sources and precedence

Read with the [Master Roadmap](master-roadmap.md), [2026-09-13](master-roadmap-addendum-2026-09-13.md), [2026-09-16](master-roadmap-addendum-2026-09-16.md), [2026-09-19 DATA-CORPUS-V1](master-roadmap-addendum-2026-09-19-data-corpus.md) addenda, [DATA-CORPUS-V1](data-corpus-v1.md), [PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [stage publication feasibility](pr10-meta-publication-path-feasibility.md), [form-review verdict](pr10-meta-form-source-review.md), [source evidence](pr10-meta-onion-blanch-evidence.json), [composition](food-composition-and-assembly.md), [Russian language](russian-language-contract.md), [security](security-architecture.md) and [verification](verification-policy.md).

Later approved DATA-CORPUS-V1 says accepted production truth must be reusable beyond one gate; external corpora are replaceable. PR10-ARCH requires at least one demonstrable safe, source-backed shared preparation for **two different actual MealEvents** with net physical-action saving `B < A`. A mere chronology of recipe steps cannot pass. This proposal **does not supersede** either contract.

## 2. FACT — why current path is blocked

- The PR10-ARCH audited subset of 30 accepted DC4 recipes reported 0/30 source-filled `batch_friendly`, `freezable`, fridge/freezer duration and `prep_time_minutes`; 1/30 `cook_time_minutes`. These are subset results, not total catalogue claims.
- PR #208 established two Wednesday source-reviewed onion-blanch instructions, but not comparable pre-blanch food form, safe combined output, equipment/batch handling, shared prep session, or net work saving.
- Merged PR #210 recorded `UNKNOWN_SOURCE_FORM_NOT_INDEPENDENTLY_VERIFIED`: an external 2021 recipe document was **not** demonstrated byte-identical to the pinned School2022 source. Similar numbering, ingredient and verb do not authorize publication.
- [PR10 publication preflight](pr10-meta-publication-path-feasibility.md) confirms per-recipe append-only `RecipeVersion` is supported; an authoritative versioned **cross-recipe stage retrieval/binding** is not currently present. An evidence JSON file is not runtime authority.
- Existing PR10-ARCH has exactly three proposed Prep tables. Nothing here silently adds a fourth table or changes accepted SQLite schema.

**Observed bottleneck:** source-backed process-stage authority and eligibility for safe actual reuse; no evidence that a new algorithm or one more substring comparison solves it.

## 3. ASSUMPTIONS to validate

A deliberately curated small **ordinary platform recipe set** may contain one or more verifiable shared kitchen stages with enough published process/food form information to pass PR10-META. Reusing existing source cards would minimize publication changes *if* originals and rights can be reviewed. New high-quality sources may be needed; their availability and licensing are not established by this proposal. Reduced actions cannot be inferred from the presence of a shared verb or ingredient.

## 4. Proposed product-data contract: ReviewedPrepOperationCandidate (evidence only)

A source-backed candidate review record should contain the following fields before eligibility is assessed. These describe **review evidence**, not a new DB aggregate or immediately executable production data.

| Evidence field | Required meaning / failure mode |
| --- | --- |
| source identity | Publisher/URL or source-id, exact card/document/version/hash, rights/use scope, reviewed date and reviewer receipt |
| recipe pins | Immutable `RecipeVersion` ID and `RecipeStep` IDs/hashes for each distinct event; immutable source recipe lineage |
| food form | Canonical `FoodIngredient`, raw/input/cooked state, verified input cut/form and output form; UNKNOWN must remain UNKNOWN |
| process | Exact source-supported action, ordered dependencies, ingredient contribution/split by step if documented; no invented stage |
| quantities | Source-based units and yield, exact structured `RecipeIngredient` and Decimal `Serving` scaling, raw/net basis |
| compatibility | Equivalent intermediate food output and batch/equipment capacity, potential incompatibility/cleanup; no text-only matching |
| timing/safety | Same physical session or independently proven stage-specific storage/hold/handling path; expiry/temperature/time only when supported |
| downstream | Separate dish-specific continuation and any handling/splitting/retrieval actions |
| work proof | Explicit unshared action graph `A` and shared action graph `B`; **net B < A** after all added operations, not just first-step count |
| lifecycle | Source and policy versions, acceptance status, invalidation triggers, bounded reviewer sign-off, Russian actionable copy |

An omitted source fact is **UNKNOWN**, never zero, safe or `false` by default. Numeric process text must pass PR10-ARCH classification; regex flags alone cannot whitelist instructions. No AI inference becomes authority.

## 5. Path comparison

| Approach | Upside | Blockers | Proposed verdict |
| --- | --- | --- | --- |
| A. Re-review existing published RecipeVersions with exact original cards | Reuses accepted recipes, ingredient nutrition and fixture where legitimate | Missing or inaccessible originals, unsupported form/hold/step authority; risky pressure to invent details | **First-pass discovery only**, bounded and stop early |
| B. Curate a small new source-backed batch-friendly process corpus | Can target documented repeated operations and safe process stages, generalizable beyond one fixture | Must establish source licensing, nutrition/form compatibility, immutable publisher and version-aware stage reader; additional data review | **Preferred fallback and likely recovery path** |

**RECOMMENDATION — proposal, not authorization:** perform a time-boxed *evidence-count bounded* review of up to **three candidate stage families** (not a requirement to fabricate three outcomes). Start with existing accepted RecipeVersions **only where exact original cards already exist and rights are reviewable**; otherwise switch to Path B. Candidate stage families are selected by demonstrable household usefulness, not by forcing the current onion fixture. The number three is a proposed review cap, not a product invariant.

For Path B, prefer sources explicitly documenting both stage input and output, batch preparation and handling. No retailer page or generative recipe is trusted authority by default; source rights must be reviewed per recipe/process. The data programme is bounded curation/publication, **not** generalized ingestion automation. Avoid adding a source-specific identifier to the Planner/Prep domain.

## 6. Proposed acceptance protocol and fixture policy

**Discovery receipt** (docs/data review, not a runtime change):
1. Record at least two distinct published, immutable RecipeVersions usable as two MealEvents, with independent version-pinned step/process evidence. The recipes may come from one legally reviewed source if each specific card independently supports its own stage; do not falsely claim two independent publishers.
2. Resolve canonical FoodIngredient and food form for each stage; explicitly resolve compatibility and output condition.
3. Demonstrate executable prep-session or reviewed safe storage/hold transition for *realistic fixture timing*; missing meal clock and absent cold-chain evidence are blocking where relevant.
4. Compute per-event contributions through existing Decimal serving rules; no invented batch yield.
5. Compare full physical operation DAGs, including setup, cut, split, clean, store and retrieve; assert net `B < A` and no altered meal nutrition/exclusions. Never invent saved minutes.
6. Produce reproducible machine receipt, negative examples and reviewed Russian instructions; QA must be able to independently falsify the candidate.

**Fixture change is a separate material decision.** Keep the currently accepted synthetic fixture untouched until a candidate is source-reviewed and an explicitly approved fixture/replan change has a new frozen baseline, input hashes, MealEvent/RecipeVersion/Serving pins, comparable before/after test and backward historical reproducibility. No substitution solely to make Gate 2 green. Even the chosen fixture must still exercise the full Household → week → portions → Shopping/Pantry → Prep → PDF core.

**Stop conditions:** If no candidate supports source form + handling + net B<A under this bounded review, record NO-GO; do not launch serial similarity audits. Escalate a product decision about Prep milestone usability and sequencing; do not silently demote the PR10 acceptance criterion.

## 7. Publication and read-path contract gate (before implementation)

The existing `append_trusted_version*` path may append *source-verified* recipe corrections without mutating old versions, but it **does not** publish a reusable cross-recipe stage. Before any new runtime stage binding:

- Draft and independently review a separate **docs-only implementation contract gate** specifying platform owner, source-stage identity, immutable version/id, exact `RecipeVersion`/step links, citation/rights, Russian instruction, read API/repository contract, approved status, invalidation/fingerprints and replay/conflict rules.
- Challenge minimality of the **three existing PR10 Prep tables**; a sidecar is evidence-only unless a deliberate authoritative publisher/reader is accepted. New schema/table/migration or source version identity requires an explicit architecture decision, not an incidental implementation PR.
- Preserve transactional/UoW boundaries, Household ownership of derived PrepPlan, no cross-Household reads, and immutability of existing meal history. Existing plans pin earlier RecipeVersions; regenerated derived artifacts must follow stale/revision rules.
- Keep process authority, recipe composition/nutrition and Pantry movements separately owned. PrepPlan generation is a proposal, never stock mutation or proof of executed/freezer inventory.
- Require failure injection and tamper tests (wrong hash, conflicting RecipeVersion, form mismatch, missing safety, invalid scaling, cross-household reference, replay, incomplete step classification); exact-head verification tier agreed before runtime.

## 8. DECISION required from product owner

**PROPOSED DECISION D1:** Approve a bounded, source-backed prep-data recovery programme, with Path A exact-source check followed by Path B curated new recipes/processes if necessary; stop unbounded same-ingredient/verb pair investigations.

**PROPOSED DECISION D2:** Allow *proposal of* a replacement Gate 2 fixture **only after** candidate evidence passes. Approval of this document alone must **not** replace the fixture, revise acceptance criteria or reorder roadmap.

**PROPOSED DECISION D3:** Require a separate stage publication/read-path implementation contract before any source-authoritative cross-recipe runtime metadata. No advance reservation of migration or new storage mechanism.

These decisions have not been approved merely by merging an evidence PR. The actual required sign-off is explicit, after independent review.

## 9. OPEN QUESTIONS

- Which accessible source cards provide sufficient handling, form and rights evidence for a reusable operation?
- Is same-session preparation feasible for a revised accepted fixture without unreviewed interim holding?
- Can reviewed stage truth be published through existing recipe-version capabilities plus a minimal separately approved reader, or does it require a new platform authority/migration?
- Does any candidate demonstrate net B<A with real physical actions once cleanup/splitting are counted?
- Which minimum exact-head test fixture proves the final system without overfitting a single recipe?

## 10. Delivery sequence (conditional, not yet authorized)

`#211 docs proposal → independent review → user D1/D2/D3 approval → scoped source/rights evidence batch → verified candidate and revised fixture decision (if needed) → stage publication implementation contract → PR10-META actual READY gate → PR10-A calculator → PR10-B persistence → PR10-C API → PR10-PDF → Gate 2`.

PR10-META remains **BLOCKED** today. No Prep execution, storage/freezer guarantees, PR11 PWA, Retail or AI is started by this proposal.
