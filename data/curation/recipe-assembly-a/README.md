# RECIPE-ASSEMBLY-A — BLOCKED at evidence preflight

Reviewed: `2026-09-12`. Accepted base and fetched `origin/main`:
`e8a75e5b828ef935292da593f9f4d5edbd199474`.
[PR #30](https://github.com/Mitronomik/family-food-os/pull/30) is independently
verified MERGED at `2026-09-12T08:32:53Z`, with that merge commit. PR6 and
PR6-CLOSE are COMPLETE. Requested branch: `codex/recipe-assembly-a`.

The user authorized exactly **three production RecipeTemplate families** and
explicitly required stopping BLOCKED if three candidates cannot pass every hard
gate. This package records that stop. **Zero production templates are published**;
three candidates are deferred. This is an incomplete operation, not a reduced
production corpus, accepted milestone, or review-ready catalogue implementation.

## Findings

All 30 current source-backed RecipeVersions were screened against the accepted
PR6-CLOSE row evidence and exact FoodIngredient composition inventory. Twenty-nine
have unavailable required masses; the remaining oats recipe has two approved
required masses but lacks an accepted composition for its milk form. Therefore
none can be carried forward unchanged using only current mass/form authority.
This screen is not a claim that source-backed new rules are impossible or that
an INCOMPLETE Nutrition v1 status alone is a template blocker.

| Candidate family | Concrete blocking evidence |
| --- | --- |
| Овсянка на ночь с яблоком и корицей | Current v2: required milk and oats have reviewed masses; MILK_1_PERCENT has no accepted composition. Optional APPLE remains blocked. Source milk/soy and rolled/quick alternatives do not establish exact tested replacement rules. |
| Соте из весенних овощей | Eight required masses unavailable; POTATO and GREEN_BEANS lack compositions. Optional water is a conditional 1–2 tablespoon range; the old stored upper bound cannot become a newly reviewed exact template rule. |
| Капустный салат с йогуртовой заправкой | Ten of eleven required masses available; CRANBERRIES_DRIED is blocked for profile representativeness and lacks composition. The fixed source does not authorize omission or replacement of cranberries. |

Kitchen verification for exact reusable variant scopes was **not established**.
This means missing evidence, not an assertion that nobody cooked the dishes.
The [USDA bulletin](https://content.govdelivery.com/accounts/USFNS/bulletins/37d3aa8)
positively identifies testing of its named breakfast/snack collections. That
claim cannot be transferred to arbitrary FNS/WIC recipes or generalized choices.
Its exact collection links and two donor pages returned HTTP 403 through the web
tool. The coleslaw card was readable; it describes a fixed recipe. Access failures
are retained as uncertainty, never as proof of absent verification.

Required terminal inputs include RU_AVAILABLE foods without established reviewed
ordinary substitution paths. Prior dated market evidence is retained as evidence,
not upgraded to default eligibility or a current store-stock claim. No independent
RU_RECIPE_FAMILIAR classification was completed for these deferred variants; Russian
research titles alone do not satisfy it. No compatibility/culinary rule is invented
to meet feature coverage.

## Evidence map

- [Candidate review](candidate-review.json): all 30 screened current versions,
  source provenance, exact missing-row references, and three deferred families.
- [Template decisions](template-decisions.json): stopping reason, unchanged gates,
  migration decision and concrete options for resuming.
- [Source manifest](source-manifest.json): SHA-256 pins for accepted inputs;
  external source IDs, historical hashes and retrieval uncertainty preserved.
- [Research observations](research-observations.json): dated primary-source
  inspection summaries, positive testing evidence scope and access limitations.
- [Kitchen verification](kitchen-verification.json): explicit unestablished scope;
  no fabricated verification date/version/quantity/process.
- [RU familiarity](ru-familiarity.json): NOT_REVIEWED, no automatic approval.
- [Market evidence](market-evidence.json): fixed-donor required inputs and exact
  references to accepted market records; no composite graph is manufactured.
- [Implementation evidence](implementation-evidence.json): what was actually
  checked, what was not implemented, and unavailable/not-run checks.
- [Checksums](checksums.json): retained package integrity; changes require review.

These files are research evidence, **not a runtime database or production seed**.
No original source binary or website asset is republished. Historical source
hashes identify earlier reviewed artifacts; fresh web observations are not claimed
to have identical bytes. Missing historical retrieval instants stay null.
No production quantity rule is derived from rounded legacy normalized quantities.

## Verification and scope

Run the read-only evidence audit from the repository root:

```sh
AI_ENABLED=false python3 scripts/audit_recipe_assembly_a_preflight.py
```

Exit 0 means **evidence consistency PASS; operation BLOCKED**. It does not mean
production acceptance. The audit hash-checks accepted inputs/package contents,
recomputes the 30-recipe mass/form screen, matches candidate rows and required
terminal inputs, and checks that no positive publication/review status is claimed.
Without `--database` it does not open a database. It never validates hypothetical
templates.

For the reproducible disposable-database check:

```sh
AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_preflight.py --database
```

The existing PR6 closure measurement function was also used on a disposable
accepted database to recheck the factual baseline; exact execution results are in
implementation-evidence.json. Its historical command-line main-head guard was
not changed. No real household/developer database is opened.

Runtime/domain/persistence, source RecipeVersions, FoodIngredients, compositions,
vectors, assessments, production seeds and historical migrations remain unchanged.
No public API/UI, AI, Retail, RecipeAssembly, Planner, Serving or MealPlan is added.
Migration stays `0029_food_composition_core`: no persisted catalogue was implemented,
so there is no schema change to migrate. This does **not** waive migration
`0030_recipe_template_catalogue` for a resumed implementation.

The full implementation/migration/UoW/seed/backup/regression acceptance suite is
not executed for an absent implementation; none of those gates is marked PASS.
Full backend/launcher regression remains required before the original requested
implementation can become review-ready. The 40 estimates, five deferred forms
and three known yield cases remain blocked.

## Resumption

Recommended: obtain or verify a bounded evidence package for exactly three
families, including precise kitchen-tested variant scope, exact forms/grams,
curated substitutions, compatibility, RU familiarity and terminal-input policy.
Use alternative primary candidates if they satisfy the same gates. Resolve any
food/composition gaps only under the appropriate explicit authorization; this task
does not start a new FoodIngredient or yield/retention research programme.

A schema-only split would require an explicit changed task decision and would
not satisfy the original acceptance criteria. It is not implemented here.
RECIPE-ASSEMBLY-B and PR7+ remain NOT STARTED / unauthorized. No autonomous merge.
