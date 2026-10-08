# Current focus

Updated: 2026-10-08.

## Gate1-CLOSE — final decision review

Accepted main:

`c85fae8e8e2c135855f1ba64ca6722de20e1bd29`
(merged PR #179 — corrected-runtime DC4 rerun PASS).

Current operation:

- Issue #180;
- PR #181;
- branch `docs/gate1-close`;
- Gate1 closure validator evidence head
  `4f3be9ad3d9c9ff929c86c7478a3881c65aa3c93`.

### Closure evidence

Gate1 validator result:

- decision: **CLOSE**;
- Planning Core status: **COMPLETE**;
- active FoodIngredient count: **227** (threshold >=80);
- verified current RecipeVersions: **51** (threshold >=30);
- DC4 rerun: PASS / blockers=[];
- Planner: `planner-v0.5`;
- mandatory fixtures: 7/7, 14/21, 21/42 MealEvents/Servings;
- bounded milk+egg infeasibility: fail-closed / no partial MealPlan;
- reused domain/adversarial evidence matrix: complete;
- migration 0042 / no 0043;
- AI disabled;
- failed closure criteria: none.

Evidence receipt:

- workflow `Gate1 closure`;
- run `37808665837`;
- job `113419518103`;
- artifact `11563757892`;
- machine: `data/curation/gate1-close/decision.json`;
- human: `docs/family-food/gate1-closure.md`.

## Current authorization

PR #181 is the explicit Gate1-CLOSE decision. It must be independently reviewed
and merged before the milestone is considered closed.

Until #181 merge:

- Gate1 is not yet durably CLOSED;
- PR9 Shopping Engine is **not** authorized to start.

On #181 merge:

```text
GATE1-CLOSE COMPLETE
→ PR9 Shopping Engine — NEXT AUTHORIZED MILESTONE
```

No PR10/Prep/PDF/PWA/Retail/AI/Auth/PostgreSQL work is authorized by this closure.

---

Updated: 2026-10-08.

## DC4 corrected-runtime rerun — final review

Accepted main:

`2482c52085d7ba9e530f650105a6664ed6d369a7`
(merged PR #177).

Accepted correction tracks:

- A1 / PR #168 — MERGED;
- A2 / PR #173 — MERGED;
- A3 / PR #177 — MERGED; Track A accepted;
- B1 / PR #169 — MERGED;
- B2 / PR #175 — MERGED; Track B accepted;
- current Planner = `planner-v0.5`.

Current operation:

- Issue #178;
- PR #179;
- branch `evidence/dc4-rerun-v05`;
- exact execution evidence head
  `35cf1d154467ac4171979ea2943b600548c0fb27`.

### Verified rerun evidence

Dedicated workflow run `37771436384`, job `113291728664`, artifact
`11548231670`:

- focused rerun tests: 7 passed;
- Layer A: 51 active / 51 PASS / 0 BLOCKED;
- Planner exact-energy supply: 51 = 17 breakfast / 33 main / 1 sandwich;
- Planner version: `planner-v0.5`;
- Fixture 1: 7 events / 7 Servings — PASS;
- Fixture 2: 14 events / 21 Servings — PASS;
- Fixture 3: 21 events / 42 Servings — PASS;
- selected hard exclusions respected;
- bounded MILK_2_5 + EGG case: `NO_ELIGIBLE_CANDIDATE`, no partial plan;
- `overall_status=PASS`, `blockers=[]`;
- migration 0042 / no 0043;
- `AI_ENABLED=false`.

Durable receipts:

- `data/curation/dc4-corpus-readiness/rerun-summary.json`;
- `docs/family-food/dc4-corpus-readiness-rerun-report.md`.

Historical PR #165 evidence remains unchanged and truthfully records the old
BLOCKED result on pre-correction catalogue + `planner-v0.4`.

## Current authorization

The only current operation is **independent review of PR #179**.

The rerun evidence is PASS, but the accepted project state does not advance to
Gate1-CLOSE until #179 is reviewed and merged.

After #179 merge:

```text
DC4 rerun accepted
→ separate Gate1-CLOSE decision
→ PR9 Shopping Engine only if Gate1-CLOSE passes
```

Do not start PR9 directly from rerun evidence. Do not merge #179 autonomously.

---

Updated: 2026-10-08.

## Post-DC4 bounded corrections — A3 final review

Accepted main:

`2a16521a69d48b6df6dcec944ef39fd270d0a95f`
(merged PR #175 after merged PR #173).

Accepted correction sequence:

```text
Track A
A1 evidence investigation                         MERGED #168
→ A2 immutable RecipeStep correction Contract Gate MERGED #173
→ A3 RecipeVersion runtime/data correction         PR #177 — CURRENT / REVIEW-READY
→ A accepted only after #177 merge

Track B
B1 ordering investigation                          MERGED #169
→ B2 planner-v0.5 ordering runtime correction       MERGED #175
→ B accepted
```

Current Planner algorithm/version is **`planner-v0.5`**. Historical
`planner-v0.4` remains a replay version and was not silently rewritten.

### A3 verified runtime evidence

PR #177 runtime freeze:

`0aa949c7989f70658c2633e4792371c251bfcd7f`.

Focused post-correction evidence:

- workflow run `37762618205`, job `113262471748`;
- exact-run artifact `11543480822`;
- active catalogue 51;
- Layer-A blocked rows 0;
- `RUSSIAN_STEPS_NOT_READY` 0;
- all seven prior Russian-step blockers cleared;
- Planner exact-energy eligible 51 = 17 breakfast / 33 main / 1 sandwich;
- Planner version `planner-v0.5`;
- full old/new steps, source commitments, expected energy and exact-run
  predecessor/successor RecipeVersion IDs are frozen in
  `data/curation/dc4-a3-russian-step-corrections/evidence.json`;
- human receipt:
  `docs/family-food/dc4-a3-post-correction-evidence.md`.

This focused receipt is **not** a full DC4 rerun.

## Current authorization

The only current operation is **final independent review of PR #177**.

Do not merge autonomously.

DC4 remains **BLOCKED / not re-accepted** until A3 is merged and a separate full
DC4 rerun executes the accepted DC4 contract, including all three Gate1 fixtures
and bounded infeasibility.

After A3 merge, the next authorized operation is:

```text
A3 MERGED + B2 MERGED
→ separate DC4 rerun on planner-v0.5/current corrected catalogue
→ separate Gate1-CLOSE only if DC4 passes
→ PR9 Shopping Engine only after Gate1-CLOSE
```

Do not start Gate1-CLOSE or PR9 directly from the focused A3 evidence.

---

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
