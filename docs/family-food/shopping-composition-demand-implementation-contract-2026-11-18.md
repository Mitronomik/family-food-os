# Shopping component-aware demand — Implementation Contract Gate

**Status:** PROPOSED — docs-only; independent review and owner merge required before runtime.
**Decision date:** 2026-11-18.
**Accepted base:** `main@44adc9bf5cc0013c42d05a43fa1f3ed916f4d47e` (PR #292 merged 2026-11-18).
**Scope owner:** Shopping Engine. This document **does not** implement calculation, release or a new schema.
**Read with:** [root AGENTS](../../AGENTS.md), [Shopping V1 contract](pr9-shopping-implementation-contract.md), [MealPlan 0044 contract](mealplan-multicourse-persistence-implementation-contract-2026-11-16.md), [architecture](architecture.md), [roadmap](master-roadmap.md), and [current focus](../../state/current-focus.md).

## 1. Goal, accepted facts, and the gap

**Goal:** make one source-pinned, complete seven-day `MealPlanDetail` containing `COOK_COMPOSITION` yield deterministic per-ingredient grocery demand with correctly scaled member-component servings, no duplicate demand, independently verifiable provenance, date-aware Pantry allocation, immutable Shopping snapshots and explicit capability gating. The first runtime proof is **internal diagnostic only**. It grants no consumer-ready meal or physical-portion approval.

**FACT (accepted `main`):**
- PR #292 added immutable `COOK_COMPOSITION` events with **null parent** RecipeVersion and **no legacy event Serving**; every composed event has an immutable full rule snapshot, ordered components and exact member-component Decimal Servings. `get_detail` replays the complete week and rejects corrupted/missing slots; the writer remains synthetic/internal.
- Shopping V1 uses `calculate_shopping`, `ShoppingService`, a shared `SqlAlchemyShoppingUnitOfWork` with physical `BEGIN IMMEDIATE`, and immutable `shopping_lists`, `shopping_list_items`, `shopping_unresolved_obligations` under migration `0043`.
- Existing `shopping-v1a` requires event-level `Serving`, resolves `COOK_RECIPE` through `RecipeVersionDetail`, aggregates by compatible FoodIngredient/unit, applies dated FEFO against a **read-only Pantry snapshot**, rounds once at the end and stores source/content fingerprints.
- `0043` unresolved-obligation source-kind CHECK does **not** include `COOK_COMPOSITION`. Therefore silently converting a composed event into an unresolved obligation would change the persisted contract and cannot be an undocumented fallback.
- MealPlan #291/#292 explicitly leaves Shopping and production activation for a separate reviewed PR. Historical Shopping results and frozen Planner/MealPlan evidence must remain independently readable.

**FACT — current failure:** `ShoppingService._calculate` loads recipe facts only for `COOK_RECIPE`, while `calculate_shopping` checks `serving_map[event.id]` before handling source kinds. A composed parent has neither a parent recipe nor event-level Servings; today's correct behavior is fail-closed.

## 2. Option evaluation and proposed boundary

| Option | Result | Disposition |
| --- | --- | --- |
| A. Fabricate one parent `COOK_RECIPE` or legacy Serving from the components | False nutrition/source identity; lost courses; possible duplicate shopping quantities | **REJECT** |
| B. Mark `COOK_COMPOSITION` as a generic unresolved/partially shoppable legacy event | `0043` CHECK does not support it; hides known component demand or stores misleading partial lists | **REJECT** |
| C. Unconditionally change V1 calculation/hash for all plans | May invalidate accepted historical source fingerprints and Shopping current/idempotency behavior | **REJECT** |
| D. Preserve V1a byte/semantic behavior for legacy-only plans; introduce a separately versioned deterministic composition-capable Shopping calculation under an **internal diagnostic admission gate**, reusing immutable V1 schema only if parity is proven | Enables meaningful new proof while protecting frozen history and consumer rollout | **RECOMMENDED — subject to review** |

**PROPOSED DECISION:** version the new calculation as `shopping-v1b-composition` (label subject to review); keep `shopping-v1a` for every legacy-only plan. Do not create a migration, API route or editable sidecar merely to support diagnostic component demand. If the exact existing schema cannot preserve required provenance and fail-closed semantics, **stop for a reviewed docs-only amendment before any runtime code**.

## 3. Source/quantity algorithm — deterministic, no invented authority

1. The Shopping UoW loads one current, Household-scoped complete `MealPlanDetail` and its accepted immutable source recipe versions, canonical FoodIngredients, Pantry snapshot and Household timezone under the **same physical `BEGIN IMMEDIATE`**. Do not reopen an independently committed reader between these steps.
2. Legacy `COOK_RECIPE` events continue using **only their event-level `Serving`** and the accepted `shopping-v1a` formula; never manufacture component rows for them.
3. For every `COOK_COMPOSITION`, require exactly one restored immutable rule snapshot; matching event ID, role and source kind; contiguous ordered components; each source-pinned `RecipeVersion` and the exact member-component allocation. The parent `recipe_version_id` remains NULL; the parent has zero legacy Servings. A missing course/participant, orphan or mismatched serving, invalid rule digest or incomplete week is **BLOCKING**.
4. For each component `c`, calculate `target_base_servings(c) = Σ(member_component_serving.portion_servings)` for that **component only**. Each ingredient input `i` contributes `input_quantity(i) × target_base_servings(c) / recipe_version.base_servings` using positive finite `Decimal` and accepted immutable input units. **Do not multiply** by attending member count or use the old target event's Serving factor.
5. Multiple components using the same RecipeVersion represent distinct explicitly stored courses and each contributes once. Repeating the same ingredient in FIRST, SECOND, DESSERT (or in a legacy event elsewhere in the week) must **add**, not overwrite or deduct one course from another. Within each `(event_id, FoodIngredient, compatible form/basis, unit)`, sum exact component demand **before** the dated FEFO allocator. Prevent any intermediate per-component rounding.
6. Preserve `shopping-v1a` FoodIngredient authority: the ingredient must be active, its version verified and rights-reviewed, quantities/base servings positive, no unknown `optional` ingredient choice, and its input unit compatible with canonical default. Do not infer densities, yield, piece weight, raw↔cooked interchangeability, or resolve an unapproved physical meal fraction. If ingredient form cannot truthfully use `CANONICAL_FOOD_ID`, **BLOCK** rather than merge unlike forms.
7. Use the accepted dated `PantryPolicy v1`: process event needs by `(local_date, event.position, event.id)`; allocate from eligible lots once in FEFO order using per-lot **in-memory** balances, with `required_date=max(as_of_date,event.local_date)`. Estimated, expired, null-expiry and incompatible lots remain excluded/warned. Components of the same event share one dated demand; do not double-allocate its Pantry lots.
8. Round only after total aggregation: requirements up to `0.001`, actual allocated stock down to `0.001`, purchase amounts up to `0.001` (whole pieces for `pcs`). All existing `MAX_QUANTITY` and `ShoppingCalculationError` overflow/NaN/negative boundaries remain enforced.
9. Component ingredient quantities are **grocery need**, not proof that a dish has safe physical cooked mass, approved role suitability, nutrition completeness, actual stock or a purchasable retail SKU. No inference fills untracked out-of-home opportunities.

### 3.1 Provenance and versioned fingerprints

- Legacy-only paths use their **unchanged `shopping-v1a` serializer, engine label, source/content fingerprints and persisted results**. Prove this by comparing golden source/quantity/metadata outputs at the same pinned input and clock, not merely totals.
- New composition-capable fingerprints include: plan ID/revision/week/config; all event IDs/roles/local dates/positions/source kinds; pinned member selection mapping; the **full canonical rule identity, schema version, ordered requirements and stored SHA**; for each component its UUID, event, position, course kind and source RecipeVersion ID; every `(component_id,member_id,exact Decimal factor)`; source RecipeVersion identity/version/source-document SHA and actual ingredient IDs/quantities/units; FoodIngredient identity/form/unit and eligibility/order metadata; Household timezone; accepted Pantry snapshot hash/as-of/eligibility policy; engine version. Canonical ordering is explicit, independent of unordered SQL iteration or process hash seed.
- Persist an audit-friendly **per-component input/scale contribution ledger** in versioned `provenance_json`, while `shopping_list_items` remain one canonical aggregate row per compatible ingredient key and `ShoppingLotAllocation` stays event-level. Check the JSON is sufficient to reconstruct every contribution, including components that share the same ingredient, without inventing a component-level SQL relation. If it is insufficient, reopen the schema gate.
- Source fingerprint MUST change if a component, its order/course, recipe source pin, exact member factor, rule snapshot, whole plan revision, Pantry input, applicable date or engine version changes. It must be identical across new independent processes for exactly identical inputs. A changed output under an unchanged source fingerprint is a persistence conflict, not an overwrite.
- Recalculation preserves Shopping V1's immutable history, same-source idempotent reuse, explicit stale/current results and same-UoW commit. A composed revision must never inherit a legacy ShoppingList or imply the legacy list is current.

### 3.2 Normative minimum `provenance_json` V2 contract (P2)

**DECISION proposed for review:** only composition-capable diagnostic snapshots use `schema="SHOPPING_SOURCE_SNAPSHOT_V2_COMPOSITION"` **together with** header `engine_version="shopping-v1b-composition"`. Both identifiers MUST agree with `provenance.calculation.engine`; one is not a fallback for a missing/invalid other. Legacy-only lists retain the exact existing `schema="SHOPPING_SOURCE_SNAPSHOT_V1"` + `engine_version="shopping-v1a"` pair and their existing payload bytes/serialization behavior. No existing V1 JSON, hash or persisted row is migrated, reclassified, or retroactively required to include V2 fields. An unknown/mismatched pair or malformed V2 is fail-closed and **never** interpreted as V1.

The following is the **minimum required V2 logical JSON shape**, not an example with fabricated source identities. Bracketed descriptions indicate types; the runtime must replace them with real validated source facts, **not** persist placeholders. Every field is mandatory, including empty collections for absent source types:

```text
{
  "schema": "SHOPPING_SOURCE_SNAPSHOT_V2_COMPOSITION",
  "calculation": {
    "household_id": UUID, "plan_id": UUID, "plan_revision": integer,
    "week_start": date, "config_version": string, "as_of_date": date,
    "engine": "shopping-v1b-composition", "policy": policy_version,
    "pantry_hash": sha256, "source_hash": sha256, "content_hash": sha256,
    "config_fingerprint": sha256, "timezone": IANA_timezone
  },
  "plan_events": [complete ordered immutable event facts],
  "member_selection_pins": [{ "member_id": UUID, "selection_id": UUID }],
  "servings": [complete legacy-only event/member/Decimal Serving facts],
  "compositions": [{
    "meal_event_id": UUID,
    "rule": {
      "schema_version": 1, "code": string, "version": integer,
      "meal_role": role, "coverage": "EVENT|PER_PARTICIPANT",
      "requirements": [
        {"kind": course, "minimum": integer, "maximum": integer}
      ],
      "sha256": sha256
    },
    "components": [{
      "component_id": UUID, "position": positive_integer,
      "course_kind": course, "recipe_version_id": UUID,
      "member_servings": [{
        "member_id": UUID, "portion_servings": exact_decimal_string
      }]
    }]
  }],
  "recipe_inputs": [{
    "recipe_version_id": UUID, "recipe_version_number": integer,
    "source_document_sha256": sha256, "source_version": string_or_null,
    "verification_status": code, "rights_review_status": code,
    "recipe_is_active": boolean, "base_servings": exact_decimal_string,
    "ingredients": [{
      "recipe_ingredient_id": UUID, "food_ingredient_id": UUID,
      "quantity": exact_decimal_string, "unit": unit, "optional": boolean
    }]
  }],
  "foods": [complete canonical ingredient/form/unit/eligibility/order facts],
  "pantry_items": [complete lot identity, quantity, form, dates and FEFO facts],
  "component_contributions": [{
    "meal_event_id": UUID, "local_date": date, "event_position": integer,
    "component_id": UUID, "component_position": integer,
    "course_kind": course, "recipe_version_id": UUID,
    "recipe_ingredient_id": UUID, "food_ingredient_id": UUID,
    "form_basis": string, "unit": unit,
    "base_servings": exact_decimal_string,
    "member_servings": [{"member_id": UUID, "portion_servings": exact_decimal_string}],
    "total_component_servings": exact_decimal_string,
    "input_quantity": exact_decimal_string,
    "scale_factor": unrounded_decimal_string,
    "contribution_numerator": exact_decimal_string,
    "contribution_denominator": exact_decimal_string,
    "unrounded_contribution": unrounded_decimal_string
  }],
  "event_demands": [{
    "meal_event_id": UUID, "local_date": date, "event_position": integer,
    "food_ingredient_id": UUID, "form_basis": string, "unit": unit,
    "unrounded_required": unrounded_decimal_string
  }],
  "items": [persisted canonical item identity and 0.001 quantities],
  "unresolved": [existing V1 accepted unresolved-obligation facts],
  "warnings": [existing V1 warning facts],
  "allocations": [existing V1 event-level Pantry FEFO allocation facts]
}
```

**Required identity and completeness rules:**
- `plan_events` covers the **whole** readback week (legacy plus composed), including local date, role, position, source kind and parent recipe/source-reference fields. `servings` contains only the actual legacy event-level Servings. `member_selection_pins` and `compositions` must reconcile with this exact MealPlan revision, not a current mutable catalogue lookup.
- Every `compositions[*].rule` includes the **full stored ordered requirement body**, immutable rule code/version/coverage, schema version and persisted SHA. Each component has exactly one event/position/course/RecipeVersion pin and a full sorted list of its exact per-member Serving factors. Check member attendance and the original rule hash independently; never substitute a mutable rule definition.
- `recipe_inputs` contains **all recipe versions used by any legacy or component demand**, each complete ingredient input and immutable provenance pin; `foods` contains every referenced canonical FoodIngredient and the exact relevant classification/form/default unit/active/order facts. `pantry_items` contains every Household lot relevant to the source hash (including ineligible lots), with amounts, unit, dates, estimated flag and location to reconstruct eligibility and FEFO. Empty or absent source facts are not interchangeable.
- Exactly one `component_contributions` entry is required for **each component × recipe-ingredient input row** (including when two components pin the same RecipeVersion or food), keyed by `(meal_event_id,component_id,recipe_ingredient_id)`. Repeated component/ingredient identities from separate events remain distinct; duplicate keys, missing required rows or extra rows block persistence/readback. Each entry repeats the pinned full member-serving list so it can be audited in isolation, and that list **must equal** the immutable component's serving list.
- `total_component_servings = Σ member_servings` for that component, `contribution_numerator = input_quantity × total_component_servings`, `contribution_denominator = base_servings`, `scale_factor = total_component_servings / base_servings` and `unrounded_contribution = contribution_numerator / contribution_denominator`. The numerator/denominator are stored as exact finite Decimal strings so a non-terminating quotient can be verified without misrepresenting it as mathematically exact. `scale_factor` and `unrounded_contribution` are the **deterministic 50-significant-digit Decimal computation, before any 0.001 shopping rounding**, with the accepted arithmetic context and no floats. A mismatch rejects the entire snapshot.
- `event_demands` has one aggregated **dated** demand per `(meal_event_id,FoodIngredient,compatible form_basis,unit)`, combining all component contributions for composed events and accepted legacy recipe inputs for legacy events. Match its amount to the summed raw inputs **before** Pantry allocation; never create an unresolved `COOK_COMPOSITION` record. `items`, `allocations`, `warnings` and `unresolved` mirror the corresponding immutable Shopping output (including price status) and are not authority to redefine the underlying sources.

**Canonical byte and hashing contract:**
1. UUIDs serialize as lowercase canonical hyphenated strings; dates as ISO `YYYY-MM-DD`; UTC instants as normalized ISO strings with timezone; JSON numbers only for *bounded integral* ordinal/version values, booleans as JSON booleans. `null` is explicit and never silently omitted for optional scalar source pins.
2. All quantities are **finite Decimal strings** without exponent, commas or binary float. Member `portion_servings` uses the persisted **six fractional digits**; source input/base/rational numerator/denominator and 50-precision calculated values use plain fixed notation, normalize `-0` to `0`, and remove insignificant trailing decimal zeros. Do not change numerical values or quantize source facts to produce the string. A different spelling of the same exact quantity must not cause process-dependent hashing.
3. Sort `plan_events` by `(local_date,event_position,event_id)`, `member_selection_pins` by member UUID, `servings` by `(event date,position,member UUID)`, `compositions` by event date/position, `components` by position, `member_servings` by member UUID, `recipe_inputs` by RecipeVersion UUID, ingredients by stable ingredient row ID, `component_contributions` by `(date,event position,component position,recipe_ingredient_id)`, `event_demands` by `(date,event position,FoodIngredient,form_basis,unit)`, and `items` by the existing V1 canonical food ordering. Duplicate semantic keys are rejected, not silently deduplicated.
4. Canonical JSON: UTF-8, `ensure_ascii=false`, object keys lexicographically sorted, `separators=(",",":")`, no NaN/Infinity, no implicit defaults. **Fingerprint preimages** are explicit: `source_fingerprint` is SHA-256 of the canonical **input-only** subset (`schema/engine/policy, complete plan/pins/rules/components/legacy Servings, recipe/food facts, Pantry snapshot/as-of/timezone`); it does **not** include derived contributions, allocation/output, or itself. `content_fingerprint` is SHA-256 of canonical `{source_fingerprint,component_contributions,event_demands,items,unresolved,warnings,allocations}`. `pantry_hash` uses the unchanged accepted Pantry V1 policy; `config_fingerprint` pins the accepted plan config, engine and policy. Never hash a JSON object that includes its own digest.
5. Header `source_fingerprint`, `content_fingerprint`, `config_fingerprint`, `engine_version`, `source_pantry_snapshot_hash` and `as_of_date` must equal the V2 calculation fields and independent recomputation from the stored source snapshot. Reopen the gate rather than inventing a column if these identities cannot reconcile in `0043`.
6. Recompute from V2 inputs in a **new Python process** with no warm source catalogue. Verify every contribution, event sum, event-level dated FEFO allocation, then `Σ event_demands` against canonical `items.required_quantity` rounded up **once** to `0.001`, allocated quantity rounded down, and purchase shortfall (whole-piece ceiling for `pcs`). Compare the stored rows and both hashes exactly. Drift, missing pins, malformed V2 or mismatched sums are **BLOCKING**, not a partial/`INCOMPLETE` list. For V1 lists do not reserialize under this new format or recalculate historical fingerprints.

This schema is the **minimum implementation contract**, not permission to persist arbitrary extra client-facing fields. It explicitly uses the existing `0043` JSON column; new SQL tables are **not assumed necessary**, but size, replay, consistency and read-isolation must be proven before runtime. If any invariant cannot be met by `provenance_json` and the current immutable tables, a fresh reviewed docs-only schema amendment is mandatory.

## 4. Source kinds, readiness and rollout safety

| Source kind | Calculation in the new internal path |
| --- | --- |
| `COOK_RECIPE` | Existing source-backed event Serving scaling |
| `COOK_COMPOSITION` | Every valid source-pinned component with exact per-member component Servings, aggregated by canonical compatible food/form/unit |
| `ASSEMBLY` | Existing `ASSEMBLY_UNSUPPORTED` unresolved V1 behavior; no invented assembly authority |
| `LEFTOVER`, `PREPARED`, `READY_MEAL` | Existing unresolved supply semantics, no recipe double charge |
| `ORDER_OUT`, `EAT_OUT` | No grocery demand, no fabricated out-of-home meal |

**BLOCKING:** invalid component/source/member/rule, missing verified recipe or ingredient, incompatible unit/form, unsupported quantity conversion, incomplete weekly plan, unexpected legacy Serving on composed parent, source drift or changed plan during write. **No persisted partially authoritative ShoppingList** is allowed for these errors.

**INCOMPLETE:** only accepted unresolved V1 source-kind obligations; clearly distinguish from failed composition calculation. **COMPLETE:** all grocery quantities are resolved, with no unresolved obligations, **not** a claim of meal safety, suitable dessert or ready-to-use household experience. In both cases `price_status=UNKNOWN`.

**Critical rollout hold:** `COOK_COMPOSITION` is still `DIAGNOSTIC_ONLY` under #291/#292. The new calculation may be invoked only through an explicit internal synthetic test/dev path. Normal `ShoppingService` construction and current `/api/...` routes must continue to reject composed DRAFTs by default, **on both writes and reads**. Do not add a public enable flag or introduce consumer current-list promotion in this PR. Separate reviewed authorization must cover source/role suitability, physical feasibility, nutrition, Pantry supply and derived-state exposure before real-family activation.

### 4.1 P2 decision — mandatory isolation on **all** public reads

**FACT (current API):** the public FastAPI router exposes five routes under `/api/households/{household_id}`: `POST /meal-plans/{plan_id}/shopping-lists`, `POST /meal-plans/{plan_id}/shopping-lists/regenerate`, `GET /shopping-lists/{list_id}`, `GET /meal-plans/{plan_id}/shopping-lists`, and `GET /meal-plans/{plan_id}/shopping-lists/current`. `ShoppingService.get_detail()` and `list_history()` currently return persisted rows without diagnostic filtering. `get_current()` may return the **entire latest ShoppingListDetail** as `STALE` on a calculation failure, while the API projector currently accepts only `SHOPPING_SOURCE_SNAPSHOT_V1`. Therefore **write-only isolation is insufficient**.

**DECISION for the later runtime PR:** the existing standard `ShoppingService` and all API projections are **public legacy-only read boundaries**. Before a row reaches response construction — including nested calls to `get_current()` during a detail/history projection — classify it by a strict **triple**: `shopping_lists.engine_version`, validated `provenance_json.schema`, and the referenced MealPlan's source/admission status. Only the accepted legacy combination (`shopping-v1a`, `SHOPPING_SOURCE_SNAPSHOT_V1`, legacy-only MealPlan) is public-eligible. `shopping-v1b-composition` / `SHOPPING_SOURCE_SNAPSHOT_V2_COMPOSITION` is always internal diagnostic. Unknown/missing/mismatched engine/schema, invalid JSON or inconsistent plan-source classification must **fail closed**, never be guessed as V1 or exposed through the V1 projector. The internal diagnostic reader is a **separate deliberately restricted test/dev capability** with no public dependency provider, route, feature flag or implicit fallback.

| Public operation | Required behavior with a persisted V2 diagnostic list | Legacy V1 preservation |
| --- | --- | --- |
| `GET /shopping-lists/{list_id}` / `ShoppingService.get_detail` | Return the existing non-disclosing `404 SHOPPING_NOT_FOUND` for a direct diagnostic UUID (identical to absent or cross-Household ID); **no** items, IDs, provenance, hashes, status, warnings or allocations in the payload. Validate Household scope before classification. | Existing Household-owned V1 detail remains readable (including a historical stale V1 detail) with the exact V1 allowlisted API projection. |
| `GET /meal-plans/{plan_id}/shopping-lists` / `list_history` | The public result includes **only V1-eligible** ShoppingLists; diagnostics never appear in records, counts, ordering, linked successor IDs, metadata or nested projections. When an existing composed-plan ID has only diagnostic lists, return HTTP 200 with `{"shopping_lists":[]}`; never leak a diagnostic count/UUID. Unknown/malformed stored classifications fail closed rather than being passed as V1. | Preserve all actual V1 history in its original stable order for legacy plan IDs; don't truncate or rewrite history. Filter before pagination/ordering/projection so hidden rows cannot distort visible results. |
| `GET /meal-plans/{plan_id}/shopping-lists/current` / `get_current` | For a composed diagnostic plan, return non-quantity-bearing `409 SHOPPING_CONFLICT` with a Russian-safe unsupported message **before** selecting any persisted latest or stale fallback. No `ShoppingCurrent.detail` and no `STALE` containing V2 contents. This includes a previously stored V2 list, source-invalid fallback, changed source and other error branches. | For a legacy plan, only a V1 row may be returned as `CURRENT` or `STALE` with its usual contents and reasons; a hidden V2 row must never replace its selected visible V1 record. |
| `POST generate` and `POST regenerate` | Existing public service rejects composed DRAFT up front, with no list insertion or partial results. Return non-quantity-bearing `409 SHOPPING_CONFLICT`; do not allow internal version via a request field or query parameter. | Legacy-only generation and idempotency remain unchanged. |
| API `_provenance` / `_detail_response` / `_current_response` | **Defense in depth:** V2 or unknown schema/engine cannot enter V1 projection, including through a returned `STALE` object. No raw `provenance_json` or `component_contributions` / `recipe_inputs` may appear in public response, error or logger. No new V2 public response schema is authorized. | Keep exactly the accepted V1 `warnings` and `allocations` allowlist, Russian messages, amounts-as-strings and response shape. |

**Classification and mixed-history rules:** A previously persisted V1 ShoppingList tied to an **old legacy MealPlan revision** remains fetchable via its ID and visible in that old plan's history even when a newer composed revision exists for the same Household/week. Its historical stale lifecycle may be reported under the existing V1 contract, but its content is never replaced by V2. Never relabel a V2 list as V1 based only on the plan ID or apparent `COMPLETE` status. If a V1 and V2 list are physically present against one plan ID because of test instrumentation or corruption, visibility is decided **per list** (and legacy-plan eligibility); public `get_current()` must not choose latest V2 then return it as stale. Unknown/inconsistent classification fails with the existing non-leaky availability error (HTTP 503), distinct from a known diagnostic 404 and unrelated to the actual grocery quantity completeness.

**Enforcement points:** the service must mediate `get_detail`, `list_history` and `get_current` before returning content; repository data access remains Household-scoped and stores the complete immutable internal history. The API serializer must independently reject non-V1 provenance on every response, including nested history and stale fallbacks. Do not rely on the current strict V1 `_provenance()` ValueError/503 as a substitute for data isolation: the prohibited quantity may already have reached a service caller, and `_detail_response` can otherwise be called from multiple routes. Protect both read scopes and projection boundaries.

## 5. Persistence/UoW/data/API preservation matrix

| Surface | Required preservation / change |
| --- | --- |
| 0043 Shopping schema | **No schema change proposed**; all historical rows, item uniqueness, obligation enum CHECKs, FK/triggers and old Shopping fingerprints unchanged |
| 0044 MealPlan schema | Read-only dependency; **no migration, update, backfill or fake legacy Serving** |
| MealPlan/Recipe/FoodIngredient | Read exact pinned accepted versions only; no mutation/publication |
| Pantry | Read-only snapshot and in-memory FEFO allocation; **no PantryMovement, reservation or stock mutation** |
| Shopping domain | New version-gated component demand and explicit provenance; old V1a byte/semantic regression frozen |
| Shopping service/UoW | Fetch component RecipeVersion details and canonical FoodIngredients from typed MealPlan `compositions` inside existing `BEGIN IMMEDIATE`; reject incomplete/revised inputs |
| Shopping snapshots | Immutable append-only, same `shopping_lists`/items/obligations for valid internal test; source/content fingerprints and provenance versioned **and classified as diagnostic on every public read**; internal-only complete immutable history stays accessible through a distinct guarded reader |
| API/UI/PDF/Planner/Nutrition/Prep | **No newly enabled consumer handling**; public Shopping detail/history/current/generate/regenerate plus provenance projections must isolate V2, even on STALE fallback; V1 history remains readable |
| AI/Retail/Auth/PostgreSQL | Out of scope; `AI_ENABLED=false` |

### Pre-runtime preflight checkpoints

1. Check the migration head and verify the existing `0043` table constraints can store **the complete `3.2 V2 provenance and exact replay inputs**, maintain strict V1/V2 classification through every public read, and preserve old fingerprints, uniqueness and auditability. If the required trace or isolation is not representable, return to contract review; do **not** silently append `0045`.
2. Prove that using the existing `ShoppingService._calculate` and its recipe/FoodIngredient readers with `MealPlanDetail.compositions` does not create an unguarded public path. Specifically inspect `get_detail`, `list_history`, `get_current`, its stale fallback, and `_provenance`/`_detail_response`/`_current_response` in the existing API. Enforce the `4.1 decision before a diagnostic row can be returned.
3. Verify existing actual source RecipeVersion ingredient units, optional handling and canonical FoodIngredient form basis match this policy. No fictitious missing catalogue data.
4. Confirm no need to change the frozen `0043` / `0044` migration sources, accepted Shopping V1a snapshots, or compiled frozen Planner fixtures. The historical 21-event/42-Serving reference stays immutable.

## 6. Required adversarial acceptance matrix (next runtime PR)

**Pure calculation:** one member FIRST/SECOND/optional DESSERT, multi-member FIRST+SECOND with DESSERT only for one member; different exact Decimal factors per course; same RecipeVersion in two distinct stored components; same FoodIngredient in FIRST+SECOND and elsewhere in week; zero fake event-level Serving; no count-by-member double multiplication; correct per-event dated FEFO and total-once rounding; `pcs` conservative whole-piece buys.

**Source validation:** one missing component/RecipeVersion/ingredient; unverified source or unreviewed rights; wrong Household/participant; orphan/malformed Serving; invalid Decimal/optional unit/conversion; incomplete week or wrong course rule digest; no stored list on any blocking error. The MealPlan service's prior allergen/restriction checks do not authorize Shopping to invent current allergy/preference truth.

**Snapshot provenance:** enforce every mandatory field and relationship of `3.2 (`SHOPPING_SOURCE_SNAPSHOT_V2_COMPOSITION`); source/ingredient/version UUID and complete ordered rule SHA round-trip; exact per-component member Serving sum, scale numerator/denominator, 50-precision unrounded contribution; per-event component sum reconciles with dated demand and final `shopping_list_items` after one rounding; negative tests for missing/reordered/duplicated contributions and altered Decimal encodings. Recompute hashes independently in a new process; change of course order, factor, ingredient source or Pantry must change appropriate fingerprint; same-source/different-output conflicts. Legacy V1 bytes/hashes must stay unchanged.

**Historical compatibility:** at the same old plan/pantry/time, legacy-only V1a `ShoppingCalculation`, source/content fingerprints, item ordering, price status, persisted rows, history and public API output are unchanged. Old ShoppingList linked to an old plan remains readable when a synthetic new composition revision is produced; new current/version logic never reinterprets that history.

**Transactions:** success and injected failure after writing header/item/provenance with rollback to zero new rows; SQLite second writer blocked by active `BEGIN IMMEDIATE`; conflicting plan/Pantry/source changes never commit a stale derived snapshot; no Pantry mutation; verify correct same-Household-only reads/idempotency and cross-Household denial.

**Capability isolation (P2 blocking):** seed internal `shopping-v1b-composition` snapshots **in the existing 0043 tables**, then call **all five** real HTTP routes: `POST generate`, `POST regenerate`, `GET /shopping-lists/{list_id}`, `GET /meal-plans/{plan_id}/shopping-lists` and `GET .../current`. Direct V2 ID returns non-disclosing 404; V2-only history is empty; current returns non-payload 409 even when a stored V2 row is latest and its source cannot be recalculated; generate/regenerate return 409 without inserting. Assert no hidden ID, quantity, item, hash, provenance key, diagnostic row count, warning or allocation in API JSON/errors. Test `ShoppingService.get_detail/list_history/get_current` independently (not only router) and API `_provenance`, `_detail_response`, `_current_response` as defense in depth. Inject unknown/mismatched engine and provenance/schema: fail closed; never fallback to V1 or expose V2 as STALE. Verify ordinary historical V1 detail/history/current/stale remain readable with exact V1 allowlisted projection and Russian text, including after a newer composed plan for the same week. Internal guarded diagnostic reader can inspect V2 for tests, but no public route/flag is added.

**End-to-end:** exercise the actual 21-event seven-day MealPlan, retaining the 20 unaffected events and substituting exactly the one diagnostic lunch with FIRST+SECOND+optional DESSERT. Independently verify the aggregated ingredient needs and source pins, old 21/42 history, and absence of Pantry movements. No claim of physical portion, source-suitability or Gate2 release.

**Verification tier:** focused Shopping domain/service/UoW tests, new-process deterministic replay, fresh+upgrade no-migration parity and FK/immutable-shopping preservation, SQLite concurrency/fault tests, existing legacy Shopping API regression, full backend+launcher test matrix at frozen runtime HEAD, docs/ruff checks, accepted PR10-FF two-process evidence. Never claim PASS from an unexecuted test.

## 7. Delivery and stop conditions

**This gate PR:** only this canonical document and minimal `state/current-focus.md`, `state/progress.md`, `state/handoff.md` updates. No runtime code, migration, seed, test fixture, API/Shopping activation or consumer UX.

**Next (only after independent review and owner merge):** one bounded Shopping-owned runtime PR implementing the approved version-gated calculation, UoW integration, provenance and tests. Keep `main` green and merge only on explicit owner authorization. No automatic follow-on Retail, AI, Prep or source publication.

**OPEN QUESTION for independent review:** Is the existing event-level allocation trace plus per-component `provenance_json` sufficient for all required audit/replay consumers, or does a new component-level persisted relation become necessary? The chosen default is **no migration**, but that assumption must be proven in preflight; failure reopens this gate.

**Decision requested:** approve or amend Option D, the versioned legacy-preserving calculation/provenance policy, strict diagnostic-only rollout hold and no-new-migration assumption. Until approved, this document authorizes **no** Shopping runtime change.
