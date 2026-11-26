# HouseholdMember ingredient exclusions — implementation contract gate

**Status:** PROPOSED / DOCS-ONLY / independent review and owner merge required before persisted runtime work.
**Date:** 2026-11-25.
**Accepted base:** `main@c74f4d9996f6e2a4a788ceada88b1d9972437ee2` (PR #305 merged).
**Authority:** [owner-approved non-medical ingredient-exclusion direction](ingredient-exclusions-product-decision-2026-11-23.md), replacing allergen attestation as MVP scope.
**Implementation owner:** Household (persisted member preference) → Planner (read-only consumption). Read with [AGENTS](../../AGENTS.md), [architecture](architecture.md), [security](security-architecture.md), [verification](verification-policy.md).

## Goal and scope

A user selects unwanted canonical foods **once** for a HouseholdMember; future week generation applies the exclusions without making the user re-enter UUIDs. Exactly selected `FoodIngredient` identities are excluded by the deterministic Planner for that member. No medical reason is requested or stored.

**Bounded first runtime slice:** HouseholdMember exclusion persistence and service methods, existing Planner's authoritative input composition, tests. Consumer search/API/mobile UI is a separate subsequent slice once this contract is accepted and the backend is proven; avoid introducing auth/shared deployment or a generic preference platform in this bounded PR.

## FACT / ASSUMPTION / PROPOSED DECISION / OPEN

**FACT**
- `HouseholdMember` and `HouseholdState` have no stored exclusion collection; `household_members` currently has no exclusion table.
- `GenerationMemberConstraints.excluded_food_ingredient_ids` already accepts strictly typed `frozenset[UUID]` (merged #305); deterministic Planner candidate filtering has focused and persisted integration tests (merged #304).
- Existing authoritative `PlannerService.compose_authoritative_request` copies exclusions from each incoming command rather than loading persistent member preferences. An omitted request currently means empty exclusions.
- Canonical `FoodIngredient` identity lives in the platform catalogue; names/aliases are UI search aids, not identity authority.
- Product deliberately makes no allergen-free or medical claims. Historical `allergens_reviewed` flags are not a prerequisite for non-medical preference filtering.

**ASSUMPTION (verify against current migration registry before implementation):** a single new Household-owned member-to-canonical-food association table is sufficient; no general preference JSON column, snapshot of a medical reason, or new FoodIngredient authority is necessary.

**PROPOSED DECISION, pending independent approval:** persist a **per-member set** of canonical `FoodIngredient` UUID references with a Household FK and a unique compound key. Do not add a text reason, diagnosis, allergen code, severity, or user-supplied food name to stored rows. A fully replaced selection is the default API semantics; a no-op identical replace performs no writes. For first release, household-wide exclusions are out of scope; a user can apply the same choice to several members explicitly.

**OPEN:** exact migration ID (select first unreserved ID after established repository migration head, never overwrite or repurpose existing migrations); exact end-to-end API shape / authentication integration in a later PR; how a historical plan should display preferences changed since generation.

## Persistence contract and existing-data preservation

**Proposed relation** `household_member_excluded_food_ingredients` (final name to be reviewed):
- `household_id` UUID, FK to `households.id`, required;
- `member_id` UUID, parent scope enforced against **the same** `household_id` (composite key/foreign key or a supported equivalent checked transactionally);
- `food_ingredient_id` UUID, FK to canonical `food_ingredients.id`, required;
- unique `(household_id, member_id, food_ingredient_id)`;
- optional minimal created timestamp only if justified by actual read/use (avoid unused audit columns).

**Do not** add `allergens_reviewed`, medical reason, clinical labels or denormalized names here. Must preserve all existing `Household`, `HouseholdMember`, `FoodIngredient`, `RecipeVersion`, `MealPlan`, `Serving` and Shopping/Pantry rows byte-for-byte on migration.

- **Fresh and upgrade:** existing databases upgrade to an empty exclusion set for every member without changing historical facts or existing MealPlan eligibility. Empty set means *no preference selected*, never a safety assertion.
- **Write authority:** Household service + repository + UoW, not Planner SQL. Validate member belongs to requested Household and is active at update; validate every selected canonical food ID exists and matches the intended platform identity. No silent matching by Russian name or rejected/deleted/foreign identity.
- **Inactive foods:** preserve a previously selected inactive FoodIngredient in readback; do not silently clear its exclusion. At new selection time, disallow inactive/unknown IDs with an actionable error. An inactive food must not become eligible through stale identity reuse.
- **Replace semantics:** input sorted/deduplicated as a set of real UUIDs at boundary. Replace all member exclusions in one UoW. `FRESH` changes set atomically; `EXACT_REPLAY` makes no writes; `CONFLICT` returns an explicit outcome for missing member, wrong Household or unknown food. Reject oversized input with a bounded limit rather than unbounded DB transactions (limit to be set and tested in runtime PR; avoid undocumented arbitrary quotas).
- **Concurrency:** simultaneous conflicting replacements cannot silently lose updates. Choose and document optimistic revision/expected version or transaction-lock policy before implementation, with deterministic conflict regression. Explicitly changing this strategy requires reopening the gate.
- **Rollback:** fault after delete/insert/validation/commit must not expose half-updated selection. Use the existing migration runner and synchronous SQLAlchemy Core UoW. Check `PRAGMA foreign_key_check` and failure injection on fresh/upgrade.
- **Deletion/deactivation:** preserve already selected IDs as non-medical preference history while their canonical ingredient remains; no cascade wiping member preference from FoodIngredient deactivation. Member deletion/hard removal follows established FK policies and requires separate explicit analysis.

## Planner contract and no-bypass requirement

- **Source of truth:** for each active member, Planner loads the persisted exclusion set under the same Household read boundary and unions it with *additional* request-supplied exclusions; caller may add temporary exclusions but **cannot remove persisted exclusions** by omitting or supplying an empty set.
- Read the accepted member patterns and current exclusion state before candidate evaluation. Invalid reference/read failure returns a typed fail-closed error; never replace unknown preferences with empty/default.
- Preserve per-member splitting of shared dishes, exact `RecipeVersion` ingredient UUID membership and `PlannerTrace.applied_exclusions`. No exclusion requirement from `allergens_reviewed`.
- Changes to preferences **must not mutate immutable prior plans**; future generate/replan must use current preferences, and regenerating Shopping/Prep/PDF for an old plan must not silently present it as if re-evaluated. Any downstream freshness integration requiring a persisted snapshot/revision is a separate explicit contract; do not claim it is implemented in this slice.
- Preserve `AI_ENABLED=false`, all independent recipe source, nutrition, role, physical/Prep and consumer-release restrictions.

## Security and UX boundaries

These preferences may indirectly reveal sensitive personal circumstances even without a reason field. Treat them as protected HouseholdMember data: enforce Household membership and per-member object authorization in the future API; avoid emitting selections in generic audit logs, telemetry, public search or unrelated households. Data minimization **does not** equal absence of privacy obligations.

Consumer text: «Не используем» / «Исключённые продукты». Search Russian ingredient names/aliases and add/remove simple choices. No diagnosis, allergy severity, regulatory class or absolute allergy-safety promise. Consumer UX is mobile-first, but UI is not part of the first persistence PR.

## Adversarial tests / Definition of Done for the runtime PR

1. Fresh migration + upgrade from old DB with a populated Household/Member and historical plans: no old data rewritten; exclusions default empty; FK integrity.
2. Member A excludes a canonical food, member B does not: readback after new process/engine; Planner's next generated week for A never includes that food, while B remains independently eligible.
3. Omitted command exclusions still apply the persisted A selection; request supplied exclusions form a **union**, not replacement/bypass.
4. Exact retry is idempotent/no writes; atomic replacement, rollback at each write point, concurrency conflict behavior and fail-closed unknown/missing/inactive food.
5. Wrong-household member ID, cross-Household reads/writes, duplicate IDs, malformed UUID strings, removed member, stale revision and unknown FoodIngredient cannot modify or disclose a selection.
6. No medical fields, no LLM or `allergens_reviewed` dependency, no user-facing allergen-free claim.
7. Broad backend **and launcher** verification on frozen exact runtime HEAD (persistence/UoW/migration risk) plus targeted Planner tests and Ruff; `main` stays working.

## Dependency order, rollback and non-goals

**Merge this docs-only contract after independent reviewer challenge**, then one small runtime PR Household persistence + Planner read with tests, then separate thin API + Russian mobile-first selection UI. This is a single contract gate, **not** a proposed sequence of additional research/taxonomy gates.

No invented source data, allergen attestations, medical logic, food safety claims, arbitrary retailer ingestion, Auth/PostgreSQL migration, Prep activation, or UI navigation restructuring.

If this contract is rejected, no runtime code is authorized. If accepted but the persistence plan proves incompatible with existing Household keys/UoW or release constraints, stop and revise this contract rather than silently changing schema or dropping a hard exclusion.


## Proposed bounded runtime choice — PR #307 (pending independent acceptance)

**Exact migration:** `0045_household_member_food_exclusions`, following the accepted `0044_meal_plan_components`. Two additive schema objects: the member-scoped food-exclusion relation and a unique composite member/Household index needed for SQLite FK enforcement. No old Household/Member fields or rows are rewritten.

**Concurrency policy:** optimistic *expected-set compare-and-swap* in the existing Household Unit of Work. Every replacement must supply the previously read complete canonical UUID set; a changed set fails with a typed conflict, an identical replay performs no writes, and a failing delete/insert transaction rolls back. Concurrent SQLite write contention is also failed closed; no last-write-wins fallback is allowed. This avoids adding a separate preference revision table. **Limitation:** the set itself is the concurrency token, so an ABA change (A → B → A) is not independently detectable; future multi-user editing requiring stronger revision semantics must return for a separately reviewed persistence extension, not silently claim this CAS solves ABA.

**Planner boundary:** HouseholdService reads Household members and all persisted selections in a single read scope, and Planner unions these sets with any additional request-scoped exclusions. An absent/invalid entry for an existing member blocks planning, not interprets it as an empty set. Historical MealPlans are unchanged; old plan freshness/promotion remains outside this PR.

**Review status:** Implementation-specific decision offered for independent architecture/QA review in PR #307, **not automatically accepted by passing CI**. Validate concurrent CAS races, source-pin compatibility, FK scope, restore prefixes, and exact-head full backend+launcher checks before owner merge.
