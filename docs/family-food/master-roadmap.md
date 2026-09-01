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

## 3. Canonical master sequence

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

## 4. Canonical terminology and supersessions

### 4.1 PR2 split

The older single milestone `PR2 — Food Domain Foundation` is superseded by the
completed split:

```text
PR2-A Architecture & Persistence Contract
PR2-B Persistence Foundation
PR2-C Household Foundation
```

PR2 must not be represented as one future implementation PR.

### 4.2 FoodIngredient

`FoodIngredient` is the canonical repository-domain name for the platform-owned
food concept. Older references to `CanonicalIngredient` name the same
historical concept; they do not define a second aggregate.

```text
FoodIngredient != RetailSKU
```

`FoodProductType` is not a mandatory MVP aggregate. A later Retail/catalogue
classification may introduce product-form metadata only when a concrete
downstream use case justifies it.

### 4.3 Deterministic core and AI

The core must work with:

`AI_ENABLED=false`

Nutrition, quantities, serving sizes, allergens, prices, availability and
storage truth remain deterministic and provenance-aware. AI is an optional
later gateway for proposal/interpretation work and never becomes critical-path
truth.

### 4.4 Retail ordering

The generic Shopping Engine precedes Retail. Shopping remains useful without a
retailer connector. Retail enrichment maps a `FoodIngredient` to independently
owned `RetailSKU` and timestamped price/availability data.

## 5. Milestone contracts

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

### PR4 — Recipe Catalogue

PR4 introduces the platform production recipe catalogue with versioned
`Recipe`, immutable/publishable `RecipeVersion`, `RecipeIngredient` references
to `FoodIngredient`, structured `RecipeStep` data and source/verification
provenance. It replaces cosmetic recipe invariants rather than renaming them.

### PR5 — Pantry

PR5 introduces Household-owned Pantry state and movements. It adapts useful
transaction, non-negative balance, expiry and FEFO patterns without imposing
industrial lot-accounting UX on a household.

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

### PR8 — Planner v0

PR8 provides the simplest useful deterministic week planner: hard filtering,
bounded scoring/heuristics, complete seven-day output and traceable candidate,
rejection, score, selection and warning evidence. Advanced optimization must
prove value over this baseline.

### GATE 1 — Planning Core

Before continuing, the repository must prove a deterministic, traceable path
from Household and catalogue data through Recipe/Nutrition to a complete
MealPlan with individualized Servings.

### PR9 — Shopping Engine

PR9 implements the generic flow:

```text
MealPlan
→ scale RecipeIngredients
→ normalize and aggregate
→ subtract Pantry
→ ShoppingList
```

It has no `RetailSKU`, retailer or scraping dependency. Shopping-list
generation reads but does not mutate Pantry.

### PR10 — Prep / Freezer

PR10 produces deterministic Prep/Freezer plans from MealPlan and recipe
metadata. Plan generation does not consume Pantry or create prepared stock;
confirmed execution remains a separate state-changing workflow.

### PR10-PDF — Backend Weekly PDF

PR10-PDF adds the reproducible backend Weekly PDF from authoritative MealPlan,
ShoppingList and PrepPlan state. The PDF is derived/versioned output, not a
source of truth. It belongs to the MVP0 backend before the consumer PWA.

### GATE 2 — MVP0 Backend

The complete backend vertical slice works without AI or Retail and can produce
a printable weekly artifact before consumer-PWA implementation begins.

### PR11–PR13 — Consumer foundation and weekly UX

PR11 creates the mobile-first Consumer PWA shell. PR12 implements Household
Onboarding UX; before Auth, this is product/household setup, not account
registration or authentication onboarding. PR13 makes Today, Week, Shopping,
Prep and Pantry flows usable from the PWA.

### PR14 — PDF / Print UX

PR14 exposes consumer download/print behavior over the backend artifact already
created in PR10-PDF. It does not own backend PDF generation.

### PR15 — Feedback & History v0

PR15 introduces structured signals such as liked, disliked, skipped, replaced,
leftover and repeat requested, plus deterministic history/personalization input
for the next week. It exists before real-family testing and before Retail.

### GATE 3 — Consumer Core

The consumer can onboard a Household, use the week, shop, prep, use/print the
backend PDF, record structured feedback and begin the next-week loop.

## 6. Data Readiness Gate

Data Readiness is a quality gate, not the complete automated Data Ingestion
Platform. Before real-family testing, the active catalogue must provide:

- enough verified recipes for a useful and sufficiently varied test;
- complete `FoodIngredient` resolution for active recipes;
- valid nutrition sources, versions and provenance;
- no critical catalogue gaps for the intended test households.

Bounded seed/import and review work may satisfy the gate. The full ingestion
automation platform belongs to the later Data Program.

## 7. Shared-deployment sequence and gate

Before multiple independent real families use one shared deployment, complete:

### SHARED-1 — PostgreSQL Cutover

Define and verify the PostgreSQL target baseline, data migration/reconciliation,
adapter conformance and SQLite-lineage freeze/retirement rules. Alembic may
become the PostgreSQL authority only at this explicit cutover.

### SHARED-2 — Auth + HouseholdMembership

Add authenticated principals, `HouseholdMembership`, roles/authorization and
trusted propagation of authorized Household scope. A client-provided
`household_id` is never proof of authorization.

### SHARED-3 — Tenant Isolation + Hosted Operations

Prove adversarial tenant isolation and establish the hosted operational
baseline, including deployment, secrets, backup/restore, monitoring and safe
migration operations appropriate to the shared environment.

### GATE 4 — Shared Deployment

```text
PostgreSQL
+ Auth
+ HouseholdMembership / authorization
+ tenant isolation
+ hosted operational baseline
```

must be verified before shared-family testing. Billing is not part of this
safety gate and remains later.

## 8. Validation and downstream programs

### Real Family Testing

After Consumer Core, Data Readiness and Shared Deployment gates, test with
`10–30 households` through the full repeated loop:

```text
week → use → feedback → next week
```

Isolated/local single-Household validation may occur earlier, but it must not be
described as shared real-family testing.

### Data Program

After core/shared-family validation, build the full Data Ingestion Platform and
catalogue-expansion/quality automation. Untrusted parsed data still follows the
draft/normalize/validate/review or explicit trusted-source policy.

### Retail Program

After the generic Shopping Engine and Data Program, introduce Retail Foundation
and then one Retail Connector. Keep `FoodIngredient`, `RetailSKU` and
`PriceSnapshot` separate.

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
