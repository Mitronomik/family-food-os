# FamilyFoodOS — Architecture Compatibility Addendum, 2026-09-13

**Status:** canonical addendum to `architecture.md`
**Decision date:** 2026-09-13
**Scope:** MealPlan / Serving, Planner, Recipe Catalogue, Meal Pattern Catalogue and mixed-source authority compatibility

## 1. Purpose

This addendum closes two ambiguities introduced when the configurable
meal-pattern and Household Food OS decisions were integrated after the existing
Recipe Catalogue implementation.

It does **not** redesign accepted PR2–PR6/PR36 runtime. It defines how future
PR7/PR8 work must extend the current architecture without repurposing already
implemented recipe semantics or forcing every planned meal event to have a
RecipeVersion.

## 2. Authority

`architecture.md` remains the canonical base architecture. This later approved
addendum supersedes only the conflicting or incomplete interpretation of
sections 6.3, 6.5 and 6.6 described below.

The existing architecture and migration sequence remain unchanged:

```text
UI
→ API
→ services/domain
→ repositories / Unit of Work
→ persistence adapters
→ database
```

No runtime code, schema, migration, catalogue data, Nutrition authority or
RecipeVersion is changed by this documentation decision.

## 3. Recipe classification is not a member meal role

The already implemented Recipe Catalogue owns `RecipeVersion.meal_type_code`.
Its current production enum is a recipe-classification contract with values such
as:

```text
breakfast
main
side
salad
sandwich
other
```

The new planning model owns a separate semantic concept, `MealRole`, with
examples such as:

```text
BREAKFAST
LUNCH
DINNER
SNACK
PRE_WORKOUT
POST_WORKOUT
OTHER
```

These concepts are intentionally distinct.

Canonical invariant:

```text
RecipeVersion.meal_type_code != MealRole
```

`RecipeVersion.meal_type_code` answers what kind of recipe/component a catalogue
entry is. `MealRole` answers what eating opportunity a HouseholdMember is
planning in their daily schedule.

PR7/PR8 must therefore **not**:

- rename or reinterpret the existing Recipe Catalogue enum as a schedule enum;
- add `DINNER`, `LUNCH`, `PRE_WORKOUT` or similar values to the recipe enum merely
  because the Planner needs those roles;
- migrate already accepted recipe data simply to express a member schedule;
- duplicate the recipe enum as a second source of catalogue truth.

Planner/selection may instead use an explicit deterministic suitability mapping
or rule layer, for example conceptually:

```text
MealRole.DINNER
→ compatible recipe/component classes
→ MAIN / SIDE / SALAD / validated assemblies
```

and:

```text
MealRole.BREAKFAST
→ compatible recipe/component classes
→ BREAKFAST / other explicitly approved compatible candidates
```

The exact mapping model, versioning and tests belong to the owning PR7/PR8
implementation contract. Suitability is planning logic; it does not mutate
Recipe Catalogue truth.

## 4. MealPlan events have an explicit meal source

The earlier architecture wording that a MealPlan owns references to selected
RecipeVersions or validated RecipeAssemblies must not be read as saying that
every planned eating event requires a recipe.

A future MealPlan event/opportunity has an explicit source kind. The exact enum
names remain an implementation decision, but the architecture must support at
least the following source families:

```text
COOK_RECIPE
ASSEMBLY
LEFTOVER
PREPARED
READY_MEAL
ORDER_OUT
EAT_OUT
```

A recipe/assembly reference is conditional on the source type rather than a
universal field requirement.

Conceptually:

```text
COOK_RECIPE → immutable RecipeVersion
ASSEMBLY    → reproducible validated RecipeAssembly
LEFTOVER    → represented prior prepared/meal supply
PREPARED    → represented PreparedBatch / authoritative prepared supply
READY_MEAL  → represented ready-food item when that source model exists
ORDER_OUT   → no fake RecipeVersion required
EAT_OUT     → no fake RecipeVersion required
```

The implementation must not create synthetic or provenance-free RecipeVersions
merely to satisfy a foreign-key shape for `READY_MEAL`, `ORDER_OUT`, `EAT_OUT`,
leftovers or other non-recipe sources.

Where a later source model has not yet been implemented, the Planner may support
only the subset for which authoritative state exists. It must not invent future
PreparedBatch/Pantry/Retail state.

### 4.1 Source capability contract

Representation and automatic Planner eligibility are separate capabilities.
PR7 must be able to represent the approved source kinds without schema redesign,
but the presence of an enum value is never evidence that the Planner may treat
that source as available supply, known nutrition or known cost.

| Source | Authority / reference | Nutrition authority | Shopping demand | Existing supply | Cost authority | Planner availability |
|---|---|---|---|---|---|---|
| `COOK_RECIPE` | immutable verified `RecipeVersion` | Nutrition Engine from RecipeVersion + Serving | authoritative recipe ingredient demand | Pantry subtraction remains Shopping/Pantry behavior, not source truth | generic Shopping estimate; Retail later | PR8 baseline may auto-select |
| `ASSEMBLY` | reproducible validated `RecipeAssembly` | Nutrition Engine from composition/assembly + Serving | authoritative assembly ingredient demand | Pantry subtraction remains Shopping/Pantry behavior | generic Shopping estimate; Retail later | PR8 baseline may auto-select after Assembly B |
| `LEFTOVER` | household leftover/prepared-supply record with origin and confirmed remaining quantity | original immutable origin/version plus confirmed remaining quantity | no new ingredient demand | consumes authoritative represented supply | sunk/unknown unless an owning model records cost | representation/user-fixed before supply model; auto-selection only after authoritative leftover supply exists, normally PR10+ |
| `PREPARED` | `PreparedBatch` / prepared inventory created by confirmed Prep execution | batch origin/version plus confirmed quantity | no new ingredient demand | consumes authoritative prepared supply | authoritative batch cost if later modeled, otherwise unknown | representation/user-fixed before PR10; auto-selection only after PR10 confirmed-execution inventory exists |
| `READY_MEAL` | validated ready-food/product reference from its future owning catalogue/Retail model | authoritative product/source profile when present; otherwise unknown | ready-item purchase demand only; never expand into invented recipe ingredients | only if an owning inventory model says it is already held | authoritative source/Retail snapshot when available | representation allowed; auto-selection deferred until ready-food authority exists, not PR8 baseline |
| `ORDER_OUT` | explicit user-fixed event or future validated provider/order reference | authoritative provider/platform profile when present; otherwise unknown | no grocery ingredient demand | no | user-confirmed/provider cost when authoritative; otherwise unknown | PR8 may preserve/render user-fixed events; automatic selection deferred |
| `EAT_OUT` | explicit user-fixed external event | authoritative provider/platform profile when present; otherwise unknown | no grocery ingredient demand | no | user-confirmed/provider cost when authoritative; otherwise unknown | PR8 may preserve/render user-fixed events; automatic selection deferred |

Rules:

- `representable != Planner-selectable`;
- unknown nutrition/cost stays unknown and cannot be silently counted as meeting a
  deterministic nutrient or budget target;
- `LEFTOVER`/`PREPARED` cannot be auto-selected merely because their source code
  exists; authoritative identity and available quantity are required;
- `ORDER_OUT`/`EAT_OUT` are valid user schedule facts before provider integration,
  but PR8 baseline does not autonomously choose them;
- PR8 Gate 1 deterministic fixture planning may rely on `COOK_RECIPE` and
  `ASSEMBLY`; other source kinds are tested for representation and fail-closed
  behavior until their owning authority is implemented.

## 5. Serving and nutrition semantics remain truthful

A `Serving` remains the member-specific allocation for an event, but its
calculation/evidence depends on the source.

For RecipeVersion/RecipeAssembly sources, existing deterministic quantity and
Nutrition rules apply.

For non-recipe sources, the product must represent only nutrition/quantity facts
that have an authoritative or explicitly estimated source. It must not fabricate
precise kcal, mass or nutrients simply because a MealPlan slot exists.

Hard exclusions and food-safety rules continue to dominate sharedness and source
selection.

## 6. Planner candidate space

The Planner remains deterministic and recipe truth remains owned by Recipe
Catalogue / Recipe Assembly.

The earlier phrase "candidate pool from verified RecipeVersions / validated
RecipeAssemblies" describes the culinary candidate pool, not the complete future
source-choice space.

Future Planner inputs may therefore include:

```text
verified RecipeVersions / RecipeAssemblies
+ accepted member meal patterns
+ represented leftovers / prepared supply
+ allowed ready/out-of-home source options
+ Pantry / Nutrition / schedule / constraints
```

and produce:

```text
Household meal events
+ explicit source kind
+ source reference where required/available
+ individualized Servings
+ deterministic trace/explanation
```

The generation/replan trace must record enough source-choice information to
explain and reproduce why an event was `COOK_RECIPE`, `LEFTOVER`, `PREPARED`,
`EAT_OUT` or another supported source.

## 7. Shopping compatibility

Shopping derives ingredient demand only from MealPlan sources that actually
create ingredient demand.

At minimum:

- `COOK_RECIPE` / `ASSEMBLY` contribute their authoritative ingredient demand;
- `LEFTOVER` / `PREPARED` consume represented prior supply and must not silently
  purchase the original ingredients a second time;
- `READY_MEAL` contributes only the purchase demand represented by its owning
  source model when implemented;
- `ORDER_OUT` / `EAT_OUT` do not create grocery ingredient demand unless a later
  explicit product contract says otherwise.

This preserves the existing generic Shopping-first architecture and prevents
mixed-source planning from double-counting demand.

## 8. Meal Pattern Catalogue ownership and readiness

`MealPatternProgram` is platform-owned curated planning data. It belongs to a
**Meal Pattern Catalogue** boundary inside the existing modular monolith; this is
a code/data ownership boundary, not a new deployed service.

The Meal Pattern Catalogue owns:

- `MealPatternProgram` identity and immutable/versioned published revisions;
- Russian display/explanation text;
- eligibility rules and supported wellness goals/contexts;
- evidence/provenance references, review status and safety gates;
- lifecycle/publish/deactivate state;
- deterministic catalogue validation.

A focused platform-scoped `MealPatternProgramRepository` (or equivalently named
repository contract) exposes published eligible versions to application services.
Planner is a consumer of this catalogue; Planner does not author or publish
program truth.

`MemberMealPatternSelection` is separate, Household-owned state. It records the
accepted program ID/version or `CUSTOM`, recommender version when applicable,
user overrides and history. Household scoping applies to every selection read and
write.

Before PR7/PR8 consume production programs, the roadmap requires the bounded
supporting operation `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`. That operation owns the
catalogue schema/repository/validation and initial curated evidence-reviewed
program data. It is not a new product milestone and does not reorder the numbered
roadmap.

Children do not create a readiness exception: if no age-appropriate published
program has approved evidence, automated recommendation returns an
unsupported/safety outcome while manual/custom scheduling remains available.

## 9. Compatibility with already implemented work

This decision is deliberately additive.

It requires **no redesign** of the accepted implementations of:

- Household / HouseholdMember foundation;
- FoodIngredient / composition authority;
- Recipe / immutable RecipeVersion provenance;
- Pantry and household-scoped movements;
- Nutrition Core;
- the PR36 source corpus and its migration lineage.

PR7 owns the first schema/domain representation of meal opportunities,
participation, source kind and accepted meal-pattern reference. PR8 owns the
first deterministic planning/recommendation/replan behavior over that model.

Any required PR7 persistence change is a new forward migration after the current
migration head. Existing migrations are not rewritten.

## 10. Required compatibility tests for PR7/PR8

Future implementation must include cases proving at least:

- `MealRole.DINNER` can select compatible existing `MAIN`/component recipe
  classifications without changing `RecipeVersion.meal_type_code`;
- breakfast schedule logic works without turning every compatible recipe into a
  new catalogue enum value;
- `COOK_RECIPE` requires an immutable RecipeVersion reference;
- non-recipe source kinds do not require a fake RecipeVersion;
- mixed-source weeks remain reproducible;
- Shopping demand does not double-count leftovers/prepared supply;
- historical MealPlan revisions preserve their original source kind/reference.

## 11. Read-together rule

For PR7/PR8 and any later MealPlan/Planner work, read this addendum together
with:

- `architecture.md`;
- `master-roadmap.md`;
- `master-roadmap-addendum-2026-09-13.md`;
- `meal-pattern-programs.md`;
- `product-strategy.md`;
- `security-architecture.md`.

If older wording is read as requiring a RecipeVersion for every meal event or as
making the Recipe Catalogue meal-type enum the member schedule enum, this
addendum controls that interpretation.
