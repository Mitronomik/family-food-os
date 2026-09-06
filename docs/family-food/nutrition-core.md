# PR6 Nutrition Core

Status: canonical PR6 implementation/calculation contract; engine ACCEPTED / MERGED
in PR #18 at `7c449672c039c66b8d475064462eba2a9f6d38e6`.
PR6 milestone NOT COMPLETE, pending data readiness / closure.
Version: `FAMILY_FOOD_NUTRITION_V1`. Implementation is on demand with
`AI_ENABLED=false`; no remote formula loading or LLM calculation.

## Boundary and composition

```text
FoodIngredient + current FoodNutritionProfile
→ immutable RecipeVersion detail nutrition
→ member reference-target formula/config foundation
```

`NutritionService` exposes `food_ingredient`, `recipe_version` and
`member_reference_target` application operations. There are no public HTTP
endpoints or frontend changes. The existing catalogue and Household models
remain authoritative. No derived-result persistence, caches, second nutrition
history or new schema is introduced; migration head remains `0025_pantry`.

A calculation enters `NutritionReadScope` once. The SQLAlchemy Core adapter
composes existing repositories on one project `SqlAlchemyReadOnlyScope`
connection/transaction, including the RecipeVersion read and all current-profile
lookups. The accepted SQLite engine uses `autocommit=False`; even SELECTs share
the transaction snapshot. Exit always rolls back and closes; no write UoW is
needed. Contracts expose read methods and domain objects, never driver objects.
Member lookups require both Household and member identifiers.

Serving, MealPlan, member/day/week aggregation, Planner, Shopping, Pantry use,
Prep, Retail, AI and medical policies are outside PR6. In particular,
`per_base_serving` is only `required_total / RecipeVersion.base_servings`.
It creates no Serving entity or personalized allocation.

## Ingredient calculation and provenance

For each nutrient, compute `profile_value × mass_g / profile.basis_grams`.
The existing `FoodNutritionProfile` owns the current 100 g edible-portion basis,
source kcal and nutrients. Ingredient kcal is never reconstructed from macros.

- `g`: the normalized RecipeIngredient quantity is the exact gram input.
  No additional `edible_fraction` transformation is applied.
- `ml`: multiply by the canonical positive `density_g_per_ml` only. Missing
  density produces `MISSING_DENSITY` and unavailable contribution values.
  There is no water-density or category fallback.
- `pcs`: `UNSUPPORTED_PIECE_MASS`; v1 has no reviewed grams-per-piece metadata.
  Neither eggs nor other piece quantities acquire an assumed weight.

`IngredientNutrition` contains the immutable canonical FoodIngredient and exact
FoodNutritionProfile input, quantity, unit, resolved mass, values, warnings,
status and config. Retaining the existing objects avoids a parallel nutrition
model and preserves profile UUID, source name/id/version/type, verified instant,
estimation flag, values and basis. Ingredient metadata includes the exact density
and update instant. A mismatched or non-current supplied profile is rejected.
A missing current profile produces `MISSING_NUTRITION_PROFILE`, never zero.

`RecipeIngredientNutrition` retains the immutable recipe row alongside its
contribution, including normalization/source text, row ID, unit and optional flag.
`RecipeVersionNutrition.version` retains version identity, base servings and
recipe source/hash provenance. Every row's resolved profile is available even
when its mass conversion fails. Repeated FoodIngredient references are loaded
once per calculation, but warnings retain individual row context.

Results identify the inputs actually read, not the nutrition state that happened
to exist when the RecipeVersion was published. Later on-demand calls may see a
new current profile or density. No calculation overwrites catalogue history.
A future authorized historical consumer must snapshot/reference exact inputs and
config; PR6 does not promise historical replay from RecipeVersion ID alone.

## Result semantics

`NutritionValues` contains nullable Decimal `kcal`, `protein_g`, `fat_g`,
`carbohydrates_g`, `fiber_g`. Unknown is `None`, independently of numeric zero.

| Status | Meaning |
| --- | --- |
| `COMPLETE` | All five ingredient/required-recipe nutrients available, no warnings or optional rows. |
| `COMPLETE_WITH_WARNINGS` | Energy and three macros available, with explicit uncertainty; fiber may be unknown. Member EER always carries `REFERENCE_ESTIMATE`. |
| `CONDITIONAL` | Required recipe energy/macros available, but optional rows exist as separate contributions. |
| `INCOMPLETE` | Required mass/profile/ingredient input unavailable, or member EER unavailable. |

Status is not a substitute for per-nutrient availability. Unknown fiber alone
produces `UNKNOWN_FIBER`, preserves known energy/macros and leaves fiber `None`.
`estimated=True` produces `ESTIMATED_SOURCE`; `estimated=None` produces
`ESTIMATION_STATUS_UNKNOWN`. Neither blocks supported numeric arithmetic or
silently becomes a verified exact source.

Required rows are summed before rounding. An unavailable required contribution
propagates `None` to each affected authoritative nutrient, including its
per-base-serving value. Diagnostic component contributions remain visible but
are never returned as an authoritative partial sum. There is no partial-total
fallback. A required failure takes precedence over optional/uncertainty status.

Optional rows never enter `required_total` or `per_base_serving`. They appear in
`optional_contributions` and each produces `OPTIONAL_INGREDIENT`, even when its
own contribution cannot be calculated. A recipe with only optional rows has an
empty required sum (zero) and conditional status. This does not describe the
nutrition of a chosen optional combination.

Warning order is fixed: recipe position order, then missing ingredient or
conversion, profile absence, unknown fiber, estimation flag, optional flag.
Member warnings follow the input-validation sequence in the implementation.
No sets, random IDs or current timestamps are introduced into results.

## Formula/config and primary sources

All constants are checked in at
[`nutrition_config.py`](../../backend/app/domain/nutrition_config.py).
Changing coefficients, rounding, age policy, supported mappings or behavior
requires a new configuration version, not a silent v1 edit.

| Result config field | Pinned identifier |
| --- | --- |
| `version` | `FAMILY_FOOD_NUTRITION_V1` |
| `eer_version` | `NASEM_EER_2023_V1` |
| `amdr_version` | `DRI_AMDR_2002_2005_V1` |
| `fiber_version` | `DRI_TOTAL_FIBER_AI_2002_2005_V1` |
| `atwater_version` | `ATWATER_GENERAL_4_4_9_V1` |
| `age_policy_version` | `COMPLETED_CHRONOLOGICAL_YEARS_V1` |
| `rounding_version` | `DECIMAL_80_HALF_UP_6DP_V1` |

Primary references, verified 2026-09-06:

1. National Academies of Sciences, Engineering, and Medicine (2023),
   *Dietary Reference Intakes for Energy*, DOI `10.17226/26818`,
   [Chapter 5, Tables 5-15 and 5-16, pp. 99–101](https://www.nationalacademies.org/read/26818/chapter/7).
   The implementation transcribes intercept/age/height/weight coefficients for
   the supported sex/PAL rows. Height is cm; weight is kg; age is years.
   Child growth additions follow Table 5-15 footnotes b/c and pp. 98–100:
   boys/girls at 3: 20/15 kcal; 4–8: 15/15; 9–13: 25/30; 14–18: 20/20.
   Adult equations begin at 19 and add no growth allowance.
2. Institute of Medicine (2002/2005), *Dietary Reference Intakes for Energy,
   Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and Amino Acids*.
   The National Academies' 2019 DRI Appendix J reproduces the source tables:
   [AMDR, table appJ_tab5](https://www.ncbi.nlm.nih.gov/books/NBK545442/table/appJ_tab5/)
   and [Total Water and Macronutrients, table appJ_tab4](https://www.ncbi.nlm.nih.gov/books/NBK545442/table/appJ_tab4/).
   Only carbohydrate/protein/fat ranges and supported Total Fiber AI cells are
   transcribed. Fiber uses the fixed AI, with no interpolation or EER rescaling.
3. FAO, *Food energy — methods of analysis and conversion factors*, Food and
   Nutrition Paper 77 (2003),
   [section 3.5.1](https://www.fao.org/4/y5022e/y5022e04.htm).
   General Atwater carbohydrate/protein/fat factors are 4/4/9 kcal per gram.
   PR6 uses them only for AMDR fraction-of-reference-energy → gram bounds.

Full copyrighted source tables are not copied into the repository. Member
results carry the source URLs, table/section locators, configuration identifiers
and the selected EER table and growth allowance.

## Supported member inputs and uncertainty

`calculate_member_reference_target` requires an explicit date (not datetime).
Age is completed chronological years; formula and growth bands switch on the
birthday. For February 29 births, a non-leap year's age increment occurs March 1.
Supported ages start at 3, with children/adolescents through completed age 18.
Under-3, missing birth dates and birth dates after `as_of_date` return no EER.

Only exact Household-normalized sex codes `male` and `female`, and PAL codes
`inactive`, `low_active`, `active`, `very_active` are supported. No sex is inferred.
`moderate`, `sedentary`, case variants and arbitrary strings receive explicit
unsupported warnings; existing Household storage and rows remain unchanged.
Height and weight must be present, finite, positive Decimal values within the
existing Household sanity bounds. Nonpositive computed EER is unavailable.

`MemberReferenceNutritionTarget` contains the explicit date, completed age,
reference energy, three `ReferenceGramRange` values (bounds, source energy
fractions and factor), fiber AI, sources, warnings, status and all config versions.
`MemberTargetInputs` preserves the member/Household IDs, birth date, sex, height,
weight, PAL, goal and member update instant, without copying the member's name.

Missing energy inputs leave AMDR gram ranges unavailable. Fiber can still be
available when its own age/sex inputs are sufficient; the ages 3–8 table does not
require sex. Age 9+ with unsupported sex receives no invented fiber AI.

All calculated EERs carry `REFERENCE_ESTIMATE`: formula reproducibility does not
make an estimate a measured individual need or medical prescription. A `maintain`
goal receives the unadjusted reference. Any other goal preserves exactly the same
EER and adds `GOAL_ADJUSTMENT_NOT_APPLIED`. No deficit, surplus, BMI policy,
diagnosis or therapeutic claim is implemented. Pregnancy/lactation is neither
inferred nor calculated: authoritative fields and a separate approved safety
contract are absent from HouseholdMember.

## Decimal and rounding policy

Calculations create a private Decimal context: precision 80, `ROUND_HALF_UP`,
standard Decimal traps/exponent bounds. Caller Decimal precision and rounding do
not affect results. All nutrient outputs and AMDR/fiber outputs are quantized
once to six decimal places, matching the catalogue nutrient precision. Metadata,
source values, resolved mass and explicit input quantities are retained exactly.
Six decimal places are a domain representation, not a claim of measurement accuracy.

Ingredient contributions are not rounded before recipe aggregation, and recipe
totals are not rounded before base-serving division. Independently rounded
component displays can therefore differ slightly from the rounded total.
Recurring divisions retain 80 significant digits before the result boundary.

Direct scaling requires a finite positive Decimal quantity in `[1e-18, 1e24]`;
base servings use the same arithmetic safety bounds. Unsupported quantity types
(including floats, booleans, strings and integers) raise TypeError; outside-bound
Decimal quantities raise ValueError. Existing canonical recipe/profile validation
remains unchanged. Supported finite input precision fits the private context;
no binary floating-point arithmetic participates.

## Accepted production catalogue coverage

Audit uses a fresh temporary database seeded by the existing accepted loaders,
not a developer's local database. It evaluates all 30 current verified
RecipeVersions and their 189 ingredient rows. Reproduce with:

```sh
AI_ENABLED=false python3 -m pytest -q -s backend/app/tests/test_nutrition_catalogue.py
```

Result on 2026-09-06: **0 COMPLETE, 0 COMPLETE_WITH_WARNINGS, 0 CONDITIONAL,
30 INCOMPLETE**. Required conversion gaps take precedence over optional status.

| Reason | Row occurrences | Affected recipes |
| --- | ---: | ---: |
| Missing density for ml | 123 | 30 |
| Unsupported pcs mass conversion | 35 | 21 |
| Missing FoodIngredient | 0 | 0 |
| Missing current nutrition profile | 0 | 0 |
| Unknown fiber | 30 | 21 |
| Estimated source (`true`) | 0 | 0 |
| Estimation status unknown (`null`) | 189 | 30 |
| Optional ingredient | 4 | 2 |

Counts cover all rows, including optional rows; reasons overlap. They are neither
unique-FoodIngredient counts nor mutually exclusive categories. Optional rows
occur in `SNAP4_SPRING_VEGETABLE_SAUTE` (1) and
`WIC1_OVERNIGHT_OATS_CINNAMON_APPLE` (3). The audit prints per-recipe source
versions, statuses and reason counts. The test pins these counts as review evidence,
not a requirement to invent conversions to make coverage green.

PR7 can consume the engine and explicit diagnostic states, but **none of the 30
accepted production recipes currently has a complete authoritative energy total**.
The supporting
[PR6-DATA-A audit](nutrition-data-readiness.md) now records source-backed
conversion candidates, semantic/source-quantity blockers and an implementation
recommendation. A global density is not generally safe for the accepted forms.
Next action is project review and explicit authorization of DATA-B; no production
data, schema or runtime change is authorized by the recommendation. Accepted
recipe/source provenance and all nutrition, density and serving quantities remain
unchanged in DATA-A.

## Verification and acceptance

Focused tests cover ingredient scaling and precision, aggregate failure states,
optional rows, provenance, member equations for all four PAL categories and both
sexes, age/growth/fiber boundaries, goal invariance, read-snapshot coherence under
concurrent profile replacement, Household isolation, read-only behavior, retained
profile history and import/schema boundaries. Exact executed test counts and
required full backend/launcher regression evidence live in
[state/progress.md](../../state/progress.md#pr6-implementation-evidence).

PR #18 engine implementation is ACCEPTED / MERGED. PR6 milestone remains NOT
COMPLETE pending data readiness and explicit closure acceptance. PR7 and later
remain unauthorized; DATA-A evidence does not pre-authorize DATA-B.
