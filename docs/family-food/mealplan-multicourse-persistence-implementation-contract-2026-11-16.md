# MealPlan multi-course persistence — Implementation Contract Gate

**Status:** PROPOSED — docs-only; requires independent review and owner merge **before** schema/runtime work.
**Decision requested:** approve the bounded persisted **diagnostic** composite-event model and preservation/gating below, or return with revisions. This document itself implements **no migration, API, runtime logic, Shopping support or release permission**.
**Accepted base:** `main@e32ae5ef07937ed4ef545e7f9d77801a6757f7b9` — [PR #290 merged](https://github.com/Mitronomik/family-food-os/pull/290), 2026-11-16.
**Parent evidence:** [PR #289](https://github.com/Mitronomik/family-food-os/pull/289) (real, one-member, 3-course diagnostic lunch), [PR #290](https://github.com/Mitronomik/family-food-os/pull/290) (non-persistent component/member Serving model and `EVENT` vs `PER_PARTICIPANT` course requirements).
**Read with:** [Root AGENTS](../../AGENTS.md), [Architecture](architecture.md), [Compatibility Addendum](architecture-addendum-2026-09-13.md), [Product Strategy](product-strategy.md), [Meal Pattern Programs](meal-pattern-programs.md), [PR7 MealPlan](pr7-mealplan-serving.md), [Shopping Contract](pr9-shopping-implementation-contract.md), [Planner Serving Plausibility](planner-serving-plausibility-contract-2026-10-17.md), [Verification](verification-policy.md).

## 1. FACT / ASSUMPTION / PROPOSED DECISION / OPEN

**FACT:**
- `HouseholdMealEvent` is currently a `MealSourceKind.COOK_RECIPE` event with one `recipe_version_id`, or a non-recipe source with no `recipe_version_id`. It does **not** have an authoritative multi-recipe mode. `Serving(event_id, member_id, portion_servings)` is unique per event/member and means a scale of the event's one RecipeVersion.
- `MealPlan` is immutable and versioned by `(household_id, week_start, revision_number)`, with `supersedes_plan_id`. `SqlAlchemyMealPlanRepository.add_detail()` inserts plan, member selection/reference pins, events, Servings within one UoW; `get_detail(household_id, plan_id)`, `get_current(household_id, week_start)`, `list_history()` are household-scoped.
- SQLite migration registry currently ends at `0043_shopping_engine`; `0033` remains reserved and is **not** inserted into the already accepted prefix. The custom SQLite migration runner is the sole authority. `meal_plan_events.source_kind` is CHECK-constrained and `COOK_RECIPE` requires a non-null recipe. Events, Servings and MealPlan revisions have immutable-row triggers.
- Shopping v1a iterates persisted `MealPlanDetail.events` + legacy `Serving`; for `COOK_RECIPE` it multiplies each pinned ingredient by sum of Servings/base. It does **not** read component Servings. A composed event masquerading as ordinary `COOK_RECIPE` would **under-count or double-count** groceries. `EAT_OUT` has no recipe-demand expansion.
- #290's `MealEventCompositionDraft`, `MealComponentDraft`, `MemberComponentServingDraft` and explicitly selected `RequiredCourseCoverage` validate **structure only**; they neither validate full nutrition, recipe suitability, physically feasible portions nor Shopping/Prep authority.
- For the accepted illustrative Tuesday 2026-11-03 lunch, member #1 is the only at-home lunch participant; members #2/#3 have no home lunch and must not acquire phantom events, kcal or groceries.

**ASSUMPTION TO CHALLENGE:** an additive immutable set of component tables, plus a strictly new source kind that old engines cannot interpret as ordinary recipe demand, is the smallest safe persistence evolution. SQLite table rebuilding can preserve all historical `meal_plan_events` dependent FKs and triggers if a fresh/upgrade/failure-injection proof passes.

**PROPOSED DECISION:** use a new `COOK_COMPOSITION` meal-event source kind for **new, explicitly diagnostic-only DRAFT plan revisions**, with course structure and exact member-component Servings persisted atomically. Preserve all existing `COOK_RECIPE`/legacy `Serving` semantics without backfill. **Do not activate composite events as accepted consumer plans or Shopping demand in the persistence PR.** A later separately reviewed Shopping/context integration is a distinct authorization, not an implicit permission from storing rows.

**OPEN FOR OWNER/REVIEWER:** exact public API shape for a future consumer multi-course editor, eventual approved role policy and source rights, physical portion eligibility, final transition from diagnostic DRAFT to an authoritative composition with compatible Shopping/Prep/Nutrition. None of these questions may be silently resolved by the first persistence PR.

## 2. Ownership and compatibility options

| Option | Consequence | Disposition |
| --- | --- | --- |
| A. Add components to a legacy `COOK_RECIPE` event, leaving old `Serving` as an anchor | Existing Shopping/Nutrition/Prep silently read **only** the primary recipe; adding component rows after the fact also undermines immutability | **REJECT** |
| B. Represent a multi-course meal as `ASSEMBLY` | Conflates a multi-course meal with a recipe assembly that has independent source/composition authority | **REJECT** |
| C. Separate new `COOK_COMPOSITION` source kind, explicit component rows and member-component Servings, new append-only DRAFT MealPlan revision | Requires a CHECK-preserving migration rebuild, explicit mixed-read handling and fail-closed downstream tests; no silent ingredient demand | **RECOMMENDED (proposed)** |
| D. Store free-form JSON as `source_reference` | No typed source-pin/Decimal identity; weak constraints, poor auditing and migration to Shopping | **REJECT** |

The role rule is an explicit, versioned research/proposal input, **not** a published `MealPatternProgram`. Its `coverage` must be explicit: for the requested home lunch, `FIRST` and `SECOND` are mandatory **PER_PARTICIPANT**, while `DESSERT` has `minimum=0`. `EVENT` is allowed as a separate, explicitly weaker draft rule and must never be treated as per-person completeness.

### 2.1 Source-kind and legacy contract

- Add `MealSourceKind.COOK_COMPOSITION` to domain, SQL CHECK and adapter/read mapping only in the **future runtime PR**. It means **multiple immutable recipe versions under one eating opportunity**, not an invented RecipeVersion/RecipeAssembly.
- For `COOK_COMPOSITION`, the parent `meal_plan_events.recipe_version_id` MUST be NULL and `source_reference` MUST be NULL. Its source authority comes from all child `recipe_version_id` pins.
- `COOK_RECIPE` and all historical non-recipe kinds remain byte-identical, semantically unchanged and read without synthetic component rows or altered Serving values.
- `COOK_COMPOSITION` has **no legacy `servings`**. Its participant set is the union of exact child component Servings. Do **not** insert fake `Serving.portion_servings=1` attendance rows, which would mislead Nutrition/Shopping.
- The original #289 `MealPlan` remains immutable. The new sample is a separate append-only **revision** with its own plan/event UUIDs and correct `supersedes_plan_id`; existing plans are neither rewritten nor assigned sidecar components.

## 3. Proposed additive data model and source pins (future migration 0044, pending availability check)

Migration candidate name: **`0044_meal_plan_components`** — verify it remains unallocated against latest `main` **at runtime start**. Do not change `MIGRATION_MODULES` in this docs PR.

**Parent:** existing `meal_plans` (household/week/revision) and `meal_plan_events` (local day, position, role). New event `source_kind=COOK_COMPOSITION` with null `recipe_version_id`. Existing `meal_plan_member_selections` and exact reference-methodology pins remain the accepted Household selection/revision snapshot.

**New tables (proposed names and key constraints):**

| Table | Columns and hard keys | Role |
| --- | --- | --- |
| `meal_plan_event_compositions` | `event_id PK/FK → meal_plan_events.id`; `structure_rule_code TEXT NOT NULL`, `structure_rule_version INTEGER >0`, `required_coverage ENUM(EVENT,PER_PARTICIPANT)`, `admission_status='DIAGNOSTIC_ONLY'`, `created_at` | Explicit immutable rule provenance for one new composed event. No implicit role template/physical PASS |
| `meal_plan_event_components` | `id UUIDv4 PK`; `event_id FK → meal_plan_event_compositions.event_id`; `position INTEGER >0`; `course_kind` from PR290 `MealCourseKind` (not `RecipeVersion.meal_type_code`); `recipe_version_id FK → food_recipe_versions.id`; `created_at`; `UNIQUE(event_id,position)` | Ordered, immutable source-pinned recipe component |
| `meal_plan_component_servings` | `component_id FK → meal_plan_event_components.id`, `member_id FK → household_members.id`, `portion_servings TEXT NOT NULL` (exact positive finite Decimal, 0.000001 precision), `created_at`; `PRIMARY KEY(component_id,member_id)` | One physical allocation per participant and component. Not a legacy event Serving |

**Schema guarantees:** SQLite `FOREIGN KEY`/CHECK/UNIQUE, canonical 32-char UUID encoding, required course-kind enum, positive integer positions, immutable UPDATE/DELETE triggers on all new tables, indexes for event/position and component/member, `ON DELETE RESTRICT`. In SQLite, a simple CAST-only CHECK is insufficient to prove valid canonical Decimal: application validation and negative SQL tests must reject `NaN`, scientific notation, locale commas, negative/zero, too many fractional digits and excessive magnitude. No float or silent quantization. A direct DB write that is well-formed but would create an incomplete multi-course event must remain **inaccessible outside the tested UoW**; domain + repository transactional validation are mandatory.

**Necessary cross-row invariants (application/domain + UoW):**
1. New parent event belongs to the **new** Household-owned MealPlan revision and is `COOK_COMPOSITION`. Parent and components are inserted in the **same transaction**. Each child recipe must be an exactly pinned, verified/reviewed eligible `RecipeVersion`; no synthetic recipe identity.
2. One composition header per event; 1..N components, contiguous positions, distinct component identity; course kinds comply with the **explicit** versioned structure rule. `PER_PARTICIPANT` minimums are checked against each actual member, not just event totals; optional course may be absent for one member.
3. Attending members belong to the plan's **pinned Household selections**, have explicit selected at-home opportunities for that local date/role and pass hard ingredient exclusions. No out-of-home placeholder meal. Component Serving positive exact Decimal and member/component unique. No unauthorized household cross-reference.
4. `COOK_RECIPE` retains its historical event-level `Serving` rows and immutable recipe pin. `COOK_COMPOSITION` has **only** member-component Servings, with no legacy Serving. Every stored component must have at least one participant; every attending member must meet the draft role rule's mandatory courses.
5. `admission_status=DIAGNOSTIC_ONLY` and `MealPlan.status=DRAFT` are enforced **before commit**; no public CONFIRMED composition, no partial plan writes. Source-ingredient/canonical FoodIngredient authority, unknown nutrients, member contraindications and physical portion feasibility remain separate reviews; passing structure is not their substitute.
6. A plan revision cannot be mutated by adding/removing child components after its initial transaction. New choices always create **another** plan revision, not an in-place edit.
7. Deterministic ordering is `(local_date, event.position, component.position, member UUID)`, preserving Household-local date; no implicit per-day energy redistribution.

### 3.0 Rollout hold: current-plan and Shopping safety

**Critical accepted behavior:** current `SqlAlchemyMealPlanRepository.get_current(household_id, week_start)` returns the **highest revision, regardless of DRAFT/CONFIRMED status**. Thus creating a diagnostic composition revision for an already active household/week would immediately change what existing readers consider `current`, and could make prior Shopping snapshots stale *before* any component-aware Shopping engine exists. This is **not permitted as a routine user write** in the first runtime PR.

Until a separately reviewed activation plan and component-aware Shopping/consumer readers exist, `add_diagnostic_composition_revision` must be **developer/test-only**, without a public API, normal Planner invocation, or production-household enrollment; use a dedicated synthetic Household/isolated test database for the demonstration. Do not silently change `get_current` selection semantics to hide DRAFTs: that would be a different behavior contract and would break existing callers. Tests must prove the old operational plan and Shopping state are unaffected by normal application paths. Any subsequent proposal to enable diagnostic revisions in an active Household/week must revisit this gate and explicitly address current-plan selection, derived-state staleness, and the reader capability matrix. A local prototype is not authorization to deploy or expose the writer.

### 3.1 Domain / repository / application shape

- Extend `MealPlanDetail` **additively** with typed read-only composition tuples defaulting to `()` for historical callers. Preserve the old tuple-of-legacy-Serving API for `COOK_RECIPE` events; introduce explicit `composed_event_details` / `component_servings` for the new kind, not fictitious legacy Servings. Existing `MealEventCompositionDraft` and validator from #290 can be adapted for the new event source with explicit input references; their current source-anchoring assumption (`COOK_RECIPE` original) cannot be reused blindly.
- Add an **explicitly named** repository/UoW operation (e.g. `add_diagnostic_composition_revision(...)`) rather than making generic `add_detail()` accept an incomplete composition. The service owns member/selection, source-verified recipe/ingredient and admission checks. The repository owns transactional writes and conflict translation; no SQL in domain/services.
- Reading `get_detail(household_id, plan_id)` and `get_current(household_id, week_start)` returns explicit typed components and per-component Servings when present, with complete roundtrip identity/quantity/provenance. Existing callers still get legacy events/Servings unchanged for legacy revisions. Malformed partial data is **fail-closed**, never treated as a valid one-recipe meal.
- `MealPlanNutrition` calculation, derived weekly UI/PDF, Planner historical traces, Shopping and Prep must **fail closed or explicitly report unsupported composition** until their separate integration is accepted. In particular, Shopping v1a must **never** count a primary recipe as a substitute, double-count components, or declare `COMPLETE` on a `COOK_COMPOSITION` event. New source kind must enter no implicit `COOK_RECIPE` calculation branch.
- Canonical `source_fingerprint` for future Shopping will pin **each** component position, RecipeVersion immutable source id/hash/version, exact member Serving, source plan revision and Pantry snapshot, with deterministic aggregation by canonical FoodIngredient+unit. That algorithm, idempotency and staleness are **owned by the future Shopping PR**, not implemented or authorized here.

## 4. Migration safety, replay, rollback and failure semantics

**Preferred migration shape:** `0044` adds three tables. To extend the existing `meal_plan_events.source_kind` CHECK **without dropping integrity**, use the already supported `foreign_key_rebuild` migration mode where necessary. Recreate the parent table with the original constraints, indexes, immutable triggers, FK relationships, original rows and only the added `COOK_COMPOSITION` enum/null-recipe semantics. The runner's rebuild mode disables FKs on a dedicated connection inside a managed transaction, owns the migration marker and executes `PRAGMA foreign_key_check` before commit. Never use Alembic/ORM/`create_all` or `executescript` in the foreign-key rebuild transaction. Do **not** alter accepted `0032`, `0037`, `0043` or earlier migration bytes.

**Risk:** `meal_plan_events` is referenced by historical `servings`, `shopping_` metadata/allocations and potentially other dependent tables. Before choosing the exact SQL rebuild, inventory **every** referencing FK, trigger and index on the runtime HEAD, and prove the rebuilt table is semantically identical for every preexisting source kind. If this cannot be done safely with the existing runner, **stop and amend this contract**, not a best-effort table rename that breaks historical FKs. No orphaned child rows or dropped immutability trigger.

**Fresh:** empty SQLite applies migrations in exact existing order ending 0043, then 0044; `expected_migration_ids`, metadata parity, `PRAGMA foreign_key_check`, snapshot equality; initial schema has no synthetic component rows.

**Replay/upgrade:** a DB already at 0043 with legacy multi-week MealPlans, `member_meal_pattern_selections`, reference pins, old Servings and Shopping snapshots upgrades to 0044 while preserving row counts/identities/quantities and the **exact historical plan fingerprint**. Running `apply_migrations` again is a no-op. No backfill, content rewrite, source-kind recoding, or presentation changes on historical plans. Previously known weekly `get_current` and `list_history` remain well-defined.

**Conflict/failure injection:** invalid UUID or orphan component/Serving; duplicate position or member/component; wrong Household or plan; truncated course set; negative/overprecision Decimal; forbidden course/missing member; stale selection/reference or source Version; simultaneous revision creation; new migration interrupted after the first DDL/row copy, after indexes/triggers, or before marker; failure after writing parent/event but before final component Serving; failed user validation; readback corruption. Every path must rollback *entire* new revision and its children with no partially visible current plan/Shopping state and no partial migration marker. Verify failure error is stable and non-leaky.

**Rollback:** migration downgrade is **not** an in-place deletion of new tables or old revisions. Restore a verified pre-upgrade backup as the recovery path if a migration is not safely completed; test backup/export and restore against existing migration ledger. For an application-only rollback after 0044, keep schema additive and old readers operational; new composed DRAFT revisions remain stored/blocked, never silently converted to legacy `COOK_RECIPE` events. If pre-upgrade binary cannot handle a new `COOK_COMPOSITION` current revision, use an explicit compatibility/rollout hold before enabling writers.

## 5. Phased enablement and preservation matrix

| Surface | Old historical revisions | New composed diagnostic revision | Until separately reviewed future authorization |
| --- | --- | --- | --- |
| MealPlan source | Existing source enum/RecipeVersion pins unchanged | Explicit `COOK_COMPOSITION`, no parent recipe | New writes only through diagnostic DRAFT operation |
| Member attendance | Legacy positive `Serving` per event/member | Set of member-component Servings; all required courses per member | No fake legacy Servings |
| Nutrition | Original computed/UNKNOWN status intact | `UNSUPPORTED_COMPOSITION` or explicit fail-closed diagnostic | No kcal or KБЖУ approval |
| Shopping | Existing ingredient demand and immutable source snapshots unchanged | **UNSUPPORTED** until new generic Shopping composition PR | No partial basket, primary-only fallback or duplicate demand |
| Prep/Freezer | Existing safety and Gate2 gates unchanged | **NO_GO** (not executable, not supply) | No prepared batch/storage authority |
| UI/API/PDF | Existing historical read surfaces unchanged | No consumer route/editing exposed in this PR | No inferred outside-home meals or physical portions |
| Planner | `planner-v0.3/0.4/0.5` history and frozen A/B immutable | No automatic multi-course generation | New Planner version and rule policy require separate decision |
| Persistence | Same `MealPlanDetail` + legacy Serving rows; original hashes retained | New typed composition readback and **new append-only** revision | No in-place edits to old revision |

**Non-goals of the post-gate runtime PR:** automatic recipe selection, dynamic course policy publication, clinician/diet prescriptions, full Nutrition, final edible output/physical portion PASS, inferred kcal redistribution, Shopping/Prep/PDF recalculation, Retail/AI, consumer UI, cross-household sharing, auth/PostgreSQL migration, changing accepted fixtures or source catalogue facts.

## 6. Exact required implementation acceptance tests (future runtime PR)

1. **Migration: fresh / replay / 0043→0044 / FK-inventory / failed DDL rollback.** Existing 0043 data, trigger effects and Shopping snapshots remain byte/semantically unchanged; `foreign_key_check` empty; runner marker atomic; no leaked new tables on fault.
2. **Legacy regression:** a stored `COOK_RECIPE` event with one Serving/member has identical `MealPlanDetail`, historical plan hashes, Shopping v1a quantities and source fingerprint before/after migration. Existing manual/Planner 7-day fixture stays reproducible across two actual independent processes.
3. **One real case:** create a *new* DRAFT plan revision for synthetic Tuesday 2026-11-03 at-home LUNCH, one `COOK_COMPOSITION` event with FIRST source-backed soup, SECOND original verified casserole, optional DESSERT candidate marked **role applicability NOT_PROVEN**. Exactly member #1 attends; members #2/#3 do not get home lunch. Persist/read all exact component IDs, positions, source Version pins, structure-rule version/coverage and Decimal servings. Do not use the UNREVIEWED dessert as a consumer-approved selection.
4. **Per-person completeness:** two-member lunch FIRST only member A and SECOND only B rejected despite event-level coverage. Both receive FIRST+SECOND with optional DESSERT only A succeeds structurally. A versioned EVENT-only rule does not silently satisfy a PER_PARTICIPANT policy.
5. **Hard exclusions and source authority:** reject unverified/stale RecipeVersion, unknown or inactive FoodIngredient, wrong unit, excluded allergen/food, wrong source-variant/rights and insufficient source publication; do not insert source-invented dish.
6. **Partial-at-home schedules:** breakfast-only, dinner-only, lunch-only, breakfast+dinner and mixed Household schedule; create only explicitly selected opportunities, no faux `EAT_OUT`, no unexpected member Servings, no daily energy redistribution.
7. **Transaction/immutability:** abort after parent/event/component/Serving write, retry/concurrency and duplicate revision, attempt UPDATE/DELETE each component row, wrong Household for read/write, orphan/duplicate component and member, oversized Decimal, role/order/unknown policy mismatch. No partial persisted revision.
8. **Cross-context fail-closed:** call unmodified Shopping v1a on new composite DRAFT: must reject or return an explicitly unresolved **non-COMPLETE** state (without any component or primary-only ingredient purchases). Likewise Nutrition/Prep and any exposed generated week UI cannot treat new event as ordinary `COOK_RECIPE`; no stale/freshness bypass.
9. **Versioning and rollback:** new revision supersedes only its immediately prior accepted revision, old revisions remain addressable; 0044 is appended only to the end of the migration list; repeated upgrade idempotent; backup/export/restore intact.
10. **Verification tier:** focused domain/service/repository tests; full fresh+upgrade migration/replay; UoW rollback and race tests; full backend and launcher/regression once at frozen exact HEAD; existing independent 2-process PR10-FF proof and docs/typed identity checks. Preserve `AI_ENABLED=false` and no Gate2/real-family promotion.

No green unit suite substitutes for the actual migration/FK/rollback/replay proof. Failure of a required branch yields **BLOCKED / NO_GO**, not a favorable synthetic snapshot.

## 7. Merge/authorization sequence

```text
PR #290 (merged; non-persisted domain draft)
    ↓
THIS PR (docs-only Implementation Contract Gate — independent review + owner merge)
    ↓
MealPlan-only runtime PR (new 0044 migration + typed UoW/readback + guarded diagnostic writes)
    ↓
Separate Shopping Engine contract/review and integration PR (component-aware canonical demand)
    ↓
Separate source/role/physical-portion/Nutrition acceptance and future Planner/consumer gating
```

**This contract PR is deliberately docs-only.** Never start the runtime migration or create authoritative component Shopping demand until its gate has been reviewed/merged. A later discovered schema/cross-context conflict must return here for a reviewed amendment instead of changing accepted contracts silently.
