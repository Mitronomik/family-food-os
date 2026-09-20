# Russian nutrition methodologies — versioned calculation policy

Status: implementation contract explicitly confirmed by the user on 2026-09-20
during PR75 review, after PR74 merged. This adds an explicitly selected Russian
method path; historical V1 calculations and registry snapshots are immutable.
The same confirmation explicitly approves
`RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1` under the constraints below.

## Decision and scope

Russian published composition must not be rejected merely because its analytical
method differs from the bootstrap USDA source. Preserve the nutrient definition,
method, observation state, source, food form, mass basis and calculation version.
Available carbohydrates are the intended principal carbohydrate concept for the
new Russian path. Total carbohydrates including fibre remain separately named.
Norm compatibility must be established before comparing intake to a target.

This bounded implementation delivers domain interpretation, energy accounting,
reference selection/comparison and internal read-only services. It does not
publish book data, alter persisted profiles, change the HTTP/UI/Planner default,
or replace NASEM personal estimates with population table entries. No migration
is introduced and reserved0033 remains unchanged.

PR74 is accepted at
`4c9598b623b9042924bb1f8d864c56d3d0a407c4`. Its five-profile preparation,
rights block, input lock and numeric-free verification receipt are upstream
evidence for this methodology layer. PR75 does not weaken or supersede PR74's
`BLOCKED_PENDING_RIGHTS_REVIEW`, zero imported profiles or zero canonical
numeric-value publication.

## Components and uncertainty

`nutrition_methodology.py` supports protein, fat, fibre, available/total carbs,
and separately published/computed energy. Source positive amounts, missing,
below-detection and held observations are distinct. Provenance must specify
source edition, locator, observation, exact form and method reference.

Available carbohydrate by analytical summation, by difference excluding fibre,
and source-published available carbohydrate with unspecified row method are
accepted by the Russian source-native policy. The original method remains in
lineage; the latter two return explicit warnings. Acceptance is a calculation
policy, not a claim that all methods are analytically identical. The book2002
general method does not prove the exact method of every row.

`RU_SOURCE_NATIVE_STRICT_V1` preserves below-detection as unavailable.
`RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1` is an explicitly selected and
user-approved alternative: a literal published zero with below-detection state
may be interpreted as numeric `0` only as an **estimate**. The original
`below_detection` state remains in lineage, detection limit remains unknown,
`estimated=true` is mandatory and the estimate warning remains attached.
Missing, held and unsupported-method observations cannot use this rule.

This estimated zero is never:
- an exact analytical zero;
- evidence of allergen absence;
- permission to erase censoring provenance;
- a default Planner/API/UI truth without the methodology version being pinned;
- a substitute for source-use rights or profile publication authority.

Neither policy supplies an upper confidence bound. Source estimated/unknown-
estimation flags are preserved independently.

Amounts use Decimal. Aggregation scales matching edible input forms, retains
all inputs/methods and propagates unavailable values. It is not a cooked-output
calculation and applies no yield or retention coefficient. Mixed nutrient
concepts cannot be added together. No total-to-available subtraction is implicit.

## Energy

`russian_energy.py` implements the coefficients in MR2.3.1.0253-21 appendix3,
printed/PDFp58, visually checked against the official72-page document. Coefficients
have their own version `RU_MR_2_3_1_0253_21_ENERGY_V1`; they are not a universal
labelling or personalized-needs policy. Published energy stays separate from
computed energy, with an explicit difference only when calculation is complete.

All energy terms retain amount provenance, method, common basis and food form.
The full generic partition requires every component to be known (including
confirmed zeros) and a reviewed disjoint-partition reference. Carbohydrate,
polyol and acid values must not overlap. Missing components produce a known-term
subtotal, not a full energy value. Experimental sugar/starch factors are available
for explicit method-specific terms; they cannot accompany total available carbs
and their pair alone is not proof of a complete carbohydrate inventory. Fibre,
ethanol, erythritol, glycerol and separately specified acids have distinct factors.
Do not adjust published energy to force agreement with any formula.

Primary source:
https://ion.ru/upload/medialibrary/e70/xq18hm3mm1f1b3izde8kcb5136l8373z/%D0%9D%D0%BE%D1%80%D0%BC%D1%8B%20%D1%84%D0%B8%D0%B7%D0%B8%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D1%85%20%D0%BF%D0%BE%D1%82%D1%80%D0%B5%D0%B1%D0%BD%D0%BE%D1%81%D1%82%D0%B5%D0%B8%CC%86%202021.pdf

## Reference needs and vitamin definitions

`russian_reference_targets.py` selects rows from an explicitly supplied reviewed
immutable table by definition, sex, completed-year interval, exact KFA and
wellness life stage. It rejects overlapping alternatives. It never maps American
activity labels to Russian KFA, interpolates age gaps or silently chooses another
methodology. A population reference is returned as `individualized=false`.
Pregnancy/lactation, clinical scenarios, infant month bands, inequalities and
range-valued references need specific subsequent contracts; they are not coerced
into this scalar completed-year selector. Missing applicable rows remain visible.

`reference_comparison.py` compares daily amounts only with the same nutrient
concept. Compatible mass units can be converted; µg alone does not establish
RE=RAE, niacin=niacin equivalent or alpha-tocopherol=tocopherol equivalent.
Percent-energy rows cannot be compared directly to grams. A comparison is to a
group reference, never proof of individual adequacy or a treatment recommendation.
The [compatibility matrix](../../data/curation/russian-methodology/reference-compatibility.json)
records additional definition gaps. Numeric Russian target tables are not newly
published here: extracted corpus rows still require the documented source review.

## Service integration and stability

`NutritionMethodologyService.atomic_input` reads pinned existing ATOMIC
composition/profile IDs through existing `CompositionReadScope` ports and sealed
vectors. It checks profile ownership, exact registry version and mass state.
It refuses transformed compositions and gross/discard masses; use the composition
engine for processes. Requested absent available carbs never fall back to total
carbs. Held vector observations retain their original reason/evidence and enter
the reproducible receipt. A missing seal is not an empty profile.

`NutritionService.russian_member_group_reference` is a new explicit internal use
case. It keeps household-scoped member lookup and checks the requested table
version. Its reviewed-table provider is optional; without one it reports
unavailable rather than falling back to NASEM. Existing `member_reference_target`
and all existing APIs remain V1. Service callers must choose the new method;
no silent default migration is authorized by adding these operations.

## Broader audit and remaining integration work

| Area | Current conclusion | Next bounded implementation/acceptance |
|---|---|---|
| Profile persistence | Legacy macro columns still require values | Support partial immutable profiles/vector ownership; preserve old IDs and current selector; migrate through custom runner, test old snapshots and rollback |
| Registry | V1 definitions remain immutable | Add a new reviewed version for required Russian concepts, with source-method adapters and target compatibility; never edit old snapshot bytes |
| Protein | Published protein can be interpreted with method provenance | Review nitrogen factors/true-protein distinctions before conversions; no universal6.25 repair |
| Energy needs | Existing personal model is NASEM | Publish reviewed Russian group tables; separately decide an individualized Russian algorithm rather than calling tables a personal formula |
| Units | Decimal, explicit basis and unit-safe comparison implemented | Add specific evidence-based conversions only; no generic IU or volume-to-mass assumption |
| Waste/yield/retention | Existing mass-state DAG is suitable | Attach applicability to exact food, season, operation and source; no double cold/heat loss; retain source-published dish analysis separately |
| Household storage | Institution/industrial conditions do not transfer | Publish only evidence with temperature, packaging, state and household applicability |
| Allergens | Unknown is not absent | Retain composition propagation and reviewed source claims; analytical nutrient zero cannot certify safety |
| Planning | New method outputs are explicit | Pin methodology in planning revisions before enabling Russian targets/defaults; replay must reproduce old plans |

The user has authorized the PR75 Russian methodology implementation and confirmed
the published-zero estimate policy above. Source-rights decisions, schema/profile
migration, production publication, Planner/API/UI enablement and later milestones
remain separately gated. This PR completes the bounded calculation-policy and
internal-service layer, not all persistence/catalogue/Planner integration.

## Verification and rollback

Focused tests cover method/zero/held semantics, food form and basis matching,
Decimal context isolation, energy overlap/incompleteness, exact KFA/age/definition
selection, RE/RAE/NE rejection, household isolation, repeated receipts and actual
SQLite composition/vector reads. V1 Nutrition/targets/composition regressions
must pass. AI is not required.

`trial_ru_nutrition_methods.py` can run both policies on the five PR74-pinned
external profiles and keeps numeric output outside the public repository. Merge
acceptance does not depend on an unretained local A/B trial. Instead,
[the numeric-free receipt](../../data/curation/russian-methodology/trial-verification-receipt.json)
is validated in CI against accepted PR74 nonnumeric profile evidence, PR74 input/
verification receipts and current methodology code. It proves the reviewable
5-profile / 25-core-observation / 50-policy-evaluation shape, 3 strict unknowns,
3 approved estimated-zero interpretations and zero canonical profile imports
without committing source numeric tables.

An external trial remains useful operator evidence when the source corpus is
available, but it does not establish rights, publication readiness, profile
import or recipe readiness. Rollback disables new explicit method calls and
reverts optional new modules; no stored data or historical results need rewriting.
