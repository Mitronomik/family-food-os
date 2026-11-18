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

**Critical rollout hold:** `COOK_COMPOSITION` is still `DIAGNOSTIC_ONLY` under #291/#292. The new calculation may be invoked only through an explicit internal synthetic test/dev path. Normal `ShoppingService` construction and current `/api/...` routes must continue to **reject** composed DRAFTs by default, even if the calculation can generate an internally valid quantity result. Do not add a public enable flag or introduce consumer current-list promotion in this PR. Separate reviewed authorization must cover source/role suitability, physical feasibility, nutrition, Pantry supply and derived-state exposure before real-family activation.

## 5. Persistence/UoW/data/API preservation matrix

| Surface | Required preservation / change |
| --- | --- |
| 0043 Shopping schema | **No schema change proposed**; all historical rows, item uniqueness, obligation enum CHECKs, FK/triggers and old Shopping fingerprints unchanged |
| 0044 MealPlan schema | Read-only dependency; **no migration, update, backfill or fake legacy Serving** |
| MealPlan/Recipe/FoodIngredient | Read exact pinned accepted versions only; no mutation/publication |
| Pantry | Read-only snapshot and in-memory FEFO allocation; **no PantryMovement, reservation or stock mutation** |
| Shopping domain | New version-gated component demand and explicit provenance; old V1a byte/semantic regression frozen |
| Shopping service/UoW | Fetch component RecipeVersion details and canonical FoodIngredients from typed MealPlan `compositions` inside existing `BEGIN IMMEDIATE`; reject incomplete/revised inputs |
| Shopping snapshots | Immutable append-only, same `shopping_lists`/items/obligations for valid internal test; source/content fingerprints and provenance versioned |
| API/UI/PDF/Planner/Nutrition/Prep | **No newly enabled consumer handling**; old fail-closed/unsupported composition behavior remains |
| AI/Retail/Auth/PostgreSQL | Out of scope; `AI_ENABLED=false` |

### Pre-runtime preflight checkpoints

1. Check the migration head and verify the existing `0043` table constraints can store the new trace entirely in `provenance_json` and `engine_version` while preserving old fingerprints, uniqueness and auditability. If the required trace is not representable, return to contract review; do **not** silently append `0045`.
2. Prove that using the existing `ShoppingService._calculate` and its recipe/FoodIngredient readers with `MealPlanDetail.compositions` does not create an unguarded public path.
3. Verify existing actual source RecipeVersion ingredient units, optional handling and canonical FoodIngredient form basis match this policy. No fictitious missing catalogue data.
4. Confirm no need to change the frozen `0043` / `0044` migration sources, accepted Shopping V1a snapshots, or compiled frozen Planner fixtures. The historical 21-event/42-Serving reference stays immutable.

## 6. Required adversarial acceptance matrix (next runtime PR)

**Pure calculation:** one member FIRST/SECOND/optional DESSERT, multi-member FIRST+SECOND with DESSERT only for one member; different exact Decimal factors per course; same RecipeVersion in two distinct stored components; same FoodIngredient in FIRST+SECOND and elsewhere in week; zero fake event-level Serving; no count-by-member double multiplication; correct per-event dated FEFO and total-once rounding; `pcs` conservative whole-piece buys.

**Source validation:** one missing component/RecipeVersion/ingredient; unverified source or unreviewed rights; wrong Household/participant; orphan/malformed Serving; invalid Decimal/optional unit/conversion; incomplete week or wrong course rule digest; no stored list on any blocking error. The MealPlan service's prior allergen/restriction checks do not authorize Shopping to invent current allergy/preference truth.

**Snapshot provenance:** full ordered rule SHA and component/member/ingredient pins round-trip; order-stable hashes in new OS process; different course order or one member factor changes fingerprint; source version change invalidates current; identical inputs return identical source/content fingerprints; same hash/different content conflicts. Maintain deterministic source fingerprint despite SQLite row ordering and sorting ties.

**Historical compatibility:** at the same old plan/pantry/time, legacy-only V1a `ShoppingCalculation`, source/content fingerprints, item ordering, price status, persisted rows, history and public API output are unchanged. Old ShoppingList linked to an old plan remains readable when a synthetic new composition revision is produced; new current/version logic never reinterprets that history.

**Transactions:** success and injected failure after writing header/item/provenance with rollback to zero new rows; SQLite second writer blocked by active `BEGIN IMMEDIATE`; conflicting plan/Pantry/source changes never commit a stale derived snapshot; no Pantry mutation; verify correct same-Household-only reads/idempotency and cross-Household denial.

**Capability isolation:** normal API `POST generate`, `GET current` and regenerate **fail closed** for synthetic composed DRAFTs (no partial shopping basket); explicit test-only diagnostic call produces a valid internal result with no public activation. No new public routes or flags.

**End-to-end:** exercise the actual 21-event seven-day MealPlan, retaining the 20 unaffected events and substituting exactly the one diagnostic lunch with FIRST+SECOND+optional DESSERT. Independently verify the aggregated ingredient needs and source pins, old 21/42 history, and absence of Pantry movements. No claim of physical portion, source-suitability or Gate2 release.

**Verification tier:** focused Shopping domain/service/UoW tests, new-process deterministic replay, fresh+upgrade no-migration parity and FK/immutable-shopping preservation, SQLite concurrency/fault tests, existing legacy Shopping API regression, full backend+launcher test matrix at frozen runtime HEAD, docs/ruff checks, accepted PR10-FF two-process evidence. Never claim PASS from an unexecuted test.

## 7. Delivery and stop conditions

**This gate PR:** only this canonical document and minimal `state/current-focus.md`, `state/progress.md`, `state/handoff.md` updates. No runtime code, migration, seed, test fixture, API/Shopping activation or consumer UX.

**Next (only after independent review and owner merge):** one bounded Shopping-owned runtime PR implementing the approved version-gated calculation, UoW integration, provenance and tests. Keep `main` green and merge only on explicit owner authorization. No automatic follow-on Retail, AI, Prep or source publication.

**OPEN QUESTION for independent review:** Is the existing event-level allocation trace plus per-component `provenance_json` sufficient for all required audit/replay consumers, or does a new component-level persisted relation become necessary? The chosen default is **no migration**, but that assumption must be proven in preflight; failure reopens this gate.

**Decision requested:** approve or amend Option D, the versioned legacy-preserving calculation/provenance policy, strict diagnostic-only rollout hold and no-new-migration assumption. Until approved, this document authorizes **no** Shopping runtime change.
