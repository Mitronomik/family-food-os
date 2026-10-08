# PR9-ARCH — Generic Shopping Engine implementation contract

**Status:** PROPOSED — docs-only implementation contract gate, independent review required
**Issue:** #183
**Accepted base:** `main@73cb7ee6b20d1af958639f75f6fa5db286381cb3` (merged #181)
**Authority:** root `AGENTS.md`, [Master Roadmap](master-roadmap.md), [architecture](architecture.md), [2026-09-13 addendum](master-roadmap-addendum-2026-09-13.md).
**Next runtime stage:** PR9 Shopping, **blocked** until this contract is reviewed and merged.

## 1. Goal and factual preflight

Define the minimal backend-owned, deterministic, household-scoped Shopping derived state and its integration with **current** MealPlan/Serving, Recipe, FoodIngredient and Pantry. No runtime implementation or schema mutation is authorized by this document.

Repository facts verified against the accepted base:

- `MealPlan.revision_number` is an append-only logical revision; `MealPlanRepository.get_detail(household_id, plan_id)`, `get_current(household_id, week_start)`, and `list_history(...)` are existing service contracts. `HouseholdMealEvent` carries `source_kind`, nullable `recipe_version_id` and nullable `source_reference`; `Serving` carries `event_id`, `member_id` and positive Decimal `portion_servings` (precision 0.000001).
- Current `MealSourceKind` is **exactly** `COOK_RECIPE`, `ASSEMBLY`, `LEFTOVER`, `PREPARED`, `READY_MEAL`, `ORDER_OUT`, `EAT_OUT`. The PR7 invariant allows `recipe_version_id` **only** for `COOK_RECIPE`. No hypothetical source values are proposed here.
- `FoodIngredient` is the canonical food identity, distinct from RetailSKU; `UnitCode` is `g`, `ml`, `pcs`, `percent`. Pantry accepts **only** `g`, `ml`, `pcs` equal to `FoodIngredient.default_unit`, with three-decimal normalized quantity. Its `PantryItem` and immutable `PantryMovement` are household-scoped; movement-aware operations protect non-negative stock. Pantry has no dedicated aggregate logical revision on the current published interface.
- `PantryItemRepository.list_items(household_id, include_empty=False)`, `list_available_for_ingredient_fefo(...)` and `PantryReadScope` are available read paths; `PantryUnitOfWork` exposes write commands, which Shopping generation **must not** call. Pantry items have amount, unit, location, expiry/metadata and `estimated`.
- Current ordered SQLite migration registry ends with `0042_recipe_prepared_output_nutrition`; `0033_recipe_template_catalogue` remains reserved rather than inserted out of order. Next prospective *new* migration identifier is `0043` **only if still free at runtime start**. Existing custom SQLite runner is the sole active authority; no Alembic/ORM/`create_all`.
- The Gate1-close decision on accepted `main` certifies Planning Core; it does **not** certify Shopping, Prep or PDF. Do not reuse Gate1 tests as evidence that Shopping works.

### CONTRACT versus still requiring implementation preflight

The following are proposed cross-context contracts, **not claims of existing code**: combined read-scope/UoW, Shopping persistence tables, snapshot hashing, Shopping API, demand resolver and runtime migration. The contract below freezes calculation, Pantry eligibility, representation, transaction strategy and assembly V1 policy. Runtime preflight may verify adapter method names and map the frozen contract to existing implementation but may not reinterpret these semantics without a new reviewed docs-only amendment. If a proposed contract conflicts with an accepted physical model, return to contract review, not a silent workaround.

## 2. Source-kind demand decision table

| Current source kind | Direct new purchase demand in PR9 | Contract |
| --- | --- | --- |
| `COOK_RECIPE` | **YES** where exact immutable RecipeVersion ingredient input and participating Servings can be resolved | Sum event's positive Serving `portion_servings`; resolve ingredient inputs and normalize as specified below. Invalid/missing pins fail closed. |
| `ASSEMBLY` | **NO in PR9 V1** | The accepted repository has no production RecipeAssembly aggregate/read adapter. Always emit an `ASSEMBLY_UNSUPPORTED` unresolved obligation per event, even if `source_reference` is populated. Never infer ingredients. A later approved assembly authority requires its own contract change. |
| `LEFTOVER` | **NO automatically** | It represents already obtained food, not another fresh recipe. An accepted future remaining-serving/prepared-stock reservation contract is needed for supply validation. No duplicate ingredient demand. |
| `PREPARED` | **NO automatically** | It refers to pre-existing prepared supply. No second ingredient charge; if supply is not verified, expose unresolved supply rather than asserting it is available. |
| `READY_MEAL` | **NO canonical recipe ingredients by default** | Purchased ready-food demand belongs to a separately defined purchasable-item/retail-independent supply model; keep visible as unresolved purchase/supply when no trustworthy representation exists. Do not suppress it as fulfilled or invent ingredient decomposition. |
| `ORDER_OUT` | **NO** | Eating/order-out is not grocery ingredient demand. Any known spending is independent from grocery quantity and remains unknown in PR9 without authority. |
| `EAT_OUT` | **NO** | Not a household grocery requirement. |

A complete ShoppingList must distinguish **covered recipe grocery demand** from **unresolved obligations**. It must never silently classify unknown supply as zero requirement or silently declare the whole week shoppable. Mixed-source weeks may still yield a **partial** reviewable list with explicit `INCOMPLETE` status; whether to disallow a persisted partially resolved list for a particular case is determined by the fail-closed classification below. No inferred nutritional, cost, storage, source-kind or substitute authority.

## 3. Quantity calculation and normalization

1. Read one authoritative MealPlan **revision** and its events/Servings, not a stitched mixture of current and historical versions. Every Serving must reference an event in that same plan and member in that Household.
2. For each demand-producing event, resolve the pinned immutable recipe/validated assembly data. The recipe's declared base servings and unit-normalized ingredient inputs must be positive and source-backed. Freeze the same formula as existing `scale_recipe(detail, target_servings)` and per-base-serving nutrition: `event_target_servings = Σ Serving.portion_servings` for this event; `required_ingredient_quantity = RecipeIngredient.quantity × event_target_servings / RecipeVersion.base_servings`. All values are Decimal. Require positive base servings and ingredient quantities; validate each Serving references that event, the exact persisted plan revision, and an eligible member of the Household. Do not multiply by member count again.
3. Scale exact amounts with `Decimal` and versioned deterministic engine rules. Aggregate by `FoodIngredient` plus **compatible input form and base unit**. Same named ingredient with incompatible raw/cooked form or unresolved mass/volume/count conversion **must not** be merged. Do not silently use a density, yield, edible fraction or piece-weight without validated per-food provenance.
4. Use exact `Decimal` for recipe scaling, date-aware Pantry allocation and aggregation. **Frozen persisted precision:** `required_quantity` and `pantry_available_quantity` store three decimal places (`0.001`) for `g`, `ml` and `pcs`, matching Pantry's fixed precision. Round **once, after aggregation**: `required_quantity` upward with `ROUND_CEILING`, and the date-eligible quantity actually allocated from Pantry downward with `ROUND_FLOOR`, both to `0.001`. Store exact Decimal strings/decimal types, never floats. Unknown required quantity never becomes zero through rounding. `percent` without an authorized denominator is not purchasable.
5. `required_quantity` is aggregate gross canonical purchase-equivalent need; `pantry_available_quantity` means **date-eligible stock actually allocated** against that need, never all on-hand quantity. Compute `shortfall = max(persisted_required_quantity - persisted_pantry_available_quantity, 0)`; round `purchase_quantity` upward with `ROUND_CEILING` to `0.001` for `g`/`ml`, or upward to **whole pieces** for `pcs` (stored as three-place Decimal ending `.000`). Fractional `pcs` required/covered quantities remain representable at `0.001`, as in Pantry, but whole-piece purchasing can conservatively overbuy. The purchase amount is thus not necessarily an unrounded subtraction for `pcs`. Never subtract noncomparable raw/cooked or other forms. Price information is **independently UNKNOWN** in PR9 and is not a precondition for a complete quantity list.
6. Stable ordering is by canonical category/display name/code and immutable ID tie-break; exact input snapshot+engine version/config must produce semantically identical ordered items and warnings. UUIDs/timestamps are storage identities, **not** inputs to a semantic determinism fingerprint.

### Failure taxonomy (proposed)

- **BLOCKING / fail closed, no authoritative ShoppingList persisted:** missing or cross-household MealPlan, mixed plan revisions, invalid Serving references, missing required RecipeVersion, corrupt quantity/provenance, arithmetic overflow/negative demand, unsupported required conversion where producing a misleading number is unavoidable, source changed during persist.
- **INCOMPLETE grocery quantities:** unresolved grocery/supply obligations for `LEFTOVER`, `PREPARED`, `READY_MEAL`, or `ASSEMBLY_UNSUPPORTED`, or another explicitly supported unresolved obligation. Clearly identify each affected event. Never display such a list as fully shoppable.
- **COMPLETE grocery quantities:** every mandatory grocery ingredient quantity is calculated, and **no unresolved grocery/supply obligations remain**. `ORDER_OUT` and `EAT_OUT` do not create grocery demand. Known excluded Pantry quantities (expired, estimated or no confirmed expiry) simply increase the purchase amount with a warning; they do not prevent grocery quantity completeness.
- **Independent price dimension:** `price_status = UNKNOWN` for every PR9 V1 list, including `status = COMPLETE`. Unavailable pricing, cost and generic prices **never** set grocery status to `INCOMPLETE`. Do not present an unknown cost as zero. Price enrichment is a separately gated future feature.

The runtime implementation must test the boundary between `BLOCKING` and `INCOMPLETE` for each source kind and each conversion failure. The separate `ShoppingUnresolvedObligation` table defined in §5 is mandatory; no runtime choice between nullable items and split tables.

## 4. Pantry snapshot and subtraction

Shopping reads a coherent Household-scoped Pantry snapshot **without** writing `PantryItem`, `PantryMovement`, reserving stock or recording consumption. Pantry's current interface does not supply a logical `revision_number`; PR9 shall therefore use a **canonical Pantry snapshot fingerprint** as source identity unless a separately approved Pantry revision migration is justified.

Stable source fingerprint input, captured in one Shopping UoW together with the Household-local planning date and all applicable MealEvent dates:

- household_id;
- every relevant PantryItem: immutable identity, FoodIngredient ID, quantity, unit, location, `purchased_on`, `opened_on`, **`expires_on`**, estimated flag, and all other eligibility-relevant data;
- explicit snapshot version and eligibility policy version;
- deterministic serialization/sorting, e.g. UTF-8 canonical JSON of normalized values followed by SHA-256.

Do not hash nondeterministic row order or timestamps unrelated to availability. In particular, exclude only irrelevant metadata after proving it cannot affect the policy; a changed quantity or eligibility field **must** change the fingerprint. Item snapshot identity is not a reservation: two simultaneous Shopping runs can read the same stock; neither can decrement it.

**Frozen PR9 V1 date-aware Pantry subtraction (no reliance on repository FEFO naming as proof of usability):**

1. Capture one UTC clock instant and derive the Household-local `as_of_date` from the accepted IANA timezone. Each `HouseholdMealEvent.local_date` is the **required-use date** of its recipe ingredients (conservatively assuming usability through the meal date, without inventing earlier prep). For eligibility evaluate `required_date = max(as_of_date, event.local_date)`; an already-past meal must not be treated as evidence of past available stock.
2. The actual Pantry field is **`expires_on: date | None`**. A lot is usable for a specific event **only when** `expires_on >= required_date`, inclusive of the expiration calendar date. Lots expired at generation (`expires_on < as_of_date`) cannot cover any event. A lot that expires tomorrow **cannot** reduce purchases for a recipe next week.
3. Exclude `estimated=true` lots from subtraction, regardless of dates. Under the conservative V1 policy also exclude `expires_on=None` lots, because their future (or same-day) fitness cannot be established from accepted Pantry facts alone; expose an `EXPIRY_UNKNOWN` inventory warning rather than inventing a storage life. These exclusions do **not** create unresolved recipe demand; a list can remain `COMPLETE` with a larger purchase amount.
4. All locations `PANTRY`, `FRIDGE`, `FREEZER` are eligible only after the same confirmed quantity, expiry, canonical FoodIngredient, form and unit checks. Freezer location does not magically extend expiry or transform raw to cooked. Exclude zero/nonpositive lots. The existing `list_available_for_ingredient_fefo()` does **not** filter expired/estimated goods: Shopping must apply its own filters.
5. For each FoodIngredient/form/unit group, derive exact unrounded recipe needs per event. Process events sorted `(local_date, position, event UUID)`. For each event, allocate **only** from remaining lots satisfying that event's `required_date`, in FEFO order `(expires_on, location code, PantryItem UUID)`. Allocate `min(remaining_lot_quantity, unfilled_event_demand)` and decrease only an **in-memory** lot balance. A lot used for an early event cannot be reused for a later event. No PantryMovement, mutation, reservation or assumed physical consumption occurs.
6. Sum exact required and allocated amounts across dated events; **only then** apply §3 rounding. Persist `pantry_available_quantity` as the actual allocated coverage (rounded down), not all positive inventory. Keep deterministic event/lot allocation evidence with the immutable source snapshot metadata (no extra table). `purchase_quantity` is the nonnegative, upward-rounded residual.
7. Fingerprint the complete relevant Household Pantry snapshot (including excluded/estimated/no-expiry items), `as_of_date`, eligibility policy version and dated MealPlan input references. Different meal dates, expiry rollover or changed Pantry facts must invalidate outdated lists. A GET-current check must use the **current** Household-local date, not silently replay an obsolete earlier `as_of_date`.

**Required counterexample:** On 2026-10-09 a confirmed rice lot with `expires_on=2026-10-10` may cover an October 9 meal, but **not** an October 15 meal. The October 15 need remains in the purchase quantity even if the same lot appears in Pantry. The boundary is inclusive on October 10. An estimated or no-expiry rice lot is not deducted from either date.

**Frozen SQLite consistency contract:** one Shopping Unit of Work, one SQLite connection, explicit `BEGIN IMMEDIATE` before any authoritative source read (not a deferred read followed by an upgrade). Under the acquired writer reservation: load the exact MealPlan revision and its Servings, immutable recipe inputs and FoodIngredient truth, and the full Pantry snapshot; compute fingerprint and deterministic Shopping output; insert header, canonical items and unresolved obligations; verify all source identity/version pins while still holding that reservation; then commit once. Competing SQLite writers of MealPlan/Pantry/catalogue state cannot commit between the snapshot read and Shopping commit. A busy/locked timeout returns a structured retryable conflict; any exception rolls back the whole Shopping write. **No partial list becomes authoritative.** SQLite WAL/read snapshot semantics and busy timeout must be validated by executable concurrent-writer tests. The combined adapter must use the accepted project UoW contracts and must not let application/domain import SQLAlchemy. Do not open separate independently committed read scopes. When PostgreSQL arrives, define equivalent transaction locking/isolation in a separate approved shared-deployment contract.

## 5. Derived-state lifecycle and persistence proposal

**Decision: three separate persisted entities**: `ShoppingList` (immutable header), `ShoppingListItem` (only resolved canonical FoodIngredient demand), `ShoppingUnresolvedObligation` (event-level non-grocery or unverified obligations). Do not use a nullable FoodIngredient tagged union. This is the fixed PR9 V1 schema boundary.

- `ShoppingList` header: UUIDv4 `id`, `household_id`, `meal_plan_id`, `source_plan_revision_number`, `source_pantry_snapshot_hash` (snapshot schema/policy version and captured Household-local as-of date), `engine_version`, `config_fingerprint`, grocery quantity `status` (`COMPLETE` or `INCOMPLETE`), separate `price_status` (**only `UNKNOWN` for PR9 V1**), `content_fingerprint`, UTC `created_at`; optional `supersedes_list_id`. `status` measures quantity/obligation resolution, not price availability.
- `ShoppingListItem`: UUIDv4 `id`, `shopping_list_id` FK, **non-null** `food_ingredient_id` FK, non-null normalized input form/basis and unit, Decimal `required_quantity`, `pantry_available_quantity`, `purchase_quantity` (each nonnegative, persisted at **0.001** for `g`/`ml`/`pcs`; round-up required, round-down allocated Pantry, upward whole-piece purchases for `pcs`), deterministic `ordinal`, optional structured warnings. `UNIQUE(shopping_list_id,food_ingredient_id,form,basis,unit)` and `UNIQUE(shopping_list_id,ordinal)`. A required unresolved numeric ingredient conversion is BLOCKING rather than a fabricated amount.
- `ShoppingUnresolvedObligation`: UUIDv4 `id`, `shopping_list_id` FK, `meal_event_id` source reference, enumerated accepted `source_kind`, enum reason (`ASSEMBLY_UNSUPPORTED`, `LEFTOVER_SUPPLY_UNVERIFIED`, `PREPARED_SUPPLY_UNVERIFIED`, `READY_MEAL_UNRESOLVED`), optional safe Russian description/source reference, stable `ordinal`; quantity/price **absent**, not zero. Unique `(shopping_list_id,meal_event_id,reason)`. `ORDER_OUT`/`EAT_OUT` are documented non-grocery events and do not generate unresolved *shopping* obligations absent a separately accepted purchase requirement.
- Persist per-input provenance/pins or a canonicalized source snapshot descriptor sufficient to audit the derivation without depending on mutable recipe catalogue labels.
- Database constraints: household scope at both read and write, list/item FK, uniqueness of stable item key/ordinal per list, quantity `>=0` when known, valid enum/status/unit and revision positivity; indexes for `(household_id,meal_plan_id,created_at)`, current-week lookup and list items. Do not store a mutable `is_current` flag as sole staleness truth.

A generation creates an **immutable list snapshot** with all its items in one UoW; regeneration on changed source creates a successor, preserving prior history. A retry against the exact same input versions/config may return the existing matching snapshot (idempotent) rather than duplicating it. A `GET current` rechecks source MealPlan revision and Pantry fingerprint, re-evaluating the Household-local `as_of_date` and dated expiration policy; if different, returns `STALE` and does not claim the old list is current. Never mutate the old item's calculated quantities to match new inputs.

Do **not** assume an unrelated `MealPlan.id` automatically pins the latest `revision_number`; confirm existing revision ID/history semantics and store sufficient identity to distinguish revisions. Unknown field exactness and migration constraints are part of final contract review, not assumptions of the existing database.

### Migration boundary

- Runtime may append `0043_shopping_engine` **only if migration registry still ends at 0042 at implementation start**. Reconcile reserved 0033 without backfilling it, and check concurrent branches before claiming the number.
- New tables coexist with legacy tables; no rewrite of old meal/pantry/recipe data. No release-breaking destructive alteration. Fresh and upgrade chain, lineage, backup/export and foreign-key/integrity tests are mandatory.
- Docs-only PR9-ARCH creates **no migration and no runtime table**. The three-table schema and consistency contract above are frozen for V1; if runtime discovers a required new Pantry revision or cross-context schema dependency, return to independent contract review.

## 6. Service, repository, UoW and API boundary

Proposed pure `ShoppingEngine` computes `ShoppingCalculation` from version-pinned ingredient demands and availability snapshot; it performs **no database I/O**. `ShoppingApplicationService` is responsible for loading an atomic snapshot, invoking the engine, persisting all-or-nothing output, and verifying freshness. `ShoppingListRepository` supports `add_detail`, `get_detail(household_id,list_id)`, `get_latest_for_plan(household_id,plan_id)`, `list_history(household_id,plan_id)`. Exact read contracts may be refined to match current MealPlan revision identity. `ShoppingUnitOfWork` composes read-only MealPlan/Recipe/FoodIngredient/Pantry repositories and Shopping writes under existing project UoW; domain/application has no SQLAlchemy dependency.

Minimum proposed backend API capability, matching existing household-scoped route conventions where possible:

- `POST /api/households/{household_id}/meal-plans/{plan_id}/shopping-lists` — generate from authoritative revision and return list/status/warnings; accept no client-supplied quantity authority.
- `GET /api/households/{household_id}/shopping-lists/{list_id}` — read snapshot and computed stale/current status, including source references.
- `GET /api/households/{household_id}/meal-plans/{plan_id}/shopping-lists/current` — discover most recent nonstale snapshot, or explicit stale/missing state.
- `POST .../shopping-lists/regenerate` — explicit recalculation when stale; separate from purchase confirmation.

These routes are *capabilities*, not a mandate to add four controllers if existing router style supports fewer safe endpoints. Missing/cross-household resources return non-disclosing errors; valid conflicts return structured 409 or documented equivalent; unresolved demand is machine-readable and explained in Russian. Auth is not yet present, so Household ID scoping must be enforced in every repository operation; household_id alone does **not** become an authorization scheme for later shared deployment. Do not expose internal codes to consumer users.

## 7. Adversarial acceptance and evidence matrix for runtime PR

**Domain:** deterministic replay and stable ordering; exact multi-member serving factors and aggregation; compatible FoodIngredient identity/form/unit; invalid count↔mass, mass↔volume, raw↔cooked or unknown yield; no floats; 0.001 three-place Decimal persistence, upward required quantity, downward allocated Pantry quantity and upward whole-piece purchasing; rounding boundary/no underbuy/overflow/0-floor; invalid percentage without denominator; full source-kind matrix, ASSEMBLY unresolved V1, no leftover double-charge. Assert a grocery `COMPLETE` list with `price_status=UNKNOWN` and a genuinely unresolved grocery `INCOMPLETE` list with the same price status.

**Pantry:** multiple lots and locations, FEFO applied to **chronological MealEvent.local_date** requirements; same-day inclusive `expires_on` boundary; a lot expiring between generation and a late-week event is excluded for the late event but can cover an earlier event; estimated and null-expiry excluded with warnings; no double use of a lot, expiry rollover/fingerprint invalidation, incompatible form/units, overstock, stock conflict and deterministic serialization. Assert **no PantryMovement or item mutation** on success, conflict or error.

**Persistence/UoW:** new list/header/items atomic; rollback on item 3 failure; stale plan revision and changed Pantry fingerprint rejected before commit; concurrent re-generation semantics; duplicate identical request; same-household history; deny cross-household plan and list reads/writes including guessed UUID; no partially authoritative list on injection; immutable old snapshot; clean fresh and upgrade migration lineage with FK checks and realistic backup/export test.

**API:** Russian-safe messages; idempotent retry; malformed IDs/amounts; missing plan and stale 409; mixed-source `INCOMPLETE`; fully computable grocery `COMPLETE` even when price_status=`UNKNOWN`; version/provenance and `AI_ENABLED=false` / no Retail support.

**Gate 2 integration:** actual accepted 3-member fixture → Planner complete 7-day plan → individualized Servings → Shopping aggregate → subtract real Pantry snapshot; independently verify expected purchase quantities and unchanged Pantry. Prep/PDF remain future stages; do not claim Gate 2 completion from Shopping-only tests.

**Verification tier:** doc-only PR runs links/scope/whitespace/contract self-checks. Subsequent runtime PR runs focused domain/application/API and persistence/migration tests, negative failure-injection, and full backend **plus launcher** regression at its exact frozen runtime head where shared persistence/startup compatibility can be affected (per `verification-policy.md`). Report tests *actually executed*, not projected.

## 8. Risks, explicit decisions and open questions

**FACT:** Gate1 is complete; Shopping core does not exist yet; the existing Pantry interface has no aggregate revision; mixed source-kind semantics are not uniformly ingredient-demand semantics; migration head is 0042.

**DECISION proposed for approval:** use generic `FoodIngredient` items only; immutable revisioned Shopping snapshots; Pantry read-only fingerprint; complete-versus-incomplete distinction; source-kind gating; fail-closed numerical authority; no Retail/AI/Prep coupling. PR9-ARCH by itself has **no implementation authority** until reviewed/merged.

**Frozen resolutions:** exact serving scaling, grocery-vs-price status and Decimal persistence rules (§3/§5); date-aware Pantry `expires_on` FEFO allocation, snapshot/fingerprint (§4); separate unresolved table (§5); SQLite `BEGIN IMMEDIATE` single UoW (§4); `ASSEMBLY` unresolved in V1 (§2). These are binding runtime acceptance criteria, not further architecture choices.

**Remaining implementation checks (non-architectural):** map accepted RecipeVersion and FoodIngredient read adapters to the already fixed formula; determine the exact SQLite UoW extension point for explicit `BEGIN IMMEDIATE` and prove it with concurrent tests; confirm the plan ID + `revision_number` storage pairing and schema field types; reconcile migration registry against `main` before allocating 0043. If any requires changing an above invariant, **stop and amend this gate under independent review**.

**Stop rule:** deliver one docs-only PR for independent review, with current-focus/progress/handoff synchronized. No schema, runtime, seed, AI, Retail, Pantry mutation, Prep, PDF or PWA changes. After merge, open a separately scoped PR9 runtime task; no autonomous merge.
