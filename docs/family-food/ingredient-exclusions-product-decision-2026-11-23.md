# Product Decision — Ingredient exclusions, not an allergen recommendation service

**Status:** OWNER-APPROVED PRODUCT DIRECTION; implementation acceptance remains subject to tests and review.
**Decision date:** 2026-11-23.
**Accepted baseline:** `main@66bcaafc600e3a12e2041fcc04fdc4c20f30cad9` (merged #300, #301).
**Authority:** explicit owner decision in FamilyFoodOS product conversation, superseding the earlier proposed whole-catalogue allergen publication direction for MVP.
**Scope:** MVP product experience and deterministic Planner constraints. This decision does **not** retroactively change food-origin, nutrition, physical portion, Prep or other Gate1/Gate2 evidence rules.

## Decision

FamilyFoodOS is a household meal-planning/wellness tool, **not an allergy diagnosis, allergen-certification, medical-diet or food-safety guarantee service**.

The only relevant MVP consumer feature is **«Исключённые продукты и ингредиенты»** (or brief «Не используем»). Users pick canonical foods they do not want in their household/member meal plans, *without entering a medical reason*. The system must filter their direct and resolved recipe ingredient references deterministically. It must not ask whether the reason is allergy, a diagnosis, religion, taste, ethics, or another personal circumstance.

**Product claim:** «Мы не добавляем выбранные продукты в предлагаемые блюда». Do not promise «не содержит аллергенов», «безопасно при аллергии», «подходит для лечения» or anything implying certified cross-contact exclusion.

## In/out of MVP

**IN:**
- Canonical `FoodIngredient` IDs as exclusion choices; Russian searchable catalogue with aliases where available.
- Per-member exclusions (and optionally household-wide preferences as a transparent combined union), default empty.
- Filter candidates at generation/replacement/replan; if a recipe contains a prohibited canonical ingredient for **any member assigned to that meal**, reject that shared recipe or create a separately verified meal for affected members where supported.
- Check every mandatory ingredient and optional ingredient if present; never silently assume an ingredient is absent solely because marked optional. Apply deterministic rules to constructed components, substitutions, and ingredient remapping wherever those paths are enabled.
- Reject an impossible plan with a clear Russian reason and a user-editable next step; never silently relax hard exclusions.
- Ensure source changes/replans do not leave stale purchase or preparation plans.

**OUT:**
- Diagnoses, allergy severity, clinical recommendation, personalised medical risk profiles.
- Whole-catalogue allergen `AllergenAttestationVersion` publisher, regulatory taxonomy and source-verified allergen-free certification for MVP.
- Retail SKU contaminant/cross-contact guarantees or medical-grade warnings.
- Any explicit allergen-related information in consumer `Household` records.

## What existing implementation already has (reviewed source)

`backend/app/services/planner.py` has `GenerationMemberConstraints.excluded_food_ingredient_ids` and passes it into `MemberPlannerConstraints`; the deterministic Planner performs candidate checks. **This is an existing input capability, not proof of end-to-end consumer readiness.** No new DB/API/UI writes or tests are claimed in this decision PR.

Current `FoodIngredient.allergens_reviewed` and `allergen_codes` are legacy catalogue metadata. Do not bulk-update or erase them. They **must not** become hard prerequisites for the new non-medical exclusions workflow. Existing composed-meal diagnostic source gates and independent four-axis evidence constraints remain unchanged until a separately scoped, tested admission decision; **do not silently lift** them. The existing #300 audit is retained as optional internal diagnostic, not a mandatory data-readiness gate.

## Supersession / decision registry

- [Merged #301 proposed allergen-attestation implementation contract](allergen-attestation-publication-implementation-contract-2026-11-23.md): **MVP publisher direction superseded**. Its `NO_RUNTIME` requirements remain applicable **only if the allergen-attestation programme is reactivated by a new explicit owner decision**. They must not be reinterpreted as a blocker to non-medical exclusion filtering.
- [PR #302 taxonomy proposal](https://github.com/Mitronomik/family-food-os/pull/302): **cancelled as an MVP prerequisite**, retains historical research status only; do not merge it as active implementation authority.
- [#300 audit](https://github.com/Mitronomik/family-food-os/pull/300): existing read-only tool can remain without requiring completion of its source-attestation backlog for the non-medical exclusions feature.
- Other safety and data contracts (provenance, nutrition, food form, portion feasibility, storage) are **not** waived by this pivot.

## End-to-end tests and DoD for next bounded runtime PR

1. Family with members A/B; only A excludes one `FoodIngredient`: generated meals for A do not include it; meals for B may include it when not shared with A. A shared meal containing it is not assigned to A.
2. Source-pinned RecipeVersion ingredient reference is checked by exact canonical ID, not text substring or guessed category; repeats and recipe scaling cannot remove exclusions.
3. Multiple excluded products, missing/inactive catalogue identities, alias selection, and a recipe using the excluded ingredient in an optional or nested course are handled without false negatives.
4. Replace/replan and fixed events cannot bypass hard exclusions; if a fixed recipe violates them, return a user-actionable conflict instead of silently accepting it.
5. Unsatisfiable constraints return a typed deterministic failure, not a 500/empty accepted week.
6. Existing `AI_ENABLED=false` behavior remains valid. No allergen review flag or regulatory taxonomy dependency appears in the exclusion admission path.
7. API, whenever introduced, must enforce Household authorization boundaries and avoid creating/storing an exclusion reason or medical-condition field. Consumer copy is Russian; PWA mobile-first; simple choose-and-remove flow.
8. Shopping/Prep/PDF are recalculated or marked stale when the accepted meal plan changes; no Pantry mutation by planning.

## Next delivery sequence

**One bounded implementation PR:** verify and complete the existing hard-exclusion Planner paths and adversarial tests first, with no new migration if current request-scope constraints suffice. Then a separate consumer/API persistence PR only when required by an approved end-to-end UX. No fabricated diet safety, no taxonomic classification or whole-catalogue data curation. Keep `main` working.

**Acceptance decision:** this document records the owner-approved product pivot, **not** proof that the consumer workflow is finished. The next agent must read current code/tests and target one concrete missing acceptance scenario rather than restart taxonomy research.
