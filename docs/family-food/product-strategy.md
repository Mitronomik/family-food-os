# FamilyFoodOS — Product Strategy Contract

**Status:** canonical product-strategy contract  
**Decision date:** 2026-09-13  
**Applies to:** Planner, MealPlan/Serving, Shopping, Prep, consumer UX, validation and product metrics

## 1. Authority and purpose

This document integrates the useful product decisions from the September 2026
Household Food OS / Grocery Weekly Planner research package into the existing
FamilyFoodOS product without re-platforming or restarting the repository.

It refines product behavior and outcome goals. It does **not** replace the
repository architecture, migration strategy or sequencing contract.

The following repository contracts remain authoritative within their scopes:

- `architecture.md` — architecture, ownership and persistence boundaries;
- `master-roadmap.md` — milestone order and delivery gates;
- `food-composition-and-assembly.md` — food identity, composition and assembly;
- `nutrition-core.md` — deterministic Nutrition truth;
- `security-architecture.md` — security and trust boundaries;
- `meal-pattern-programs.md` — configurable meal frequency and deterministic
  meal-pattern recommendation.

A later explicit user-approved decision may amend this contract.

## 2. Product thesis

FamilyFoodOS is not a recipe generator and not an AI dietitian.

It is a household food operating system that manages a recurring real-world
process:

```text
people
→ meal pattern / schedule
→ weekly plan
→ individualized servings
→ pantry / leftovers
→ shopping
→ prep / freezer
→ daily execution
→ reality changes
→ replan
→ feedback
→ next week
```

The product optimizes the week as a system rather than seven independent recipe
choices.

The governing principle remains:

> complexity inside the system, simplicity for the user.

## 3. Primary job to be done

When a person needs to feed themselves or a household through the week, the
system should let them make the minimum necessary number of decisions and give
them a realistic plan of meals, quantities, shopping and preparation that fits
people, goals, time, budget and food already available.

The expected outcome is not a mathematically elegant menu. It is a week that is
actually followed.

## 4. Product invariants

1. Household is the planning boundary; individual members retain their own
   targets, restrictions, schedule and serving needs.
2. A Recipe/RecipeAssembly is not a Serving.
3. A Household may use a common base meal with different member portions or
   variants.
4. Meal frequency is configurable; no product layer may assume "dinner only",
   three meals per day or another fixed count.
5. AI is optional and never authoritative for food, money, safety or access.
6. Retail is optional enrichment; generic Shopping remains useful without it.
7. Replanning is a normal mode of operation, not an exceptional recovery path.
8. Prepared food, leftovers and eating outside the home are legitimate meal
   sources; not every planned meal must create a new cooking process.
9. Planner output must be explainable, versioned and reproducible enough for
   debugging and user-facing reasons.
10. Medical treatment diets remain outside the MVP wellness scope.

## 5. Flexible meal pattern, not dinner-only planning

The first usable product must support a configurable daily meal pattern per
member. Initial validated product range is one to six planned eating occasions
per day, while the domain model remains extensible rather than encoding six as a
permanent architectural maximum.

Examples that must be representable without schema changes:

- dinner only;
- breakfast only;
- breakfast + dinner;
- breakfast + lunch + dinner;
- three meals + two snacks;
- six planned eating occasions for an appropriate accepted program;
- different patterns for different HouseholdMembers.

The detailed program/recommendation contract is owned by
`meal-pattern-programs.md`.

## 6. Meal events, participation and sources

Planning should distinguish a household meal event from each member's serving.
A practical target model is conceptually:

```text
HouseholdMealEvent
├── local date / time window / role
├── participants[]
├── source
├── selected RecipeVersion or RecipeAssembly when applicable
└── member Servings / variants
```

A meal source should be able to represent at least:

```text
COOK
LEFTOVER
PREPARED
READY_MEAL
ORDER_OUT
EAT_OUT
```

The exact enum/API representation belongs to the owning implementation PR, but
Planning must not assume every slot has a Recipe.

## 7. Household Reconciliation

The Planner should optimize the shared household process rather than create an
independent menu for every member.

A key concept is **sharedness**: the portion of meal components or preparation
work that can be done once for multiple people while still meeting individual
hard constraints and serving needs.

Preferred pattern:

```text
shared base
+ member-specific serving size
+ optional final variant / sauce / protein / exclusion
```

Planner scoring should eventually reward:

- household sharedness;
- fewer independent cooking processes;
- compatible serving variants;
- common ingredient preparation;
- child/adult compatibility where safely supported.

Hard exclusions always dominate sharedness. A common base is never permission to
weaken allergen or other hard constraints.

## 8. Planner objective

Planner v0 still starts with deterministic filters and scoring. The product
objective should be capable of considering:

**Reward:**

- preference fit;
- nutrition fit;
- household sharedness;
- pantry use;
- ingredient reuse;
- budget fit;
- prep efficiency;
- reasonable variety;
- familiar/available RU food patterns.

**Penalize:**

- food waste;
- unnecessary independent cooking;
- perishability risk;
- unwanted repetition;
- excessive complexity;
- avoidable package surplus when retail/package data later exists;
- unnecessary store visits when retail optimization later exists.

Exact weights are versioned configuration, not universal constants.

## 9. Reality Loop and dynamic replanning

A week is expected to change after it is generated.

Relevant events include:

- a person will not eat at home;
- a meal is skipped or moved;
- a leftover quantity differs from plan;
- a prepared batch already exists;
- food must be used sooner than expected;
- the household deliberately chooses ready food or eating out;
- later Retail may report a meaningful availability change.

Replan should operate on the remaining horizon and preserve already committed
value where possible:

```text
current accepted plan
+ authoritative current state
+ change event
→ deterministic replan
→ explicit diff / explanation
→ new plan revision
```

Replan should prefer minimum disruption while still satisfying hard constraints.
It must not silently rewrite plan history.

Shopping, Prep and PDF remain derived state. A source MealPlan revision change
makes incompatible derived outputs stale and requires explicit regeneration.

## 10. Prep as an operational graph

Prep is more useful as an execution graph than as a flat checklist.

Future Prep evolution should be able to model:

```text
PrepTask
├── operation
├── ingredient/component
├── active time
├── passive time
├── equipment
├── predecessors[]
└── resulting storage state
```

The scheduler may later optimize dependencies and parallel work, but an advanced
solver is admitted only when a simpler deterministic baseline is insufficient.

## 11. Shopping and package optimization

Generic Shopping remains first:

```text
MealPlan
→ scaled ingredient demand
→ aggregate
→ subtract Pantry
→ ShoppingList
```

Later Retail enrichment may add package selection and real SKU cost.

The useful future objective is not simply "cheapest SKU". It may include:

```text
basket price
+ delivery / service fees
+ expected package surplus / waste
+ additional-store friction
+ user time cost
```

Cross-retailer optimization stays later-stage and cannot block core product
validation.

## 12. Product metrics

The main signal remains repeated trust: the household asks FamilyFoodOS to plan
the next week again.

Real-family validation should additionally measure:

- **Planned Meal Execution Rate** — planned meal events actually followed;
- **Decision-free meals** — eating occasions where the user did not need to
  re-decide what to do;
- **Prep adoption** — use of proposed preparation work;
- **Replan success** — accepted replans after real schedule changes;
- **Recipe/meal acceptance** — planned choice retained vs replaced;
- **Waste signal** — food prepared/bought but discarded;
- **Budget variance** — actual vs planned where actual data exists;
- **time/mental-load signal** — user-reported reduction in weekly effort.

These complement Week 2 / Week 4 retention; they do not replace it.

## 13. PROBE interpretation

The external research proposed a concierge PROBE before a full build. The
repository has already completed substantial deterministic domain work, so the
project does not roll back to a pre-build state.

The useful part is retained: real-family testing should deliberately validate
execution, prep, replan, mental load and willingness-to-pay rather than merely
plan-generation quality.

This is absorbed into the existing Real Family Testing stage of the Master
Roadmap rather than creating a reboot gate.

## 14. Product scope decisions from the external package

### Adopted / integrated

- Household-first positioning;
- household reconciliation / shared-base objective;
- configurable meal patterns rather than dinner-only product design;
- planned leftovers and prepared food as first-class supply;
- ready food / eat-out as legitimate meal sources;
- Reality Loop / dynamic replan;
- cross-recipe ingredient reuse;
- Prep Graph direction;
- package-surplus objective for later Retail;
- outcome metrics centered on execution and cognitive load;
- AI as optional interpretation/explanation layer only.

### Adapted, not copied literally

- "dinners-only MVP" becomes an optional user configuration and possible
  validation cohort, not a domain restriction;
- "Household Reconciliation Engine" is a Planning responsibility, not a new
  network service by default;
- "Reality Engine" is a Planning/revision capability, not a mandatory separate
  deployable;
- advanced solver/service extraction remains evidence-triggered;
- retail package optimization remains after generic Shopping.

### Not adopted

- greenfield rewrite to NestJS/Prisma;
- replacing the existing FastAPI/SQLAlchemy migration path;
- mandatory separate Python optimization microservice before evidence;
- early PostgreSQL/Auth merely to match a reference scaffold;
- AI or Retail as core dependencies.

## 15. Product quality criterion

The central question for every product change remains:

> Does this make it more likely that a real household can live through the
> proposed week with fewer decisions, less avoidable effort and acceptable food,
> cost and safety — and then trust the system again next week?
