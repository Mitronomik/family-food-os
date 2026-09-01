# FamilyFoodOS — Target Architecture and Persistence Contract

**Status:** canonical architecture contract for PR2 and subsequent FamilyFoodOS work

**Version:** 1.0

**Decision date:** 2026-09-01

**Related decision:** ADR 0032, `FamilyFoodOS persistence portability and shared-deployment tenancy gate`

## 1. Authority and scope

This document is the canonical target architecture for the FamilyFoodOS food
product. For FamilyFoodOS product decisions it explicitly supersedes inherited
`docs/architecture.md`. The inherited document remains unchanged as legacy
CosmeticWorkshopOS engineering evidence; it is not the food-domain
specification.

The source-of-truth order remains the order in root `AGENTS.md`. In particular,
later explicit approved decisions may amend this contract. An implementation
detail in inherited source code does not override this contract.

**FACT:** The repository currently contains a working local FastAPI, vanilla
frontend and SQLite runtime inherited from CosmeticWorkshopOS.

**FACT:** ADR 0030 establishes hosted responsive Web/PWA delivery as the target
and classifies the local stack as transitional migration scaffolding.

**DECISION:** PR2-A defines ownership, dependency, transaction and persistence
boundaries only. It authorizes no production food model, schema, migration,
dependency, API, frontend, authentication or deployment implementation.

**ASSUMPTION:** The first food-domain implementation will remain a modular
monolith. There is no demonstrated need for separately deployed services or
distributed transactions.

## 2. Product and architectural objective

The architecture supports this recurring product loop:

```text
Household
→ Members / Preferences / Constraints
→ Recipe Catalogue
→ Nutrition
→ Planner
→ MealPlan
→ Servings
→ Pantry
→ Shopping
→ Prep / Freezer
→ Daily Use
→ Feedback
→ Next Week
```

The governing product principle is:

> complexity inside the system, simplicity for the user.

Backend-owned, deterministic and reproducible decisions are preferred over
opaque automation. A normal household should receive a useful proposal and
confirm or adjust it without operating technical infrastructure or managing
platform catalogues.

## 3. Deployment architecture

### 3.1 Transitional architecture

The current migration scaffold is:

```text
vanilla frontend
        ↓
local FastAPI
        ↓
SQLite
        ↓
launcher / local backup / Restore support
```

This stack remains valid while legacy contexts are migrated. SQLite is also a
valid development, test and early vertical-slice database. The launcher,
filesystem database paths, local Restore workflow and inherited vanilla
frontend are not the target consumer delivery architecture.

### 3.2 Target FamilyFoodOS architecture

```text
Consumer Web/PWA
        ↓
Hosted Application API
        ↓
Application services / deterministic domain engines
        ↓
Repository interfaces / Unit of Work
        ↓
Persistence adapters
        ↓
Production database
```

The target consumer product is hosted, responsive, mobile-first and installable
as a PWA. Normal end users do not manage Python, Node, Git, launcher processes,
database files or migrations.

The target remains one modular application until scale or operational evidence
justifies another topology. Context boundaries below are code and ownership
boundaries; they do not imply network services.

## 4. Dependency direction

The required compile-time and call direction is:

```text
UI
↓
API
↓
application services / domain engines
↓
repository interfaces
↓
persistence adapters
↓
database
```

**DECISION:** The following rules are mandatory for all new food-domain code:

- domain objects do not import FastAPI, API schemas or HTTP concerns;
- domain engines do not import database drivers or persistence adapters;
- application and domain services do not depend directly on SQLite-specific
  APIs;
- repository interfaces belong at the application/domain boundary;
- concrete SQLite and PostgreSQL implementations live below those interfaces;
- API request/response schemas are boundary contracts, not the domain model;
- repositories return domain/application types, not driver rows;
- the frontend calls the API and never queries persistence directly;
- critical calculations remain backend-owned;
- infrastructure may depend inward on repository contracts and domain types;
  the reverse dependency is forbidden.

Dependency injection assembles concrete adapters at the application boundary.
The choice of database must not change a planner, nutrition, shopping or pantry
service signature.

## 5. Data ownership and tenancy

### 5.1 Platform-owned data

Platform-owned data is curated once for use by authorized households. It
includes:

- canonical food ingredients, aliases, units and conversion metadata;
- nutrition sources and normalized nutrition profiles;
- the production recipe catalogue and recipe versions;
- recipe and nutrition ingestion metadata;
- retailer, store/region, SKU, mapping, availability and price snapshots;
- platform validation and review metadata.

Platform-owned data is not duplicated into each household merely to enforce
tenancy. Administrative mutation is separately authorized from consumer use.

### 5.2 Household-owned data

Household-owned data includes:

- `Household` and `HouseholdMember`;
- settings, preferences, exclusions and cooking/budget constraints;
- Pantry state and movements;
- MealPlans, day/slot structures and Servings;
- ShoppingLists and purchase state;
- PrepPlans, PrepTasks and useful household prepared/freezer batches;
- feedback, derived preference signals and household history.

**DECISION:** Every persisted household-owned aggregate has an unambiguous
`Household` ownership boundary. Every repository query or command for such data
is household-scoped, including lookups by an entity's own opaque identifier.

The vertical slice may use one fixture household without Auth. This is a
development/testing shortcut, not a global-data architecture.

**DECISION:** The older technical specification's `Household.owner_id` field is
not required by the no-Auth vertical slice. Do not add a fake, nullable or
fixture identity merely to preserve that field list. `Household` is the domain
ownership boundary; authenticated principals and household authorization are a
separate concern. An owner role may later be represented through the
Principal-to-Household membership/authorization relationship. This decision
refines the older field list without rewriting that historical Project Source.

For a shared deployment the request authorization path is:

```text
authenticated principal
        ↓
authorized household membership/role
        ↓
household-scoped application operation
```

Once Auth exists, a raw client-provided `household_id` is selection input only.
It is never sufficient proof of authorization. The API resolves the principal's
authorized household scope and supplies that scope to the application command.

**OPEN QUESTION — must be resolved before the shared-deployment implementation
PR:** the exact principal, membership and household-role model.

## 6. Bounded contexts

### 6.1 Household

Owns `Household`, `HouseholdMember`, household settings, exclusions,
preferences, cooking constraints and budget constraints. It supplies stable
household facts to planning and other household operations.

It does not own canonical food facts, production recipes or retailer products.
It must be implemented as a new food context and must not reuse or rename
`Client`.

### 6.2 Canonical Food Catalogue

Owns the platform `FoodIngredient` catalogue, nutrition-profile references,
aliases, accepted units, density, edible fraction, allergens, storage metadata
and provenance.

`CanonicalIngredient` is terminology used in earlier FamilyFoodOS Project
Sources. In this canonical architecture that same platform food concept is
named `FoodIngredient`; the two names are aliases, not separate entities.
`RecipeIngredient` references `FoodIngredient`.

`FoodIngredient` is an abstract food concept. It is separate from household
Pantry quantities and retailer SKU/package facts. Catalogue mutation belongs to
trusted platform/admin workflows, not ordinary consumer flows.

Earlier ingestion material also proposed a required `FoodProductType` layer
between canonical ingredients and retailer SKUs. The MVP deliberately does not
make `FoodProductType` a source-of-truth aggregate or bounded context. Retail
may later add product-form/classification metadata when SKU matching, package
selection, fat-content/form distinctions or normalization prove that need. Such
metadata must not become Planner truth, Nutrition truth by itself or a second
canonical ingredient entity. The MVP Retail path remains:

```text
FoodIngredient
        ↓
RetailMapping
        ↓
RetailSKU candidates
        ↓
PriceSnapshot
```

### 6.3 Recipe Catalogue

Owns platform production `Recipe`, immutable/versioned `RecipeVersion`,
`RecipeIngredient`, `RecipeStep`, base servings, meal type, preparation/cooking
time, equipment, storage/freezer metadata and provenance/verification status.

The inherited version-history pattern is useful and should be adapted.
Cosmetic percentage-total rules and cosmetic phases are not food invariants.
Published production recipe versions require verifiable provenance and may not
be silently mutated.

### 6.4 Nutrition Engine

The Nutrition Engine is deterministic and versioned. It computes:

```text
FoodIngredient nutrition
→ RecipeVersion nutrition
→ Serving nutrition
→ Member/day/week aggregates
```

It owns formulas, normalization/rounding policy, configuration version and
calculation warnings. An LLM is never the source of truth for kcal, nutrients,
serving mass or allergens. Uncertainty is represented explicitly rather than
invented as precision.

### 6.5 MealPlan / Serving

Owns `MealPlan`, day and meal-slot structure, references to selected immutable
recipe versions, individualized `Serving` values, planner/configuration version
references and generation-trace references.

A recipe describes how food is made. A serving describes how much of a selected
recipe is allocated to one household member for one meal. They are distinct
concepts and may evolve independently.

### 6.6 Planner

The Planner is a deterministic application/domain engine.

Inputs include household members, constraints and preferences, candidate recipe
versions, nutrition, budget, cooking constraints, recent history, Pantry and a
planning mode. Outputs include a complete seven-day MealPlan, individualized
Servings and trace/explanation metadata.

Planner v0 uses deterministic filtering plus scoring/heuristics. OR-Tools or
another solver is optional later and must demonstrate measurable improvement
over the baseline.

Each generation records or durably references enough trace information to
reproduce and explain it: planner version, configuration, candidate pool,
constraints, rejected candidates and reasons, scores, selections, warnings and
duration. Trace storage must avoid duplicating sensitive household details when
stable references or bounded snapshots suffice.

### 6.7 Pantry

Pantry is household-owned. It owns quantities, units, storage locations,
purchase/open/expiry facts, movements and estimated flags.

Movement-derived balances, non-negative protections, expiration ordering and
FEFO patterns from the inherited system are candidates for adaptation. Normal
household UX does not require supplier records or industrial lot-accounting
terminology. A simple state such as `eggs — 6 pcs` remains valid.

### 6.8 Shopping

Shopping owns the generic deterministic Shopping Engine, `ShoppingList` and
`ShoppingItem`:

```text
MealPlan
→ scale recipe ingredients
→ normalize units
→ aggregate
→ subtract Pantry
→ ShoppingList
```

Each item can carry required quantity, available Pantry quantity, purchase
quantity, unit and a generic estimated price. Retail data is optional enrichment
and is not required for the engine to work.

Generating a ShoppingList reads a Pantry snapshot and may calculate
`required_quantity`, `pantry_available_quantity` and `purchase_quantity`. It is
read-only with respect to Pantry: generation does not reserve or consume stock,
create movements or alter quantities. Any future reservation is a separately
modeled operation and is not implied by list generation.

### 6.9 Prep / Freezer

Consumes MealPlan selections and recipe preparation/storage metadata. Owns
`PrepPlan`, `PrepTask` and a household-oriented prepared/freezer batch
representation where it produces clear value.

Its goals are batch cooking, common preparation, freezing, defrost/reheat
sequencing and lower weekday effort. It does not inherit industrial
`ProductionBatch` semantics, costing, tax, sale or workshop packaging.

Generating a PrepPlan is planning only. It does not consume ingredients, create
prepared/freezer stock or create Pantry movements. Confirmed execution is a
separate application command that may create Pantry movements or prepared
inventory changes under the Prep/Pantry transaction contract. Its exact model
belongs to the owning implementation PR.

### 6.10 Ingestion

Ingestion is a platform/admin context:

```text
Source
→ Raw record
→ Parse
→ Normalize
→ Resolve
→ Validate
→ Review / policy-controlled auto-approval
→ Canonical catalogue
```

It adapts the inherited draft, preview, validation and explicit apply patterns.
Untrusted parsed data never silently becomes production truth. Consumer flows
do not depend on ingestion internals or expose confidence/parser details.

### 6.11 Retail

Retail is a later, separate context. It owns `Retailer`, `RetailStore` or region
scope, `RetailSKU`, `RetailMapping`, `PriceSnapshot`, availability and package
metadata.

```text
FoodIngredient != RetailSKU
```

Retail mapping relates the concepts; it does not merge them. Planner does not
depend on a concrete retailer. Connectors are infrastructure adapters behind a
retail contract and come only after generic Shopping works.

### 6.12 Feedback / Personalization

Owns household feedback such as liked, disliked, skipped, replaced, leftover
and repeat requested, plus deterministic derived preference/history signals.
Planner may consume these signals without an LLM. Raw feedback interpretation
and authoritative structured signals remain separate steps.

### 6.13 AI Gateway

AI is an optional boundary behind a provider-neutral gateway. Allowed uses
include natural-language input, feedback interpretation, ingestion assistance,
matching suggestions, explanations and substitution candidates.

All AI output is untrusted proposal data until deterministic validation. AI
never directly becomes trusted nutrition, quantity, allergen, price,
availability or storage truth. Every core workflow works with
`AI_ENABLED=false`.

### 6.14 Artifacts / PDF

PDF and other artifacts are derived representations of current deterministic
product state:

```text
MealPlan + ShoppingList + PrepPlan
→ printable weekly PDF
```

The artifact is not a source of truth and is reproducible from authoritative
state plus the artifact renderer version. Existing safe creation,
non-overwrite, verification and truthful partial-success patterns may be
adapted. Hosted artifact storage/recovery requires a later explicit design.

### 6.15 Daily Use

Daily Use is an application/read-model boundary rather than a separate source
of truth. It composes today's MealPlan slots and Servings with Prep/defrost
instructions and relevant Pantry state. Confirmed mutations, such as skipping a
meal or consuming Pantry, are delegated to the context that owns that state and
use its transaction rules. The Today UI does not create a second copy of plan,
prep or pantry truth.

## 7. Domain identifiers, timestamps and API identity

### 7.1 Identifiers

Domain identifiers are opaque to clients and carry no business meaning. They
may be used in URLs or references, but consumer workflows present names, dates
and actions rather than database IDs.

Clients must not infer ordering, tenancy, type or authorization from an ID.
APIs must not leak internal row objects or database-driver values.

**OPEN QUESTION — must be resolved by the first schema implementation PR:** use
of integer, UUID or another identifier representation for new food entities.
The decision must consider offline fixtures, PostgreSQL migration, URL safety,
index/storage cost and server-side generation. PR2-A does not invent a mixed or
premature ID scheme.

### 7.2 Instants and the household planning calendar

**DECISION:** True instants are persisted in UTC. This includes created/updated
timestamps, audit and import events, retail `PriceSnapshot.captured_at`, external
synchronization timestamps and confirmed execution events.

`Household` owns an IANA timezone identifier. MealPlan weeks, calendar days and
meal-slot dates use date/local-calendar semantics in that Household timezone;
they are not inferred directly from a UTC timestamp. API/UI presentation
converts instants for the household/user experience without redefining stored
planning dates. Exact SQL column types and API serialization formats are first
schema/API implementation decisions.

## 8. Data provenance

### 8.1 Nutrition

At minimum, authoritative nutrition data records or references:

```text
source
source_id
version
verified_at
estimated/confidence where relevant
```

Derived nutrition also records the calculation formula/configuration version
and the ingredient nutrition versions used.

### 8.2 Recipes

At minimum, a production recipe records or references:

```text
source
source_url or source_id
source_date
original_servings
verification_status
recipe_version
```

Rights/licensing status must be reviewable where externally sourced content is
stored. An LLM-generated recipe is not production truth solely because a model
produced it.

### 8.3 Retail prices

Every retail price later records:

```text
source
captured_at
retailer
store or region scope
```

Staleness is explicit. A timeless or provenance-free retail price is not
presented as current.

## 9. Repository contracts

Conceptual interfaces for the new food domain include:

```text
HouseholdRepository
FoodIngredientRepository
RecipeRepository
PantryRepository
MealPlanRepository
ShoppingListRepository
PrepPlanRepository
FeedbackRepository
```

Additional focused query repositories are allowed where a read model crosses
multiple aggregates without transferring ownership.

**DECISION:** Repository interfaces:

- return domain/application entities, value objects or explicit read models;
- never return raw database rows, cursors, SQL expressions or driver errors;
- hide SQL syntax, placeholder style and driver types;
- never expose `sqlite3.Connection` or any concrete driver session through the
  interface;
- never expose SQLAlchemy `Connection`, DBAPI connection or transaction types
  through domain/application APIs;
- receive transaction context through a Unit of Work rather than a concrete
  database connection exposed to the application service;
- require household scope for household-owned reads and writes;
- expose intent-oriented methods, not unrestricted query builders;
- do not commit or roll back independently;
- map constraint/driver failures to stable persistence/application errors at
  the adapter boundary.

The inherited repository classes are implementation evidence only. Their
optional raw connection parameters and session-local behavior are not the
target food repository contract.

## 10. Unit of Work and transaction ownership

One write application command owns one connection and one transaction:

```text
Application command
        ↓
UnitOfWork
        ↓
one connection + one transaction
        ↓
all participating repository reads and writes
        ↓
commit OR rollback
```

All repositories participating in the command use the same active Unit of Work,
including validation, existence and concurrency reads. They do not open an
unrelated read or write connection while it is active. Any failure rolls back
the complete command, and repositories never commit or roll back independently.

The Unit of Work exposes repository contracts required by the command and
`commit`/`rollback` lifecycle semantics. Its transaction handle is opaque above
the persistence layer. Application services do not receive a database-driver
connection.

Read-only application operations use one consistent read-only Unit of Work or
query scope and never commit. A trivial read need not pretend to be a write
transaction, but repositories still may not leak connection ownership or driver
types through the application boundary.

The inherited `backend/app/db/session()` helper is implementation evidence and
transitional infrastructure. Because it owns commit-on-context-exit semantics,
it is not the target FamilyFoodOS food-domain Unit of Work. PR2-A does not modify
that helper.

Operations expected to need atomic multi-repository writes include:

- create MealPlan plus days, slots, Servings and generation-trace reference;
- replace a meal and persist all recalculated dependent state;
- apply purchased ShoppingList quantities and movements into Pantry;
- consume Pantry quantities for a confirmed persisted workflow;
- publish a verified recipe version and its ingredient/step records;
- apply an approved ingestion draft to canonical records plus audit state.

Pure deterministic calculation should run before the write transaction where
practical. The command may then revalidate version/concurrency facts inside the
transaction before writing. Long-running planner, network, AI, retailer or PDF
work must not hold a database transaction open.

This is a local database transaction contract, not a distributed transaction
framework. Cross-resource artifact workflows use explicit prepared/finalized
state and truthful partial-success semantics rather than pretending filesystem
and database writes are atomic.

## 11. Persistence strategy

### 11.1 Immediate vertical slice

SQLite remains the persistence adapter for the immediate MVP/vertical slice
because:

- it is the verified repository baseline;
- it keeps local and test setup small;
- it supports deterministic core-loop development;
- the vertical slice has no shared multi-user requirement;
- it permits isolated fixture households and repeatable tests.

SQLite is an adapter choice, not a domain assumption. New application services
must not use SQLite paths, pragmas, placeholder syntax, row types, backup APIs
or connection classes.

### 11.2 PostgreSQL target and transition seam

PostgreSQL is required before the first shared multi-family deployment:

```text
domain/application        unchanged
repository contracts     unchanged
Unit of Work contract     unchanged
SQLite adapter
        ↓ replace/add
PostgreSQL adapter
```

Adapter conformance tests run against both implementations during the
transition. Database-specific migration/deployment, backup and restore behavior
remains infrastructure-specific and is not hidden as portable domain logic.

### 11.3 Inherited portability hazards

**FACT:** Current repository evidence includes direct database connection and
row types, SQLite `?` placeholders, `sqlite_master`, pragmas, filesystem
database assumptions, launcher/Restore assumptions and session helpers that
commit on context exit. Repository methods frequently open their own local
session unless a caller passes a connection.

**DECISION:** Those patterns remain valid only inside inherited/transitional
code or a concrete SQLite adapter. New food-domain application and domain code
must not repeat them. PR2-A does not repair inherited areas.

## 12. Persistence adapter technology evaluation

### Option A — direct SQLite SQL behind clean interfaces

Use the standard SQLite driver in a new adapter and later implement a separate
PostgreSQL adapter.

| Criterion | Evaluation |
|---|---|
| New dependency/complexity | Lowest initially |
| Unit of Work | Feasible, but transaction/session abstraction must be built and tested |
| SQLite/PostgreSQL portability | Contracts can be portable; SQL and migrations are duplicated |
| Migration tooling | Can extend inherited custom sequential migrations for SQLite; PostgreSQL needs a second mechanism or substantial evolution |
| Testability | Good with adapter contract tests, but more handwritten plumbing |
| Long-term risk | Highest risk of two drifting SQL implementations and dialect-specific behavior |
| Coexistence | Simple at first because it matches inherited runtime |

### Option B — SQLAlchemy Core for new food contexts only

Use synchronous SQLAlchemy 2.x Core for new food runtime persistence, without
rewriting inherited CosmeticWorkshopOS repositories. Schema migration authority
is a separate decision in section 13; selecting Core does not select or add
Alembic during the SQLite period.

| Criterion | Evaluation |
|---|---|
| New dependency/complexity | One later dependency and focused conventions; less lifecycle machinery than ORM |
| Unit of Work | Explicit connection/transaction primitives support a project-owned UoW |
| SQLite/PostgreSQL portability | Stronger shared statement/mapping layer, while dialect-specific features still require explicit tests |
| Migration tooling | Independent of runtime Core; the existing custom runner remains authoritative for active SQLite |
| Testability | Strong adapter integration and rollback fixtures; both dialects can share conformance tests |
| Long-term risk | Lower risk than maintaining two full handwritten SQL implementations |
| Coexistence | Limited to new food adapters while inherited repositories remain on `sqlite3` |

**DECISION:** New FamilyFoodOS food bounded contexts use **synchronous
SQLAlchemy 2.x Core** as their persistence adapter technology. Core provides
database-dialect portability between SQLite and PostgreSQL, explicit connection
and transaction ownership, and clean support for the project-owned Unit of Work.
It avoids coupling domain objects to an ORM identity map/session lifecycle, uses
less machinery than ORM for the current deterministic domain, and avoids two
separate handwritten SQLite and PostgreSQL repository implementations.

Synchronous database access is the baseline for the current backend. FastAPI's
support for async handlers is not evidence that async database drivers are
needed. A future performance-driven ADR may revisit this only with measured
evidence.

This decision applies only to new food persistence adapters and does not
authorize rewriting inherited repositories. PR2-A does not add SQLAlchemy,
tables, metadata, repositories or engines. Exact dependency versions,
SQLAlchemy module/table organization, row mapping and query conventions are
first-schema implementation concerns.

## 13. Migration coexistence

Historical migrations `0001` through `0021` remain immutable. They continue to
describe the inherited SQLite schema and FamilyFoodOS identity boundary.

New food entities are created beside legacy tables. Specifically:

- do not transform `clients` into household-member tables;
- do not transform `orders` into meal-plan tables;
- do not transform production tables into Prep tables;
- do not reinterpret packaging tables as retail packages;
- retain legacy tables until their bounded contexts have replacements and the
  migration plan authorizes removal.

**DECISION:** Exactly one schema migration authority governs each physical
database and phase. While SQLite is the active vertical-slice persistence, the
existing custom migration runner, ordered lineage and `schema_migrations` truth
remain the sole authority. Later food-table migrations append to that mechanism.
SQLAlchemy Core is runtime persistence only.

Against the active SQLite database, do not run Alembic migrations,
`MetaData.create_all()`, ORM auto-schema creation or any second independent
migration history. Historical migrations remain immutable and new food tables
coexist beside inherited tables.

An explicit later PostgreSQL cutover PR freezes the SQLite custom chain as
source-system history and establishes the PostgreSQL target schema through a
defined baseline/transition. That PR owns the target baseline, required data
migration, verification/reconciliation, PostgreSQL-adapter activation, and
SQLite-lineage freeze/retirement semantics. Alembic then becomes the sole
migration authority for PostgreSQL and subsequent target-schema evolution.
SQLite-specific historical migrations are not replayed against PostgreSQL.

Selecting SQLAlchemy Core does not require adding Alembic now. No physical
database is governed by two independent migration histories. PR2-A creates or
modifies no migration.

## 14. Deployment and tenancy phases

### Phase 1 — Local vertical slice

```text
single dev/test deployment
SQLite
no Auth
fixture Household
```

Prove the deterministic core and repository/UoW boundaries.

### Phase 2 — Functional household MVP

SQLite remains allowed for development and isolated testing. Prove:

```text
Household → Planner → MealPlan → Shopping → Pantry → Prep
```

Auth, PostgreSQL and billing do not block proof of this isolated core.

### Phase 3 — Shared multi-family deployment gate

Before any shared deployment is used by multiple independent families:

```text
PostgreSQL
Auth
tenant isolation
hosted deployment
```

The gate includes authorization and isolation tests. A raw household ID is not
authorization. The exact deployment implementation requires a separately
scoped PR.

### Phase 4 — Paid beta

Add as justified:

```text
billing
subscription tiers
monitoring / hardening
retail / AI feature access
```

Billing remains a commercial concern and does not block early isolated core
validation. Paid beta cannot bypass the shared-deployment gate.

## 15. Cross-context flows

### 15.1 Generate week

```text
Household + members + constraints/preferences
+ Recipe Catalogue
+ Nutrition
+ Pantry
+ history
        ↓
Planner
        ↓
MealPlan + Servings + trace
```

The application service reads a coherent input snapshot, performs deterministic
generation outside the write transaction, then commits the complete plan
aggregate atomically after revalidating required versions.

### 15.2 Build shopping list

```text
MealPlan
↓
RecipeVersion ingredients
↓
scale by Servings
↓
aggregate / normalize
↓
subtract Pantry
↓
ShoppingList
```

The list preserves the recipe and ingredient versions needed for explanation
or reproducibility. It also records the MealPlan revision and Pantry
revision/snapshot used by the Shopping Engine.

### 15.3 Retail enrichment later

```text
ShoppingItem
↓
FoodIngredient
↓
RetailMapping
↓
RetailSKU candidates
↓
PriceSnapshot
↓
package selection
```

Failure or absence at any retail step leaves the generic ShoppingList usable.

### 15.4 Prep

```text
MealPlan
+ recipe prep/freezer metadata
↓
PrepPlan
```

PrepPlan records the source MealPlan revision and Prep Engine version.

### 15.5 Feedback

```text
completed week
↓
structured feedback
↓
preference/history signals
↓
next Planner generation
```

Natural-language interpretation may suggest structured feedback, but the
persisted signal is explicit and reviewable.

### 15.6 Source state, derived snapshots and invalidation

**DECISION:** Authoritative source state includes Household configuration,
published RecipeVersion data, Pantry state/movements, and MealPlan/Serving state
after an accepted generation or explicit user edit. A mutable source aggregate
that feeds persisted derived output exposes a logical revision. At minimum, a
MealPlan has a conceptual revision such as `revision = N`; changing its Serving
or other authoritative plan state advances that revision.

ShoppingList, PrepPlan, printable/PDF output and other persisted materialized
views are derived snapshots. Each records the source revisions/input snapshot
and engine or format version required to identify and reproduce its calculation.
Conceptually:

```text
ShoppingList
  source MealPlan revision
  source Pantry revision or snapshot
  Shopping Engine version

PrepPlan
  source MealPlan revision
  Prep Engine version

printable/PDF artifact
  source MealPlan/ShoppingList/PrepPlan revisions
  artifact format/renderer version
```

Exact physical field names belong to the owning implementation PRs. If a
relevant source revision changes, its derived object is no longer current, is
treated as stale, and must not be presented as current truth until explicitly
regenerated. Old snapshots may remain immutable for useful audit/history; they
are not silently mutated to claim newer inputs.

A Planner generation trace is an immutable record of one planner generation and
the MealPlan revision it produced. Later manual edits do not cause that trace to
reinterpret itself as an explanation of the edited revision. This contract does
not require event sourcing.

Prep execution remains an explicit state-changing workflow:

```text
PrepPlan
        ↓
user confirms execution
        ↓
execution command
        ↓
Pantry movements / prepared inventory changes
```

## 16. Reuse matrix

| Inherited capability | Decision | FamilyFoodOS use |
|---|---|---|
| API-first layering | Reuse as-is as a principle | Keep UI/API/backend ownership and thin HTTP routes |
| Transaction safety | Adapt pattern | Replace raw connection passing above adapters with UoW; retain atomic rollback semantics |
| `AuditLog` | Adapt pattern | Keep bounded, privacy-safe audit of important actions; define food vocabulary separately |
| Backup/export safety | Adapt pattern | Preserve consistent snapshots, no-overwrite publication, verification and truthful partial success; redesign hosted storage later |
| `RecipeVersion` concept | Adapt pattern | Keep immutable/versioned history; replace cosmetic fields and invariants with food provenance, servings, steps and storage metadata |
| Units / Decimal helpers | Adapt pattern | Reuse exact numeric/rounding discipline after food-unit review; do not reuse cosmetic percentage rules |
| Stock movements | Adapt pattern | Use immutable Pantry movements and derived balances where useful |
| FEFO / expiration logic | Adapt pattern | Use expiry-aware household selection; simplify industrial lot UX |
| Import preview/apply | Adapt pattern | Use source/raw/draft/validate/review/apply and idempotency for platform ingestion |
| Client/order/production semantics | Do not reuse | Introduce Household, MealPlan/Serving and Prep as new contexts |
| Packaging semantics | Do not reuse | Retail package metadata belongs to RetailSKU; Prep containers are a separate UX concern if introduced |
| Tax/margin logic | Do not reuse | Food budget, planned/actual spend and waste require new semantics |
| Local launcher | Transitional only | Keep for migration/development while needed; not target consumer delivery |
| Inherited frontend | Transitional/evidence only | Reuse interaction/accessibility lessons; build the separately gated consumer PWA |

## 17. Architectural invariants

1. `AI_ENABLED=false` never breaks the core.
2. Nutrition truth is deterministic and versioned.
3. Planner truth is deterministic and traceable.
4. Shopping quantity truth is deterministic.
5. Household-owned queries and commands are household-scoped.
6. Platform catalogue and household data are distinct.
7. `FoodIngredient != RetailSKU`.
8. `Recipe != Serving`.
9. Price always carries timestamp and provenance.
10. Domain and application services do not depend on database-driver types.
11. Repositories do not independently commit one logical cross-repository command.
12. Legacy CosmeticWorkshopOS entities are not mechanically renamed into food entities.
13. Consumer UI never talks directly to persistence.
14. Production recipes require provenance and verification status.
15. Retail failure never breaks basic MealPlan or Shopping.
16. AI failure never breaks basic MealPlan or Shopping.
17. PostgreSQL, Auth and tenant isolation are a shared-deployment gate, not a prerequisite for proving the local core.
18. PDF and other artifacts are derived state, not product truth.
19. New food persistence remains replaceable behind repository/UoW contracts.
20. A client-supplied identifier never proves authorization.
21. ShoppingList generation never reserves, consumes or mutates Pantry.
22. PrepPlan generation never consumes Pantry or creates prepared/freezer stock.
23. Persisted derived output records source revisions and is stale when relevant
    source revisions change.
24. No physical database is governed by two independent migration histories.
25. Household planning dates use the Household's IANA timezone; true instants
    are persisted in UTC.
26. `CanonicalIngredient` and `FoodIngredient` name one canonical platform food
    concept and must not be implemented as separate entities.

## 18. Material facts, assumptions, decisions and open questions

### FACT

- The current runtime is FastAPI plus direct SQLite persistence and a custom
  sequential migration registry ending at `0021_family_food_identity`.
- Current transaction helpers can share one SQLite connection and roll back
  multi-write workflows.
- Current tests prove transactional audit rollback, movement-derived balances,
  expiration ordering, safe import apply, and consistent SQLite backup patterns.
- Current persistence code contains SQLite-specific driver, SQL, schema
  inspection and filesystem behavior.
- No portable database toolkit or PostgreSQL driver is currently declared.

### ASSUMPTION

- A modular monolith and synchronous application-command model are sufficient
  for the initial food-domain slices.
- The first shared deployment will be multi-family and therefore cannot safely
  retain the no-Auth fixture-household shortcut.

### DECISION

- New food contexts use inward dependency direction, repository interfaces and
  an opaque Unit of Work.
- New food persistence adapters use synchronous SQLAlchemy 2.x Core; inherited
  repositories are not rewritten by this decision.
- SQLite is retained for the vertical slice and isolated MVP development.
- PostgreSQL, Auth and tenant isolation are mandatory before shared families use
  one deployment.
- The existing custom migration lineage is the sole SQLite schema authority;
  Alembic becomes the sole PostgreSQL authority only at explicit cutover.
- Legacy schema coexists unchanged until bounded replacements are verified.
- Persisted derived snapshots carry source revisions and become stale when
  relevant authoritative input changes.

### OPEN QUESTION

PR2-A resolves the persistence technology, migration authority/cutover,
Unit-of-Work semantics, derived-state invalidation, ingredient terminology,
Food Product Type disposition, Household/Auth separation, and UTC versus
household-local calendar semantics.

**Resolve before the first schema implementation PR:**

- integer, UUID or other physical ID representation;
- exact dependency versions;
- SQLAlchemy module/table organization, row mapping and query conventions;
- exact timestamp SQL types and API serialization details;
- SQLite persistence conformance-test layout.

The first schema task must resolve and document these before creating production
food tables; they are not license for silent implementation choices.

**Resolve in the owning bounded-context PR:**

- unit conversion/density policy;
- Recipe publication/verification workflow details;
- aggregate-specific optimistic concurrency;
- Planner trace representation and retention;
- artifact storage implementation;
- Prep execution representation;
- optional Pantry reservation, only if later justified.

**Resolve before shared multi-family deployment:**

- Principal model, HouseholdMembership and authorization roles;
- Auth-context propagation into application commands;
- PostgreSQL adapter conformance and tenant-isolation enforcement;
- hosted backup/restore, production data migration and monitoring/operations.

## 19. PR2-A non-goals

PR2-A does not create production food models, tables, migrations, repositories,
dependencies, APIs or frontend behavior. It does not implement PostgreSQL,
Auth, tenancy middleware, Nutrition, Planner, Shopping, Pantry, Prep, Retail,
AI, PDF, a PWA, retailer research or legacy removal. It modifies no inherited
migration and does not select an exact hosted deployment implementation.
