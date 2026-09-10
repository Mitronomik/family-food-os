# Progress

Updated: `2026-09-10`

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

## PR6-ARCH-COMPOSITION verification

Exact starting main: `47299ceb2c740f40f69f3b02359ce71c8be6b1c1` (PR #23 merged).
Branch: `docs/pr6-arch-composition`. This changeset establishes only the approved
docs / architecture / roadmap / governance / state contract. PR6 remains NOT COMPLETE.
The existing user checkout and its unrelated `.DS_Store` change are preserved;
work is isolated in a separate worktree from the exact base.

Approved user decisions and consequences: Option A is DECISION / APPROVED;
FoodIngredient is sole identity; atomic/composite, exact/declared-only composition,
recursive versioned DAG, distinct mass states, evidence-backed yield/retention,
extensible NutrientVector with nutrient-level provenance/unknown != zero, RU
availability/familiarity, full Russian consumer/admin display without English
fallback, and deterministic RecipeTemplate/Assembly precede MealPlan/Serving.
[Composition](../docs/family-food/food-composition-and-assembly.md) and
[language](../docs/family-food/russian-language-contract.md) own the contracts;
[roadmap §6.5](../docs/family-food/master-roadmap.md#65-pr6-arch-composition--approved-roadmap-differences)
records the exact approved reorder and unchanged downstream gates.

Exact changed-file scope (13 documentation/governance/state files):

- `AGENTS.md`;
- `docs/family-food/architecture.md`;
- `docs/family-food/master-roadmap.md`;
- `docs/family-food/nutrition-core.md`;
- `docs/family-food/nutrition-data-readiness.md`;
- `docs/family-food/recipe-localization-and-substitution.md`;
- `docs/family-food/technical-spec.md`;
- `docs/family-food/data-ingestion.md`;
- `docs/family-food/food-composition-and-assembly.md` (new canonical owner);
- `docs/family-food/russian-language-contract.md` (new canonical owner);
- `state/current-focus.md`;
- `state/progress.md`;
- `state/handoff.md`.

Production/runtime/schema/data impact: none. Nutrition v1 remains the current
implementation; 30 current FNS recipes / 189 rows / 30 INCOMPLETE remain technical
production baseline. All 43 estimates remain non-executable. Migration head:
`0027_recipe_same_source_revisions`. Old PR6-DATA-B2-B2: **SUPERSEDED / PENDING
REDESIGN**. Next logical operation: PR6-NUTRIENT-VECTOR — NOT STARTED / requires
separate authorization after merge; PR7+ — UNAUTHORIZED.

Verification executed on 2026-09-10, docs-only tier:

- `git diff --check`: PASS after fixing newly added Markdown hard-break trailing
  spaces. No whitespace defect remains.
- `git diff --cached --check`: PASS; staged scope is exactly the 13 authorized
  files. Runtime/data/schema/CI/dependency paths are absent from the staged diff.
- Read-only Git-blob audit against exact base: all **957** baseline tracked files
  outside the allowed documents are byte-identical. The audit uses `git ls-tree -r`
  and hashes each worktree file as a Git blob; it covers runtime, schema,
  migrations, seeds, all curation (including B2-B1), scripts, dependencies and CI.
  Exact changed-file allowlist is the 13 files above, including the two additions.
- Migration inventory: latest module is `0027_recipe_same_source_revisions`;
  no 0028 exists. No production database is opened or modified.
- Nutrition Core's entire prior document is preserved as an exact prefix before
  the later target section; current config IDs and PR #18 history are unchanged.
- Retained audit v3 SHA-256:
  `baac9e19b0b6cd3f6990a059a098ab5d69162b9c5459db0e61d9e59e4b547100`.
  Read-only JSON assertions confirm 30 records / 189 rows / 30 INCOMPLETE and
  exactly 43 CONVERSION_ESTIMATE_NOT_ACCEPTED rows, each with mass_g=null.
  These are checks of accepted evidence, not a fresh runtime audit execution.
- Relative Markdown link and GitHub-style heading/explicit-anchor validation:
  **109 links / 42 fragments PASS** across the exact changed-file scope.
  Repository search found no inbound links using the renamed historical headings.
- Static conflict audit with `rg` over root AGENTS, active `docs/family-food/*.md`
  and state: no active unapproved Option A, old B2-B2-next instruction, mandatory
  FoodProductType Nutrition layer, fixed-five-field final target or permitted
  English fallback remains. Hits were inspected in context: historical B2-B1
  recommendations are labelled and superseded; persistence Option A is unrelated;
  migration-plan allows only later classification metadata; source TЗ diagrams
  have explicit supersession notes. Unchanged curation report remains historical
  research evidence, not an active implementation/architecture authority.
- Roadmap regression audit: sequence from Gate 1 onward, PR9–PR15/Gates 2–3,
  shared-deployment/PostgreSQL/Auth/Retail/AI/Billing sections and the acceptance
  fixture section are byte-identical to base. Added qualitative gates and
  pre-PR7 supporting operations are the explicit approved differences in §6.5.
- No backend/frontend/launcher tests, builds, nutrition replay, dataset re-research
  or localization runtime tests were run: no such behavior changed. This follows
  the docs-only verification tier; later implementation must add its own gates.

## PR6-INFRA verification

Exact base: `2ce9917f51ac3161d4cb2839f6003e7a24bc96bd` (PR #20 merged).
Branch: `infra/sqlite-rebuild-migration-runner`. This changeset establishes the
explicit SQLite rebuild capability documented in
[architecture §13.1](../docs/family-food/architecture.md#131-sqlite-foreign-key-table-rebuild-capability-pr6-infra).
PR6 remains NOT COMPLETE. B2-A is the next separately authorized product/data
operation, starting from accepted main containing this capability. B2-B remains
NOT AUTHORIZED; PR7+ remain UNAUTHORIZED. No INFRA-CLOSE is required.

Executed with `PYTHONPATH=backend AI_ENABLED=false` using
`backend/.venv/bin/python -m pytest`:

- New runner contract tests: **22 passed in 1.00s**. Real SQLite standard →
  rebuild → standard behavior, FK OFF outside a transaction, explicit BEGIN,
  schema + marker commit, pre-commit whole-database FK check, rollback on upgrade,
  marker, check-query and FK-violation failures, restoration on all those paths,
  initial/disable/restore setting failures, connection disposal, fresh failure /
  resume, unknown modes, and prohibited module transaction/marker ownership.
- Focused migration/startup/backup/restore selection: **261 passed in 52.25s**
  with authorized local-loopback access. Selection: `test_migration_runner_rebuild`,
  `test_database_foundation`, `test_migration_lineage`, persistence
  `test_migration_coexistence` / `test_nutrition_evidence`,
  `test_d4_a_startup_compatibility`, `test_backup_consistency`, and launcher
  `test_restore_validation`, `test_restore_execution_coordinator_c4i`,
  `test_restore_startup_recovery`.
- The same focused sandbox attempt had **235 passed, 5 failed, 21 errors in
  41.20s**; all failures/errors were launcher loopback socket permission denials.
  No tests were weakened or skipped to resolve this environment restriction.
- Full backend + launcher sandbox attempt (`--maxfail=1 --tb=short`):
  **2862 passed, 1 failed in 197.22s**. The first failure was the launcher
  backend-handshake test attempting a denied `127.0.0.1` bind.
- Full backend + launcher with authorized local-loopback access:
  **3498 passed in 496.89s (0:08:16)**, zero failures/errors/skips. Command:
  `PYTHONPATH=backend AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests launcher/tests --tb=short`.
- Static/scope checks: Ruff check and format check pass for the two changed
  Python files; `git diff --check` and `git diff --cached --check` pass. Seven
  intended files staged; unrelated `.DS_Store` excluded. Local documentation
  links resolve; protected production paths are byte-identical to accepted base.
- Populated prerequisite fixture: 30 v1 RecipeVersions / 189 RecipeIngredients /
  B1 57 evidence / 189 assessments / 123 issues. Full SQL dump before/after an
  opt-in no-op migration is identical after excluding only its synthetic marker;
  this includes all existing IDs, values, indexes, triggers and FK relationships.
- Accepted-runner comparison: loaded the original runner from exact base using
  `git show`, migrated separate empty temporary databases with accepted and new
  runners, and compared every `(type, name, tbl_name, sql)` schema object. All
  **172 schema objects are identical**. Both chains have exactly 26 migrations,
  head `0026_nutrition_measure_evidence`, empty FK checks and `[]` on second apply.
  SHA-256 of the ordered schema JSON:
  `9ec78400ce9efd57e2fa92c8fb6e6884cb105946e4a11491515557258255a727`.

Production migrations 0001–0026 and all `data/` bytes are unchanged. No production
migration ID, table, RecipeVersion, RecipeIngredient, FoodNutritionProfile or
B1 payload changes. Synthetic migration modules exist only in tests.

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

Initial B1 verification at `8aae50a` (`AI_ENABLED=false`): focused Nutrition/targets/DATA-A
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

Review correction seals issue sets at assessment INSERT using a deferred child
FK and a late-insert rejection trigger. Regression first reproduced the old
loophole, then focused persistence/migration/reassessment/UoW and affected
Nutrition tests passed: **102 passed in 23.31s**; the additional pre-commit sealing
assertion passed in its targeted rerun (**1 passed in 0.67s**). Ruff/format and
diff/staged scope checks PASS. Calculation policy, DATA-A classifications and
57/189/123 payloads remain byte-identical to `8aae50a`. Per user instruction,
full regression was not repeated; its result above remains historical evidence.
Current focus and handoff retain durable B1 outcomes and authorization boundaries.

PR6 engine and DATA-A are ACCEPTED / MERGED. B1 is established by this changeset.
PR6 remains NOT COMPLETE; DATA-B2 is
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

## PR6-DATA-B2-A verification

Updated: `2026-09-08`. Persistence/migration + production curation verification
under the explicit B2-A task. Exact starting branch HEAD and merge base:
`74bc80eb3ef0e34e17751856638ac58bbccb840e`. Continued
`data/pr6-b2a-source-quantity-corrections` by fast-forward from its previous
pre-implementation base; unrelated `.DS_Store` remained modified and excluded.

This changeset establishes the bounded result described in the
[B2-A decision](../docs/family-food/nutrition-data-readiness.md#decision--pr6-data-b2-a-same-source-quantity-corrections):
five immutable v1→v2 chains, all six source-quantity outcomes resolved,
32 new ingredient rows with 32 explicit assessments, and audit v3. All original
external provenance remains identical. PR4 v1 and B1 57/189/123 payloads remain
byte-identical to the starting main; SHA-256 values are pinned in the
[correction manifest](../data/seed/recipe_corrections/pr6-data-b2a/manifest.json).

Executed evidence:

- Initial Recipe seed/migration/repository suite: **30 passed**.
- B2-A + B1 persistence + Nutrition architecture + runner focused suite:
  **87 passed** (`AI_ENABLED=false python3 -m pytest
  backend/app/tests/test_recipe_same_source_revisions.py
  backend/app/tests/persistence/test_nutrition_evidence.py
  backend/app/tests/test_nutrition_architecture.py
  backend/app/tests/test_migration_runner_rebuild.py -q`).
- Final lineage/startup/backup, read-scope, migration, architecture and B2-A
  suite: **143 passed**. After aligning the existing current-verified index's
  descending order in Core metadata, the affected B2-A + Nutrition read-scope
  suite passed **23 tests**.
- Actual 0027 migration runs through the established runner on empty and
  populated 0026 databases. Before correction publication, every pre-existing
  table row/value/UUID/timestamp is identical and all unrelated sqlite_master
  definitions are unchanged. Both FK checks return `[]` with enforcement ON.
  Observed connection events prove FK OFF before the active rebuild transaction,
  then marker → whole-database FK check → commit → FK ON. Injecting failure
  after the real rebuild restores the exact old dump and schema without a 0027
  marker; resuming succeeds. Only RecipeVersion is rebuilt.
- Schema inspection proves external provenance uniqueness removed, internal
  `(recipe_id, version_number)` uniqueness retained, and matching non-unique
  metadata/index inventory. Backup tests prove pre-migration copies retain the
  old UNIQUE while the live database advances to 0027. Lineage explicitly maps
  0027 to no new persistent table.
- Exact PR4→B1→corrections→assessments double pass: second pass inserts zero
  versions, evidence or assessments; database dump remains identical and no v3
  exists. Historical v1 details and Nutrition outputs remain exactly equal.
  New v2 rows initially have no mass authority; all 32 receive explicit new
  assessments before current audit. The six changed rows use new review
  decisions; 26 unchanged rows carry explicit row/profile equality proofs.
  Parent corruption, conflicting v2/parent chain, conflicting review and partial
  insert failures are rejected transactionally. An unresolved finding suppresses
  its entire recipe's revision and assessment promotion in the publication-gate test.
- `python3 scripts/promote_pr6_data_b2a.py` and
  `AI_ENABLED=false python3 scripts/audit_pr6_data_b2a.py` reproduce committed
  payloads/report without differences. Audit: 30 current versions / 189 rows;
  30 INCOMPLETE, all other Nutrition statuses zero. Current assessments:
  21 direct, 66 exact, 37 estimate-review, 65 blocked; 118 current issues.
  All six matrix outcomes are RESOLVED on v2.
- `python3 scripts/validate_pr6_data_a.py --protected-revision
  60908eb8270ef356eff8552855b4cc5d2aa9ee44` passes and retains all 43 historical
  estimate candidates. Direct git byte comparison confirms protected PR4/B1
  inputs against the exact B2-A starting main.

The first full sandbox run reported **171 failed / 3224 passed / 121 errors**:
launcher localhost binds were denied (`PermissionError: [Errno 1]`); nine backend
failures exposed stale head/count expectations and the missing 0027 lineage map.
Those defects were corrected without weakening the checks. An initial loopback
run, started before those fixes, was interrupted after **9 failed / 3115 passed**;
it is not claimed as verification of the final files. Final full regression and
publication scope results are recorded below.

PR6 remains **NOT COMPLETE**. B2-B remains **NOT AUTHORIZED**; PR7+ remain
**UNAUTHORIZED**. Accepted estimated conversions: **0**. Form/profile corrections
started: **0**. No separate B2-A-CLOSE operation exists.

Final complete regression on the final runtime/tests:

```sh
AI_ENABLED=false python3 -m pytest backend/app/tests launcher/tests -q
```

**3516 passed in 517.91s (0:08:37)** with explicitly authorized local loopback
access. No test was weakened or skipped to bypass the sandbox failures.
Ruff check and Ruff format check pass for all **22 changed Python files**.
Relative documentation links and B2-A payload hashes validate; no database UUIDs
occur in the committed curation/production artifacts. The bounded inventory is
**34 intended files**, excluding `.DS_Store` and every protected PR4/B1/DATA-A
payload, all API/frontend and FoodIngredient/Profile data.

Final diff and staged-scope checks pass: `git diff --check` and
`git diff --cached --check`; staged inventory exactly matches the 34 intended
files. Only migration 0027 is added; protected source/seed files, local databases,
credentials and unrelated `.DS_Store` are absent from the changeset.

## PR6-DATA-B2-B1 verification

Historical PR #23 evidence below is preserved. Option A was then a recommendation;
[PR6-ARCH-COMPOSITION](#pr6-arch-composition-verification) now approves it and marks
the old B2-B2 plan SUPERSEDED / PENDING REDESIGN.

Updated: `2026-09-08`. Exact starting main:
`7f17b1372bbd2e9f97fc025ac26b3f04a15cf837`. Branch:
`data/pr6-b2b1-semantic-profile-audit`.

This changeset establishes the semantic/profile research audit: 37 target issue
occurrences on 37 distinct current rows in 23 recipes, affecting 19 foods.
All 46 current uses across 25 recipes are reviewed. Twenty-five original recipe
records were reopened against 21 accepted artifact hashes, matching PR4/DATA-A.
The [report](../data/curation/pr6-data-b2b1/README.md) owns the complete matrices,
12 exact profile candidates, seven proposed forms, source limitations and A/B/C
comparison. Option A is a RECOMMENDATION, not an architecture approval.

Executed verification:

- `python3 scripts/validate_pr6_data_b2b1.py`: PASS; exact B2-A v3 hash,
  coverage/provenance, controlled decisions, Decimal source facts, all-use
  compatibility proofs, deterministic summary, 683 protected baseline files,
  migration 0027 and 43 non-executable estimates.
- `AI_ENABLED=false python3 -m pytest -q
  backend/app/tests/test_pr6_data_b2b1_research.py`: **35 passed**. Tests include
  source/Decimal corruption, missing/historical/duplicate/non-target rows,
  incomplete all-use proofs, protected-file mutation/rebaselining, forbidden
  migration inventory and unauthorized production/estimate authority claims.
  An initial collection failure used an incorrect test root path; corrected
  before these successful runs. Existing pytest-asyncio configuration warning
  remains; no test was skipped or weakened.
- `python3 scripts/promote_pr6_data_b2a.py`: PASS, no-write deterministic payload
  validation; five revisions and 32 assessments reproduce unchanged.
- `AI_ENABLED=false python3 scripts/audit_pr6_data_b2a.py`: PASS, byte-identical
  production audit v3. 30 current versions / 189 rows / 30 INCOMPLETE; COMPLETE,
  COMPLETE_WITH_WARNINGS and CONDITIONAL are zero. Current assessments remain
  66 exact, 21 direct, 37 estimate-review and 65 blocked. All 43 estimate
  descendants retain null executable mass, including six with other blockers.
- Ruff check and Ruff format check pass for the two new Python files. The only
  initial lint issue was a local lambda assignment; corrected to a named helper.
  No full backend/launcher regression is required for this research-only scope.

PR6 engine and DATA-A remain ACCEPTED / MERGED. B1, PR6-INFRA and B2-A remain
established; production bytes and audit are unchanged. B2-B1 research is
established by this changeset. PR6 remains NOT COMPLETE. B2-B2 production
corrections and estimate-policy implementation remain NOT AUTHORIZED; PR7+
remain UNAUTHORIZED. No separate B2-B1-CLOSE operation is required.

Final delivery checks: `git diff --check` and `git diff --cached --check` pass.
The staged scope audit contains exactly the 11 allowed research/test/docs/state
files; staged bytes match reviewed working files. No production seed/runtime/
schema file, local database, credential, artifact cache or unrelated `.DS_Store`
is staged. All 46 relative documentation links and heading anchors validate.
The final focused run passes **35 tests**; Ruff check/format and the offline
validator pass. Production B2-A audit reproduction remains byte-identical.

## PR6-NUTRIENT-VECTOR-A verification

Date: `2026-09-10`. Exact starting main:
`307ba3475581087b079ebcf2fa643e19a00bf06d` (PR #24 merged).
Branch: `data/pr6-nutrient-vector-a-registry`. Scope: registry/provenance research,
offline validator/tests and active docs/state only. The [report](../data/curation/pr6-nutrient-vector-a/README.md)
owns the full canonical registry, mapping exceptions, source hashes and VECTOR-B
recommendations. Current FDC Foundation April 2026 and SR Legacy April 2018
were checked against official downloads; actual archive hashes match B2-B1.

Established artifacts: 51 definitions, all 51 APPROVED_FOR_VECTOR_B, no blocked
or deferred entries; 51 Russian names, no English fallback. 140 release-specific
FDC mappings: 76 exact, 24 method-specific, 24 distinct/rejected, 6 conversion,
10 unproven. INFOODS: 36 exact, 11 method-specific, 1 conversion, 3 unproven.
All 183 accepted profile identities across seed history / 915 fields audited:
870 source-confirmed, 45 absent fibres, no mismatches or ambiguous present values.
There are 64 known zeros; 138 profiles have five confirmed values and 45 have
four plus unknown fibre. No accepted historical-only profile was found; the
original 100 profiles remain unchanged after the 83-profile expansion.

Executed verification, data-curation tier:

- `backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py
  --write-summary`: PASS. Summary is derived from the validated artifacts.
  Exact base, selected source rows/hashes, Decimal comparison, registry/mapping
  integrity, all current/historical seed provenance and 961 protected files
  are checked. Migration remains `0027_recipe_same_source_revisions`; all 43
  estimated rows retain null executable mass.
- `AI_ENABLED=false backend/.venv/bin/python -m pytest -q
  backend/app/tests/test_pr6_nutrient_vector_a_registry.py`: **69 passed in 1.71s**.
  Includes scientific collisions, unproven mapping rejection, poisoned IDs/source
  amounts, Russian/code fallback, unit/Decimal boundaries, null vs zero, missing
  fields/profiles and additional historical profile coverage. A disposable SQLite
  database confirms the complete accepted inventory with no current-only filter;
  a separate test replacement retains its prior historical profile. Definition
  and conversion evidence references are required; USDA Handbook 74 preface
  p. iii independently confirms the 4.184 energy unit factor.
- The initial root `.venv` test invocation could not collect because SQLAlchemy
  is absent there. The existing `backend/.venv` contains the project dependencies;
  the successful run above uses it. No dependency or runtime files were changed.
- Ruff check and format checks cover the new validator and focused test only.
  Runtime, seeds, schema, B1/B2-A/B2-B1 bytes are unchanged; full backend/launcher
  regression is not required for this bounded research surface.
- `git diff --check` and `git diff --cached --check`: PASS. Staged scope is
  exactly the 15 authorized files; the pre-existing `.DS_Store` modification is
  excluded. `python3 scripts/validate_pr6_nutrient_vector_a.py --staged`: PASS,
  including staged-byte agreement. Local documentation validation: **89 relative
  links and heading anchors across 8 changed Markdown files**, all resolved.

PR6-ARCH-COMPOSITION is MERGED / established. This changeset establishes VECTOR-A
registry/provenance research for final review. PR6 / PR6-NUTRIENT-VECTOR remain
NOT COMPLETE; VECTOR-B NOT AUTHORIZED; COMPOSITION-CORE / PR7+ UNAUTHORIZED.
Nutrition v1 is current, migration head 0027, 43 estimates non-executable.
