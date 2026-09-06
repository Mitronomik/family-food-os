# PR5 — Household Pantry core

Status: implemented for PR5 review; acceptance and merge are separate gates.

## Context and goal

PR5 starts from merged `main` at
`b7fb609fc28dc46fa5891fc677272b6d21b58b58`, after accepted Household,
FoodIngredient and Recipe Catalogue. It records confirmed food-at-home facts:

`Household → PantryItem → FoodIngredient → current quantity + immutable PantryMovement`.

## Scope and architecture

The context owns stock buckets, metadata, add/consume/waste/adjust commands,
Household-scoped reads, available quantities and expiring queries. Multiple items
for one FoodIngredient distinguish storage locations and calendar dates.

Domain and application code depend only on repository/UoW contracts. SQLAlchemy
Core adapters share the project-owned synchronous UoW connection. The existing
custom SQLite migration runner is the only schema authority. Earlier migration
files, catalogue truth and legacy inventory semantics remain unchanged.

## Data model and exact quantity semantics

`PantryItem` contains UUIDv4 identity, immutable Household/FoodIngredient/unit,
current Decimal quantity, PANTRY/FRIDGE/FREEZER location, estimated flag, nullable
purchase/open/expiry dates and aware UTC creation/update instants.

`PantryMovement` contains UUIDv4 identity, Household and item, positive Decimal
quantity, unit, movement type and aware UTC occurrence/creation instants.
The movement type determines direction:

- incoming: ADD, ADJUSTMENT_IN;
- outgoing: CONSUMPTION, WASTE, ADJUSTMENT_OUT.

Quantities use `0.001` precision with the existing ROUND_HALF_UP Decimal helper,
including fractional `pcs` when a confirmed portion is recorded. The supported
per-item/per-command range is `0` through `999999999999.999`. Initial stock and
movement quantities must round to a strictly positive value. Negative values
are rejected before rounding; NaN, infinity, floats and booleans are rejected.
Zero resulting balances remain durable. Unit must equal the referenced active
FoodIngredient's default unit when creating stock: `g`, `ml` or `pcs`.
There are no conversions. Deactivated FoodIngredient history remains readable
and existing stock can still be accounted for.

SQLite stores fixed three-place decimal text, preserving exact values without
binary float arithmetic. Repositories calculate a validated target with Decimal
and perform a conditional update scoped to Household, item and exact expected
old quantity. A stale snapshot cannot overwrite a changed balance; a failed
comparison or SQLite write conflict aborts the command. Clients may retry a
reported conflict after reloading. PR5 does not provide automatic retry or
idempotency keys for resubmitted successful commands.

Every successful quantity command changes the operational balance and appends
its matching movement in one UoW. The supported-command invariant is:

`quantity = ADD + ADJUSTMENT_IN − CONSUMPTION − WASTE − ADJUSTMENT_OUT >= 0`.

No-op adjustment emits no movement. Repositories never choose movement type or
commit. Raw adapter primitives are infrastructure building blocks, not public
quantity commands; callers must use the application service for ledger writes.

## Migration

Exactly `0025_pantry` appends `pantry_items` and `pantry_movements`. It installs
Household/ingredient/expiry/history indexes, UUIDv4 and exact-quantity checks,
unit/location/boolean/date/instant checks, foreign keys, an active ingredient
and unit guard for new stock, and a composite movement-to-item FK that also
matches Household and unit. SQLite rejects movement UPDATE/DELETE, item identity
changes and physical item deletion. No `pantry_lots` or second balance table.

Fresh schema and `0024 → 0025` upgrades are tested, including preservation of
previous schema and data, foreign keys, invalid persisted input and immutable
history guards. UTCDateTime normalizes aware instants into the accepted
naive-UTC storage format and restores aware UTC values.

## FEFO and dates

Available means positive quantity. FEFO order is earliest known expiry, unknown
expiry last, oldest known purchase date (unknown last), then creation instant
and UUID. Expiring stock has positive quantity and a known expiry on or before
an explicit calendar boundary. Neither query fabricates dates or excludes
expired stock from accounting. Consumption records a confirmed event; it is
not advice about whether food is safe to eat.

Ingredient consumption allocates across ordered items in one transaction.
Insufficient aggregate stock or a failure on any allocation rolls back every
item and movement. Calendar dates remain dates; the server's local timezone
never redefines them. No inferred shelf life or date-order food-safety policy
is introduced.

## API

All routes use `/api/households/{household_id}/pantry`:

| Method | Suffix | Result |
|---|---|---|
| POST | `/items` | Create item and initial ADD, 201 |
| GET | `/items` | Positive items; optional FoodIngredient/location/include_empty filters |
| GET | `/items/{item_id}` | Scoped item, including a zero balance |
| PATCH | `/items/{item_id}` | Location, estimated, purchase/open/expiry metadata only |
| POST | `/consume` | FoodIngredient/quantity/unit; returns allocated CONSUMPTION movements |
| POST | `/items/{item_id}/waste` | Positive quantity/unit removed from an item |
| POST | `/items/{item_id}/adjust` | Target_quantity/unit; returns corrected item |
| GET | `/expiring?on_or_before=YYYY-MM-DD` | Known expiries through explicit boundary |

Responses serialize Decimal quantities as strings. Request extras and generic
PATCH quantity/identity edits are rejected. Errors use 404 for missing scoped
objects, 409 for insufficient stock/inactive ingredient/state conflicts and
422 for invalid input. A foreign Household item and an unknown item have the
same 404 response. Household selection is not authentication or authorization.

The application additionally exposes
`get_available_quantity(household_id, food_ingredient_id)`. There is no public
movement mutation or deletion endpoint.

## Tests and acceptance

Domain, service, repository, UoW, migration, architecture and API suites cover
positive/negative inputs, exact ledger reconciliation, FEFO, Household
isolation, atomic rollback and terminal repository handles. Full backend and
launcher regression is the final gate. Exact run evidence belongs in
[state/progress.md](../../state/progress.md).

Acceptance requires the complete add/read/consume/waste/correct/metadata/expiry
flow, no negative stock, ledger reconciliation, deterministic multi-item FEFO,
isolation and unchanged accepted-context regressions. The final PR report lists
base/head, changed files, schema/API, test counts, checks, limitations and PR URL.

## Non-goals, frontend and next gate

Frontend: N/A. No PantryLot, supplier, retail package or conversion, Planner,
Shopping, MealPlan/Serving, Nutrition Engine, Prep, AI, Auth, PostgreSQL, receipt
or barcode workflow. Legacy inventory is not removed. No catalogue data changes.

PR5 stops at READY FOR REVIEW. Project acceptance and explicit merge permission
are required before closure; PR6 and later work remain unauthorized.
