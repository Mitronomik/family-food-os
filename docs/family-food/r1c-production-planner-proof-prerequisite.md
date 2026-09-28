# R1-C — Production Planner Proof Prerequisite Contract
**Status:** docs-only preflight / blocker contract
**Decision date:** 2026-09-28
**Accepted base:** `b27ab1e6338fd0ae76f25ce0040416fc15780891` (merged PR #107)
**Parent:** #99, #100, #67
## 1. Goal
R1-C must prove that the production Planner can generate and persist a real
repository-backed household week using ordinary active R1 RecipeVersions and
their deterministic V2 Nutrition truth.
This proof must not substitute:
- synthetic Planner candidates;
- gate-only nutrition;
- inactive R1 RecipeVersions;
- input-composition energy presented as cooked-dish energy;
- invented yield/retention;
- non-R1 legacy recipes merely to make the proof pass.
## 2. FACT — #100 is closed and Planner allocation authority is now v0.4
PR #107 merged into `main` at:
`b27ab1e6338fd0ae76f25ce0040416fc15780891`.
The authoritative Planner path now uses:
`planner-v0.4`
with:
`meal-role-recipe-v2`.
Therefore the older text in issue #99 that names `planner-v0.3` is superseded by
the later merged #100 decision. Historical v0.3 plans remain historical truth;
new R1-C production proof must use v0.4.
## 3. FACT — current R1 production candidate count is zero
R1-B reviewed five USSR82 candidates.
Current accepted dispositions:
| Source recipe | Current disposition |
| --- | --- |
| USSR82-697 — Курица отварная | published, **inactive** |
| USSR82-453 — Яйца вареные | BLOCKED — V2 Composition authority missing for EGG |
| USSR82-1081 — Блины | BLOCKED — V2 Composition authority missing for BUTTER_UNSALTED |
| USSR82-467 — Омлет | BLOCKED — required salt quantity unquantified |
| USSR82-492 — Сырники | BLOCKED — required salt quantity unquantified |
The R1-B publication code intentionally returns:
`activated_count = 0`.
USSR82-697 is persisted with:
`initial_is_active = false`
and package disposition:
`INACTIVE_PENDING_TRANSFORMATION_AUTHORITY`.
Therefore an ordinary production catalogue read cannot currently expose any active
R1 RecipeVersion to Planner.
## 4. FACT — R1-B Nutrition is input-composition truth, not final cooked-dish truth
USSR82-697 has exact reviewed input Composition bindings:
- CHICKEN_CATEGORY_1_RAW;
- ONION_BULB_FRESH.
Its deterministic V2 input-composition energy is:
`255.892000 kcal`.
Its source-backed output is:
`75 g`
for the selected cooked main-product branch.
These facts do **not** authorize:
- treating 255.892 kcal as exact consumed cooked-dish energy;
- deriving a reusable chicken-boiling yield factor from 75/107;
- inferring nutrient retention;
- assuming cooking water/root losses;
- activating the RecipeVersion for Planner.
R1-B explicitly froze those non-inferences.
## 5. FACT — Step 7 currently publishes no production numeric transformation authority
The accepted transformation-applicability contract intentionally published zero
production numeric transformation/yield/retention factors from the retained
Russian corpus.
It requires any later numeric authority to have its own reviewed:
- exact source/process identity;
- exact FoodIngredient applicability;
- yield/retention evidence where used;
- registry binding;
- rights/provenance receipt;
- season/source applicability as required.
A source-published dish output is not automatically a reusable
FoodTransformation/YieldModel/RetentionProfile.
## 6. DECISION — R1-C must fail closed at preflight while active R1 candidates = 0
R1-C cannot claim product success until at least one R1 RecipeVersion is:
1. source-backed and immutable;
2. active in the ordinary Recipe Catalogue;
3. exact-energy-ready through the accepted V2 consumption projection;
4. safe under current food/form/process authority;
5. eligible through normal Planner catalogue reads.
Until those conditions exist, R1-C may only report a bounded prerequisite blocker.
No synthetic candidate or legacy non-R1 candidate may be used to satisfy the R1-C
success path.
## 7. DECISION — activation requires a separately reviewed authority operation
The next permissible support operation is a bounded reviewed activation-authority
step for an R1 recipe.
For USSR82-697, that operation must first prove an accepted way to represent the
cooked recipe's consumption Nutrition without violating Step 7 or R1-B.
It may reuse existing models only if the evidence actually supports them.
It must not silently choose one of these interpretations:
- recipe output mass as reusable FoodTransformation yield;
- recipe output mass as a generic cooked-chicken composition;
- source-declared output as nutrient-retention evidence;
- input energy as final cooked serving energy.
If current models cannot truthfully represent the evidence, stop for a separate
Implementation Contract Gate before schema/runtime expansion.
## 8. OPEN QUESTION — exact authority route for USSR82-697
Before activation, review must determine which evidence-backed route is valid:
### Route A — reusable exact FoodTransformation authority
Allowed only if retained evidence supports the exact:
- CHICKEN_CATEGORY_1_RAW food identity;
- boiling process;
- output state;
- yield;
- retention behavior required by V2 Nutrition;
- applicability scope.
One recipe-card output alone is not sufficient evidence for a reusable generic
transformation unless explicitly reviewed as such.
### Route B — recipe-specific cooked-output Nutrition/consumption authority
If the source supports the prepared recipe output but not a reusable generic food
transformation, a recipe-specific authority may be more truthful.
This is not currently an accepted architecture path and would require its own
Implementation Contract Gate before runtime/schema changes.
### Route C — remain blocked
If neither route has adequate evidence, USSR82-697 remains inactive and R1-C
cannot produce a successful R1 week yet. The project then returns to the accepted
corpus programme to close additional R1/R2 candidates rather than weakening
truth.
## 9. R1-C acceptance after prerequisite closure
Once ordinary active R1 candidate truth exists, R1-C must prove at least:
1. PlannerService reads active R1 RecipeVersions from the normal repository path;
2. neutral V2 projection is exact-energy-ready and positive;
3. Planner version is `planner-v0.4`;
4. compatibility remains `meal-role-recipe-v2`;
5. repository-backed households include materially different accepted meal patterns;
6. at least one complete seven-day plan is generated and persisted;
7. individualized Servings are plausible under frozen opportunity shares;
8. deterministic replay produces the same semantic week and trace fingerprint;
9. one bounded infeasible case returns explicit failure and persists no partial plan;
10. one hard FoodIngredient exclusion removes every affected R1 candidate while
    preserving other members/sharedness;
11. no automatic allergen-filtering claim is made without separately reviewed
    allergen truth;
12. AI is not required.
## 10. Required R1-C product metrics
The proof must report before/after:
- selected R1 recipes accepted / blocked;
- active Planner-eligible R1 RecipeVersions;
- exact-energy-ready active R1 RecipeVersions;
- breakfast candidate count;
- main candidate count;
- materially different repository-backed household patterns proven;
- successful persisted complete weeks;
- explicit infeasible outcomes;
- remaining authority blockers.
## 11. Non-goals
This prerequisite does not authorize:
- publication of numeric transformation/yield/retention data;
- activation of USSR82-697;
- new Food/Nutrition authority;
- new schema/migration;
- R2/R3 corpus expansion;
- Gate1-CLOSE;
- Shopping/PR9;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.
## 12. Sequence
```text
PR107 / #100 merged
→ R1-C preflight
→ active R1 candidate count = 0
→ reviewed activation-authority prerequisite
→ active exact-energy-ready R1 RecipeVersion(s)
→ R1-C production Planner proof
→ R2/R3 corpus expansion
→ DC4 / Gate1-CLOSE
→ PR9 Shopping
```
Do not skip the activation-authority prerequisite by using synthetic or inactive
recipe truth.