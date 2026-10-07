# Current focus

Updated: 2026-10-07.

## Accepted state

PR #165 / DC4 execution evidence is MERGED at:

`c521e6d89a4d9fcc2900804ff7e05de66f14b093`.

Independent blocker investigations are also MERGED:

- PR #168 / Issue #166 — seven Russian RecipeStep findings confirmed as genuine consumer-language violations;
- PR #169 / Issue #167 — Fixture 3 failure isolated to a Planner household-event ordering bug under the existing MealPlan completeness contract.

Current accepted main:

`d3e73072e4e24dde25a1251e19327731455e306f`.

DC4 remains **BLOCKED**.

## Current bounded authorization

Two independent correction tracks are authorized after this reconciliation PR is reviewed and merged.

### Track A — immutable Russian RecipeStep correction

Goal: remove the seven confirmed consumer-language violations without mutating accepted RecipeVersions in place or losing provenance.

Exact sequence:

```text
A1 evidence investigation                         MERGED #168
→ A2 docs-only immutable correction Contract Gate
→ A3 separately reviewed RecipeVersion runtime/data correction
→ A accepted
```

A2 must define the lawful immutable/version-aware publication path before any production RecipeVersion publication or activation. The gate must preserve source/card hashes, source semantics, rights review, process bindings, ingredient quantities, Nutrition authority/UNKNOWN semantics, immutable prior versions and replay/conflict/rollback behavior.

**Merging A2 alone does not complete Track A and does not authorize a DC4 rerun.** Track A is accepted only after the separately reviewed A3 runtime/data correction is merged and its required verification passes.

No in-place mutation of an accepted RecipeVersion is authorized.

### Track B — focused Planner household-event ordering correction

Goal: correct the local Planner ordering defect identified in PR #169 while preserving each member's accepted opportunity order and the existing MealPlan completeness validation.

No cross-context contract change is currently required by the accepted investigation.

**Planner versioning is mandatory:** the known Fixture 3 ordering correction changes deterministic event ordering for the same accepted inputs, so B2 is expected to introduce a new Planner algorithm/config version rather than silently changing behavior under `planner-v0.4`. Preserving the old version identity would require a separate, explicit and independently reviewed proof that the version semantics are in fact unchanged.

The runtime correction must retain exact Fixture 3 expectations:

- 21 household MealEvents;
- 42 individualized Servings;
- member-specific hard beef exclusion;
- deterministic replay;
- no weakening of `validate_complete_plan`.

If implementation disproves the local-bug assumption and requires changing a cross-context contract, stop and create a docs-only Implementation Contract Gate before runtime changes.

## Sequence

Tracks A and B may proceed independently after this reconciliation is accepted.

```text
Track A
A1 evidence                         MERGED #168
→ A2 docs-only immutable correction Contract Gate
→ A3 separately reviewed RecipeVersion runtime/data correction
→ A accepted

Track B
B1 investigation                    MERGED #169
→ B2 versioned Planner ordering runtime correction
→ B accepted

A3 accepted + B2 accepted
→ separate DC4 rerun
→ Gate1-CLOSE
→ PR9 Shopping Engine
```

Do not start the DC4 rerun after A2 alone. It is authorized only after both A3 and B2 are accepted and merged.
Do not start Gate1-CLOSE or PR9 before a passing rerun and separate closure decision.

---

Updated: 2026-10-06.

## Accepted state

PR #163 / DC4 Contract Gate is MERGED into `main` at:

`0ce316009eb6223d05756f175f388869ae8debd8`.

DATA-CORPUS-V1 / DC3 is COMPLETE. DC4 contract is accepted.

## Current bounded operation

**DC4 execution/evidence — corpus readiness audit + Gate1 consumption.**

Issue: `#164`.

Branch:

`feat/dc4-corpus-readiness`.

Accepted base:

`0ce316009eb6223d05756f175f388869ae8debd8`.

Scope:

- deterministic full-active catalogue audit;
- separate Planner-eligible exact-energy reconciliation to 51 = 17/33/1;
- exact three frozen Gate1 fixtures;
- exact fail-closed MILK_2_5 + EGG breakfast case;
- machine-readable summary + human-readable report;
- focused tests / dedicated CI;
- state synchronization.

No production data publication, migration 0043, Planner redesign, Gate1-CLOSE
or PR9 scope is authorized.

## Sequence decision

```text
DC4 execution/evidence             CURRENT
→ Gate1-CLOSE
→ PR9 Shopping Engine
```

DC4 audit evidence is BLOCKED on this bounded branch:

- Inventory A: 51 active, 44 PASS, 7 Russian-step readiness BLOCKED;
- Inventory B: 51 eligible exact-energy, 17/33/1 (PASS);
- Fixture 1: persisted 7/7; Fixture 2: persisted 14 events / 21 Servings;
- Fixture 3: Planner produced 21 events but persistence rejected role/order;
- MILK_2_5 + EGG infeasibility: fail-closed PASS.

Review the current PR #165 and the frozen evidence in
`data/curation/dc4-corpus-readiness/summary.json` and
`docs/family-food/dc4-corpus-readiness-report.md`.
Do not silently repair production truth in this PR. Gate1-CLOSE and PR9 remain
blocked until separately reviewed correction and a passing DC4 re-audit.

---

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
operation freezes the two-inventory audit model (dynamic full active catalogue +
51-row Planner-eligible exact-energy baseline), exact Gate1 fixture matrix,
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
