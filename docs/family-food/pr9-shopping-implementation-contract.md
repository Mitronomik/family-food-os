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

The following are proposed cross-context contracts, **not claims of existing code**: combined read-scope/UoW, Shopping persistence tables, snapshot hashing, Shopping API, demand resolver and runtime migration. During PR9 runtime preflight verify concrete RecipeVersion/Assembly ingredient read methods, FoodIngredient edible/raw-form normalization semantics, current plan event lookup, and Pantry expiration policy. If a proposed contract conflicts with an accepted physical model, return to contract review, not a silent workaround.

## 2. Source-kind demand decision table

| Current source kind | Direct new purchase demand in PR9 | Contract |
| --- | --- | --- |
| `COOK_RECIPE` | **YES** where exact immutable RecipeVersion ingredient input and participating Servings can be resolved | Sum event's positive Serving `portion_servings`; resolve ingredient inputs and normalize as specified below. Invalid/missing pins fail closed. |
| `ASSEMBLY` | **CONDITIONAL** | Only if an accepted, source-pinned validated RecipeAssembly materializes exact per-ingredient input, yield/scale and source reference. Do not treat `source_reference` as an arbitrary recipe id; missing authority produces explicit unresolved status. |
| `LEFTOVER` | **NO automatically** | It represents already obtained food, not another fresh recipe. An accepted future remaining-serving/prepared-stock reservation contract is needed for supply validation. No duplicate ingredient demand. |
| `PREPARED` | **NO automatically** | It refers to pre-existing prepared supply. No second ingredient charge; if supply is not verified, expose unresolved supply rather than asserting it is available. |
| `READY_MEAL` | **NO canonical recipe ingredients by default** | Purchased ready-food demand belongs to a separately defined purchasable-item/retail-independent supply model; keep visible as unresolved purchase/supply when no trustworthy representation exists. Do not suppress it as fulfilled or invent ingredient decomposition. |
| `ORDER_OUT` | **NO** | Eating/order-out is not grocery ingredient demand. Any known spending is independent from grocery quantity and remains unknown in PR9 without authority. |
| `EAT_OUT` | **NO** | Not a household grocery requirement. |

A complete ShoppingList must distinguish **covered recipe grocery demand** from **unresolved obligations**. It must never silently classify unknown supply as zero requirement or silently declare the whole week shoppable. Mixed-source weeks may still yield a **partial** reviewable list with explicit `INCOMPLETE` status; whether to disallow a persisted partially resolved list for a particular case is determined by the fail-closed classification below. No inferred nutritional, cost, storage, source-kind or substitute authority.

## 3. Quantity calculation and normalization

1. Read one authoritative MealPlan **revision** and its events/Servings, not a stitched mixture of current and historical versions. Every Serving must reference an event in that same plan and member in that Household.
2. For each demand-producing event, resolve the pinned immutable recipe/validated assembly data. The recipe's declared base servings and unit-normalized ingredient inputs must be positive and source-backed. The event factor is **sum of participating members' `portion_servings`**, interpreted using the accepted Recipe/MealPlan serving convention; do not multiply by household size again. Confirm this convention against current RecipeScaling and Serving tests before runtime coding.
3. Scale exact amounts with `Decimal` and versioned deterministic engine rules. Aggregate by `FoodIngredient` plus **compatible input form and base unit**. Same named ingredient with incompatible raw/cooked form or unresolved mass/volume/count conversion **must not** be merged. Do not silently use a density, yield, edible fraction or piece-weight without validated per-food provenance.
4. Display and persist required input quantities with explicit precision/rounding policy. Intermediate arithmetic remains exact within Decimal precision; round **once** at the documented output boundary, upward where necessary to avoid understating purchase demand, not per event before aggregate. Unknown required quantity remains unknown. `percent` without an accepted mass denominator is not a purchasable unit.
5. `required_quantity` represents **gross canonical purchase-equivalent need after any authorized form/edible-fraction conversion**; `pantry_available_quantity` is compatible, valid, non-reserved on-hand quantity; `purchase_quantity = max(required_quantity - pantry_available_quantity, 0)`. Do not subtract pantry from a noncomparable edible/raw demand. Missing generic price must remain UNKNOWN; pricing, SKU/package selection and retailer availability are not PR9 prerequisites.
6. Stable ordering is by canonical category/display name/code and immutable ID tie-break; exact input snapshot+engine version/config must produce semantically identical ordered items and warnings. UUIDs/timestamps are storage identities, **not** inputs to a semantic determinism fingerprint.

### Failure taxonomy (proposed)

- **BLOCKING / fail closed, no authoritative ShoppingList persisted:** missing or cross-household MealPlan, mixed plan revisions, invalid Serving references, missing required RecipeVersion, corrupt quantity/provenance, arithmetic overflow/negative demand, unsupported required conversion where producing a misleading number is unavoidable, source changed during persist.
- **INCOMPLETE with explicit unresolved rows/warnings:** non-cooking sources needing independently confirmed supply (`LEFTOVER`, `PREPARED`, `READY_MEAL`), unverified conditional `ASSEMBLY`, safe omission of a *not computable* subset while correctly identifying affected event, and unknown price. Incompleteness must never be shown as a complete grocery order.
- **Normal:** well-formed recipe events and zero demand for out-of-home events. Budget/cost totals are UNKNOWN unless every included price has accepted authority; do not display a fabricated zero-cost week.

The runtime implementation must test the boundary between `BLOCKING` and `INCOMPLETE` for each source kind and each conversion failure. If representing unresolved rows requires another schema concept, settle it in this contract before a runtime PR.

## 4. Pantry snapshot and subtraction

Shopping reads a coherent Household-scoped Pantry snapshot **without** writing `PantryItem`, `PantryMovement`, reserving stock or recording consumption. Pantry's current interface does not supply a logical `revision_number`; PR9 shall therefore use a **canonical Pantry snapshot fingerprint** as source identity unless a separately approved Pantry revision migration is justified.

Proposed stable fingerprint input, captured in one transaction/read-consistent boundary:

- household_id;
- every relevant pantry item: immutable item identity, ingredient ID, exact Decimal quantity, unit, location, expiry/opened/estimated/status facts that determine availability;
- explicit snapshot version and eligibility policy version;
- deterministic serialization/sorting, e.g. UTF-8 canonical JSON of normalized values followed by SHA-256.

Do not hash nondeterministic row order or timestamps unrelated to availability. In particular, exclude only irrelevant metadata after proving it cannot affect the policy; a changed quantity or eligibility field **must** change the fingerprint. Item snapshot identity is not a reservation: two simultaneous Shopping runs can read the same stock; neither can decrement it.

Define availability policy before shipping: expired vs future-expiring goods, estimated inventory, multiple locations, and incompatible units/forms. Prefer conservative subtraction: verified compatible positive amounts only, capped at required amount, using deterministic FEFO for explanation; an estimated/unverified amount must be flagged and not treated as guaranteed purchased coverage. Distinguish Pantry `quantity` from genuinely usable stock in all responses. A Pantry location alone does not prove an ingredient in a certain prepared form.

At generation commit, prevent time-of-check/time-of-use mismatch: reread/validate the plan revision and Pantry fingerprint under the transaction strategy supported by the current SQLite UoW. If inputs differ, rollback the entire derived write and return a conflict/retryable stale-input response. Specify SQLite read/write locking behavior in the runtime implementation; an application-only before/after hash with a write window is insufficient. Any persisted list must declare exactly which snapshot produced it.

## 5. Derived-state lifecycle and persistence proposal

New proposed Household-owned aggregates: `ShoppingList` and `ShoppingListItem` (use one canonical name; avoid duplicate `ShoppingItem` synonym). Proposed header:

- UUIDv4 `id`, `household_id`, `meal_plan_id`, `source_plan_revision_number`, `source_pantry_snapshot_hash` (and snapshot schema/policy version), `engine_version`, `config_fingerprint`, `status` (`COMPLETE` or `INCOMPLETE`), `content_fingerprint`, UTC `created_at`; optional `supersedes_list_id` for successor provenance.
- An authoritative `ShoppingListItem` stores `shopping_list_id`, canonical `food_ingredient_id` (nullable **only for explicitly unresolved noncatalogue obligations**), ingredient form/basis and unit, exact required/available/purchase quantities **or structured unknown**, Russian display-safe warning metadata and deterministic ordinal. A companion unresolved-obligation representation may be required to avoid overloading an ingredient row; decide exact normalized schema in the contract review, prior to runtime.
- Persist per-input provenance/pins or a canonicalized source snapshot descriptor sufficient to audit the derivation without depending on mutable recipe catalogue labels.
- Database constraints: household scope at both read and write, list/item FK, uniqueness of stable item key/ordinal per list, quantity `>=0` when known, valid enum/status/unit and revision positivity; indexes for `(household_id,meal_plan_id,created_at)`, current-week lookup and list items. Do not store a mutable `is_current` flag as sole staleness truth.

A generation creates an **immutable list snapshot** with all its items in one UoW; regeneration on changed source creates a successor, preserving prior history. A retry against the exact same input versions/config may return the existing matching snapshot (idempotent) rather than duplicating it. A `GET current` rechecks source MealPlan revision and Pantry fingerprint; if different, returns `STALE` and does not claim the old list is current. Never mutate the old item's calculated quantities to match new inputs.

Do **not** assume an unrelated `MealPlan.id` automatically pins the latest `revision_number`; confirm existing revision ID/history semantics and store sufficient identity to distinguish revisions. Unknown field exactness and migration constraints are part of final contract review, not assumptions of the existing database.

### Proposed migration boundary

- Runtime may append `0043_shopping_engine` **only if migration registry still ends at 0042 at implementation start**. Reconcile reserved 0033 without backfilling it, and check concurrent branches before claiming the number.
- New tables coexist with legacy tables; no rewrite of old meal/pantry/recipe data. No release-breaking destructive alteration. Fresh and upgrade chain, lineage, backup/export and foreign-key/integrity tests are mandatory.
- Docs-only PR9-ARCH creates **no migration and no runtime table**. Schema specifics are a reviewable proposal; any new Pantry revision or cross-context schema dependency demands an explicit change to this contract and another review before runtime.

## 6. Service, repository, UoW and API boundary

Proposed pure `ShoppingEngine` computes `ShoppingCalculation` from version-pinned ingredient demands and availability snapshot; it performs **no database I/O**. `ShoppingApplicationService` is responsible for loading an atomic snapshot, invoking the engine, persisting all-or-nothing output, and verifying freshness. `ShoppingListRepository` supports `add_detail`, `get_detail(household_id,list_id)`, `get_latest_for_plan(household_id,plan_id)`, `list_history(household_id,plan_id)`. Exact read contracts may be refined to match current MealPlan revision identity. `ShoppingUnitOfWork` composes read-only MealPlan/Recipe/FoodIngredient/Pantry repositories and Shopping writes under existing project UoW; domain/application has no SQLAlchemy dependency.

Minimum proposed backend API capability, matching existing household-scoped route conventions where possible:

- `POST /api/households/{household_id}/meal-plans/{plan_id}/shopping-lists` — generate from authoritative revision and return list/status/warnings; accept no client-supplied quantity authority.
- `GET /api/households/{household_id}/shopping-lists/{list_id}` — read snapshot and computed stale/current status, including source references.
- `GET /api/households/{household_id}/meal-plans/{plan_id}/shopping-lists/current` — discover most recent nonstale snapshot, or explicit stale/missing state.
- `POST .../shopping-lists/regenerate` — explicit recalculation when stale; separate from purchase confirmation.

These routes are *capabilities*, not a mandate to add four controllers if existing router style supports fewer safe endpoints. Missing/cross-household resources return non-disclosing errors; valid conflicts return structured 409 or documented equivalent; unresolved demand is machine-readable and explained in Russian. Auth is not yet present, so Household ID scoping must be enforced in every repository operation; household_id alone does **not** become an authorization scheme for later shared deployment. Do not expose internal codes to consumer users.

## 7. Adversarial acceptance and evidence matrix for runtime PR

**Domain:** same pinned input/config deterministic; exact multi-member factors; duplicate ingredient collapse; cross-event aggregation; stable ordering; Decimal/no float; compatible canonical units; invalid count↔mass, mass↔volume, raw↔cooked and unknown yield; no under-rounding, overflow or negative purchase; 0-floor; percentage without denominator rejected; full source-kind matrix; assembly with and without validated authority; supplied leftovers never counted twice.

**Pantry:** two lots, FEFO, multiple locations, expiry boundary at household-local date, estimated stock, zero-balance item, incompatible unit/form, stock exceeding demand, stock mutation attempted during generation, concurrent stock adjustment, deterministic fingerprint through equivalent serialized snapshots. Assert **no PantryMovement, no quantity/metadata change** on success, conflict or error.

**Persistence/UoW:** new list/header/items atomic; rollback on item 3 failure; stale plan revision and changed Pantry fingerprint rejected before commit; concurrent re-generation semantics; duplicate identical request; same-household history; deny cross-household plan and list reads/writes including guessed UUID; no partially authoritative list on injection; immutable old snapshot; clean fresh and upgrade migration lineage with FK checks and realistic backup/export test.

**API:** Russian-safe messages; idempotent retry; malformed identifiers/quantity rejection; missing plan; stale 409; mixed-source `INCOMPLETE` clearly labeled; version/provenance metadata; independent `AI_ENABLED=false` and Retail unavailable path.

**Gate 2 integration:** actual accepted 3-member fixture → Planner complete 7-day plan → individualized Servings → Shopping aggregate → subtract real Pantry snapshot; independently verify expected purchase quantities and unchanged Pantry. Prep/PDF remain future stages; do not claim Gate 2 completion from Shopping-only tests.

**Verification tier:** doc-only PR runs links/scope/whitespace/contract self-checks. Subsequent runtime PR runs focused domain/application/API and persistence/migration tests, negative failure-injection, and full backend **plus launcher** regression at its exact frozen runtime head where shared persistence/startup compatibility can be affected (per `verification-policy.md`). Report tests *actually executed*, not projected.

## 8. Risks, explicit decisions and open questions

**FACT:** Gate1 is complete; Shopping core does not exist yet; the existing Pantry interface has no aggregate revision; mixed source-kind semantics are not uniformly ingredient-demand semantics; migration head is 0042.

**DECISION proposed for approval:** use generic `FoodIngredient` items only; immutable revisioned Shopping snapshots; Pantry read-only fingerprint; complete-versus-incomplete distinction; source-kind gating; fail-closed numerical authority; no Retail/AI/Prep coupling. PR9-ARCH by itself has **no implementation authority** until reviewed/merged.

**OPEN QUESTION — must close before runtime:**
1. Which current RecipeVersion/RecipeAssembly persisted read adapter provides an exact input-grams/servings snapshot without introducing a new version authority? Which `ASSEMBLY` modes are actually producible?
2. Can the accepted SQLite UoW provide read-consistent cross-context snapshots and a safe fingerprint recheck under concurrent writes without a new abstraction? Identify exact locking strategy and failure path.
3. Are Pantry metadata, expiration and estimated stock policies sufficient to subtract safely, and how are canonical food form conversions validated? Incomplete evidence must not become an estimated quantity silently.
4. Is a distinct unresolved-obligation table preferable to nullable ingredient rows for READY_MEAL/PREPARED/LEFTOVER, and what is the precise persisted structure?
5. What are the exact existing RecipeScaling/Serving portion units and plan revision lookup semantics at runtime head? Revalidate before final schema/API freeze.

**Stop rule:** deliver one docs-only PR for independent review, with current-focus/progress/handoff synchronized. No schema, runtime, seed, AI, Retail, Pantry mutation, Prep, PDF or PWA changes. After merge, open a separately scoped PR9 runtime task; no autonomous merge.
