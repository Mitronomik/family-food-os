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
remain authoritative. No derived-result persistence or caches are introduced. B1 adds platform
measure evidence and versioned row review through migration
`0026_nutrition_measure_evidence`; see the [B1 decision](nutrition-data-readiness.md#decision--pr6-data-b1-exact-evidence-and-row-binding).

A calculation enters `NutritionReadScope` once. The SQLAlchemy Core adapter
composes existing repositories on one project `SqlAlchemyReadOnlyScope`
connection/transaction, including the RecipeVersion, current/pinned profiles, row assessments,
measure evidence and ordered assessment issues. The accepted SQLite engine uses `autocommit=False`; even SELECTs share
the transaction snapshot. Calculation exit always rolls back and closes. A separate project write UoW
imports reviewed evidence/assessments; calculation never writes. Contracts expose read methods and domain objects, never driver objects.
Member lookups require both Household and member identifiers.

Serving, MealPlan, member/day/week aggregation, Planner, Shopping, Pantry use,
Prep, Retail, AI and medical policies are outside PR6. In particular,
`per_base_serving` is only `required_total / RecipeVersion.base_servings`.
It creates no Serving entity or personalized allocation.

## Ingredient calculation and provenance

For each nutrient, compute `profile_value × mass_g / profile.basis_grams`.
The existing `FoodNutritionProfile` owns the current 100 g edible-portion basis,
source kcal and nutrients. Ingredient kcal is never reconstructed from macros.

For direct `NutritionService.food_ingredient` only:

- `g`: the requested quantity is the exact gram input.
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

RecipeVersion calculation is assessment-driven under
`ROW_ASSESSMENT_EXACT_ONLY_B1_V1`. Missing review produces
`MISSING_NUTRITION_ASSESSMENT` and no mass, even for g. Approved clean g uses its
existing quantity. `APPROVED_EXACT` requires matching ml/pcs evidence, an explicit
non-estimated source, no review blockers, and the still-current pinned profile.
Mass is `row.quantity × evidence.gram_weight / evidence.normalized_input_quantity`
in the private Decimal context with no intermediate quantization. FoodIngredient
global density is never a recipe fallback.

`REVIEW_REQUIRED_ESTIMATE` contributes no authoritative mass or nutrients and
emits `CONVERSION_ESTIMATE_NOT_ACCEPTED`. `BLOCKED` emits
`NUTRITION_ASSESSMENT_BLOCKED`, retaining every structured issue, including issues
on g rows. Missing evidence emits `MISSING_MEASURE_EVIDENCE`; mismatched units or
invalid authority fail closed. A changed current profile emits
`NUTRITION_ASSESSMENT_PROFILE_STALE`; old review is not automatically rebound.

`RecipeIngredientNutrition` retains the immutable row, contribution, full
assessment (ID/version/status/ordered issues), selected measure evidence
(ID/key, source name/id/version/form, numerator/denominator/unit and estimated
flag), and exact pinned assessment profile. Contribution.profile is the current
profile read. Historical pinned profile remains exposed after invalidation.
`RecipeVersionNutrition.version` retains version identity, base servings and
source/hash provenance. Repeated ingredient/profile inputs are read once per
calculation where reusable; warnings retain individual row context.

Results identify the coherent inputs actually read. Explicit reassessment for
a new current profile creates a new version and retains history. Recipe rows
remain immutable. New RecipeVersion rows start without assessments and fail
closed until reviewed. No calculation changes catalogue or review history.
A future historical consumer must retain these exact inputs/config references;
RecipeVersion ID alone does not promise historical replay.

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
| `recipe_mass_policy_version` | `ROW_ASSESSMENT_EXACT_ONLY_B1_V1` |
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

## Historical PR6 engine production coverage (before B1)

The original engine audit used a fresh temporary database seeded by the accepted loaders,
not a developer's local database. It evaluates all 30 current verified
RecipeVersions and their 189 ingredient rows. The current command below now
verifies the B1 audit; original audit code and results remain in DATA-A accepted
main and its protected hashes:

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
The later B1 implementation establishes exact evidence and row assessments
without changing production RecipeVersion or FoodNutritionProfile contents.

## Historical production coverage after B1

[Audit v2](../../data/seed/nutrition_measure_evidence/production-audit-v2.json)
reports 30 INCOMPLETE recipes, all other statuses zero; 189 current assessments,
57 evidence records and 123 issue rows. Assessments: 66 APPROVED_EXACT,
20 APPROVED_NO_CONVERSION, 37 REVIEW_REQUIRED_ESTIMATE and 66 BLOCKED.
All 43 estimate candidates remain non-executable. Eleven g rows remain blocked.

Runtime counts: missing assessment 0, blocked 66, estimate not accepted 43,
stale profile 0, missing evidence 0, unknown fiber 30, unknown profile estimation
189, estimated nutrient source 0, optional 4, missing ingredient/profile 0.
Recipe missing-density/unsupported-piece warnings are both zero. Direct
FoodIngredient behavior remains as above. Reproduction, exact source hashes,
status derivation and remaining B2 blockers live in the
[B1 decision](nutrition-data-readiness.md#decision--pr6-data-b1-exact-evidence-and-row-binding).

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
remain unauthorized. B1 and PR6-INFRA are established. B2-A establishes the
bounded quantity correction slice below; B2-B remains NOT AUTHORIZED.


## Current production coverage after B2-A

External provenance does not identify an internal RecipeVersion revision. The
same accepted source artifact can support immutable v1 and a reviewed corrected
v2; historical Nutrition remains bound to the historical row IDs and sealed B1
reviews. `get_current_verified` selects the highest verified version. New v2
rows never inherit assessment authority through `created_from_version_id`.

B2-A publishes five same-source v2 versions and 32 explicit new row assessments:
26 equal-row/profile carry-forwards and six new quantity review decisions.
The separate loader verifies complete parent/v2 contents and row/profile
provenance, requires new row identities, and fails atomically on conflicts.
Before assessment import all 32 new rows lack mass authority. After import only
the corrected kale g row gains approval; independent profile/form/measure
blockers stay in force. Every historical v1 calculation remains reproducible.

[Audit v3](../../data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json)
covers 30 current recipes / 189 current rows: 30 INCOMPLETE, all other statuses
zero; current assessments 21 APPROVED_NO_CONVERSION, 66 APPROVED_EXACT,
37 REVIEW_REQUIRED_ESTIMATE and 65 BLOCKED. All 43 estimated conversion
candidates remain non-authoritative; no tolerance, enabling flag, midpoint rule,
profile value/estimated-flag change or fiber fill is introduced. Detailed six-row
source review, warning/issue counts and replay commands are canonical in the
[B2-A decision](nutrition-data-readiness.md#decision--pr6-data-b2-a-same-source-quantity-corrections).
PR6 remains NOT COMPLETE; B2-B remains NOT AUTHORIZED; PR7+ remain UNAUTHORIZED.

## Later approved target architecture — superseding implementation direction

**DECISION — 2026-09-10, PR6-ARCH-COMPOSITION.** Nutrition v1 was a correct bounded
engine for its accepted data contract. PR #18, the five-field `NutritionValues`,
`FAMILY_FOOD_NUTRITION_V1`, B1 exact bindings, tests and historical results retain
their meaning. Everything above describes the current implementation or labelled
historical evidence, not the final nutrient target. No config ID is renamed here.

The next versioned target is `NutrientDefinition → FoodNutritionProfileVersion →
NutrientValue[]` / NutrientVector: extensible energy, macros, fiber, minerals,
vitamins and other required micronutrients without a new SQL column per nutrient.
Each value retains stable code, Russian display name, canonical unit, source
nutrient identifier, Decimal value or unknown, provenance, release/version and
estimation/uncertainty. `PR6-NUTRIENT-VECTOR` must define the initial registry from
authoritative datasets and product requirements, with explicit v1 compatibility;
this docs PR does not choose the exhaustive registry or persisted schema.

Unknown != zero at nutrient level. Cross-source values cannot silently become
one measured profile; a separately approved versioned policy is required.
Calculation has one authority path per food version: direct profile or exact
composition. Declared-only lists never supply inferred quantitative components.
Exact recursive calculation is Decimal-only on a versioned DAG; cycles fail closed.
Canonical input is the form-specific `recipe_input_mass_g`, with B1-compatible
reviewed evidence for pcs/ml. Gross/raw/input/cooked mass are not interchangeable.

Yield measures mass change; retention measures each nutrient's conservation or
loss through a versioned transformation. `NutrientRetentionEvidence` is distinct
from yield. Unknown retention preserves known input totals but does not permit
exact cooked totals or hidden 100% retention; no universal cooking-loss percentage.
The [composition contract](food-composition-and-assembly.md#nutrientvector-и-retention)
owns the full mass/transformation/vector pipeline and uncertainty propagation.

Nutrition consumes catalogue identity/composition and supplies calculations to
Recipe Assembly and later PR7. PR7 supports selected immutable RecipeVersion or
validated RecipeAssembly and consumes Nutrition without duplicating its logic.
The [Russian-language contract](russian-language-contract.md) gates human-facing
nutrient/status/error display, including admin, API messages and PDF.

Old PR6-DATA-B2-B2: **SUPERSEDED / PENDING REDESIGN**. All 43 estimates remain
non-executable; production audit v3 still has 30 current recipes / 189 rows, all
30 INCOMPLETE. Migration head remains `0027_recipe_same_source_revisions`.
PR6 — NOT COMPLETE; PR6-NUTRIENT-VECTOR is being delivered in bounded A/B
slices described below. VECTOR-B is NOT AUTHORIZED; PR7+ — UNAUTHORIZED. The
[roadmap](master-roadmap.md#5-canonical-master-sequence) owns the new sequence.


## PR6-NUTRIENT-VECTOR-A — registry and legacy provenance

This changeset establishes the bounded registry/provenance audit from exact
starting main `307ba3475581087b079ebcf2fa643e19a00bf06d` (merged PR #24).
[The research report](../../data/curation/pr6-nutrient-vector-a/README.md) owns the
51 canonical definitions, Russian names/units, release-specific source mappings,
full legacy crosswalk, source hashes and implementation recommendations.
USDA Foundation April 2026 and SR Legacy April 2018 were verified on 2026-09-10.

All 183 accepted profile provenance identities across seed history are audited:
915 field observations, 870 source-confirmed values and 45 absent fibres. No
value mismatches or ambiguous present values were found. The original 100
profiles were retained unchanged when 83 were added; no historical-only profile
exists in this accepted corpus. Additional deployment-specific historical
profiles require their own provenance inventory before backfill.

Every legacy carbohydrate is source 1005, **CARBOHYDRATE_BY_DIFFERENCE**, not
available carbohydrate. Energy preserves 81 SR 1008, 97 Foundation 2048 and
5 Foundation 2047 observations; methods are not erased. RAE/retinol/beta-carotene,
total folate/DFE/folic acid and fat totals/species remain distinct canonical codes.
Unproven FDC/INFOODS mappings remain explicit exceptions, not guessed identifiers.

Recommendation for separately authorized VECTOR-B: attach normalized nutrient
values to the **existing FoodNutritionProfile** identity/version/provenance
container. Keep one current-profile system and historical B1 FKs. No numeric
value row means unknown; an explicit zero row means known zero. This requires
atomic value-set import and complete reads; query omission/failed import cannot
be interpreted as source absence. Preserve uncertainty, nutrient-level source
locator and immutable mapping metadata. Missing source IDs may only produce an
explicit legacy projection with independently proved semantics. Ambiguous or
mismatching values cannot be silently promoted or corrected.

Canonical micrograms use `µg` (U+00B5), with Russian display `мкг`; the remaining
units display as ккал/г/мг. English/code fallback is forbidden for all 51 entries.
DIRECT_COMPONENT is a chemical/group definition, not certification of measurement;
DERIVED_COMPONENT identifies operational/activity definitions. Source derivation
and estimation state remain separate, and cross-source blending stays forbidden.

Runtime/schema/seeds remain unchanged; FAMILY_FOOD_NUTRITION_V1 is current,
migration head is 0027 and all 43 estimates are non-executable.
PR6 and PR6-NUTRIENT-VECTOR are NOT COMPLETE. VECTOR-B is NOT AUTHORIZED;
COMPOSITION-CORE and PR7+ remain UNAUTHORIZED. No implementation follows
automatically from registry readiness.
