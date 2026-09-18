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

Under `planner-v0.2`, `meal-role-recipe-v2` and
`max_recipe_repetitions=3`, seven opportunities for one role require
`ceil(7 / 3) = 3` independently eligible versions. A seven-day schedule with
BREAKFAST, LUNCH and DINNER has 21 automatic recipe opportunities:

* BREAKFAST accepts `breakfast` or `sandwich` and requires capacity 7;
* LUNCH accepts `main` or `sandwich`, DINNER accepts only `main`, and together
  require capacity 14;
* DINNER alone requires at least three `main` versions;
* because the catalogue has only one `sandwich`, the smallest feasible set is
  three `breakfast`, four `main`, and one `sandwich` version (eight versions).

An allocation proving sufficiency is 7 breakfast uses across three breakfast
versions, 12 lunch/dinner uses across four main versions, and 2 lunch uses of the
sandwich version. Every version is used no more than three times. Fewer than
eight cannot work with the actual catalogue classifications: at least three
breakfast-capable versions are needed, while the 14 lunch/dinner uses need five
versions and only the single sandwich can overlap the breakfast-capable set.

The current eligible inventory is one breakfast and zero main/sandwich versions.
Therefore the minimum truthful repair set is seven versions: the other two
breakfasts, four of five mains, and the sole sandwich.

## Evidence-backed stop

No production truth is changed by this package, so there is no new write path,
rollback behavior, or repair replay to claim. Each accepted historical data
operation retains its own idempotency/rollback evidence; the audit deliberately
uses their required fresh-install order rather than replaying an old loader over
newer replacement profiles. The row matrix proves that the
minimum seven-version repair cannot be obtained by rebinding already accepted
exact repository evidence. Examples include missing exact same-form authority
for spinach volume, piece-size ambiguity, a lemon/juice form mismatch, and
several explicitly rejected compatible-form estimates. Promoting any of these
rows would violate the accepted rule that `REVIEW_REQUIRED_ESTIMATE` is not
exact authority.

Closing the gap therefore requires a new bounded primary-source evidence package
and, where source recipe form or quantity truth changes, new immutable
RecipeVersions. Those authorities were not present on the authorized starting
tree and must not be invented. No schema or migration change is indicated;
migration head remains `0032_meal_plan_serving`, and reservation
`0033_recipe_template_catalogue` is untouched.

Because candidate capacity is not present, the three repository-backed outcome
fixtures and successful persisted seven-day plan/Serving proof cannot truthfully
be produced yet. Gate1-CLOSE and PR9 remain not started.
