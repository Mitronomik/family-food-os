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

## Capacity: observed fixture versus models

The audit now exhaustively assigns participant sets to compatible candidates
under `planner-v0.2`, `meal-role-recipe-v2` and
`max_recipe_repetitions=3`. The generic seven-day BREAKFAST/LUNCH/DINNER lower
bound is **seven** versions: two `breakfast`, four `main`, and the one available
`sandwich`. A concrete allocation is six breakfasts to the two breakfast
versions, one breakfast plus two lunches to the sandwich, and the remaining 12
lunch/dinner events to four main versions. This explicitly uses the sandwich in
both compatible roles and keeps every count at or below three.

The current repository fixture is read from the shared specification used by
`test_planner_gate1_fixtures.py`. Its three household shapes require respectively
3, 6 and 7 eligible versions. It currently has no fixed event and no explicit
hard exclusion. Its largest shape is the generic three-meal case, so its repair
gap from the one eligible oatmeal is six versions.

A harder scenario is retained only as a **proposal**, never as observed fixture
truth. It excludes real `BREAD_WHOLE_WHEAT`, which occurs only in the sole
sandwich candidate `WIC1_BEYOND_BASIC_GRILLED_CHEESE`, for one of two participants
at all opportunities. Planner split semantics make its minimum eight versions
(3 breakfast + 5 main); the sandwich supplies no net shared capacity. This
scenario would add one candidate beyond the generic path, but it is not yet a
repository-backed Gate1 fixture.

## Evidence classification and selected targets

Planner eligibility is recorded separately from Nutrition status and requires
the production rule actually used by Planner: status other than `INCOMPLETE`,
non-null kcal, and kcal greater than zero. Consumer readiness remains false.

For each blocker the audit searches current assessments, non-estimated exact
measure evidence attached to current `APPROVED_EXACT` assessments, the exact
FoodIngredient/profile/unit identity, and persisted composition snapshots.
Reusable evidence additionally must pass deterministic source-measure, size,
form, edible-basis, preparation and target-source-text checks. Unproved semantic
compatibility fails closed. Current blocker totals are:

* `NEW_PRIMARY_EVIDENCE_REQUIRED`: 70;
* `IMMUTABLE_RECIPE_REVISION_REQUIRED`: 16;
* `ALREADY_ACCEPTED_EVIDENCE_REBIND`: 7;
* `PROFILE_OR_FORM_DATA_REPAIR`: 1.

All seven legal reuses are teaspoon-derived black-pepper rows using
`FDC-PORTION-87560:exact`. Unspecified `6 eggs (in shell)` correctly rejects the
large-egg evidence; the explicit `6 large eggs` control accepts it. The grilled
cheese source permits Muenster, Monterey Jack or mozzarella but does not establish
cheddar, so exact cheddar cup evidence is rejected and an immutable recipe-truth
decision is required.

Candidate comparison uses lexicographic ascending counts, highest-authority cost
first: immutable revision, new primary evidence, deterministic profile/form or
assessment repair, then accepted exact rebind. The current generic minimum-cost
set is recorded in JSON and contains one remaining breakfast, four of five mains,
and the sole sandwich (six repairs). Because every such set depends on authority
not yet present, its status is
`TARGET_SELECTION_BLOCKED_PENDING_PRIMARY_EVIDENCE_REVIEW`; it is a deterministic
comparison result, not authorization to publish those repairs. The proposed
exclusion scenario's seven-repair set is reported separately.

## Evidence-backed stop

No production truth is changed by this package, so there is no new write path,
rollback behavior, or repair replay to claim. Each accepted historical data
operation retains its own idempotency/rollback evidence; the audit deliberately
uses their required fresh-install order rather than replaying an old loader over
newer replacement profiles. The row matrix proves that the
minimum generic repair cannot be obtained solely by rebinding accepted
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
