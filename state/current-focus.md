# Current focus

Updated: 2026-10-06.

## Accepted state

PR #161 post-R3-D reconciliation is MERGED into `main` at:

`d3fc30d7eb677d3dc7aec8f6cb219fffa22762e4`.

DATA-CORPUS-V1 / DC3 is COMPLETE.

## Current bounded operation

**DC4 Contract Gate — corpus readiness audit + Gate1 consumption.**

Issue: `#162`.

Branch:

`docs/dc4-gate1-consumption-contract`.

Accepted base:

`d3fc30d7eb677d3dc7aec8f6cb219fffa22762e4`.

Canonical contract target:

`docs/family-food/dc4-corpus-readiness-contract.md`.

Scope is docs/state plus one verification-only CI compatibility correction. This
operation freezes the audit inputs, exact Gate1 fixture matrix,
PASS/BLOCKED/DEFERRED rules, adversarial acceptance and verification for the
later DC4 execution.

The CI correction adds only the same downstream changed-path guard already used
by the R3-D gate workflow; focused R3-D verification remains active. No runtime,
data publication, schema, migration, Planner-algorithm, API or UI change is
authorized in this contract PR.

## Sequence decision

```text
DC3 COMPLETE
→ DC4 contract                    CURRENT
→ DC4 execution/evidence
→ Gate1-CLOSE
→ PR9 Shopping Engine
```

Do not create R3-E/R3-F merely to increase catalogue size.

Do not start DC4 execution before this contract is independently reviewed and
merged. Do not start Gate1-CLOSE or PR9 automatically.

---

Updated: 2026-10-05.

## Accepted state

PR #160 / R3-D final DC3 runtime is MERGED into `main` at:

`bbab6a0899c74f995c988455fe57d8d1f63d79af`.

DATA-CORPUS-V1 / DC3 is COMPLETE.

Accepted post-R3-D production Planner truth includes:

- 51 active exact-energy RecipeVersions;
- 17 `breakfast`;
- 33 `main`;
- 1 `sandwich`;
- MAIN family distribution: beef 14 / fish 9 / chicken 4 / meat-free 6;
- exact-beef unaffected MAIN = 19 / repetition capacity 57;
- hard exact `MILK_2_5` breakfast unaffected set = 3 / repetition capacity 9;
- migration head remains `0042_recipe_prepared_output_nutrition`;
- no migration `0043`;
- `AI_ENABLED=false`;
- Planner role mapping/scoring/repetition remain unchanged by R3-D.

## Current bounded operation

**Post-R3-D reconciliation → DATA-CORPUS-V1 / DC4 corpus readiness audit + Gate1 consumption.**

This reconciliation PR is state/docs only. It records the accepted merge and
authorizes preparation of the next bounded DC4 audit operation after this PR is
reviewed and merged.

Canonical sequence:

```text
PR8 Planner v0                         COMPLETE
→ Gate1-A audit/readiness baseline    COMPLETE
→ DATA-CORPUS-V1 / DC0               COMPLETE
→ DC1 source authority/coverage       COMPLETE
→ DC2 food publication               COMPLETE
→ DC3 recipe publication             COMPLETE
→ DC4 corpus readiness audit + Gate1 consumption   NEXT
→ GATE1-CLOSE
→ PR9 Shopping Engine
```

## DC4 objective

DC4 must audit existing accepted production truth rather than grow the catalogue
for its own sake.

At minimum it must determine:

- corpus-wide active RecipeVersion readiness;
- required FoodIngredient resolution;
- accepted nutrition/provenance authority;
- Russian display readiness;
- meal-role and weekly variety capacity;
- three materially different repository-backed fixture households;
- complete 7-day authoritative Planner generation where feasible;
- individualized Servings;
- hard exclusions;
- heterogeneous meal patterns;
- deterministic trace/replay;
- explicit bounded infeasibility for unsupported cases;
- whether Gate1 can consume ordinary production catalogue truth without a
  gate-only data exception.

Any material corpus defect found by DC4 requires a separately reviewed bounded
correction. DC4 itself must not silently expand into another R3 batch.

## Sequence decision

Do not create R3-E/R3-F merely to increase catalogue size.

Do not start:

- Gate1-CLOSE before DC4 evidence;
- PR9 Shopping Engine before Gate1-CLOSE;
- Prep / Freezer / PDF;
- consumer PWA;
- Retail;
- AI;
- PostgreSQL/Auth/shared deployment.

The next implementation milestone after a successful DC4 + Gate1-CLOSE is:

`PR9 — Shopping Engine`.

## Current scope boundaries

No runtime, schema, migration, Planner algorithm, Nutrition authority, API or UI
change is authorized by this reconciliation operation.
