# ADR 0032 — FamilyFoodOS persistence portability and shared-deployment tenancy gate

## Status

**ACCEPTED FOR PR2-A — NORMATIVE ONLY WHEN PR2-A IS MERGED TO `main`**

Date: `2026-09-01`

## Context

FamilyFoodOS is beginning new food bounded contexts beside an inherited
CosmeticWorkshopOS runtime. ADR 0030 defines a hosted responsive Web/PWA as the
target while retaining the local FastAPI/SQLite stack as transitional
scaffolding.

The inherited runtime proves useful engineering patterns: service-owned
transactions, rollback across multiple writes, immutable movements, recipe
versioning, import preview/apply, audit and safe backup/export workflows. It is
also concretely SQLite-specific. Repository and service signatures expose
SQLite connections and rows; SQL uses SQLite placeholders, schema inspection
and pragmas; sessions commit on context exit; database paths, backup and Restore
assume a local file.

The old migration roadmap grouped PostgreSQL, Auth and Billing in a single late
Paid-Beta/SaaS step. That grouping is not precise enough. The deterministic core
does not need those capabilities to prove product value in an isolated vertical
slice, but a shared deployment serving independent families needs identity,
authorization and tenant isolation before real household data is colocated.

**FACT:** SQLite is the verified current implementation and no portable
persistence toolkit or PostgreSQL driver is declared in the repository.

**FACT:** The current custom sequential migration chain ends at
`0021_family_food_identity`; those historical migrations are required evidence
and upgrade history.

**ASSUMPTION:** The near-term food product remains a modular monolith, so a
database Unit of Work is sufficient and distributed transactions are not
required.

## Decision

### Persistence boundary

New FamilyFoodOS food application/domain services depend on database-agnostic
repository interfaces and an opaque Unit of Work. Concrete persistence adapters
own database sessions, SQL/dialect behavior, row mapping and driver errors.

One write application command owns one Unit of Work, one connection and one
transaction. Every participating repository read and write—including validation
and existence reads—uses that active Unit of Work. Repositories do not open
unrelated connections or commit independently. Failure rolls back the command.
Domain/application APIs do not receive or expose SQLAlchemy `Connection`, DBAPI
connections, `sqlite3.Connection`, transaction handles or raw row types.

Read-only application operations use one consistent read-only Unit of Work or
query scope and do not commit. Pure deterministic calculation runs outside a
write transaction where practical.

SQLite remains the immediate adapter for local development, tests and the
deterministic vertical slice. SQLite-specific APIs remain inside the SQLite
adapter or inherited transitional infrastructure; they are not new domain
assumptions.

The inherited `backend/app/db/session()` helper owns commit-on-context-exit
semantics. It is transitional implementation evidence, not the target food
Unit of Work, and is not modified by PR2-A.

### Persistence adapter technology

New FamilyFoodOS food bounded contexts use **synchronous SQLAlchemy 2.x Core**
for runtime persistence adapters. This decision is limited to new food-domain
persistence and does not authorize rewriting inherited CosmeticWorkshopOS
repositories.

Core provides database-dialect portability between SQLite and future
PostgreSQL, explicit connection/transaction ownership and clean support for the
project-owned Unit of Work. It does not couple domain objects to ORM identity-map
or session lifecycle, uses less machinery than ORM for the current deterministic
domain, and avoids maintaining separate handwritten SQLite and PostgreSQL
repository implementations.

Synchronous access is the baseline for the current backend. Async database
drivers are not introduced merely because FastAPI can expose async handlers; a
future evidence-based performance ADR may revisit the choice. PR2-A does not add
SQLAlchemy or pin a version. Exact dependency versions, module/table layout, row
mapping and query conventions are first-schema implementation concerns.

### Migration coexistence

Exactly one schema migration authority governs each physical database and
phase. While SQLite is the active vertical-slice persistence, the existing
custom migration runner, ordered migration lineage and `schema_migrations`
version truth remain the sole authority. Later food-table migrations append to
that mechanism. SQLAlchemy Core is runtime persistence only.

Do not run Alembic, `MetaData.create_all()`, ORM auto-schema creation or any
second independent migration history against the active SQLite database.
Historical migrations remain immutable. New food tables coexist beside legacy
tables and are never created by transforming `clients`, `orders`, production or
packaging tables.

An explicit later PostgreSQL cutover PR freezes the SQLite custom chain as
source-system history and establishes the PostgreSQL schema through a defined
baseline/transition. That PR defines the target baseline, any required data
migration, verification/reconciliation, PostgreSQL-adapter activation and
SQLite-lineage freeze/retirement semantics. Alembic then becomes the sole
migration authority for PostgreSQL and subsequent target-schema evolution.
SQLite-specific historical migrations are not replayed against PostgreSQL.

Selecting SQLAlchemy Core does not require adding Alembic now. No physical
database is governed by two independent migration histories. This ADR
authorizes no schema or migration change.

### Persisted derived state

Persisted ShoppingList, PrepPlan and printable/PDF outputs are derived snapshots
of versioned source state. They record the source revisions/input snapshot and
engine or renderer version needed to identify their calculation. When a
relevant source revision changes, the snapshot is stale and must not be
presented as current until explicitly regenerated. ShoppingList and PrepPlan
generation do not mutate Pantry; confirmed execution is a separate command.
Planner trace is immutable for the generation/MealPlan revision it describes.

### Shared-deployment gate

PostgreSQL, Auth, tenant isolation and hosted deployment are required before the
first shared multi-family deployment.

They are not prerequisites for proving the isolated deterministic loop:

```text
Household
→ Planner
→ MealPlan
→ Shopping
→ Pantry
→ Prep
```

All household-owned persistence is designed as household-scoped from its first
schema, even while the vertical slice uses one fixture household without Auth.
In a shared deployment, the authorization path is:

```text
authenticated principal
→ authorized household(s)
→ household-scoped application operation
```

A raw client-provided household identifier is not authorization.

### Billing timing

Billing and subscriptions remain later commercial/paid-beta concerns. They do
not block isolated core validation and are not bundled technically with the
earlier shared-deployment safety gate. Paid beta may require billing, but it may
not bypass PostgreSQL/Auth/tenant isolation if families share a deployment.

## Considered alternatives

1. **Keep direct SQLite SQL behind clean interfaces and later build a separate
   PostgreSQL adapter.** This minimizes initial dependencies, but requires
   project-owned transaction plumbing, two SQL implementations, two migration
   strategies and ongoing dialect-conformance work. Rejected for the current
   architecture; changing this requires a superseding decision with evidence.
2. **Use a portable persistence layer for new food contexts only.** Selected as
   the architectural direction. It adds setup and conventions now, but provides
   mature transaction primitives, shared mapping/query code, better adapter
   testing and a smaller SQLite-to-PostgreSQL replacement surface.
3. **Rewrite the inherited runtime onto a new database layer before food work.**
   Rejected because it broadens PR2, risks verified legacy behavior and does not
   create household product value.
4. **Move immediately to PostgreSQL/Auth before the vertical slice.** Rejected
   because the isolated deterministic core has no shared-user requirement and
   should prove value first.
5. **Wait until paid beta to add PostgreSQL/Auth/tenant isolation.** Rejected
   because multiple independent families must not share an unauthenticated,
   weakly scoped SQLite deployment.
6. **Bundle Billing with the shared-deployment gate.** Rejected because payment
   capability is a commercial decision, not a prerequisite for safe early
   shared validation.

## Consequences

- The first food persistence implementation PR will add one SQLAlchemy 2.x
  dependency; PR2-A itself adds none.
- Inherited repositories may remain on direct `sqlite3` while new food
  repositories use SQLAlchemy Core behind different bounded-context adapters.
- New repositories are defined from application needs, return domain/application
  types, never expose driver/toolkit types, and are tested through adapter
  conformance suites.
- Multi-repository write commands use one Unit of Work, one connection and one
  commit or rollback; participating reads share the same scope.
- SQLite remains fast and simple for local/isolated work without leaking into
  the domain contract.
- The custom runner remains the only active SQLite schema authority. Alembic is
  added only by the explicit PostgreSQL cutover PR.
- PostgreSQL adapter activation requires conformance tests while leaving domain,
  application and repository contracts stable.
- New household tables carry an ownership boundary before Auth exists.
- A shared-deployment implementation must add authorization and adversarial
  tenant-isolation tests before independent families use it.
- Billing can be implemented later without weakening the shared-deployment gate.
- The migration period temporarily contains inherited `sqlite3` and new
  SQLAlchemy Core persistence styles behind separate bounded contexts.
- Inherited migrations, launcher, Restore, backup and export behavior are not
  changed by PR2-A.

## Open questions

**OPEN QUESTION — resolve before the first schema implementation PR:**

- physical identifier representation;
- exact SQLAlchemy dependency versions and module/table organization;
- exact timestamp SQL types and API serialization;
- SQLite persistence conformance-test layout.

**OPEN QUESTION — resolve in the owning bounded-context PR:**

- aggregate-specific optimistic concurrency;
- units/density policy, publication workflows, Planner trace retention,
  artifact storage and Prep execution representation.

**OPEN QUESTION — must be resolved before shared deployment:**

- principal, account, household-membership and role model;
- authorization-context propagation into application commands;
- PostgreSQL adapter conformance and tenant-isolation enforcement;
- hosted backup, restore, production data migration, monitoring and operations.

## Scope and supersession

This ADR becomes normative only when PR2-A is merged to `main`.

It refines the persistence/Auth/Billing timing in the migration plan and the
bounded non-authorization language in ADR 0030. It does not change ADR 0030's
hosted Web/PWA target, does not reopen ADR 0031's package retirement and does
not alter inherited Restore, backup, export or artifact safety semantics.

It authorizes no dependency, production code, database schema, migration,
PostgreSQL service, Auth flow, tenancy middleware, Billing feature, deployment,
API or frontend change inside PR2-A.
