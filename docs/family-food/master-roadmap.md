# FamilyFoodOS — Master Roadmap

**Status:** canonical repository sequencing and delivery-gate contract  
**Updated:** `2026-09-02`

## 1. Authority

This document is the repository-local source of truth for FamilyFoodOS product
implementation order and delivery gates. It preserves the later user-approved
Master Roadmap in repository form so that work does not depend on chat memory or
an external Project Source.

Where an older sequence in `docs/family-food/migration-plan.md`,
`docs/family-food/technical-spec.md`, `docs/family-food/data-ingestion.md` or an
older state file conflicts with this roadmap, this roadmap controls sequencing.
The architecture contract in `docs/family-food/architecture.md` and accepted
ADRs continue to control architecture within their scopes.

`docs/family-food/migration-plan.md` remains the authority for migration
strategy, legacy coexistence/replacement discipline, reuse/removal strategy and
historical migration rationale. It must point here rather than compete with
this document on current implementation order.

No agent may materially reorder this roadmap without a later explicit
user-approved decision. A conflict that cannot be reconciled within the
approved order is an open question, not permission to invent a new sequence.

## 2. Verified current state

```text
PR0   Frozen Fork                          COMPLETE
PR1   Identity Detox                       COMPLETE
PR2-A Architecture & Persistence Contract COMPLETE
PR2-B Persistence Foundation               COMPLETE
PR2-C Household Foundation                 COMPLETE
```

PR2-C closure evidence:

- GitHub PR: `#5` — merged;
- accepted head: `13f7c7c480469853579912a7836680afc4734ad7`;
- merge commit: `48c72aeba19a1e6ece0dc729f0a80de930be88a8`;
- merged at: `2026-09-01T21:23:23Z`;
- final project review: `PR2-C FINAL REVIEW: ACCEPT`.

The next product milestone is:

`PR3 — FoodIngredient Catalogue`

`PR2-DOCS — Canonical Roadmap & PR2-C Closure Sync` is a documentation-only
governance operation between PR2-C and PR3. It is not a product milestone and
does not alter the sequence below. PR3 implementation must wait until PR2-DOCS
is reviewed and merged.

## 3. North Star and core-loop contract

FamilyFoodOS exists to remove the recurring cognitive and operational burden of
feeding a household. The product is not a recipe generator and is not an
AI-dietitian. Its recurring product loop is:

```text
Household
→ Members / Preferences / Constraints
→ FoodIngredient Catalogue
→ Recipe Catalogue
→ Nutrition
→ Planner
→ MealPlan
→ individualized Servings
→ Shopping
→ Pantry
→ Prep / Freezer
→ Daily Use
→ Feedback / History
→ Next Week
```

The governing principle is:

> complexity inside the system, simplicity for the user.

The system should propose a useful week and let the user confirm or change it.
It should not move platform catalogue, calculation or infrastructure work into
consumer forms.

The North Star is repeat trust:

> the household trusts FamilyFoodOS to plan the next week again.

The decisive evidence is not the number of recipes, screens, AI requests or
generated plans. It is the repeated loop:

```text
week received
→ week used
→ shopping/prep completed
→ feedback recorded
→ next week requested and trusted
```

## 4. Immutable architecture rules

These rules apply to every milestone unless a later explicit approved decision
changes them:

1. The complete core works with `AI_ENABLED=false`.
2. Critical calculations are deterministic, versioned and backend-owned.
3. LLM output is never authoritative calories, nutrients, quantities, serving
   sizes, allergens, prices, availability or storage duration.
4. Production recipes and nutrition data require verifiable provenance.
5. Dependency direction remains:

   ```text
   UI
   → API
   → application services / domain engines
   → repository interfaces
   → persistence adapters
   → database
   ```

6. New food persistence uses synchronous SQLAlchemy 2.x Core behind repository
   contracts and a project-owned Unit of Work. Domain/application APIs do not
   expose SQLAlchemy, DBAPI or `sqlite3` connection types.
7. The custom ordered migration chain is the sole SQLite schema authority.
   Alembic begins only at the explicit PostgreSQL cutover and is never a second
   authority for the active SQLite database.
8. Legacy CosmeticWorkshopOS contexts coexist until a verified replacement and
   an authorized removal step exist. Mechanical domain renames are forbidden.
9. `FoodIngredient` is the canonical platform food concept.
   `CanonicalIngredient` is its historical alias, not a second aggregate.
10. `FoodIngredient != RetailSKU`; Retail is an optional enrichment layer over
    generic Shopping.
11. `Recipe != Serving`; immutable/versioned recipe truth is distinct from a
    member's allocated portion.
12. Platform catalogue data and Household-owned data are separate. Every
    Household-owned operation is Household-scoped from its first schema.
13. UUID opacity is not authorization. Shared deployment requires an
    authenticated principal, `HouseholdMembership`, authorization and tenant
    isolation.
14. True instants are UTC; planning dates are Household-local calendar dates.
15. ShoppingList generation reads but does not reserve, consume or mutate
    Pantry. PrepPlan generation likewise does not consume Pantry or create
    prepared stock.
16. Persisted derived output records source revisions and engine/renderer
    versions and becomes stale when relevant authoritative input changes.
17. Generic Shopping precedes Retail connectors. Planner never depends on one
    retailer.
18. PostgreSQL, Auth, `HouseholdMembership`, tenant isolation and hosted
    operations are mandatory before multiple real families share one
    deployment. Billing is not part of that safety gate.
19. FamilyFoodOS MVP is not medical treatment and does not claim diagnosis,
    treatment or therapeutic effectiveness.
20. The mobile-first consumer surface keeps platform administration,
    ingestion, SKU matching and audit outside primary navigation.

## 5. Canonical master sequence

```text
✅ PR0   Frozen Fork
✅ PR1   Identity Detox
✅ PR2-A Architecture & Persistence Contract
✅ PR2-B Persistence Foundation
✅ PR2-C Household Foundation

→ PR3   FoodIngredient Catalogue
→ PR4   Recipe Catalogue
→ PR5   Pantry
→ PR6   Nutrition Core
→ PR7   MealPlan / Serving + serving-nutrition integration
→ PR8   Planner v0

──────── GATE 1 — PLANNING CORE ────────

→ PR9   Shopping Engine
→ PR10  Prep / Freezer
→ PR10-PDF Backend Weekly PDF

──────── GATE 2 — MVP0 BACKEND ────────

→ PR11  Consumer PWA Shell
→ PR12  Household Onboarding UX
→ PR13  Today / Week / Shopping / Prep / Pantry UX
→ PR14  PDF / Print UX
→ PR15  Feedback & History v0

──────── GATE 3 — CONSUMER CORE ────────

→ DATA READINESS GATE

→ SHARED-1 PostgreSQL Cutover
→ SHARED-2 Auth + HouseholdMembership
→ SHARED-3 Tenant Isolation + Hosted Operations

──────── GATE 4 — SHARED DEPLOYMENT ────────

→ REAL FAMILY TESTING
   10–30 households
   week → use → feedback → next week

→ DATA PROGRAM — Data Ingestion Platform
→ Catalogue expansion / quality automation

→ RETAIL PROGRAM — Retail Foundation
→ Retail Connector #1

→ Optional AI Gateway

→ Commercial / Billing
→ Production Hardening
→ Additional Retail Connectors
→ Production v1
```

## 6. Canonical terminology and supersessions

### 6.1 PR2 split

The older single milestone `PR2 — Food Domain Foundation` is superseded by the
completed split:

```text
PR2-A Architecture & Persistence Contract
PR2-B Persistence Foundation
PR2-C Household Foundation
```

PR2 must not be represented as one future implementation PR.

### 6.2 FoodIngredient

`FoodIngredient` is the canonical repository-domain name for the platform-owned
food concept. Older references to `CanonicalIngredient` name the same
historical concept; they do not define a second aggregate.

```text
FoodIngredient != RetailSKU
```

`FoodProductType` is not a mandatory MVP aggregate. A later Retail/catalogue
classification may introduce product-form metadata only when a concrete
downstream use case justifies it.

### 6.3 Deterministic core and AI

The core must work with:

`AI_ENABLED=false`

Nutrition, quantities, serving sizes, allergens, prices, availability and
storage truth remain deterministic and provenance-aware. AI is an optional
later gateway for proposal/interpretation work and never becomes critical-path
truth.

### 6.4 Retail ordering

The generic Shopping Engine precedes Retail. Shopping remains useful without a
retailer connector. Retail enrichment maps a `FoodIngredient` to independently
owned `RetailSKU` and timestamped price/availability data.

## 7. Milestone contracts

### PR0 — Frozen Fork — COMPLETE

**Goal:** preserve a reproducible engineering baseline before changing product
identity or domain behavior.

**Delivered:** full Git history, bootstrap tag, source provenance, verified
backend/frontend/package/startup baseline and a clean FamilyFoodOS repository
boundary. PR0 intentionally introduced no FamilyFoodOS runtime domain model.

**Exit evidence:** `bootstrap-cosmetic-workshop-2026-08-31` and
`docs/migration-source.md` preserve the source repository, source commit and
verification baseline.

### PR1 — Identity Detox — COMPLETE

**Goal:** make active project/runtime/launcher/frontend identity FamilyFoodOS
without pretending the inherited CosmeticWorkshopOS business domain had already
been migrated.

**Delivered:** current product paths, environment names, artifact identity,
frontend identity and agent guidance now identify FamilyFoodOS. Remaining
CosmeticWorkshopOS references are bounded legacy/provenance or intentionally
preserved domain code.

**Non-goal preserved:** PR1 did not mechanically rename Client, Order,
ProductionBatch or other inherited business concepts.

### PR2-A — Architecture & Persistence Contract — COMPLETE

**Goal:** freeze the food-domain architecture before schema implementation.

**Delivered:** bounded-context ownership, dependency direction,
repository/Unit-of-Work contract, SQLite/PostgreSQL seam, migration authority,
derived-state invalidation, tenancy boundary, FoodIngredient terminology,
Recipe/Serving separation and shared-deployment safety gate.

**Exit evidence:** `docs/family-food/architecture.md` and ADR 0032 are accepted.

### PR2-B — Persistence Foundation — COMPLETE

**Goal:** implement the portable transaction/persistence foundation without a
production food schema.

**Delivered:** synchronous SQLAlchemy 2.x Core, driver-independent Unit of Work,
SQLite engine conventions, UUIDv4 identity and UTC instant persistence while
the custom migration chain remained sole SQLite schema authority.

**Tests/exit:** transaction terminality, rollback isolation, pooled-command
cleanliness, foreign keys, UUID and UTC persistence passed final adversarial
review: `PR2-B FINAL REVIEW: ACCEPT`.

### PR2-C — Household Foundation — COMPLETE

**Goal:** implement the first production FamilyFoodOS bounded context beside
legacy schema.

**Delivered data/capabilities:**

- `Household` with UUIDv4 identity, name, IANA timezone, optional city, exact
  weekly budget, generic cooking profile and UTC timestamps;
- `HouseholdMember` with Household ownership, stable profile fields and UTC
  timestamps;
- Household-scoped repository operations and bounded-context UoW/read scope;
- migration `0022_household_foundation` after `0021_family_food_identity`;
- create/read/update API and the complete three-member acceptance path.

**Non-goals preserved:** no Auth, fake `owner_id`, PostgreSQL, Alembic, ORM,
async persistence, Client reuse, FoodIngredient or later product context.

**Exit evidence:** GitHub PR `#5`, accepted head
`13f7c7c480469853579912a7836680afc4734ad7`, merge commit
`48c72aeba19a1e6ece0dc729f0a80de930be88a8`, and
`PR2-C FINAL REVIEW: ACCEPT`.

### PR3 — FoodIngredient Catalogue

PR3 introduces the canonical platform-owned food catalogue. It is not
Household-owned.

Minimum model/capabilities:

```text
FoodIngredient
IngredientAlias
FoodNutritionProfile, or an equivalent provenance representation
IngredientUnitProfile, only where genuinely required
```

The slice supports:

- canonical code and name;
- category and default unit;
- optional density and edible fraction;
- nutrition/macros/fiber, either directly represented or through a referenced
  nutrition profile;
- nutrition source, version and provenance;
- allergen metadata;
- storage metadata/profile;
- activate/deactivate behavior and timestamps;
- name and alias lookup;
- idempotent seed/import.

The PR3 technical slice contains `80–120 FoodIngredient` records. The broader
MVP catalogue target remains approximately `250–350`, but PR3 does not attempt
full catalogue automation.

Application/persistence capabilities include a focused
`FoodIngredientRepository`, catalogue service/query operations, alias-aware
lookup and one bounded idempotent seed/import path. Ordinary Household users do
not own or manually create platform catalogue truth.

Required PR3 verification includes:

- idempotent seed/import;
- alias lookup;
- unit validation;
- Decimal semantics;
- required nutrition provenance;
- duplicate prevention;
- deactivation behavior;
- no `RetailSKU` coupling.

PR3 non-goals:

- `RetailSKU`, retailer parsing or retailer prices;
- full ingestion automation;
- Recipe or Pantry;
- Nutrition Engine calculations;
- Planner;
- AI.

PR3 continues the accepted persistence contract: synchronous SQLAlchemy 2.x
Core behind repository contracts and a Unit of Work, SQLite through the custom
migration chain, and the next migration after `0022`. No ORM, async database
layer, Alembic, PostgreSQL, Auth, Retail or AI belongs in PR3.

**Exit criteria:** the `80–120` item slice can be seeded repeatedly without
duplicates; canonical and alias lookup works; invalid units/numbers are safely
rejected; nutrition provenance is mandatory; deactivation is deterministic;
and no schema, repository, API or seed couples `FoodIngredient` to RetailSKU.

### PR4 — Recipe Catalogue

**Goal:** introduce the verified platform recipe catalogue used by Nutrition,
Planner, Shopping and Prep.

**Data/capabilities:**

```text
Recipe
→ immutable/versioned RecipeVersion
→ RecipeIngredient → FoodIngredient
→ ordered RecipeStep
```

Recipe versions carry original/base servings, meal type, preparation/cooking
time, equipment, difficulty, batch/freezer/storage metadata and verifiable
source/rights/verification status. Publishing creates or selects an immutable
version; it does not silently rewrite historical truth.

**Services/persistence:** focused recipe repository contracts and catalogue
operations load structured recipes, version history, ingredient quantities and
steps without exposing database rows. The initial technical corpus is
`30 verified recipes` whose required ingredients resolve to PR3 catalogue data.

**Tests:** version immutability, ingredient/step ordering, deterministic serving
scaling, required FoodIngredient references, provenance/verification rules,
archive/deactivate behavior and transaction rollback.

**Non-goals:** no Planner, MealPlan, Serving, Shopping, Retail, AI-generated
production truth or cosmetic 100-percent/phase invariants.

**Exit criteria:** 30 structured, verified recipes can be loaded and scaled;
every required ingredient resolves to one FoodIngredient; source/rights and
verification status are reviewable; historical versions remain unchanged.

### PR5 — Pantry

**Goal:** introduce simple Household-owned food-at-home state before Shopping
and Planner consume Pantry facts.

**Data/capabilities:** `PantryItem` and immutable `PantryMovement`, scoped by
Household and FoodIngredient, with quantity/unit, Pantry/Fridge/Freezer
location, estimated flag and relevant purchase/open/expiry facts. A bounded lot
representation is allowed only if it creates real household value.

**Services:** add, consume, adjust, waste and query available/expiring stock.
Balances derive from or are reconciled with movements; negative stock is
rejected; expiry-aware/FEFO selection may be adapted from inherited patterns.

**Tests:** Household isolation, unit validation, movement atomicity,
non-negative protection, expiry ordering, rollback and a simple
`buy 10 eggs → consume 4 → balance 6` flow.

**Non-goals:** no industrial supplier/lot workflow, RetailSKU ownership,
shopping-list generation, automatic purchase ingestion or computer vision.

**Exit criteria:** a Household can maintain understandable Pantry state through
transactional movements without exposure to industrial inventory concepts.

### PR6 — Nutrition Core

PR6 owns the deterministic Nutrition Core only through:

```text
FoodIngredient nutrition
→ RecipeVersion nutrition
→ Member target formula/config foundation
```

PR6 does not require `Serving`; Serving does not exist until PR7. Formulas,
rounding/configuration versions, provenance and deterministic test coverage
belong here.

**Capabilities/services:** normalize FoodIngredient nutrition data, calculate
RecipeVersion totals/per-base-serving values, and establish versioned member
target formula/config foundations. Results expose bounded warnings and explicit
uncertainty rather than invented precision.

**Tests:** deterministic repeated output, unit conversion, Decimal/rounding
boundaries, ingredient-to-recipe aggregation, provenance propagation, formula
versioning and representative adult/child fixture targets.

**Non-goals:** Serving, member/day/week aggregation, Planner optimization,
medical diagnosis/treatment, LLM calculation or undocumented nutrition truth.

**Exit criteria:** FoodIngredient and RecipeVersion nutrition plus member target
foundation are deterministic, versioned, provenance-aware and usable by PR7.

### PR7 — MealPlan / Serving + serving-nutrition integration

PR7 introduces `MealPlan`, its day/slot structure and individualized `Serving`.
It integrates:

```text
RecipeVersion nutrition
→ Serving nutrition
→ Member/day totals
→ week aggregates
```

MealPlan history begins with this context. PR15 later owns structured feedback
and personalization history.

**Data/capabilities:** `MealPlan`, `MealPlanDay`, `MealSlot` and `Serving`, with
Household ownership, week start/local planning dates, selected immutable
RecipeVersion references, per-member allocations, status and source/config
revision references.

**Services:** manually assemble/read/update one coherent seven-day plan,
calculate Serving nutrition from RecipeVersion nutrition, and aggregate
member/day/week totals. A plan revision advances when authoritative plan or
Serving state changes.

**Tests:** Household scoping, local-date semantics, Recipe/Serving separation,
different allocations for different members, Serving nutrition, day/week
aggregation, source-version retention, atomic persistence and stale-derived
state signaling.

**Non-goals:** automatic plan generation, ShoppingList, PrepPlan, Retail or AI.

**Exit criteria:** a three-member Household can be assigned a complete
structured week manually, with individualized Servings and reproducible
nutrition totals.

### PR8 — Planner v0

PR8 provides the simplest useful deterministic week planner: hard filtering,
bounded scoring/heuristics, complete seven-day output and traceable candidate,
rejection, score, selection and warning evidence. Advanced optimization must
prove value over this baseline.

**Inputs:** Household/member constraints, exclusions/preferences, candidate
RecipeVersions, Nutrition, Pantry, recent MealPlan history, budget/cooking
constraints and planning mode.

**Output/services:** one complete seven-day MealPlan with individualized
Servings plus a durable/reproducible trace containing planner/config version,
candidate pool, constraints, rejected candidates/reasons, scores, selections,
warnings and duration.

**Tests:** deterministic repeatability, exclusion enforcement, complete-week
generation, member allocation, candidate rejection reasons, trace
reproducibility, constrained failure reporting and fixture-household variation.

**Non-goals:** OR-Tools or another advanced solver without measured benefit,
Retail dependence, AI decisions, ShoppingList or PrepPlan.

**Exit criteria:** all Gate 1 criteria below pass.

### GATE 1 — Planning Core

Before continuing, the repository must prove a deterministic, traceable path
from Household and catalogue data through Recipe/Nutrition to a complete
MealPlan with individualized Servings.

Gate 1 is passed only when all of the following are true:

- `3 fixture households` cover materially different household constraints;
- the active fixture corpus contains `30 verified recipes`;
- the catalogue contains `80+ FoodIngredient` records;
- Planner v0 is deterministic for identical inputs and configuration;
- allergies, exclusions and hard constraints are respected;
- every fixture receives a complete seven-day week or an explicit bounded
  failure instead of a partial silent result;
- Servings are individualized for Household members;
- the planner trace is persisted or otherwise reproducible and explains the
  candidate pool, rejections, scores, selections and warnings.

Passing isolated unit tests is necessary but not sufficient: the complete
fixture path must be exercised through repository-backed application services.

### PR9 — Shopping Engine

PR9 implements the generic flow:

```text
MealPlan
→ scale RecipeIngredients
→ normalize and aggregate
→ subtract Pantry
→ ShoppingList
```

**Capabilities/services:** scale immutable RecipeVersion ingredient quantities
through actual Servings, normalize compatible units, aggregate by
FoodIngredient, subtract available Pantry quantities, preserve unresolved or
non-convertible items as explicit warnings, and create a Household-owned,
revisioned ShoppingList.

**Data:** ShoppingList, ShoppingListItem and source revision/version references
sufficient to reproduce or mark the list stale. A list item points to a
FoodIngredient or is explicitly unresolved; it does not point to RetailSKU.

**Tests:** deterministic scaling/aggregation, compatible and incompatible unit
handling, Pantry subtraction without Pantry mutation, duplicate collapse,
rounding/Decimal boundaries, Household isolation, stale-source detection and
the Gate 2 fixture flow.

**Non-goals:** RetailSKU, prices, retailer availability, retailer parsing,
cart integration, Pantry reservation/consumption or AI.

**Exit criteria:** a complete MealPlan produces a reviewable ShoppingList whose
quantities are reproducible, Pantry-aware and useful without any retailer.

### PR10 — Prep / Freezer

**Goal:** turn the selected week into a feasible preparation/freezer plan using
recipe batch, storage, freezer, equipment and timing metadata.

**Capabilities/services:** group reusable prep work, suggest batch quantities,
sequence preparation tasks, surface storage/freezer instructions and warnings,
and create a revisioned PrepPlan linked to its authoritative inputs.

**Tests:** deterministic grouping and order, batch scaling, storage/freezer
metadata, Household isolation, source-revision staleness and no side effects
during generation.

Plan generation does not consume Pantry, create prepared stock or claim work
was completed. Confirmed execution remains a separate state-changing workflow.
Retail, industrial production scheduling and AI optimization are non-goals.

**Exit criteria:** the Gate 2 household receives a coherent PrepPlan that can be
regenerated from the same authoritative inputs without hidden state changes.

### PR10-PDF — Backend Weekly PDF

PR10-PDF adds the reproducible backend Weekly PDF from authoritative MealPlan,
ShoppingList and PrepPlan state. It includes the week overview, individualized
servings where needed, Shopping and Prep information, and sufficient generation
metadata to identify its source revisions and renderer/template version.

The PDF is derived/versioned output, not a source of truth. A changed MealPlan,
Pantry-sensitive ShoppingList or PrepPlan marks an older artifact stale; it is
not silently presented as current. PDF rendering is backend-owned and works
without the PWA, AI or Retail.

**Tests/exit:** deterministic fixture generation, required sections/content,
source/version metadata, stale detection and a readable backend artifact for
the exact Gate 2 vertical slice. Consumer download/print presentation waits for
PR14.

### GATE 2 — MVP0 Backend

The complete backend vertical slice works before consumer-PWA implementation:

```text
Household
→ Members
→ Planner
→ 7-day MealPlan
→ Serving calculation
→ ingredient aggregation
→ Pantry subtraction
→ ShoppingList
→ PrepPlan
→ PDF
```

Mandatory runtime conditions:

```text
AI_ENABLED=false
RetailConnector=none
```

Exact acceptance fixture:

- `1 Household`;
- `3 members`;
- `30 verified recipes`;
- `80–120 FoodIngredient`.

The fixture must produce a complete seven-day plan, individualized servings,
nutrition, Pantry-aware ShoppingList, PrepPlan and backend PDF through the real
repository/application-service path. No PWA, Auth, Retail connector or AI call
may be necessary to pass Gate 2.

### PR11 — Consumer PWA Shell

**Goal:** establish the mobile-first installable consumer shell only after the
MVP0 backend gate is real.

**Capabilities:** app routing/navigation, loading/error/empty/offline-aware
states, API integration boundary, accessibility baseline and the primary
consumer sections Today, Week, Shopping, Prep and Pantry. Administrative
catalogue, ingestion and retailer-matching work remains outside primary
navigation.

**Non-goals:** onboarding workflow, full weekly interactions, Auth, admin UI,
Retail, AI or moving authoritative calculations into the frontend.

**Tests/exit:** supported mobile widths and responsive desktop behavior,
keyboard/focus/accessibility baseline, routing, installability, API
loading/error/empty states and no horizontal page overflow. The shell is ready
for PR12/PR13 without embedding future business logic.

### PR12 — Household Onboarding UX

**Goal:** let a Household establish the minimum product facts required to
receive a useful week: household profile, members, constraints/exclusions,
preferences, budget/cooking context and relevant Pantry starting state.

Before Auth, this is product/Household setup, not account-registration or
authentication onboarding. The UI uses the backend Household boundary and does
not invent authorization semantics.

**Tests/exit:** a new local/single-Household user can complete, revisit and
correct onboarding with accessible validation and no requirement for Auth,
Retail, AI or platform catalogue administration.

### PR13 — Today / Week / Shopping / Prep / Pantry UX

**Goal:** expose the normal weekly operating surfaces over the deterministic
backend.

The user can generate/view the week, use Today and Week, change a meal, see the
dependent Shopping state recalculate, maintain Pantry, follow Prep and complete
the ordinary consumer flow without editing platform catalogue data.

**Tests:** mobile/responsive and accessibility behavior, loading/error/empty
states, meal-change invalidation/recalculation, Shopping and Pantry
interactions, Prep visibility and an end-to-end fixture path.

### PR14 — PDF / Print UX

PR14 exposes consumer download/print behavior over the backend artifact already
created in PR10-PDF. It handles current/stale state, regeneration affordance,
download and print presentation. It does not own backend PDF generation or
recalculate authoritative weekly data in the frontend.

**Tests/exit:** current and stale artifact states, regeneration request,
download, browser print, readable A4 output and accessible consumer controls.
Backend rendering, renderer/persistence ownership, Retail and AI are non-goals.

### PR15 — Feedback & History v0

PR15 introduces structured signals such as liked, disliked, skipped, replaced,
leftover and repeat requested, plus deterministic history/personalization input
for the next week.

**Data/capabilities:** structured MealFeedback plus the smallest justified
Household/member recipe or ingredient preference projections. Every feedback
event retains its Household, MealPlan/meal and RecipeVersion context where
applicable, and projections can be deterministically rebuilt.

Feedback is Household/member/meal/version scoped where relevant and preserves
the difference between an event and a derived preference. MealPlan history that
began in PR7 remains authoritative; PR15 makes completed-week and structured
feedback history usable by the next planning cycle.

**Tests/exit:** finish-week behavior, structured-signal validation, historical
RecipeVersion reference retention, Household isolation, deterministic next-week
input and the complete Gate 3 repeated loop. PR15 exists before real-family
testing and before Retail.

### GATE 3 — Consumer Core

The complete consumer loop must work through the mobile-first PWA:

```text
Household onboarding
→ generate week
→ use Today / Week
→ change a meal
→ receive recalculated Shopping
→ maintain/use Pantry
→ follow Prep
→ download or print PDF
→ finish week
→ record structured feedback
→ generate the next week using History / Feedback
```

The loop must be understandable and operable without platform-admin forms,
Retail or AI. Passing Gate 3 does not authorize shared real-family testing:
Data Readiness and Gate 4 still follow.

## 8. Data Readiness Gate

Data Readiness is a quality gate, not the complete automated Data Ingestion
Platform. Before real-family testing, the active catalogue must provide:

- `50–80+ verified recipes` suitable for the intended test households;
- complete required `FoodIngredient` resolution;
- `100%` required FoodIngredient coverage for the active recipe corpus;
- valid nutrition source/version/provenance for required nutrition data;
- no unresolved required ingredients;
- no critical sanity-validation errors;
- reviewable RecipeVersion source provenance and rights status;
- reasonable weekly variety across the active corpus;
- progress toward the broader FoodIngredient target of approximately
  `250–350`, with that broader target explicit rather than hidden inside PR3.

Bounded seed/import, curation and review work may satisfy this gate. Data
Readiness does not require the complete automated Data Ingestion Platform; that
platform belongs to the later Data Program. Conversely, an ingestion pipeline
existing is not proof that the active catalogue passes these quality checks.

## 9. Shared-deployment sequence and gate

Before multiple independent real families use one shared deployment, complete:

### SHARED-1 — PostgreSQL Cutover

Define and verify the PostgreSQL target baseline, data migration/reconciliation,
adapter conformance and SQLite-lineage freeze/retirement rules. Alembic may
become the PostgreSQL authority only at this explicit cutover.

Exit requires repository/UoW contract conformance on PostgreSQL, an explicit
and rehearsed migration path, row/count/invariant reconciliation, rollback or
recovery procedure, backup/restore evidence and no accidental second schema
authority over the former SQLite lineage.

### SHARED-2 — Auth + HouseholdMembership

Add authenticated principals, `HouseholdMembership`, roles/authorization and
trusted propagation of authorized Household scope. A client-provided
`household_id` is never proof of authorization.

Tests cover membership creation/removal, role boundaries, missing/invalid
principal behavior, cross-Household denial and application-service/repository
scope propagation. Auth is introduced here, not retrofitted into pre-Auth
onboarding semantics.

### SHARED-3 — Tenant Isolation + Hosted Operations

Prove adversarial tenant isolation and establish the hosted operational
baseline, including deployment, secrets, backup/restore, monitoring and safe
migration operations appropriate to the shared environment.

Isolation must be verified across reads, writes, generated artifacts, history,
background/operational paths and failure messages. Hosted operations include
least-privilege secret handling, health/observability, restore rehearsal,
migration safety, incident ownership and a documented support baseline.

### GATE 4 — Shared Deployment

```text
PostgreSQL
+ Auth
+ HouseholdMembership / authorization
+ tenant isolation
+ hosted operational baseline
```

must be verified before shared-family testing. Billing is not part of this
safety gate and remains later. Gate 4 passes only with documented evidence for
PostgreSQL cutover/reconciliation, Auth and HouseholdMembership authorization,
adversarial tenant isolation, deployability, monitoring and backup/restore.

## 10. Validation and downstream programs

### Real Family Testing

After Consumer Core, Data Readiness and Shared Deployment gates, test with
`10–30 households` through the full repeated loop:

```text
week → use → feedback → next week
```

Isolated/local single-Household validation may occur earlier, but it must not be
described as shared real-family testing.

Testing records week generation, actual use, replacements, Shopping/Pantry/Prep
friction, completion, structured feedback and whether the Household requests
and trusts the next week. Safety, support and rollback paths stay active
throughout the cohort; the cohort is not a shortcut around Gate 4.

### Data Program

After core/shared-family validation, build the full Data Ingestion Platform and
catalogue-expansion/quality automation. Untrusted parsed data still follows the
draft/normalize/validate/review or explicit trusted-source policy.

The program may add source adapters, raw snapshots, parsing, entity resolution,
unit normalization, provenance, quality rules, review queues, publication,
versioning and refresh/retirement operations. It automates maintenance of
already-defined canonical concepts; it does not make parsed data production
truth or redefine FoodIngredient as a retailer product.

### Retail Program

After the generic Shopping Engine and Data Program, introduce Retail Foundation
and then one Retail Connector. Keep `FoodIngredient`, `RetailSKU` and
`PriceSnapshot` separate.

Retail Foundation owns connector abstractions, explicit ingredient/SKU match
confidence and review, package/unit conversion, timestamped price/availability
snapshots and failure isolation. Connector #1 proceeds only against a researched
and permitted integration path; one retailer must never become a Planner or
generic Shopping dependency.

### Optional AI, Commercial and production

The remaining order is:

```text
Optional AI Gateway
→ Commercial / Billing
→ Production Hardening
→ Additional Retail Connectors
→ Production v1
```

Billing does not retroactively become part of the shared-deployment gate. AI
remains optional, and external retailer/AI failures never break the generic
core.

The Optional AI Gateway is allowed only after a useful deterministic product
exists. It may assist with parsing, natural-language input, feedback, matching,
explanations and proposals behind deterministic validation and explicit failure
handling. It must remain disableable.

Commercial/Billing begins only after shared safety and evidence of recurring
value. Production Hardening then closes operational, security, privacy,
performance, accessibility and support gaps demonstrated by actual use.
Additional Retail Connectors remain individually justified rather than a
precondition for initial value or Paid Beta.

## 11. End-to-end acceptance fixtures

Fixtures are product evidence, not merely seed convenience. They use stable
identifiers/data, run through public application/repository boundaries and are
kept deterministic enough to reproduce a failure.

### Fixture set A — Planning Core

The Gate 1 set contains `3 fixture households`, `30 verified recipes` and
`80+ FoodIngredient`:

1. a general three-member Household with differing serving needs;
2. a Household with material allergy/exclusion constraints;
3. a Household with tighter budget, time/equipment or variety constraints.

All receive a complete valid week or an explicit bounded infeasibility result,
with individualized Servings and a reproducible planner trace.

### Fixture set B — MVP0 Backend

The exact Gate 2 vertical fixture is:

```text
1 Household
3 members
30 verified recipes
80–120 FoodIngredient
AI_ENABLED=false
RetailConnector=none
```

It executes:

```text
Household → Members → Planner → 7-day MealPlan → Serving calculation
→ ingredient aggregation → Pantry subtraction → ShoppingList → PrepPlan → PDF
```

### Fixture set C — Consumer repeat loop

The Gate 3 fixture onboards a Household, generates a week, uses Today/Week,
changes a meal, observes recalculated Shopping, uses Pantry and Prep,
downloads/prints PDF, finishes the week, records structured feedback and
generates the next week from retained History/Feedback.

### Fixture set D — Shared deployment

Gate 4 uses at least two independently authenticated Household tenants and
adversarially proves that neither can read, change, infer or receive artifacts
from the other. It also exercises deployment, migration, monitoring and
backup/restore evidence on the shared PostgreSQL environment.

## 12. Phase Definition of Done

A milestone or gate is done only when its specified outcome exists in the
repository and its evidence is reviewable. Unless a milestone explicitly says
otherwise, Definition of Done includes:

- accepted domain/application/persistence boundaries and migrations where data
  changes;
- deterministic behavior for authoritative calculations;
- positive, negative, isolation, rollback and regression coverage appropriate
  to the slice;
- fixtures and seed/import operations that are repeatable and provenance-aware;
- user-visible errors/warnings rather than silent partial truth;
- updated canonical documentation and state/handoff evidence;
- no secrets, private user data or undocumented operational dependency;
- no future-milestone coupling introduced to make the current slice pass;
- relevant static, test, build and smoke checks recorded exactly;
- adversarial review acceptance and merge before the next milestone begins.

Gate completion additionally requires its full end-to-end fixture, not an
assumption that independently passing component tests compose into the product
loop.

## 13. Sequencing safeguards

### Later capabilities must not block earlier stages

- Auth, PostgreSQL and hosted multi-tenancy must not block local/single-
  Household core validation; they become mandatory at the shared-deployment
  gate.
- Billing must not block shared-deployment safety or value validation.
- Retail connectors, prices and carts must not block generic Shopping.
- AI must not block any core, consumer, shared-deployment or production path;
  `AI_ENABLED=false` remains valid.
- Full ingestion automation must not block Planning/Core validation or Data
  Readiness when bounded curated data satisfies the explicit quality gate.
- Consumer PWA work must not block proving the MVP0 backend vertical slice.
- Advanced optimization must not block Planner v0.
- `FoodProductType` must not block the FoodIngredient Catalogue without a
  concrete downstream use case.

### Foundational obligations must not be postponed

- deterministic calculation, Decimal/unit semantics, provenance and versioning
  are introduced with the first authoritative data they govern;
- Household scoping begins with every Household-owned schema and repository;
- RecipeVersion immutability and FoodIngredient resolution begin with Recipe;
- planner traceability begins with Planner v0;
- derived-state source revisions/staleness begin with Shopping, Prep and PDF;
- structured Feedback/History exists before real-family testing and Retail;
- Data Readiness is measured before shared real-family testing;
- PostgreSQL, Auth, HouseholdMembership, tenant isolation and hosted operations
  are proven before multiple real families share a deployment;
- legal/privacy and production operational readiness are closed before the
  corresponding commercial/production exposure.

These rules prevent both premature infrastructure and deferred correctness.

## 14. Roadmap PR discipline

Each product milestone is a small reviewable PR or an explicitly approved,
bounded PR series with one outcome. A PR states context, goal, scope,
non-goals, architecture/data/API/frontend impact, tests, acceptance criteria,
risks and final evidence.

The normal order is:

```text
read canonical contracts
→ inspect existing code/tests and legacy assumptions
→ implement only the current milestone
→ run proportional verification
→ update durable docs/state
→ adversarial review
→ merge
→ begin the next milestone
```

Parallel agents may work only inside the current authorized milestone/gate or
on explicitly bounded research, QA, fixture/data preparation and supporting
work that does not implement a future product milestone. Parallel capacity is
not authorization to skip sequence: Planner implementation waits for PR8,
Consumer PWA for Gate 2/PR11, Retail for its later program and AI remains
optional and later.

A documentation/governance PR such as PR2-DOCS may occur between milestones to
synchronize already-approved decisions. It does not acquire a product milestone
number or silently change delivery order.

## 15. Decision and roadmap-change protocol

Only a later explicit user-approved decision may change this sequence, a gate
or an immutable rule. A proposed change must:

1. identify the exact existing contract and evidence creating pressure to
   change it;
2. state affected milestones, gates, architecture, migrations, fixtures,
   security and product risks;
3. distinguish correction/clarification from a substantive reorder;
4. update this roadmap plus affected architecture/ADR/domain/state documents in
   one reviewable governance change;
5. preserve superseded wording as historical provenance where useful and remove
   it as active instruction;
6. receive explicit approval before implementation depends on the new order.

If documents conflict and no approved resolution exists, record an `OPEN
QUESTION`; do not choose a new roadmap through code or an implementation PR.

## 16. Agent read and use protocol

Before significant work, an agent reads:

```text
AGENTS.md
→ docs/family-food/project-operating-manual.md
→ state/current-focus.md
→ docs/family-food/master-roadmap.md
→ relevant architecture / ADR / domain documents
→ relevant source code and tests
→ state/handoff.md when continuing work
```

The agent identifies the current milestone, its prior gate, dependencies,
non-goals and exit evidence before editing. It treats legacy source/history as
engineering provenance rather than current product specification and checks any
nested `AGENTS.md` in scope. Durable decisions go under `docs/`; execution state
goes under `state/`; chat memory is never the only source.

At handoff, record what was verified, exact commits/migrations/checks, unresolved
risks and the next authorized action. “Next milestone” does not mean “may start
before the current PR is accepted and merged.”

## 17. Final master path

The final product path is:

```text
deterministic household planning core
→ generic Shopping / Prep / backend PDF
→ usable consumer repeat loop with Feedback / History
→ explicit catalogue Data Readiness
→ safe shared PostgreSQL/Auth/tenancy operations
→ evidence from 10–30 real households
→ scalable data maintenance
→ optional Retail enrichment
→ optional AI assistance
→ Commercial / Billing after value and safety
→ Production Hardening
→ justified additional connectors
→ Production v1
```

The final product remains a household system that repeatedly earns trust in the
next week, not a collection of disconnected recipes, integrations or AI demos.
