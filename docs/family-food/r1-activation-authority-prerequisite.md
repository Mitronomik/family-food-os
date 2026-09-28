# R1 Activation Authority Prerequisite
**Status:** docs-only reviewed authority gate
**Decision date:** 2026-09-28
**Accepted base:** `b6973baa2f93ecfaded9c93cb7e5711300f247ee` (merged PR #108)
**Parent:** #99, #108, #67
## 1. Goal
Determine whether the currently published but inactive R1 RecipeVersion
`USSR82-697 — Курица отварная` can be truthfully activated for ordinary
production Planner use under the accepted Step 7 and Step 10 Nutrition contracts.
This gate reviews authority only. It does not publish transformations, retention,
Nutrition, RecipeVersion revisions or activation state.
## 2. FACT — current production state
R1-B published one R1 RecipeVersion:
`USSR82_697_BOILED_CHICKEN`.
It remains inactive with the reviewed disposition:
`INACTIVE_PENDING_TRANSFORMATION_AUTHORITY`.
The production Planner reads only active Recipe catalogue truth. Therefore R1-C
cannot use this recipe until activation authority is closed.
## 3. FACT — exact source recipe/process truth
The selected branch is USSR82 recipe 697, variant III, chicken, main product only,
without garnish or sauce.
R1-B already pins:
- CHICKEN_CATEGORY_1_RAW — 107 g net;
- ONION_BULB_FRESH — 2 g net;
- cooked main-product output — 75 g;
- source-backed boiling instructions;
- deterministic V2 input-composition energy — 255.892000 kcal.
The accepted R1-B contract explicitly forbids interpreting the 75 g output as an
automatic yield/retention authority.
## 4. Reviewed corroboration — USSR82 Table 23
The same 1982 collection contains Table 23,
“Расчет расхода сырья, выхода полуфабрикатов и готовых изделий из птицы
сельскохозяйственной”.
For category-I semi-eviscerated chicken, whole, boiling, the reviewed row matching
the selected recipe branch records:
- net/semifinished chicken mass: 107 g;
- thermal loss: 28% of net/semifinished mass;
- portioning loss after cooking: 3%;
- finished product mass: 75 g.
The recipe 697 technology explicitly points to Table 23 for portioning loss.
Public corroboration references:
- recipe 697:
  `https://www.interdoka.ru/kulinaria/1982/11_bluda_ptica/1.html`;
- Table 23:
  `https://interdoka.ru/kulinaria/1982/21_prilojenia/3-ptica/5-1.html`.
These public pages corroborate the retained source facts. Production publication
still requires the repository's normal hash-pinned retained-source receipt; a web
page alone is not the durable authority boundary.
The Table 23 row is specifically for **category-I semi-eviscerated whole chicken**.
The current canonical identity is `CHICKEN_CATEGORY_1_RAW / Курица 1 категории,
сырая`; it does not itself persist the semi-eviscerated/whole form qualifier.
Therefore the row-to-recipe mass match does not, by itself, prove exact Step 7
FoodIngredient applicability.
## 5. DECISION — Table 23 can support mass/process review, not Nutrition retention
The Table 23 row is sufficient evidence to review the exact **source-branch**
process/mass relation.
It is not yet sufficient to publish `TransformationApplicability` for
`CHICKEN_CATEGORY_1_RAW`: exact canonical form applicability still requires a
reviewed mapping receipt under Step 7.
It also does **not** provide nutrient-specific V2 retention factors.
It therefore does not by itself authorize exact final:
- ENERGY_KCAL;
- protein;
- fat;
- carbohydrate;
- micronutrient
content of the 75 g cooked output.
The 2 g onion is a recipe/process input and the 75 g output is explicitly the
boiled poultry mass, not a 109 g whole-recipe output transformation. No onion or
broth nutrient transfer into the final meat may be invented.
## 6. FACT — generic nutrient-loss guidance is insufficient for this activation
Reviewed external guidance exists for generalized nutrient losses during cooking,
including animal/meat categories.
That guidance is not an accepted exact `CHICKEN_CATEGORY_1_RAW + boiling`
retention authority under Step 7.
In particular:
- category-level guidance is not automatically exact FoodIngredient applicability;
- the current repository has no reviewed V2 ENERGY_KCAL retention package for this
  exact chicken/process;
- the 2026 Rospotrebnadzor methodology that includes generalized energy-loss
  guidance has an effective date after this gate date and is not accepted project
  authority for this publication.
No generic loss table is promoted by this gate.
## 7. FACT — current Recipe Nutrition calculation cannot consume transformed bindings
Current `RECIPE_COMPOSITION_NUTRITION_V1` calculates RecipeVersion Nutrition from
required gram RecipeIngredient rows bound to FoodComposition authority.
Its current calculation path explicitly requires each bound composition to be:
- `MassState.INPUT`;
- untransformed;
- without composition steps.
A transformed chicken Composition produced through Step 7 therefore cannot be
silently substituted into the current Recipe Nutrition calculation.
Changing that rule would create a new versioned Recipe Nutrition calculation
contract and requires a separate Implementation Contract Gate.
## 8. Route review
### Route A — reusable exact FoodTransformation authority
**Disposition: SOURCE MASS PATH SUPPORTED, CANONICAL AUTHORITY INCOMPLETE.**
Supported evidence:
- exact USSR82 source process branch;
- exact 107 g source chicken input basis;
- boiling;
- exact source mass-loss/output relation to 75 g;
- explicit portioning loss.
Missing authority:
- reviewed exact applicability from the source's semi-eviscerated/whole chicken
  form to `CHICKEN_CATEGORY_1_RAW`;
- exact V2 nutrient retention, including ENERGY_KCAL;
- accepted retained-source publication receipt for the Table 23 numeric process
  package;
- Recipe Nutrition calculation version capable of consuming transformed
  Composition authority.
Therefore Route A cannot currently produce an exact-energy-ready production
RecipeVersion.
### Route B — recipe-specific cooked-output Nutrition authority
**Disposition: NOT SUPPORTED BY CURRENT EVIDENCE / CURRENT ARCHITECTURE.**
The reviewed recipe source provides cooked output mass and technology, but no
source-backed cooked nutrient analysis for the selected 75 g chicken output.
Current Recipe Nutrition has no persisted recipe-output Nutrition authority kind.
Creating such a path without numeric source evidence would only move invented
precision into a new schema.
Route B is rejected for the current R1 evidence.
### Route C — remain blocked
**Disposition: SELECTED.**
`USSR82-697` remains inactive.
This is not a failure of the Planner. It is an explicit data/authority boundary:
the system has source-backed recipe/process truth but not enough accepted consumed
Nutrition truth to expose the recipe as an exact-energy Planner candidate.
## 9. DECISION — no activation runtime is authorized after this gate
Merging this gate does **not** authorize:
- changing `is_active`;
- publishing YieldModel or NutrientRetentionProfile;
- publishing TransformationApplicability;
- binding a transformed composition into Recipe Nutrition;
- changing Recipe Nutrition calculation version;
- creating recipe-output Nutrition tables;
- using generalized loss factors as exact authority.
Activation remains blocked.
## 10. Next allowed bounded R1 operation
The next operation must remain inside R1 and close one of these evidence paths:
### Option 1 — exact transformed-consumption authority for USSR82-697
Requires, before runtime:
1. retained/hash-pinned Table 23 process receipt for the exact selected chicken
   branch;
2. reviewed exact FoodIngredient applicability for the Table 23 source form;
3. reviewed exact nutrient-retention authority sufficient to produce positive
   exact ENERGY_KCAL under RU_NUTRIENT_REGISTRY_V2;
4. a docs-only Implementation Contract Gate for the next Recipe Nutrition
   calculation version that can consume applicability-aware transformed
   Composition;
5. fresh/replay/conflict/rollback and historical-preservation rules.
Only after all five are accepted may activation runtime be proposed.
### Option 2 — another R1 candidate
Review another already selected R1 candidate under the same truth standard.
It may proceed only if its Food/Nutrition/process authority can be closed without
weakening unknown != zero, raw != cooked or provenance rules.
R2 remains out of scope until successful R1-C unless the user explicitly changes
sequencing.
## 11. Preservation requirements for any future transformed Recipe Nutrition gate
Any later calculation-contract gate must preserve:
- historical `RECIPE_COMPOSITION_NUTRITION_V1` results and bindings;
- existing Step 10-A immutable binding history;
- planner-v0.3 historical replay;
- planner-v0.4 allocation semantics;
- RecipeVersion immutable source truth;
- R1-B source output fields;
- Step 7 exact applicability requirements;
- unknown nutrients as unknown;
- no implicit 100% retention;
- no input-energy fallback for cooked consumption.
A new calculation version must be explicit and version-pinned in resulting
Nutrition provenance.
## 12. R1-C impact
Before this gate:
- active Planner-eligible R1 RecipeVersions: 0;
- exact-energy-ready active R1 RecipeVersions: 0.
After this docs-only gate:
- active Planner-eligible R1 RecipeVersions: 0;
- exact-energy-ready active R1 RecipeVersions: 0.
R1-C remains preflight-blocked.
The gate improves the project by replacing an ambiguous “pending transformation”
label with an exact reviewed authority disposition and a bounded next path.
## 13. Non-goals
This gate does not authorize:
- runtime code;
- schema/migration;
- transformation/yield/retention publication;
- Recipe activation;
- new FoodIngredient or Nutrition profile;
- R2/R3;
- DC4 / Gate1-CLOSE;
- Shopping/PR9;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.
## 14. Sequence
```text
PR108 merged
→ R1 activation-authority review
→ USSR82-697 Route C: remains inactive
→ bounded R1 authority closure
   ├─ exact transformed-consumption authority + new Recipe Nutrition contract
   └─ or another selected R1 candidate
→ active exact-energy-ready R1 production candidate(s)
→ R1-C production Planner proof
→ R2/R3
→ DC4 / Gate1-CLOSE
→ PR9 Shopping
```
Do not reinterpret this gate as permission to activate from mass-output evidence
alone.
