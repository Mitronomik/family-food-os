# Gate1-CLOSE — Planning Core closure decision

**Status:** CLOSE — effective when PR #181 is independently reviewed and merged  
**Issue / PR:** #180 / #181  
**Accepted base:** `c85fae8e8e2c135855f1ba64ca6722de20e1bd29` (merged PR #179)  
**Machine receipt:** [decision.json](../../data/curation/gate1-close/decision.json)  
**DC4 rerun:** [dc4-corpus-readiness-rerun-report.md](dc4-corpus-readiness-rerun-report.md)  
**Closure verification:** GitHub Actions `Gate1 closure`, run `37808665837`, job `113419518103`, artifact `11563757892`, exact head `4f3be9ad3d9c9ff929c86c7478a3881c65aa3c93`.

## DECISION

**Gate1 — Planning Core is ready to CLOSE.**

Merge of PR #181 is the explicit Gate1-CLOSE decision required by the canonical
roadmap. After that merge, **PR9 — Shopping Engine** becomes the next authorized
bounded product milestone.

This decision does not implement Shopping and does not authorize PR10, Consumer
PWA, Retail, AI, PostgreSQL/Auth or shared deployment.

## FACT — canonical thresholds are met

The closure validator rebuilt current accepted production truth on a fresh
database through the merged A3 publication path and reconciled the accepted DC4
rerun receipt.

| Gate1 requirement | Required | Current accepted evidence | Result |
| --- | ---: | ---: | --- |
| Materially different fixture households | 3 | 3 fixtures: 1 / 2 / 3 members | PASS |
| Verified usable RecipeVersions | >=30 | **51** verified current active recipes | PASS |
| Active FoodIngredient catalogue | >=80 | **227** active FoodIngredients | PASS |
| Planner deterministic/versioned | yes | `planner-v0.5`; deterministic fixture replay | PASS |
| Hard exclusions | respected | zero selected exclusion violations | PASS |
| Mandatory complete weeks | complete or explicit bounded failure as contracted | all 3 mandatory fixtures complete | PASS |
| Individualized Servings | required | 7 / 21 / 42 persisted Servings | PASS |
| Bounded infeasibility | fail closed | `NO_ELIGIBLE_CANDIDATE`; no partial MealPlan | PASS |
| Trace/rejection evidence | reproducible | fixture fingerprints + rejection evidence | PASS |
| MealPattern / role / source boundaries | explicit | current reused evidence matrix | PASS |
| Provenance/tamper | fail closed | R3-D hash/process drift evidence | PASS |
| Gate-only authoritative data | forbidden | none introduced by DC4 rerun | PASS |
| Migration | 0042 / no 0043 | satisfied | PASS |
| AI dependency | disabled | `AI_ENABLED=false` | PASS |

Machine result:

```text
decision = CLOSE
planning_core_status = COMPLETE
pr9_authorized_after_merge = true
failed_criteria = []
```

## FACT — accepted DC4 consumption proof

Merged PR #179 established current corrected-runtime DC4 PASS:

- full active catalogue: 51 PASS / 0 BLOCKED;
- Planner supply: 51 = 17 breakfast / 33 main / 1 sandwich;
- Fixture 1: 7 MealEvents / 7 Servings;
- Fixture 2: 14 MealEvents / 21 Servings;
- Fixture 3: 21 MealEvents / 42 Servings;
- selected hard exclusions respected;
- bounded milk+egg case fails closed with no partial state;
- `overall_status=PASS`;
- `blockers=[]`;
- current Planner: `planner-v0.5`.

Historical PR #165 remains truthful historical BLOCKED evidence and is not
rewritten by this closure.

## FACT — reused domain/adversarial evidence

Gate1-CLOSE consumes the explicit reused-evidence matrix accepted in PR #179.
It covers:

- 1/2/3/5/6 meal opportunities;
- seven-opportunity rejection;
- MealPattern acceptance/versioning/persistence;
- Recipe `MealTypeCode` distinct from `MealRole`;
- MealSourceKind capability/no-fabrication boundaries;
- source artifact tamper;
- immutable process-binding drift;
- no gate-only authoritative data.

The closure validator requires the complete matrix and every row to carry
`status=SUCCESS`.

## DECISION — nutrition/corpus interpretation

Gate1-CLOSE follows the **latest accepted** DATA-CORPUS-V1 and DC4 contracts.

The older Gate1-A minimal-data repair sequence is not reopened. The accepted
current production model permits source-backed `PREPARED_OUTPUT_V1` authority
with exact `ENERGY_KCAL` while other canonical nutrients remain explicitly
UNKNOWN. UNKNOWN is not promoted to zero, and DC4 proved every active current
RecipeVersion has its required accepted authority/provenance.

This closure therefore does not invent ingredient-derived macros/micronutrients
or silently reintroduce superseded Gate1-A corpus repair requirements.

## Non-goals / known limits

Gate1 closure proves the Planning Core required to proceed to generic Shopping.
It does **not** claim that FamilyFoodOS MVP is complete.

Still outside this decision:

- Shopping aggregation/Pantry subtraction;
- Prep/Freezer;
- PDF;
- consumer PWA;
- retailer SKU/price/availability;
- AI;
- PostgreSQL/Auth/tenant isolation;
- medical/therapeutic diet support.

The broader FoodIngredient catalogue may continue growing later according to the
roadmap; Gate1's 80+ minimum is exceeded by the current 227 active identities and
is not a reason to add filler data before PR9.

## Exit

On independent review + merge of PR #181:

```text
GATE1-CLOSE — COMPLETE
→ PR9 Shopping Engine — NEXT AUTHORIZED MILESTONE
```

Do not begin PR9 before this closure PR is merged.
