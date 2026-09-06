# Progress

Updated: `2026-09-07`

## FamilyFoodOS milestone status

```text
PR0   Frozen Fork                          COMPLETE
PR1   Identity Detox                       COMPLETE
PR2-A Architecture & Persistence Contract COMPLETE
PR2-B Persistence Foundation               COMPLETE
PR2-C Household Foundation                 COMPLETE
PR2-DOCS Canonical Roadmap Sync            COMPLETE
PR3   FoodIngredient Catalogue             COMPLETE
PR4-DATA Recipe coverage support           COMPLETE
PR4-DATA2 Russia/SPB corpus re-curation    COMPLETE
PR4   Recipe Catalogue                     COMPLETE
PR5   Pantry                               COMPLETE
PR6   Nutrition Core                       NOT COMPLETE (engine ACCEPTED / MERGED)
```

Canonical implementation order remains `docs/family-food/master-roadmap.md`.

## PR6 implementation evidence

- Accepted starting main: `0979181409d34e4a193d58b60f4bbc8fa8d1e974` (PR #17 merged).
- [PR #18](https://github.com/Mitronomik/family-food-os/pull/18): ACCEPTED / MERGED; merge commit `7c449672c039c66b8d475064462eba2a9f6d38e6`.
- Merged delivery head: `9dffb5fcbc8ec0b3d4a1f36f5349d68c944f2bbe`.
- Verified implementation commit: `0d08839216ddd40a3ef2f5fd84edb8f69b2447f6`.
  The publication commit changes only state delivery evidence; verified runtime/tests
  are byte-identical. Engine implementation is ACCEPTED / MERGED.
  PR6 milestone is NOT COMPLETE, pending data readiness / closure.
- Contract: [Nutrition Core](../docs/family-food/nutrition-core.md).
- Read-only, Decimal ingredient/RecipeVersion nutrition and member reference
  targets, with versioned NASEM/DRI/Atwater inputs and explicit uncertainty.
- No schema/cache, API/frontend, catalogue truth changes or PR7+ implementation.
  Migration head remains `0025_pantry`.
- Production seed audit: 30/30 INCOMPLETE, other status counts zero. Reasons:
  missing density 123, unsupported piece mass 35, missing ingredient/profile 0,
  unknown fiber 30, estimated=true 0, estimation status unknown 189, optional 4.
  These are overlapping row occurrences including optional rows; see the contract
  for affected-recipe counts and the bounded follow-up recommendation.

Executed verification (all with `AI_ENABLED=false`):

```sh
python3 -m pytest -q backend/app/tests/test_nutrition*.py backend/app/tests/persistence/test_nutrition*.py
# 131 passed in 2.56s (115 domain/target including 3 family fixtures,
# 8 application, 5 persistence, 2 architecture, 1 audit)

python3 -m pytest -q backend/app/tests/test_food_ingredient*.py backend/app/tests/test_food_recipe*.py backend/app/tests/test_household*.py backend/app/tests/persistence/test_food_ingredient_repository.py backend/app/tests/persistence/test_food_recipe_repository.py backend/app/tests/persistence/test_household_repository.py backend/app/tests/persistence/test_unit_of_work.py
# 225 passed in 10.20s; includes affected contexts, seed/migration compatibility,
# their architecture tests and the shared Unit of Work.

python3 -m pytest -q -s backend/app/tests/test_nutrition_catalogue.py
# 1 passed; exact 30-version audit printed, no production data edits.

python3 -m pytest -q backend/app/tests launcher/tests
# Sandbox attempt: 3100 passed, 162 failed, 121 errors in 230.19s.
# All failure/error entries are launcher tests; loopback bind was denied by
# the sandbox (PermissionError: [Errno 1] Operation not permitted).
# Required rerun with loopback access: 3386 passed in 485.55s (0:08:05),
# zero skips; all 131 new Nutrition tests included. No runtime changes after this run.
```

Ruff check and format check: PASS, 13 changed Python files. `git diff --check`:
PASS. `git diff --cached --check` and final staged scope audit: PASS, 18 files
(7 runtime, 6 tests, 2 canonical docs/status, 3 state). The only unrelated
working-tree change is `.DS_Store`, excluded from staging/commits. No milestone
completion or PR7 authorization is claimed.

## PR6-DATA-A evidence

Supporting research/data-curation starts from exact main
`7c449672c039c66b8d475064462eba2a9f6d38e6` on
`data/pr6-nutrition-conversion-audit`. The
[nutrition data-readiness audit](../docs/family-food/nutrition-data-readiness.md)
and its 290-record source manifest cover all 30 accepted RecipeVersions and
189 ingredient rows: 31 g, 123 ml and 35 pcs. All 158 conversion rows have one
controlled decision; all 189 have semantic review. Accepted original artifacts
were reopened and their PR4 hashes verified for all 30 recipes.

Numeric candidates: 66 exact, 43 estimated, 49 unresolved. Readiness: 66 exact,
0 estimated, 92 not ready. Semantic findings include 17 form mismatches,
1 identity mismatch and 19 ambiguities; source quantity findings affect six
rows in five recipes. These are review findings, not production corrections.
Exact affected-recipe counts and source limitations are in the canonical audit.

Executed DATA-A verification on 2026-09-06 (`AI_ENABLED=false` for pytest):

```sh
python3 -m pytest -q backend/app/tests/test_pr6_data_a_research.py
# 18 passed in 0.89s

python3 -m pytest -q backend/app/tests/test_pr6_data_a_research.py backend/app/tests/test_pr4_data2_research.py backend/app/tests/test_pr4_data_coverage.py backend/app/tests/test_food_recipe_seed.py
# 199 passed in 5.74s (18 research + 181 existing PR4/corpus/seed checks)

python3 -m pytest -q -s backend/app/tests/test_nutrition_catalogue.py
# 1 passed in 0.58s; 30 INCOMPLETE / 189 rows; MISSING_DENSITY 123/30 recipes,
# UNSUPPORTED_PIECE_MASS 35/21; UNKNOWN_FIBER 30/21;
# ESTIMATION_STATUS_UNKNOWN 189/30; OPTIONAL_INGREDIENT 4/2.

python3 scripts/validate_pr6_data_a.py
# PASS: exact stable-row coverage, source references, Decimal candidate
# arithmetic, pinned summary and 450 protected-file SHA-256 checks.

python3 -m ruff check scripts/validate_pr6_data_a.py backend/app/tests/test_pr6_data_a_research.py
python3 -m ruff format --check scripts/validate_pr6_data_a.py backend/app/tests/test_pr6_data_a_research.py
# PASS
```

The initial `.venv/bin/python` audit attempt could not import SQLAlchemy;
the successful checks above use the available `python3` environment. No full
backend/launcher run is claimed or required for this data/docs-only operation.

Production seeds, accepted PR4 source evidence, runtime, schema, API and frontend
remain byte-identical to the accepted base. Migration `0026` is absent.
The unrelated `.DS_Store` change is excluded from delivery.
`git diff --check`, `git diff --cached --check` and the staged scope audit PASS:
13 intended files (three curation artifacts, five canonical docs, three state
files, one offline validator and one focused test file). Documentation file links
resolve. The post-staging focused rerun passed all 18 tests in 0.88s.

Historical DATA-A delivery state: PR6 engine implementation ACCEPTED / MERGED;
PR6 milestone NOT COMPLETE. DATA-A evidence was supplied for project review;
its next action required explicit authorization of bounded DATA-B work. None was
pre-authorized. PR7+ remain unauthorized. No DATA-A-CLOSE operation is needed.

## PR6-DATA-B1 evidence

Explicit B1 supporting-operation authorization starts from DATA-A accepted main
`60908eb8270ef356eff8552855b4cc5d2aa9ee44`, branch
`feature/pr6-data-b1-measure-evidence`. Migration/head:
`0026_nutrition_measure_evidence`. Foundation established by this changeset:
57 immutable evidence records, 189 current assessments, 123 ordered issues;
66 exact approvals, 20 clean g approvals, 37 estimate reviews, 66 blocked rows.
All 43 estimate candidates remain non-executable. Production audit: all 30
recipes INCOMPLETE, missing-assessment and old recipe density/piece warnings zero.

Executed verification (`AI_ENABLED=false`): focused Nutrition/targets/DATA-A
**212 passed in 25.40s**; affected catalogue/Recipe/Household/Pantry/migration/UoW
**472 passed in 28.31s**; full backend + launcher with local loopback access:
**3467 passed in 501.50s (0:08:21)**. Preliminary sandbox run: 3158 passed,
186 failed, 121 errors in 256.02s; outdated backend schema/config/audit assertions
were corrected and launcher loopback access supplied for the final full rerun.
Ruff/format (34 Python files), deterministic promotion/audit regeneration,
diff/staged checks and staged scope audit PASS.

Fresh and populated 0025→0026 upgrade preserve prior schema/data. Idempotent seed
has zero second-run inserts and identical dump; late import/migration failures
roll back; profile replacement invalidates review, explicit v2 restores authority,
and an open snapshot retains old inputs coherently. All production recipe/profile
seed and DATA-A research bytes remain unchanged. Full commands, exact hash pins,
warning/issue counts and changed-file inventory:
[B1 verification report](../docs/family-food/pr6-data-b1-verification.md).

PR6 engine and DATA-A are ACCEPTED / MERGED. B1 is established by this changeset;
its own merge/acceptance is not claimed. PR6 remains NOT COMPLETE; DATA-B2 is
NOT AUTHORIZED; PR7+ remain UNAUTHORIZED. No DATA-B1-CLOSE is required.

## Historical delivery records

The records below describe prior accepted operations and their then-current
state. Their PR6 pre-implementation wording is historical, superseded by the
PR6 acceptance and DATA-A evidence above; it grants no current authorization.

## AGENT-HARNESS governance evidence

PR #16 (PR5-CLOSE) merge was verified via GitHub and remote main on 2026-09-06:
`abcb1ca8d464477baed72cdf8e06a0d126b5e743`, merged at `09:39:32Z`.
[PR #17](https://github.com/Mitronomik/family-food-os/pull/17) carries the agent
harness from that exact base: shorter root/scoped instructions, task routing,
one PR delivery Skill, proportional verification policy,
rule-disposition ledger and eight-case eval matrix. Roadmap edits are limited to
reading navigation; UI instruction files remain unchanged (P2 follow-up).

This is supporting governance, not a numbered milestone. No runtime/schema/data
change or backend regression run is claimed. Verification evidence is recorded
in [harness evals](../docs/family-food/agent-harness-evals.md). The harness
establishes the active repository governance/instruction design and leaves
product state unchanged: PR5 COMPLETE, PR6 AUTHORIZED / NOT STARTED,
PR7+ unauthorized.

## PR5 closure

`PR5 — Pantry — COMPLETE`

- [PR #15](https://github.com/Mitronomik/family-food-os/pull/15): MERGED;
- accepted/merged head: `4778b6e99fde027be7e70b8a8966db85394e100d`;
- merge commit / verified main: `5f1bb47199ab661d58b92b8cbb9e40b4aeb7b0d0`;
- fully tested implementation: `d5b821ce9969ee2bf167333d9b48675d0f6d470f`;
- final project review: `PR5 FINAL REVIEW: ACCEPT — READY TO MERGE`.

PR5-CLOSE reuses the accepted verification from PR #15, recorded below; no new
regression run is claimed. The publication commit changed only state files,
and the accepted head and merge commit have identical file trees.
PR6 Nutrition Core is AUTHORIZED / NOT STARTED.

## PR5 implementation evidence

- Base: `main` / `b7fb609fc28dc46fa5891fc677272b6d21b58b58`.
- Branch: `migration/pr5-pantry`; [PR #15](https://github.com/Mitronomik/family-food-os/pull/15) → `main`, MERGED.
- Verified implementation commit: `d5b821ce9969ee2bf167333d9b48675d0f6d470f`.
  Subsequent publication commit only records this PR/evidence in state files.
- Contract: [Household Pantry core](../docs/family-food/pantry-core.md).
- Dedicated PantryItem/current Decimal balance and immutable PantryMovement.
- Add, FEFO ingredient consumption, waste, target adjustment, metadata-only
  update, available quantity and expiring queries; eight HTTP route capabilities.
- One UoW per command, exact Decimal-text compare-and-swap, non-negative balance,
  positive unsigned movements, ledger reconciliation and Household isolation.
- Additive migration `0025_pantry`, custom-runner/restore-lineage registration,
  composite Household/item/unit FK and SQLite immutability guards.
- Populated `0024 → 0025` upgrade preserves all previous rows/schema, including
  the accepted 30 Recipe / 30 Version / 189 RecipeIngredient catalogue and a
  Household. Fresh migration and foreign-key enablement are verified.

### PR5 accepted checks (reused by PR5-CLOSE)

Runtime: local Python 3.12.13 via `backend/.venv/bin/python`; `PYTHONPATH=backend`.

- Focused Pantry: **267 passed in 33.33s** — 98 domain, 50 application, 62 API,
  51 persistence/UoW, 3 migration, 3 architecture.
- Affected Household/FoodIngredient/Recipe domain/application/repository and
  generic UoW regression: **167 passed in 9.52s**.
- Backend migration selection (`pytest backend/app/tests -k migration -q`):
  **142 passed, 2468 deselected in 13.60s**.
- Focused tests include exact ledger reconciliation, insufficient stock with no
  movement, multi-item rollback after second-write failure, overlapping writers,
  commit/rollback failure discard, terminal handles and foreign UUID isolation.
- Read-only adversarial review found epoch-string calendar coercion; strict ISO
  validation and API negative regressions fix it. Signed zero normalizes to
  `0.000`.
- Full backend + launcher (`pytest backend/app/tests launcher/tests -q --tb=short`):
  **3255 passed in 467.40s (0:07:47)**, zero skips, zero failures.
  The initial sandbox run
  blocked localhost socket binds; the authorized rerun enables localhost sockets.
  Obsolete migration-tail/table/backup expectations were corrected while preserving
  original historical cutoff coverage.
- Ruff format/check: PASS for all 26 changed Python files.
- `git diff --check`, `git diff --cached --check`: PASS.
- Staged scope audit: PASS, exactly 30 reviewed files; no secrets, local DBs,
  frontend/data/workflow changes or historical migration edits.

### PR5 limitations and next gate

No Auth: Household selection is not authorization. Quantity precision is 0.001
for g/ml/pcs (fractional pcs supported), with max 999999999999.999 per item or
command. No conversion, invented expiry, food-safety recommendation, automatic
conflict retry or idempotency key. Supported service commands own ledger writes;
raw repository primitives are internal. No frontend or future context work.

PR5 is COMPLETE. PR6 Nutrition Core is AUTHORIZED / NOT STARTED.
Its scope remains FoodIngredient nutrition → RecipeVersion nutrition → Member
target formula/config foundation. Serving begins only in PR7.

## PR4-DATA2 closure

PR #13 merged after `PR4-DATA2 FINAL REVIEW: ACCEPT`.

The dated `2026-09-05` [DATA2 README](../data/curation/pr4-data2/README.md)
and [correction review report](../data/curation/pr4-data2/review-report.md) remain
historical evidence snapshots. Their review status, next-action instructions
and PR5 authorization statements are superseded by the accepted closures here
and the current master roadmap; they are not operative milestone gates.

- accepted head: `918bf81b5da306fc65a57643de515ca1b3fbd1e4`;
- merge/main commit: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`;
- final corpus: 30 recipes;
- 189 selected ingredient rows;
- exact 81 existing FoodIngredient codes;
- 86 source-backed equipment rows / 34 codes;
- 0 new FoodIngredient;
- 0 unresolved required ingredient rows;
- 0 unresolved required direction-consumables;
- accepted source-specific narrow direct-FNS rights posture.

## PR4 scope reset

The user approved retaining PR #10's Recipe Catalogue runtime while removing obsolete seed/acquisition assumptions.

Superseded as PR4 hard gates:

- old 119-FI historical seed;
- all-servings-6 assumption;
- old 365 ingredient / 315 step / zero-equipment production counts;
- blanket rights inference;
- exact historical retrieval instant requirement;
- fresh-source acquisition as a prerequisite for publishing the accepted DATA2 technical corpus.

`source_retrieved_at` is nullable. Known true instants are stored; unknown values remain `NULL`.

## PR4 closure

`PR4 — Recipe Catalogue — COMPLETE`

- GitHub PR [#10](https://github.com/Mitronomik/family-food-os/pull/10): MERGED;
- merge commit: `e7a2e00615c8ef1f5bdb4634089e821542ba50dc`;
- accepted/merged head: `0ac6c9d34a3cc54052c8fd01af3acfc49786242f`;
- final project review: `PR4 FINAL REVIEW: ACCEPT — READY TO MERGE`;
- final regression gate: PASS;
- deterministic seed/idempotency and fail-closed curation validation remain accepted.

## PR4 accepted implementation

Latest fully tested implementation commit:

`173b0f5479c7af2dd7095bf54f9393b2ff68ba55`

Merged PR #10 delivered:

- Recipe and immutable/versioned RecipeVersion;
- ordered RecipeIngredient referencing `food_ingredients`;
- ordered RecipeStep and RecipeEquipment;
- exact Decimal scaling;
- source/rights/verification metadata;
- append-version/current-verified semantics;
- deactivate behavior;
- repository contracts and synchronous SQLAlchemy Core adapters;
- Recipe Catalogue UoW/read scope;
- migration `0024_food_recipe_catalogue` after `0023`;
- DB immutability triggers for version-owned rows;
- deterministic offline DATA2 compiler/seed;
- idempotent seed reconciliation;
- fail-closed validation against accepted per-recipe ingredient selection, equipment order, reviewed steps and step lineage.

Production seed counts:

```text
30 Recipe
30 SOURCE_VERIFIED RecipeVersion v1
189 RecipeIngredient
169 RecipeStep
86 RecipeEquipment
34 equipment codes
81 referenced FoodIngredient codes
0 unresolved required ingredients
0 unresolved required direction-consumables
```

Ordered steps are durably reviewed in `data/curation/pr4-runtime/recipe-steps.json`. The selected Grilled Fruit variant has three active steps; wooden-skewer soaking is conditional and not active because DATA2 selected a non-wood skewer.

## Verification

### Scope-reset / seed acceptance — run 34001179713

- DATA2 validator PASS;
- DATA2 focused `164 passed`;
- PR4 focused `55 passed`;
- fresh first seed `30/30/189/169/86`, conflicts 0;
- second identical seed 0 inserts, existing `30/30/189/169/86`, conflicts 0;
- compiler regeneration byte-identical;
- full backend+launcher `2983 passed, 2 skipped`;
- Ruff and diff checks PASS;
- final workflow diff empty.

### Final fail-closed hardening — run 34002182325

- DATA2 validator PASS;
- DATA2 focused `164 passed in 3.56s`;
- PR4 focused `58 passed in 15.56s`;
- full backend+launcher `2986 passed, 2 skipped, 1 warning in 626.61s`;
- Ruff PASS;
- `git diff --check` and staged diff PASS;
- temporary hardening workflow removed before push;
- new negative regressions prove same-count ingredient mapping drift, equipment-order drift, step-text drift and step-lineage drift are rejected.

## Current gate

PR5 is COMPLETE. PR6 engine and DATA-A are ACCEPTED / MERGED.
B1 exact evidence/binding foundation is established by this changeset.
PR6 milestone remains NOT COMPLETE; DATA-B2 is NOT AUTHORIZED and PR7+ remain
UNAUTHORIZED. No separate DATA-B1-CLOSE is required. Current authorization and
scope are in [current focus](current-focus.md).
