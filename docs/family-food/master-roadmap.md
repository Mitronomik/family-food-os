# FamilyFoodOS — Master Roadmap

**Status:** canonical repository sequencing and delivery-gate contract  
**Updated:** `2026-09-12`

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
PR2-DOCS Canonical Roadmap Sync            COMPLETE
PR3   FoodIngredient Catalogue             COMPLETE
PR4-DATA Recipe coverage support           COMPLETE
PR4-DATA2 Russia/SPB corpus re-curation    COMPLETE
PR4   Recipe Catalogue                     COMPLETE
PR5   Pantry                               COMPLETE
PR6   Nutrition Core                       COMPLETE (PR6-CLOSE merged #30)
```

PR2-C closure evidence:

- GitHub PR: `#5` — merged;
- accepted head: `13f7c7c480469853579912a7836680afc4734ad7`;
- merge commit: `48c72aeba19a1e6ece0dc729f0a80de930be88a8`;
- merged at: `2026-09-01T21:23:23Z`;
- final project review: `PR2-C FINAL REVIEW: ACCEPT`.

PR3 FoodIngredient Catalogue is COMPLETE (PR #7 merged). Supporting
PR4-DATA and PR4-DATA2 operations are COMPLETE; they do not add product milestones.

PR4 closure evidence:

- GitHub PR [#10](https://github.com/Mitronomik/family-food-os/pull/10): merged;
- accepted/merged head: `0ac6c9d34a3cc54052c8fd01af3acfc49786242f`;
- merge commit: `e7a2e00615c8ef1f5bdb4634089e821542ba50dc`;
- final project review: `PR4 FINAL REVIEW: ACCEPT — READY TO MERGE`;
- final regression gate: PASS.

PR5 closure evidence:

- [PR #15](https://github.com/Mitronomik/family-food-os/pull/15): MERGED;
- accepted/merged head: `4778b6e99fde027be7e70b8a8966db85394e100d`;
- merge commit / verified main: `5f1bb47199ab661d58b92b8cbb9e40b4aeb7b0d0`;
- fully tested implementation: `d5b821ce9969ee2bf167333d9b48675d0f6d470f`;
- final project review: `PR5 FINAL REVIEW: ACCEPT — READY TO MERGE`;
- final regression gate: PASS — **3255 passed in 467.40s**, zero skips;
- accepted PR #15 verification is reused by PR5-CLOSE; no regression rerun.

PR6 engine implementation is ACCEPTED / MERGED in
[PR #18](https://github.com/Mitronomik/family-food-os/pull/18), merge commit
`7c449672c039c66b8d475064462eba2a9f6d38e6`. PR6 milestone is **COMPLETE** under
the [PR6-CLOSE decision and limits](pr6-closure.md), merged in PR #30. The [Nutrition Core](nutrition-core.md)
contract remains active. PR6-DATA-A is ACCEPTED / MERGED in PR #19 at
`60908eb8270ef356eff8552855b4cc5d2aa9ee44`. Supporting PR6-DATA-B1 establishes
the exact evidence/row-binding foundation described in the
[data-readiness decision](nutrition-data-readiness.md), without a new numbered
milestone. B1 is established by PR #20, merged at
`2ce9917f51ac3161d4cb2839f6003e7a24bc96bd`. PR6-INFRA is established by
PR #21 at `74bc80eb3ef0e34e17751856638ac58bbccb840e`, providing the explicit
SQLite table-rebuild runner capability. B2-A is MERGED in PR #22 at
`7f17b1372bbd2e9f97fc025ac26b3f04a15cf837`: migration
`0027_recipe_same_source_revisions`, six quantity corrections across five immutable
v2 recipes, explicit new-row assessments and production audit v3. External source
provenance is distinct from internal RecipeVersion revision identity.
See the [B2-A decision](nutrition-data-readiness.md#decision--pr6-data-b2-a-same-source-quantity-corrections).

B2-B1 is MERGED in [PR #23](https://github.com/Mitronomik/family-food-os/pull/23) at
`47299ceb2c740f40f69f3b02359ce71c8be6b1c1`, the exact starting main for this
PR6-ARCH-COMPOSITION docs-only changeset. Its semantic/profile research covers
37 target rows / 23 recipes / 19 foods and all 46 current usages; source candidates
remain evidence, not production authority. The research history is preserved.

**DECISION — 2026-09-10:** PR6-ARCH-COMPOSITION architecture contract established
in merged PR #24. Option A is approved and extended by the
[composition/mass/nutrient/assembly contract](food-composition-and-assembly.md)
and [Russian-language invariant](russian-language-contract.md).
**Old PR6-DATA-B2-B2: SUPERSEDED / PENDING REDESIGN.** Its former
form/profile corrections + explicit estimate policy plan cannot execute directly.

At VECTOR-A merge, production remained 30 current RecipeVersions / 189 rows,
all 30 INCOMPLETE, migration head 0027. VECTOR-B adds migration 0028 in its
authorized implementation PR; Nutrition v1, readiness and all 43 non-executable
estimates remain unchanged.
At that historical point PR6 remained NOT COMPLETE. **PR6-NUTRIENT-VECTOR A/B — MERGED.** Bounded VECTOR-A
registry/provenance research is merged in PR #25 at `e35d87a24d5d8afb59509e566aa1ff4b7a58a11a`;
VECTOR-B is merged in PR #26 at
`b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe` (migration 0028).
COMPOSITION-CORE is MERGED in
[PR #27](https://github.com/Mitronomik/family-food-os/pull/27), merge commit
`d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc`; migration head is 0029.
PR6-RU-FOOD-DATA is MERGED in [PR #28](https://github.com/Mitronomik/family-food-os/pull/28)
at `4180297d47d68a0e0d9efbe7a7a27f3900c4f388`; its
[evidence package](../../data/curation/pr6-ru-food-data/README.md) preserves the two
food-form promotions and five deferrals. PR6-DATA-B2-B2-REDESIGNED is **MERGED /
delivered** in [PR #29](https://github.com/Mitronomik/family-food-os/pull/29) at
`3caa95e636c02e8f34657b1b6c885f646451114c`, the exact PR6-CLOSE baseline.
**PR6-CLOSE — COMPLETE; PR6 — COMPLETE**, with the explicit technical/corpus,
legacy/normalized authority and downstream limits in [the closure decision](pr6-closure.md).
All 20 reviewed criteria pass; PR #30 is MERGED at
`e8a75e5b828ef935292da593f9f4d5edbd199474` (verified 2026-09-12).
Migration remains `0029_food_composition_core`.
The mass-authoritative decision is recorded in
[Composition Core](food-composition-and-assembly.md#pr6-composition-core--concrete-runtime-contract).
Current operation: **RECIPE-ASSEMBLY-A — AUTHORIZED / BLOCKED at evidence preflight**.
The [preflight package](../../data/curation/recipe-assembly-a/README.md) records the
three deferred candidate families; no catalogue runtime/schema/seed is delivered.
Recipe Assembly B and PR7+ remain NOT STARTED. No automatic next operation.
The approved sequence changes are specified in §6.5; quantitative gates are retained.

## 3. North Star and core-loop contract

FamilyFoodOS exists to remove the recurring cognitive and operational burden of
feeding a household. The product includes a deterministic constructor from
verified templates/rules; it is not a free-form LLM recipe generator or
AI-dietitian. Its recurring product loop is:

```text
Household
→ Members / Preferences / Constraints
→ FoodIngredient Catalogue
→ verified Recipe Catalogue / deterministic Recipe Assembly
→ Nutrition
→ valid candidate pool
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
21. Food forms and raw/input/cooked masses are not interchangeable. Composition
    is a versioned DAG; yield and nutrient retention have separate evidence.
22. Target Nutrition uses an extensible macro/micronutrient vector with
    nutrient-level provenance; unknown != zero. Current v1 remains valid.
23. Consumer and admin surfaces are Russian; missing display text blocks
    publication, never permits English fallback, including errors and PDF.
24. Default automatic recipes pass RU availability/familiarity and use
    kitchen-verified templates/rules; Planner consumes valid candidates.

## 5. Canonical master sequence

```text
✅ PR0   Frozen Fork
✅ PR1   Identity Detox
✅ PR2-A Architecture & Persistence Contract
✅ PR2-B Persistence Foundation
✅ PR2-C Household Foundation

✅ PR3   FoodIngredient Catalogue
✅ PR4   Recipe Catalogue
✅ PR5   Pantry
✅ PR6 Nutrition Core (PR6-CLOSE COMPLETE; explicit limitations apply)
✅ PR6-DATA-A
✅ PR6-DATA-B1
✅ PR6-INFRA
✅ PR6-DATA-B2-A
✅ PR6-DATA-B2-B1
✅ PR6-ARCH-COMPOSITION (architecture contract established by this changeset)
✅ PR6-NUTRIENT-VECTOR (A/B merged)
✅ PR6-COMPOSITION-CORE
✅ PR6-RU-FOOD-DATA
✅ PR6-DATA-B2-B2-REDESIGNED (PR #29 merged / delivered)
✅ PR6-CLOSE (COMPLETE; PR #30 merged)
→ RECIPE-ASSEMBLY-A (authorized; BLOCKED at evidence preflight)
→ RECIPE-ASSEMBLY-B
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

FoodIngredient is the sole canonical food identity, including nutrition-relevant
forms and atomic/composite foods. `FoodProductType` is not a mandatory intermediate
aggregate or Nutrition truth layer. Any later Retail classification remains
metadata; it cannot become a second food identity or Nutrition authority.

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

### 6.5 PR6-ARCH-COMPOSITION — approved roadmap differences

**DECISION — 2026-09-10.** The old PR6-DATA-B2-B2 plan is
**SUPERSEDED / PENDING REDESIGN**, not the next implementation operation.
NutrientVector, composition/mass/transformation/yield/retention contracts and RU
catalogue/display readiness must precede redesigned production re-curation.
The replacement supporting sequence is explicit in §5 and detailed under PR6.

The intentional differences from exact base
`47299ceb2c740f40f69f3b02359ce71c8be6b1c1` are:

1. Insert PR6-ARCH-COMPOSITION → PR6-NUTRIENT-VECTOR → PR6-COMPOSITION-CORE →
   PR6-RU-FOOD-DATA → PR6-DATA-B2-B2-REDESIGNED → PR6-CLOSE after accepted B2-B1.
2. Insert RECIPE-ASSEMBLY-A/B after PR6-CLOSE and before PR7. PR7 selection
   origins become immutable RecipeVersion or validated RecipeAssembly, reusing
   Nutrition. PR8 consumes their valid Russian consumer candidate pool.
3. Add qualitative consumer readiness obligations: Russian text, RU eligible
   foods, familiar recipes/templates, valid Nutrition provenance, deterministic
   input grams, no hidden raw/cooked equivalence or unresolved critical
   composition/yield issue. Kitchen verification is separate from calculation.

No quantitative gate is removed or reduced: Gate 1 still has 3 fixture households,
30 verified recipes and 80+ foods; Gate 2 still has 1 Household / 3 members /
30 recipes / 80–120 foods; Data Readiness still requires 50–80+ recipes and 100%
required coverage with the broader 250–350-food target. Assembly counts do not
silently replace the verified-recipe counts. The 30 current FNS recipes are
technical evidence; consumer suitability requires its own readiness review.

Gate 1 → Shopping → Prep → backend PDF → Consumer UX remains in place. PostgreSQL,
Auth/HouseholdMembership, tenant isolation/shared deployment, full Data Program,
Retail, Optional AI and Commercial/Billing timing remain unchanged. Shopping
and Pantry ownership/mutation contracts are unchanged. These supporting PRs do
not start the future full ingestion or live Retail programs.

Every future operation requires separate bounded authorization; sequence position,
review readiness or merge of this docs PR is not that authorization.

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

### PR3 — FoodIngredient Catalogue — COMPLETE

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

### PR4 — Recipe Catalogue — COMPLETE

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

### PR5 — Pantry — COMPLETE

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

### PR6 — Nutrition Core — COMPLETE

The [PR6-CLOSE decision](pr6-closure.md) establishes milestone completion with
explicit limitations; it does not certify current FNS consumer readiness or Gate 1.
The accepted PR6 engine v1 bounded contract runs through:

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

#### PR6 supporting operations — later approved target

These operations extend the target, preserving accepted Nutrition v1 history.
PR6-ARCH-COMPOSITION is merged (#24). PR6-NUTRIENT-VECTOR is delivered as bounded
slices A/B: A establishes [registry/provenance research](../../data/curation/pr6-nutrient-vector-a/README.md)
without runtime/schema; B was separately reviewed and merged.
This split creates no milestone and changes no operation order. All supporting
operations through PR6-CLOSE are delivered. Assembly A is authorized but BLOCKED
at evidence preflight; Assembly B and PR7+ remain NOT STARTED / unauthorized.

| Operation | Bounded outcome and dependency |
| --- | --- |
| PR6-ARCH-COMPOSITION | Docs-only canonical architecture contract, Option A/composition/mass/vector/Russian gates and revised order; no runtime/data/schema changes. |
| PR6-NUTRIENT-VECTOR | Extensible macro/micronutrient registry/vector, nutrient-level provenance and uncertainty, initial authoritative nutrient registry and explicit backward compatibility with Nutrition v1. |
| PR6-COMPOSITION-CORE | Atomic/composite FoodIngredient; exact/declared-only composition; recursive versioned DAG; mass states; transformation/yield and retention evidence contracts. Depends on NutrientVector. |
| PR6-RU-FOOD-DATA | Consumer-ready Russian food catalogue with Russian names, ordinary basic foods and composites where needed, RU availability evidence and nutrition/composition readiness. |
| PR6-DATA-B2-B2-REDESIGNED | MERGED / delivered (#29). Migrate/re-curate affected existing recipe rows against the new form/composition/nutrient model; preserve history, re-review source/profile promotion, no direct execution of legacy B2-B2 assumptions. |
| PR6-CLOSE | COMPLETE. [Reviewed 20-criterion decision](pr6-closure.md) after preceding dependencies; engine readiness alone is insufficient. Technical corpus limitations remain explicit. |

Persisted changes in those later PRs require explicit migration/backfill/history/
backup/export strategy. Exact SQL fields and migrations are not designed here.
Estimate/uncertainty acceptance remains OPEN; all 40 remaining current estimate
usages stay non-executable. PR29 independently superseded three usages with exact
evidence without relabelling historical estimates. Closure verifies the expanded
authority/fail-closed criteria; consumer/kitchen and later quantitative gates are
not waived or claimed complete.

### RECIPE-ASSEMBLY-A — verified Russian templates and rules

2026-09-12 execution: explicitly authorized after reviewed PR30 merge; **BLOCKED**.
Exactly three production families remain required. The bounded evidence review
has not established three publishable families, so implementation stopped before
migration 0030 or seed publication. This is not milestone completion or a change
to the original exit criteria. See the [retained evidence](../../data/curation/recipe-assembly-a/README.md).

After PR6-CLOSE: introduce a bounded versioned RecipeTemplate/rule catalogue with
Russian display, RU familiarity classification, kitchen verification evidence,
allowed combinations, curated substitutions and exact quantity rules. Templates
cover atomic and composite components and the required transformation contracts.
Exit requires reviewable provenance and kitchen-validated rules/variants, not
arbitrary ingredient combinations. No Engine runtime is implied by this data step.

### RECIPE-ASSEMBLY-B — deterministic Recipe Assembly Engine

After A and before PR7: implement deterministic assembly, reproducible trace,
exact input grams and integration with Nutrition/composition/yield/retention.
The [assembly contract](food-composition-and-assembly.md#recipetemplate-и-deterministic-assembly)
defines validation versus kitchen verification and immutable RecipeVersion versus
derived assembly. Exit requires repeatable validated outputs and fail-closed
invalid/missing evidence paths with `AI_ENABLED=false`, plus RU/display gates.
Planner and MealPlan/Serving implementation remain separate later operations.

### PR7 — MealPlan / Serving + serving-nutrition integration

PR7 follows PR6-CLOSE and RECIPE-ASSEMBLY-A/B. It introduces `MealPlan`, its day/slot
structure and individualized `Serving`.
It integrates:

```text
selected immutable RecipeVersion / validated RecipeAssembly nutrition
→ Serving nutrition
→ Member/day totals
→ week aggregates
```

MealPlan history begins with this context. PR15 later owns structured feedback
and personalization history.

**Data/capabilities:** `MealPlan`, `MealPlanDay`, `MealSlot` and `Serving`, with
Household ownership, week start/local planning dates, selected immutable
RecipeVersion or validated RecipeAssembly origins, per-member allocations, status
and source/config revision references.

**Services:** manually assemble/read/update one coherent seven-day plan,
calculate Serving nutrition from the selected origin through the existing Nutrition
contract without duplicating Nutrition logic, and aggregate
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

**Inputs:** Household/member constraints, exclusions/preferences, already valid
Russian consumer candidates from verified RecipeVersions / validated RecipeAssemblies,
Nutrition, Pantry, recent MealPlan history, budget/cooking
constraints and planning mode.

**Output/services:** one complete seven-day MealPlan with individualized
Servings plus a durable/reproducible trace containing planner/config version,
candidate pool, constraints, rejected candidates/reasons, scores, selections,
warnings and duration.

**Tests:** deterministic repeatability, exclusion enforcement, complete-week
generation, member allocation, candidate rejection reasons, trace
reproducibility, constrained failure reporting and fixture-household variation.

**Non-goals:** culinary recipe generation, OR-Tools or another advanced solver
without measured benefit, Retail dependence, AI decisions, ShoppingList or PrepPlan.

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

The path must additionally demonstrate form/composition authority, exact input
grams, required nutrient provenance and explicit yield/retention uncertainty.
Consumer use requires the qualitative gates in §6.5; the technical FNS corpus
is not automatically accepted consumer truth.

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
  `250–350`, with that broader target explicit rather than hidden inside PR3;
- Russian display readiness on all consumer/admin surfaces, with no English fallback;
- current RU market eligibility and food-form correctness;
- one composition authority per food version, no critical composition cycle and
  no inferred declared-only quantities;
- deterministic recipe_input_mass_g, required nutrient-vector support and
  transformation/yield/retention readiness where needed, without hidden raw/cooked
  mass equivalence or unresolved critical composition/yield issues;
- RU recipe/template familiarity and kitchen-verified default assembly rules.

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
- `FoodProductType` must not become a mandatory intermediate FoodIngredient
  or Nutrition truth layer; any later classification remains separately justified metadata.

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
→ user-authorized merge
→ separate bounded authorization for the next operation
→ begin only that operation
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

Use root `AGENTS.md` task routing: current focus, applicable scoped AGENTS,
relevant canonical documents, code and tests. Read the Operating Manual, this
roadmap and broader architecture references when interpreting authorization,
gates, product/architecture decisions, cross-context design, source conflicts or
substantial research; do not preload them for every ordinary correction.
Read `state/handoff.md` only when continuing previous work.

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

### Assembly A supporting evidence recovery — R1 checkpoint

2026-09-12: user authorized merging PR31 and a bounded research-only donor recovery
from its exact merge commit. [R1 evidence](../../data/curation/recipe-assembly-a-r1/README.md)
records 23 screened / nine deep-reviewed / one individually ready (R1-21) /
zero selected final candidates after the authorized market-policy correction;
**R1 BLOCKED**. Existing basic-commodity exceptions and specific product reasons
apply independently of the unchanged availability classification.
This is supporting work inside the unchanged Assembly A gate, not a roadmap
reorder, milestone closure or authorization for schema. Assembly A remains
BLOCKED pending evidence recovery; Assembly B and PR7+ remain NOT STARTED.


### Assembly A targeted recovery — R2 checkpoint

2026-09-12. PR32 is MERGED at exact main `8730b9fcfdb56cec2215f7e70319241c83431371`.
R1 is COMPLETE AS BLOCKED RESEARCH (accepted 1/3); the historical R1 BLOCKED
wording above describes its result, not unfinished research. The user authorized
only R1-23/R1-13 recovery in R2. [R2 evidence](../../data/curation/recipe-assembly-a-r2/README.md)
derives Outcome A: 2/3 individually ready; final three remain empty. The fixed
100-portion oatmeal decision is unchanged. AFRS F00400 method 1 passes only its
published 100-portion scope; the selected rice branch retains kitchen/process
uncertainty. Collective optional/substitution gates remain open.
Assembly A remains BLOCKED; Assembly B and PR7+ NOT STARTED. No roadmap gate,
production data or implementation authorization changes. The next action is R2
review; neither another donor search nor food-data repair starts automatically.
Even a future evidence-ready triple needs separate authorization for Assembly A
implementation with `0030_recipe_template_catalogue`.
