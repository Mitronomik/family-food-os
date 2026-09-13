# FamilyFoodOS — Meal Pattern Programs & Recommendation Contract

**Status:** canonical product/domain contract  
**Decision date:** 2026-09-13  
**Applies to:** HouseholdMember planning profile, MealPlan/Serving, Planner, Nutrition integration and onboarding

## 1. Why this contract exists

FamilyFoodOS must not hardcode one eating schedule for every person.

A user may want:

- only dinner;
- only breakfast;
- breakfast and dinner;
- breakfast, lunch and dinner;
- three meals plus snacks;
- five or six planned eating occasions;
- a different pattern for another HouseholdMember.

The product therefore needs both:

1. a **custom meal-pattern constructor** chosen directly by the user; and
2. a **deterministic Meal Pattern Recommender** that can propose a suitable
   curated wellness program based on known member goals and context.

The user remains in control: a recommended program is never silently applied.

## 2. Terminology

### Meal role

A semantic role such as:

```text
BREAKFAST
LUNCH
DINNER
SNACK
PRE_WORKOUT
POST_WORKOUT
OTHER
```

The final machine-code set belongs to the implementation PR. Consumer display
text is Russian under the Russian-language contract.

A role is not a fixed clock time and does not imply that every member uses it.

### Meal opportunity

One planned eating occasion for one member on one local calendar day.

### Household meal event

A shared opportunity at which one or more members may participate. It can have
one common meal/assembly and different Servings or variants.

### Meal Pattern Program

A platform-owned, versioned, curated set of planning rules describing a
wellness-oriented daily eating pattern. It is not a free-form LLM output and not
a medical treatment prescription.

### Member Meal Pattern Selection

The member-specific accepted configuration used by Planner. It may originate
from a curated program or from a custom user configuration.

## 3. Initial flexibility requirement

The initial product must be able to plan one to six eating occasions per day for
a member without schema redesign.

The model should remain extensible; `6` is an initial validated UX/product range,
not a permanent database-law maximum.

A member may use a different count on different days where schedule rules allow
it. The Planner must not assume that all seven days have an identical slot set.

## 4. Custom mode

The simplest valid path is direct user choice.

Conceptually:

```text
MemberPlanningProfile
├── enabled meal opportunities
├── preferred roles
├── optional time windows
├── meals-at-home / away schedule
└── user-confirmed overrides
```

The UI should offer useful presets but must also allow an explicit custom pattern.

Examples:

```text
Dinner only
Breakfast + dinner
3 meals
3 meals + 2 snacks
Custom
```

The user should not need to understand internal program codes.

## 5. Deterministic recommendation, not "magic diet selection"

The Meal Pattern Recommender is deterministic and versioned.

It may use structured facts such as:

- age group;
- current product-supported goal;
- activity level;
- schedule / workday structure;
- training schedule where explicitly provided;
- meals normally eaten at home;
- cooking constraints;
- user preference for fewer vs more eating occasions;
- adherence/history signals when available.

It returns ranked **curated programs**, not an invented plan.

Conceptual output:

```text
MealPatternRecommendation
├── recommender_version
├── member_id
├── candidate_programs[]
│   ├── program_id/version
│   ├── fit_score
│   ├── reasons[]
│   ├── cautions[]
│   └── evidence/uncertainty summary
└── no_safe_recommendation_reason?
```

A recommendation is a proposal. User confirmation creates or changes the member's
active selection.

## 6. Evidence boundary

Meal frequency must not be encoded as if one universal number of meals were
scientifically optimal for weight loss, health or athletic performance.

Current evidence does not support such a universal rule:

- the 2025 Dietary Guidelines Advisory Committee systematic review concluded
  that evidence was insufficient to draw a general conclusion about meal/snack
  frequency and alignment with healthy dietary patterns;
- a 2023 systematic review/meta-analysis of randomized trials found no
  discernible overall advantage of higher vs lower eating frequency for
  cardiometabolic health in generally healthy adults and rated the evidence as
  very low certainty;
- sports nutrition evidence does not establish that simply increasing eating
  frequency universally improves body composition or energy expenditure.

Therefore the recommender must optimize **fit, practicality, target nutrient
allocation and adherence**, not claim that "five meals is better than three".

References:

- USDA Nutrition Evidence Systematic Review, 2025 DGAC — Frequency of meals and
  snacks and diet quality:
  https://nesr.usda.gov/2025-dietary-guidelines-advisory-committee-systematic-reviews/frequency-meals-snacks_diet-quality
- Leech et al. / systematic review of eating frequency and cardiometabolic
  outcomes, PMID 37964316:
  https://pubmed.ncbi.nlm.nih.gov/37964316/
- International Society of Sports Nutrition position stand on meal frequency,
  PMID 21410984:
  https://pubmed.ncbi.nlm.nih.gov/21410984/

## 7. Program model

A program should be immutable/versioned once published.

A target shape may include:

```text
MealPatternProgram
├── id
├── code
├── version
├── Russian display name / explanation
├── lifecycle status
├── wellness_scope = true
├── eligible age groups
├── supported goals
├── supported activity/training contexts
├── daily opportunity template
├── role sequence / allowed role alternatives
├── optional time-window guidance
├── optional energy-distribution ranges
├── optional protein-distribution guidance
├── minimum spacing / scheduling rules where evidence-backed
├── exclusions / safety gates
├── provenance[]
├── evidence grade / confidence
└── created_at / published_at
```

Not every program needs every field. Missing evidence must not be converted into
invented precision.

## 8. Program examples are data, not architecture

The architecture may support program families such as:

- regular three-meal day;
- two main meals with an additional optional snack;
- three meals plus one or two snacks;
- training-day pattern with a planned pre/post-training eating opportunity;
- high-energy-demand pattern with more distributed eating opportunities;
- custom household-defined pattern.

These are examples only. A program is not accepted into production merely
because its name sounds plausible.

Each production program requires:

- explicit target population;
- provenance/evidence;
- safety review;
- Russian user-facing text;
- deterministic rules;
- tests;
- versioning.

## 9. Medical and safety boundary

The MVP recommender is a wellness/productivity feature, not a clinical diet
prescriber.

It must not:

- diagnose a condition;
- recommend treatment for a disease;
- convert a diagnosis into a therapeutic diet;
- claim a meal frequency treats obesity, diabetes or another condition;
- use an adult weight-loss pattern as a default for children;
- silently recommend fasting or extreme restriction because of a weight goal.

If a member context requires a medical/therapeutic regimen outside the verified
wellness corpus, the recommender must return a bounded unsupported/safety state
rather than improvise.

A future medical module would require a separate evidence, regulatory and safety
contract.

## 10. Children and age-specific programs

Child nutrition requires age-specific rules and cannot inherit adult frequency
logic by default.

Where FamilyFoodOS supports young-child meal-pattern recommendation, the program
must use authoritative age-specific sources. For example, WHO guidance for
children 6–23 months defines minimum complementary-feeding frequencies that vary
by age and breastfeeding status; this is evidence that age-specific program
logic is necessary, not permission to generalize one infant schedule to older
children.

Reference:
https://www.who.int/data/gho/data/indicators/indicator-details/GHO/minimum-meal-frequency-6-23-months

Until a child program has an approved evidence package, the product may support
manual schedule configuration without issuing a normative automated
recommendation.

## 11. Relationship to Nutrition Engine

MealPatternProgram does not own nutrient truth.

Nutrition Engine remains authoritative for:

- energy and nutrient targets;
- recipe/serving nutrition;
- member/day/week aggregation;
- warnings and target-range evaluation.

A program may contain an evidence-backed distribution policy, for example a
percentage range of daily energy or protein across eating occasions. Nutrition
Engine calculates the resulting numbers.

The program never stores a second competing nutrition calculation.

## 12. Relationship to Planner

Planner receives the accepted member selections and compiles them into household
meal events.

### 12.1 MealRole is not RecipeVersion.meal_type_code

The planning role and the already implemented Recipe Catalogue classification
are separate concepts.

Canonical invariant:

```text
MealRole != RecipeVersion.meal_type_code
```

Current `RecipeVersion.meal_type_code` values such as `breakfast`, `main`,
`side`, `salad`, `sandwich` and `other` classify catalogue recipes/components.
They are not the HouseholdMember schedule enum and must not be renamed, migrated
or expanded with `DINNER`, `LUNCH`, `PRE_WORKOUT` or similar values merely to
express meal opportunities.

Planner/selection uses an explicit deterministic suitability rule or mapping
between a `MealRole` and compatible RecipeVersion/RecipeAssembly candidates.
For example, a dinner event may compose `MAIN` plus compatible `SIDE`/`SALAD`
components, while a breakfast role may prefer the existing `breakfast` class
plus other explicitly approved compatible candidates.

The exact mapping/versioning belongs to the owning implementation PR. It must not
create a second source of Recipe Catalogue truth.

See `architecture-addendum-2026-09-13.md` for the canonical compatibility rule.

Conceptually:

```text
accepted member patterns
+ member schedules
+ hard exclusions
+ candidate food/recipes
+ nutrition targets
→ household event candidates
→ reconciliation/sharedness scoring
→ MealPlan + Servings
```

Planner must support heterogeneous households. Example:

- member A: 3 eating occasions;
- member B: 5 eating occasions;
- child: age-appropriate custom/approved pattern;
- dinner is shared by all three;
- lunch may include only A and the child;
- snacks can be member-specific without forcing extra family cooking.

This is the practical meaning of household reconciliation.

## 13. Common-base objective

When multiple members participate in the same household event, Planner should
prefer one shared preparation where possible.

It may vary:

- Serving quantity;
- optional sauce;
- allowed garnish/component;
- final assembly;
- protein choice when the validated assembly model supports it.

It may not vary away a hard safety constraint after selection.

## 14. User control and explanation

The consumer flow should be:

```text
system proposes a meal pattern
→ user sees why it may fit
→ user accepts / chooses another / customizes
→ Planner uses accepted pattern
```

The product must always permit the user to select a custom schedule without
pretending that the recommender knows a single medically correct meal frequency.

Explanations should be concrete and non-clinical, for example:

- "подходит под ваш график и три приёма пищи дома";
- "добавляет перекус вокруг тренировки";
- "меньше отдельных приёмов пищи — проще соблюдать при вашем графике".

## 15. Versioning and history

The member selection should retain:

- source program ID/version or `CUSTOM`;
- recommender version when recommended;
- accepted timestamp;
- user overrides;
- superseded previous selection where history is needed.

Historical MealPlans retain the pattern/program version used to generate them.
Changing a member's pattern changes future planning; it must not rewrite old
plans.

## 16. Tests and invariants

Implementation must cover at least:

- dinner-only member;
- breakfast-only member;
- breakfast + dinner;
- 3-meal member;
- 5-meal member;
- 6-opportunity member;
- heterogeneous household schedules;
- a shared dinner compiled from different member patterns;
- recommendation reproducibility for the same input/version;
- user rejection / custom override;
- unsupported/safety state instead of improvised medical recommendation;
- no adult program automatically applied to a child outside its eligibility;
- existing `RecipeVersion.meal_type_code` remains recipe classification rather
  than being repurposed as a member schedule enum;
- MealPlan history retaining the accepted program version.

## 17. Roadmap integration

This contract does not create a new microservice or re-platform the backend.

Expected implementation ownership:

- PR7 / MealPlan-Serving domain: model meal opportunities, participation and
  accepted member pattern reference;
- PR8 / Planner v0: deterministic recommendation v0, household compilation and
  reconciliation behavior;
- consumer onboarding: proposal/accept/custom UX;
- Feedback later: adherence signals can improve ranking without AI.

Any materially larger split requires a later explicit roadmap decision.
