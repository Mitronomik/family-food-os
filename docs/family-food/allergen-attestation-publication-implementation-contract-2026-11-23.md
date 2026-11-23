# FoodIngredient allergen attestations — Implementation Contract Gate

**Status:** PROPOSED / DOCS-ONLY / independent review + owner merge required before runtime publication.
**Date:** 2026-11-23.
**Accepted base:** `main@4b634febcbda5f8364ed25a0f3ee1132871854d2`, after [#298](https://github.com/Mitronomik/family-food-os/pull/298) merged; [#299](https://github.com/Mitronomik/family-food-os/pull/299) remains separately review-ready, not merged.
**Latest owner decision:** replace one-by-one allergen repairs with a systematic source-backed capability covering every existing canonical FoodIngredient and future publication inputs.
**Read with:** [AGENTS](../../AGENTS.md), [Food Catalogue architecture](architecture.md), [DATA-CORPUS-V1](data-corpus-v1.md), [verification](verification-policy.md), [transactional publication precedent](transactional-nutrition-publication-contract.md), [current focus](../../state/current-focus.md).

## 1. Goal / scope / non-goals

Provide one safe, reusable **whole-catalogue reviewed allergen publication/rollback path**, not a list of hand-edited exceptions. It must support positive known category codes, an explicitly reviewed empty set *under a pinned taxonomy*, unknown/held evidence, supersession and revocation; it must **not** infer that a product is allergen-free because its name sounds ordinary.

The initial contract covers the **canonical FoodIngredient** boundary: source-versioned attestations, deterministic validation, publisher in Food Catalogue UoW, current projection, historical retention and future seed/curation entrypoint. It does not create a generic Data Ingestion Platform, arbitrary URL/file ingestion, retailer labels, package cross-contact statements, AI allergen classifier, medical diet authority, consumer surface or price/stock/nutrition/physical/Prep release.

**Implementation is NOT authorized by this unmerged document.** A later accepted runtime PR must be bounded to the owner and migration seams specified below. Changing Planner/MealPlan/Shopping global contracts or releasing any family diet requires separate contract review.

## 2. FACT / ASSUMPTION / proposed DECISION / OPEN

### FACT
- `FoodIngredient` currently stores `allergens_reviewed: bool` and `allergen_codes: tuple[str, ...]`; SQL stores these as the `food_ingredients` flag plus `food_ingredient_allergens` child rows. The domain rejects nonempty allergen codes when the flag is false.
- `FoodCatalogueService.reconcile_identity_seed` and `reconcile_seed` reject any already-persisted identity whose `allergens_reviewed` or code tuple differs from the new seed. The FoodIngredient repository has no reviewed metadata publication writer (aside from insert and activation).
- No source/reviewer/version/taxonomy applicability and revocation lineage is stored alongside the current flag. A bare true/empty combination cannot prove the absence of every allergy or product cross-contact.
- The existing diagnostic MealPlan/Shopping source gate correctly blocks unreviewed FoodIngredient. Source-only status `SOURCE_VERIFIED` on a RecipeVersion does not prove every ingredient's allergen set.
- Source-backed real-catalogue PR #299 identified 14 recipe rows / 12 distinct unknown FoodIngredients. Initial independent catalogue-wide [#300](https://github.com/Mitronomik/family-food-os/pull/300) CI against the **DC4-A3 test seed** observed **227/227 canonical FoodIngredients UNKNOWN** and **51/51 active recipe dependency sets blocked for composed-meal admission**. These are a current seed measurement, not a permanent product invariant or independent external source approval.

### ASSUMPTION TO VERIFY
A single new append-only allergen-attestation authority per existing FoodIngredient (with an in-transaction compatibility projection into the legacy flag/child-code tables) can preserve existing identities and old reads, while making all future revisions reviewable and revocable. A review of the proposed schema must challenge whether this is genuinely the minimum needed.

### PROPOSED DECISION — subject to independent approval
Use a **Food Catalogue-owned, versioned, immutable allergen attestation** with explicit source proof, taxonomy and applicability. Publish through one transactional, idempotent service; never use a blind seed upsert that mutates the existing flag. Approved complete statuses are `REVIEWED_WITH_CODES` and `REVIEWED_EMPTY_SET`. `UNKNOWN`/held and `REVOKED` always project `allergens_reviewed=false` with no accepted current codes. `REVIEWED_EMPTY_SET` means no flagged categories in the **exact pinned taxonomy / source-specific reviewed scope**, **not universal allergen absence**.

### OPEN — must be closed before the implementation PR
- Exact applicable Russian allergen-classification taxonomy, version, legal/reference evidence and bounded scope for each food/form, including ingredient identity vs packaged-product cross-contact. A reference rule alone cannot classify each ingredient.
- Whether any already-recorded `allergens_reviewed=true` legacy row exists outside the DC4-A3 seed, and how to preserve its historical visibility without fabricating a new attestation.
- The exact approved source-artifact access/hash receipt method, reviewer role/authorization and revocation authority. A syntactically valid JSON URL/SHA from [#300](https://github.com/Mitronomik/family-food-os/pull/300) is **not** an independent review.
- Choice of migration identity (next unreserved after 0044; **do not** silently consume a number or repurpose reserved 0033), generated table/trigger form and read implementation.

## 3. Immutable identity / evidence contract

**One exact FoodIngredient identity** per attestation: `food_ingredient_id` and frozen canonical `code`, normalized Russian name, category, form/unit and an explicit identity-snapshot digest. A review of wheat flour, dairy butter or unknown-origin refined oil cannot silently transfer to generic flour, a different fat form, any brand, a ready dish or an unreviewed supplier.

Each immutable `AllergenAttestationVersion` record shall include:

- generated attestation UUID; FoodIngredient UUID; positive monotonically increasing **version** scoped to that FoodIngredient; prior attestation ID (or none for first), reason (`INITIAL`, `CORRECTION`, `REVOCATION`);
- `status` from `REVIEWED_WITH_CODES`, `REVIEWED_EMPTY_SET`, `UNKNOWN`, `REVOKED`; sorted unique normalized allergen-code set; exact **taxonomy identity and version**; explicit unknown or held scope;
- source name, stable source record/form reference, source version/release, source locator, expected **source-byte SHA-256** (not a URL-string hash), extraction/curation identity, rights/use scope and evidence reference;
- independent reviewer/decision reference and reviewed-at timestamp, source applicability statement and exact canonical identity decision;
- immutable canonical payload digest, creation timestamp, and explicit supersession/revocation provenance; no price, nutrition, serving, household or customer information.

**No version-free boolean authority.** A review-reference string and a 64-digit hash are structural requirements, not trusted signatures; publisher must verify accepted review policy/allowlist, pinned source receipt, role, source rights, taxonomy and exact identity before accepting them. An LLM/external parser is never publication authority.

## 4. Persistence, replay and transaction contract

**Proposed schema:** append-only FoodIngredient allergen-attestation versions, source/provenance and code-set child rows or canonical immutable equivalent. An index/unique constraint prevents two versions for `(food_ingredient_id, version)` and duplicate exact current head. Use existing synchronous SQLAlchemy Core + project UoW / custom SQLite runner; no Alembic, no ORM, no distributed transaction.

**Compatibility:** retain `food_ingredients.allergens_reviewed` and `food_ingredient_allergens` until an expressly approved consumer migration. On **FRESH** reviewed publication, insert immutable attestation and in the **same UoW/transaction** replace current materialized flag/code rows from that exact attestation. On **REVOCATION/UNKNOWN**, atomically clear current projection and require fresh evidence for a new review. Reject any partial flag/code projection. Existing `FoodIngredient.id`, recipe/ingredient FKs, FoodNutritionProfile, RecipeVersion, MealPlan, Pantry and Shopping rows never get rewritten.

**Return contract:** `FRESH`, `EXACT_REPLAY` (zero writes, same identity/version/source/evidence/code set), `CONFLICT` (same authority/version with different bytes, stale parent, mismatched identity/form/taxonomy, contradictory reviewed codes), or `BLOCKED` (no actual authorized independent evidence). Publication must be idempotent and fail closed, including simultaneous writers. On any failure-injection point (attestation, code rows, legacy projection, receipt), rollback leaves all original rows byte-for-byte and preserves existing history.

**Legacy upgrade:** no automated promotions. Before a first reviewed attestation, existing flag/codes are **legacy observations**; preserve them, separately report unknown review provenance, and avoid inventing a backfilled reviewer or trusted source hash. If any already-reviewed rows exist, migration must preserve current consumer behavior until a separately approved transition/remediation strategy; never reinterpret them as new source-reviewed records.

**Historical/revoked:** existing immutable MealPlan and RecipeVersion history remains readable. A revoked current FoodIngredient attestation cannot be used for *new* composed admission; any current/derived regeneration or stale behavior outside existing source checks requires a separate reviewed downstream integration contract, not an implicit mutation of Shopping or accepted historical plan revisions.

## 5. Corpus-wide backlog / future inputs

- On each dataset/seed import, deterministic source review discovery yields `UNKNOWN` + a queue entry for every new FoodIngredient/form lacking an independently approved attestation; **catalogue insertion is permitted**, automatic Planner/consumer eligibility is not inferred.
- Source curation may batch review **all 227 existing DC4-A3 identities** by applicability/evidence family into small reviewable sets (DATA-CORPUS-V1 recommends 25–60 exact foods per batch), not one PR per recipe. Each row must be independently justified; a shared policy can support multiple foods only where its scope actually covers each.
- Publisher compares accepted source-version/identity and exact reviewed codes before updating the compatibility projection; old seeds must be replayable without trying to reset reviewed metadata to false. This requires an explicit separation of **identity seed reconciliation** from **allergen-review publication**, not weakening identity conflict checks generically.
- CI audits whole-catalogue readiness, recipe usage, source-review queue and drift after seed changes. A source exception or unsupported form remains `UNKNOWN`; no attempt to reach 100% review by fabricating negative allergen codes.
- Source review for nutritional completeness, meal role, final edible mass, kitchen output and freeze/reheat remains separate.

## 6. Acceptance & adversarial tests

Required before runtime merge:

1. **Fresh + upgrade:** create a fresh DB and upgrade old DB with `0044` prefix; add only approved new append-only tables/triggers. Recheck `PRAGMA foreign_key_check`, previous schema history, bytes of old persisted recipes and identities.
2. **Full corpus:** use real accepted DC4-A3 canonical 227+ identity corpus without truncation; reconcile every FoodIngredient and every active RecipeVersion dependency. No special-case allowlist for just 12 blockers.
3. **FRESH / EXACT_REPLAY / CONFLICT:** genuine reviewed code and explicitly reviewed empty-set positives, source/taxonomy/name/form mismatch negatives, altered source digest, duplicate code or version, stale source/version, contradictory active head. Replay must produce zero writes.
4. **UNKNOWN / revoke:** absence of source, reviewed evidence of another food/form, revocation, duplicate/unsafe code, stale approval and cross-contact uncertainty never become `REVIEWED_EMPTY_SET`; revocation atomically removes consumer-compatible current reviewed status while retaining old attestation.
5. **Injection / concurrent:** fail after each insertion, parent/lineage check, code-set insert, projection update, commit; require complete rollback and no half-reviewed component. Concurrent same-source replay or conflict must be deterministic.
6. **Regression:** identical `AI_ENABLED=false` Planner/MealPlan/Shopping/Pantry/Nutrition semantics for unchanged data; no rewriting historical RecipeVersions or old MealPlans; source isolation/cross-Household tests. Run focused app, migration fresh+upgrade and broad **backend + launcher** after runtime freeze.
7. **Rights/quality:** exact source artifact independently accessible/hash verified, reviewer scope/decision pinned, complete evidence by reviewed food/form. No per-family medical claims or automatic source authority from a CI JSON structure check.

**Exit:** audit may truthfully report `UNKNOWN` for some foods. The reusable pipeline is DONE when every current/new food is inventoried, every *approved* attestation is source-verifiable, publication/replay/revoke is atomic and versioned, new identities enter review queue without silent admission, and 0044/Shopping use no unreviewed ingredient as a positive. Full 227-food reviewed coverage is a **data curation outcome**, not achieved by this gate.

## 7. Merge / sequencing / rollback decision

**This document is a docs-only gate:** no runtime, schema, source, reviewer authority, external material, API/UI, Shopping, Planner or MealPlan code change. Review / merge this contract **before** implementing the attestation migration and publisher. No automatic authorization to publish a particular allergy mapping from the contract alone; source-review/rights/qualified evidence still separately required.

**Rollback this gate:** revert this document only; no data touched. **Rollback a later FRESH attestation** is *not deleting immutable history*; use accepted subsequent revocation/supersession with current projection updated atomically. Any crash failure rolls back UoW to pretransaction bytes.

**Owner decision to request after independent review:** accept the proposed append-only attestation + compatibility-projection path, its exact bounded status semantics and preservation/replay tests, or return with an alternative design. Do not silently introduce a migration or mutate existing allergen flags merely because the catalogue-wide auditor demonstrates large UNKNOWN coverage.
