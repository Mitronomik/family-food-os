# Handoff

Updated: `2026-09-18`.

## Accepted base and governance

PR #56 is MERGED. The user explicitly authorized the next milestone.

`PR8 — Planner v0` is ACTIVE under Issue #57.

Accepted PR8 implementation base (later Cloud authorization):

`64061b20cc7f9c6106ffbc577871616c53720892`

Accepted SQLite migration head:

`0032_meal_plan_serving`

Future RecipeTemplate reservation remains:

`0033_recipe_template_catalogue`

Issue #57 is the bounded PR8 task contract, subject to canonical repository contracts and any later explicit user-approved decision.

## Current operation

PR8 must establish a deterministic household week-planning baseline before Gate 1.

PR8 implementation constraints and default baseline from Issue #57:

- Planner is filters + bounded scoring/heuristics first; no advanced solver;
- Meal Pattern Recommender ranks only reviewed/published curated program versions and never activates them automatically;
- accepted PR7 member-pattern selections are required for generation;
- `MealRole != RecipeVersion.meal_type_code`; compatibility is explicit/versioned planning logic;
- current autonomous source baseline is authoritative recipe-backed planning; validated Assembly is optional only if an accepted implementation actually exists;
- non-recipe source kinds remain representable, but PR8 does not autonomously choose LEFTOVER/PREPARED/READY_MEAL/ORDER_OUT/EAT_OUT without owning authority;
- fixed user-decided non-recipe events may be preserved;
- current persisted HouseholdMember has no canonical exclusions/preferences model, so PR8 may accept explicit validated generation-time member constraints and must include them in request/trace evidence;
- hard exclusions dominate scoring/sharedness;
- Serving math uses existing Nutrition truth and Decimal semantics; no invented meal-role calorie percentages and no therapeutic goal adjustment;
- preferred v0 Serving baseline is member-wide weekly normalization against existing reference energy truth after the semantic week is selected; an equivalent smaller deterministic heuristic may be used only with documented implementation evidence as allowed by Issue #57;
- budget/cost is not scored as zero while cost truth is unavailable;
- Pantry is read-only Planner signal; no reservation/consumption/Shopping behavior;
- complete week or bounded failure only; no partial MealPlan write;
- new generation/replan creates an append-only MealPlan revision;
- trace includes config/input, candidate pool, rejections, score components, selections, warnings and source choices.

## Schema / migration decision

No new Planner schema/migration is expected by default.

Gate 1 allows trace to be persisted **or otherwise reproducible**. PR8 should first satisfy this with deterministic request/trace representation plus existing immutable plan/source pins and `config_version`.

If implementation evidence proves that Planner persistence is required to satisfy Gate 1 safely:

- stop;
- report the concrete blocker;
- propose a separate migration/reservation decision;
- do not consume or renumber `0033_recipe_template_catalogue` autonomously.

## Required verification

Before review-ready, Issue #57 requires:

- focused Planner/Recommender tests;
- affected Household / MealPattern / Recipe / Nutrition / MealPlan / Pantry tests;
- repository-backed Gate 1 fixture evidence with 3 materially different households, 30 verified recipes and 80+ FoodIngredient;
- hard-exclusion and household-reconciliation fixture coverage;
- full `backend/app/tests` regression;
- `launcher/tests` only if startup/application composition is changed or another concrete startup risk exists;
- Docs verification for changed docs/state;
- final diff/scope audit.

Gate 1 is not automatically COMPLETE merely because PR8 tests pass.

## Canonical invariants

- deterministic core works with `AI_ENABLED=false`;
- Recipe/Nutrition/MealPattern remain authoritative for their truth;
- unknown nutrition/cost/supply stays unknown;
- Household-owned reads/writes are Household-scoped;
- historical MealPlan revisions remain append-only;
- no existing migration history rewrite;
- no PR9, Shopping, Prep, Retail, AI, Auth/PostgreSQL or frontend scope leakage.

## Stop condition

After PR8 is review-ready and merged, stop.

Gate 1 requires separate review/closure. Do not begin PR9 automatically.

## PR8 implementation handoff

The corrected implementation uses `planner-v0.2`, explicit compatibility
`meal-role-recipe-v2`, `meal-pattern-recommender-v2`, member-wide weekly Decimal
normalization, in-memory complete-week reconciliation, bounded failures and
fingerprinted traces. It adds no migration; SQLite head remains `0032` and the
`0033_recipe_template_catalogue` reservation is untouched. See
`docs/family-food/planner-v0.md` for the exact algorithm and repository-backed
fixture result. Gate 1 remains NOT STARTED because all 30 current verified recipe
nutrition results have unknown kcal and therefore correctly fail eligibility.
PR #59 final re-review remains conditional only on exact-head full backend
verification in GitHub Actions because the Cloud image lacks `httpx`.
