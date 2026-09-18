# GATE1-A — current readiness audit and capacity decision

Status: **evidence blocker; Gate1-A is not review-ready**.

## Reproduction

The accepted implementation base is
`ce5cf6e2faaf9159e74d8c235f334d47743ab2a0`. Generate the matrix only from a
new path:

```bash
PYTHONPATH=backend python scripts/audit_gate1a_readiness.py \
  /tmp/gate1a.sqlite \
  --output data/curation/gate1a-data-readiness/current-readiness.json
```

The command applies the complete accepted seed/data-upgrade chain through normal
application and repository boundaries. The committed receipt records the UUIDs
from that disposable run; UUIDs are deployment-local, while canonical recipe
code, version number and all assessed facts are reproducible.

## Current truth

The fresh audit contains exactly 30 current verified RecipeVersions. Twenty-nine
are `INCOMPLETE` with unknown kcal. Only
`WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:v2` is technically selectable: it is
`CONDITIONAL` at `112.007500` kcal per base serving because its unresolved apple
row is optional. This is technical Planner eligibility, not a claim of consumer
publication readiness. The complete row-level matrix is
[`current-readiness.json`](current-readiness.json).

## Candidate-capacity proof

The audit now exhaustively assigns participant sets to compatible candidates
under `planner-v0.2`, `meal-role-recipe-v2` and
`max_recipe_repetitions=3`. The generic seven-day BREAKFAST/LUNCH/DINNER lower
bound is **seven** versions: two `breakfast`, four `main`, and the one available
`sandwich`. A concrete allocation is six breakfasts to the two breakfast
versions, one breakfast plus two lunches to the sandwich, and the remaining 12
lunch/dinner events to four main versions. This explicitly uses the sandwich in
both compatible roles and keeps every count at or below three.

The actual hard-exclusion fixture has two participants at all 21 opportunities
and excludes the sandwich ingredient for the child. Using that sandwich causes a
split and cannot reduce the shared capacity bound. The exhaustive result is
**eight** versions: three breakfast and five main; the sandwich is not needed.
The heterogeneous fixture removes the fixed-event participant before automatic
assignment and retains the generic seven-version bound. These fixture definitions
and computed results are embedded in `current-readiness.json`.

Current eligibility is the conditional oatmeal breakfast only. Therefore the
generic gap is six versions, while the governing hard-exclusion fixture gap is
seven: both remaining breakfasts and all five current mains. The sandwich is a
generic-only alternate, not a replacement for actual exclusion-fixture capacity.

## Evidence classification and selected targets

Planner eligibility is recorded separately from Nutrition status and requires
the production rule actually used by Planner: status other than `INCOMPLETE`,
non-null kcal, and kcal greater than zero. Consumer readiness remains false.

For each blocker the audit searches current assessments, non-estimated exact
measure evidence attached to current `APPROVED_EXACT` assessments, the exact
FoodIngredient/profile/unit identity, and persisted composition snapshots.
Reusable evidence is reported only when food identity, pinned profile, unit and
normalized evidence unit match. Current blocker totals are:

* `NEW_PRIMARY_EVIDENCE_REQUIRED`: 69;
* `IMMUTABLE_RECIPE_REVISION_REQUIRED`: 15;
* `ALREADY_ACCEPTED_EVIDENCE_REBIND`: 9;
* `PROFILE_OR_FORM_DATA_REPAIR`: 1.

The actual-fixture target set is forced by catalogue capacity rather than raw
blocker count: `TNC6_EGGS_SPINACH`, `SNAP4_SPANISH_FRITTATA`, and all five mains
(`FNS2_ORANGE_PORK_CHOPS`, `FNS4_OVEN_FRIED_FISH`,
`FNS5_BAKED_LENTILS_CASSEROLE`, `SNAP4_BRAISED_CHICKEN_SPINACH`,
`SNAP4_DILLED_FISH_FILLETS`). The matrix's `repair_plan` gives every exact target
row and required class. Two selected black-pepper rows can reuse accepted exact
`FDC-PORTION-87560:exact`; the remaining selected rows require new primary
evidence or an immutable recipe correction. The sandwich remains the generic
alternate but itself has only one accepted rebind and two new-evidence rows.

## Evidence-backed stop

No production truth is changed by this package, so there is no new write path,
rollback behavior, or repair replay to claim. Each accepted historical data
operation retains its own idempotency/rollback evidence; the audit deliberately
uses their required fresh-install order rather than replaying an old loader over
newer replacement profiles. The row matrix proves that the
minimum actual-fixture repair cannot be obtained solely by rebinding accepted
exact evidence. Some exact evidence is reusable, but it does not resolve whole
target recipes. Remaining examples include missing exact same-form authority for
spinach volume, piece-size ambiguity, a lemon/juice form mismatch, and explicitly
rejected compatible-form estimates. Promoting any estimate would violate the
accepted evidence contract.

Closing the gap therefore requires a new bounded primary-source evidence package
and, where source recipe form or quantity truth changes, new immutable
RecipeVersions. Those authorities were not present on the authorized starting
tree and must not be invented. No schema or migration change is indicated;
migration head remains `0032_meal_plan_serving`, and reservation
`0033_recipe_template_catalogue` is untouched.

Because candidate capacity is not present, the three repository-backed outcome
fixtures and successful persisted seven-day plan/Serving proof cannot truthfully
be produced yet. Gate1-CLOSE and PR9 remain not started.
