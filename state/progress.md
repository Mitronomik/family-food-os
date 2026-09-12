# Progress

Updated: `2026-09-12`

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
PR6   Nutrition Core                       COMPLETE (PR6-CLOSE accepted)
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
There are 64 source-reported numeric zeros (the original "known zeros" wording
is superseded by the zero-provenance correction below); 138 profiles have five confirmed values and 45 have
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

## PR6-NUTRIENT-VECTOR-A zero-provenance correction

Correction of the final-review blocker in existing PR #25, branch
`data/pr6-nutrient-vector-a-registry`. Before edits GitHub showed OPEN,
mergedAt=null, base `main` at `307ba3475581087b079ebcf2fa643e19a00bf06d`, and
reviewed head `f8adf97382e737d71ee36813af21b22395f68413`; no intervening commits.
The exact baseline replay passed: 183 profiles (102 Foundation / 81 SR),
915 fields, 870 SOURCE_COMPONENT_CONFIRMED, 45 VALUE_ABSENT, zero numeric
mismatches / ambiguous component mappings, 64 numeric source zeros, 961 protected
files, migration 0027 and 43 non-executable estimates. Baseline focused tests:
**69 passed in 1.68s** before edits.

The [zero audit](../data/curation/pr6-nutrient-vector-a/README.md#zero-provenance-correction--fact-open-question-and-decision)
records FACT / OPEN QUESTION / DECISION, all 64 exact source rows, orthogonal
states, supplemental same-release metadata and complete reconciliation.
`known_zero_observations` is removed: 64 SOURCE_REPORTED_ZERO = 14 Foundation +
50 SR. Censoring partition: 0 explicitly non-censored, 0 explicitly censored,
0 LOQ-present/status-unspecified, 64 without available censoring metadata.
Resolution partition: 0 exact confirmed, 0 proven-censored blocked, 64 unresolved.
None of these zeros is approved for authoritative exact normalized backfill.
Absence of metadata is not evidence of exactness. Current v1 values are preserved.

All five required original source hashes matched before analysis. Complementary
JSON exports are from the same releases and have separate pinned hashes; they
do not replace CSV truth. Thirteen Foundation and 50 SR zero records match JSON;
pollock is absent from Foundation JSON. All 35 available same-component Foundation
child measurements and their links/methods are retained. Child adjusted amounts
are not reinterpreted as LOQ. Original FDC selected extracts/hashes are unchanged.

Executed verification for the research/data/docs/tests/validator-only correction:

- `python3 scripts/validate_pr6_nutrient_vector_a.py --source-directory
  /tmp/pr6-vector-a --write-summary`: PASS; all seven pinned raw files verified
  before parsing; all 64 observations and supplemental evidence replay exactly.
- Offline VECTOR-A validator: PASS, including 961 protected files, migration
  `0027_recipe_same_source_revisions` and all 43 null executable masses.
- `AI_ENABLED=false backend/.venv/bin/python -m pytest -q
  backend/app/tests/test_pr6_nutrient_vector_a_registry.py`: **104 passed in 4.66s**.
  Includes unproven/censored zero promotion, raw LOQ loss in a synthetic trusted
  snapshot, forged row hashes, invalid states, absent/missing/failed/filtered
  states, aggregate partition mismatch, protected files, 0028 and estimate changes.
- Ruff check and format/check: PASS for the validator and focused tests.
- Comparison with reviewed HEAD: all 915 original source/profile fields and
  numeric comparisons unchanged; original selected FDC extracts unchanged.
- Local links/anchors: **91 resolved across 8 PR Markdown files**.
- `git diff --check`: PASS. Correction touches 12 of the original 15 allowed
  files; unrelated `.DS_Store` remains excluded. Full backend/launcher regression
  is not required for this unchanged production surface.
- `python3 scripts/validate_pr6_nutrient_vector_a.py --staged` and
  `git diff --cached --check`: PASS; staged bytes match the validated artifacts.

Production seed/schema/runtime, B1/B2 evidence, assessment/profile history and
Nutrition v1 behavior remain unchanged. FAMILY_FOOD_NUTRITION_V1 is current.
PR6 NOT COMPLETE; VECTOR-B NOT AUTHORIZED; COMPOSITION-CORE UNAUTHORIZED;
PR7+ UNAUTHORIZED. Next action is final re-review of PR #25; no automatic merge.

## PR6-NUTRIENT-VECTOR-B verification

Authorized implementation from fetched main
`e35d87a24d5d8afb59509e566aa1ff4b7a58a11a` (PR #25 merged),
branch `codex/pr6-nutrient-vector-b`. Migration head 0027 → 0028.

Measured [evidence](../data/curation/pr6-nutrient-vector-b/implementation-evidence.json):
51 approved definitions, 183 existing profiles examined/backfilled, 806 normalized
values; 64 unresolved zeros retained and zero promoted; 45 absent fields.
All pre-existing table rows and full runtime readiness report compare equal.
Current B2-A classifications are 66 exact / 21 no-conversion / 37 review-required /
65 blocked; 30 current versions / 189 rows / 30 INCOMPLETE and 43 non-executable
estimates. The supplied older 20/66 regression context predates B2-A.

Executed on 2026-09-12 (test runs use `AI_ENABLED=false`):

- Initial targeted implementation/research/architecture/B2-A tests: 187 passed.
- Expanded vector + nutrition architecture/read-scope + VECTOR-A tests: 155 passed.
- `scripts/audit_pr6_nutrient_vector_b.py`: before/after equality and complete audit PASS.
- `scripts/validate_pr6_nutrient_vector_a.py --content-only`: PASS.
- Mypy for all ten new/affected runtime files, using the project interpreter,
  `--follow-imports=silent --ignore-missing-imports --check-untyped-defs`: PASS.
  Existing adapter annotations now explicitly accept SQLAlchemy RowMapping;
  no conversion/behavior change was needed.
- Full backend/launcher command: `AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests launcher/tests`:
  **3699 passed in 593.83s (9:53), zero skips**. Final code verified.
- The first full run found 23 schema-inventory/lineage/startup expectation failures
  (3669 passed). Registered all four 0028 tables in restore lineage and the shared
  table guard, and updated the exact prior/head backup expectations. All 23 passed
  on immediate rerun; the full final run above then passed.
- Startup/backup/migration-lineage focused run: **107 passed in 6.72s**.
- `ruff check` and `ruff format --check` for all **25** changed Python files: PASS.
- Accepted VECTOR-A JSON and production seeds are byte-identical to base main.
- Updated documentation file links, `git diff --check`, staged scope and
  `git diff --cached --check`: PASS. Unrelated `.DS_Store` excluded.
- `origin/main` rechecked before delivery: still the exact base SHA above.

Mypy command: `mypy --follow-imports=silent --ignore-missing-imports --check-untyped-defs --python-executable backend/.venv/bin/python`,
covering migrations/lineage, vector domain/backfill, migration 0028, Core
metadata/repository/read scope, existing profile repository and vector contracts.
No type-check errors are suppressed in changed source files.

Implementation is ready for review; PR6 is not complete and merge is not authorized.

Full current content checks are retained. Old research-only scope guards are
exercised unchanged on their exact accepted Git trees; future authorized runtime
changes are not recast as changes inside those earlier research PRs.

Delivery: [PR #26](https://github.com/Mitronomik/family-food-os/pull/26) opened into `main`;
implementation commit `265aa247726d7520a7914d16ecabe6c607419f34` pushed on
`codex/pr6-nutrient-vector-b`. This delivery receipt changes state documents only;
verified runtime/test bytes are unchanged. Local `gh` returned HTTP 401; Git push
and the connected GitHub API succeeded. No publication blocker remains.

## PR6-COMPOSITION-CORE preflight

Executed 2026-09-12 on fetched `origin/main`
`b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe` (PR #26 merge).
`git fetch origin main` succeeded. Local `main` was stale; created
`codex/pr6-composition-core` directly from the verified remote base, preserving
unrelated `.DS_Store`. Runner registration and the disposable-database audit
confirm head `0028_normalized_nutrient_vector`.

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_pr6_nutrient_vector_b.py
  > /private/tmp/pr6-composition-core-baseline.json`: PASS, exit 0.
  This reruns the existing 0027 → 0028 audit on temporary seeded databases;
  its embedded VECTOR-B base SHA describes that older migration, not this task.
- Re-measured baseline: 51 definitions / 183 profiles / 806 values;
  30 current recipes / 189 ingredient rows / 30 INCOMPLETE;
  66 APPROVED_EXACT / 21 APPROVED_NO_CONVERSION /
  37 REVIEW_REQUIRED_ESTIMATE / 65 BLOCKED. All 43 estimates remain
  non-executable. The audit verifies unchanged prior tables/readiness and clean
  foreign keys. No developer or real-user database is opened.
- Canonical composition/architecture and food domain/service inspection found
  no normalized coefficient invariant. Task section 5 explicitly requires a
  decision instead of inventing normalization. Proposal and consequences:
  [approved follow-up decision](../docs/family-food/food-composition-and-assembly.md#pr6-composition-core--concrete-runtime-contract).
- Changes so far are delivery-state synchronization only. Runtime/schema and
  production data are unchanged; Composition Core tests/full regression have
  not been run because Composition Core is not implemented.
- `git diff --check` and changed Markdown local file-link validation: PASS.

Implementation and PR delivery remain pending the normalization decision.
PR6 is NOT COMPLETE; no merge or later milestone is authorized.


## PR6-COMPOSITION-CORE verification

The user explicitly resolved the preflight normalization ambiguity: exact
component `input_mass_g` is authoritative; no normalized fractions are persisted.
Implementation uses verified base `b39d9f5786796dc689bdee8ae52a90cbcc4ebdfe`
(PR #26 merged), branch `codex/pr6-composition-core`, migration 0028 → 0029.

[Reproducible measured evidence](../data/curation/pr6-composition-core/README.md):
all seven new table counts are zero; all existing rows/readiness unchanged;
all 183 vector seals verified; 30 recipes / 189 rows / 30 INCOMPLETE;
66/21/37/65 classifications and 43 non-executable estimates. No production
composition data is invented, and no existing profile/vector/B1 binding changes.

Executed checks (2026-09-12, runtime tests with `AI_ENABLED=false`):

- `backend/.venv/bin/python scripts/audit_pr6_composition_core.py`: PASS.
  Real 0028 → 0029, all prior row values compared, full before/after readiness,
  every vector seal read, clean foreign keys, zero production composition rows.
- `backend/.venv/bin/python -m pytest -q backend/app/tests/test_food_composition.py
  backend/app/tests/test_food_composition_migration.py`: **59 passed in 7.56s**.
  Includes direct/two/multi-hop cycle rejection, shared DAG reuse, corrupted
  persisted cycles, snapshot digest corruption, sparse unknown/zero distinctions,
  independent yield/retention, explicit mass-state chains, profile/child/process
  historical replay, physical database insertion-order independence, caller
  Decimal context/traps, exact Decimal roundtrip, rollback and deferred-FK failure.
- Migration/backup/rebuild corrections: **64 passed in 7.58s**. Existing assertions
  retain their exact scope and now enumerate migration 0029 and its seven tables.
  Injected mid-migration failure restores schema, existing data and marker;
  deterministic resume and native backup schema preservation are tested.
- `backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py --content-only`:
  PASS, including registry, mappings, historical observations and zero evidence.
- `ruff check` and `ruff format --check` on all **21 changed Python files**: PASS.
- `mypy --follow-imports=silent --ignore-missing-imports --check-untyped-defs
  --python-executable backend/.venv/bin/python` on all **9 new/affected runtime
  files** (domain, services/contracts, Core adapters/scopes/metadata, 0029,
  migration runner and lineage): PASS.

The first full backend/launcher run finished with **3751 passed, 1 failed in
622.58s**. The remaining failure was
`test_user_mode_startup_creates_backup_before_migration_for_existing_database`:
its backup expectation still described 0027. Updated it to assert an intact 0028
backup (including VECTOR-B), with all seven composition tables only in the live
0029 database. Immediate targeted rerun: **1 passed in 0.65s**.

Final full-suite verification uses frozen runtime/migration/adapter/audit bytes.
During that run, only the focused caller-context fixture was strengthened with
an explicit recurring division (`12 / 1.3`), precision 2 and an Inexact trap.
The complete strengthened Composition Core suite passed separately (59 tests,
above); runtime bytes remained unchanged. No weaker assertion or skipped test
was introduced.

Final full command:
`AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests launcher/tests`
— **3758 passed in 606.21s (10:06), zero skips**. The strengthened focused
suite separately passed 59 tests against the same runtime. All 9 runtime files,
migrations, adapters and audit bytes were checked unchanged against hashes taken
at full-suite launch. All required checks are green.

`origin/main` fetched again before delivery: still the exact base SHA above.
Staged scope contains 29 task files, no `.DS_Store`, production seeds, secrets,
local databases or environment files. `git diff --check`, staged diff/check and
40 relevant local Markdown file links/new anchors PASS. Nutrition v1 runtime,
VECTOR-B runtime/registry and existing seed artifacts remain byte-identical to
base; no frontend/API files changed.
PR6 remains NOT COMPLETE. No autonomous merge or next-operation authorization.


Delivery: [PR #27](https://github.com/Mitronomik/family-food-os/pull/27) opened into `main`,
branch `codex/pr6-composition-core`, implementation commit
`657c692ce5ab8e49719ed9a164cda224cdfb296d`. Git push and the connected GitHub
create-PR API succeeded. PR is ready for review, not merged. The delivery-receipt
commit changes docs/state only; all verified runtime/test/audit bytes remain
unchanged. No further implementation scope is authorized.


## PR6-RU-FOOD-DATA verification

Exact fetched starting main: `d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc`.
PR #27 is MERGED at that SHA, independently checked through GitHub; the previous
COMPOSITION-CORE delivery receipt above is historical and superseded.
Branch: `codex/pr6-ru-food-data`. Migration head before/after:
`0029_food_composition_core`. PR6 remains NOT COMPLETE.

The [version 1 package](../data/curation/pr6-ru-food-data/README.md) audits 81
current food codes (185 required + 4 optional recipe rows) and seven candidates.
PROMOTE: CAULIFLOWER_FROZEN / SR 170398 and
STRAWBERRY_FROZEN_UNSWEETENED / SR 168173. DEFER: APPLE_PEELED,
LEMON_JUICE, ORANGE_JUICE, PASTA_COOKED, SPINACH_BABY. Exact reasons, primary
source extracts and market/form review are in the package; no rejection or
forced seven-food promotion. Both official USDA archive downloads matched their
pinned hashes; fresh official Lenta food and SPB/LO presence pages were inspected.

[Reproducible implementation evidence](../data/curation/pr6-ru-food-data/implementation-evidence.json):
183 existing foods/profiles/seals retained; 2 new foods/profiles/seals, 66 nutrient
values and 60 ATOMIC versions. 60 RU_READY / 28 NOT_READY; all 88 researched
records classify as 4 mass-market / 73 available / 11 specialty-or-unclear.
Only three pass the separate food/market default gate; unknown nutrients and later
recipe/preparation gates are not waived. Existing rows, registry, all 183 seals,
B1/B2-A bindings and all historical truth are unchanged. No composite,
transformation, yield or retention rows. The second complete RU seed inserts zero
and leaves all database contents identical. Tests use disposable databases;
synthetic adversarial profiles are excluded from production counts.

Complete before/after readiness reports compare equal, including every row and
source-quantity finding, and equal accepted B2-A production audit v3. Canonical JSON
SHA-256 for both: `d209a2598bf452952314f82569d841abf57910eae3a00afa679a71883cc92490`.
Baseline remains 30 recipes / 189 rows / 30 INCOMPLETE; 66 APPROVED_EXACT,
21 APPROVED_NO_CONVERSION, 37 REVIEW_REQUIRED_ESTIMATE, 65 BLOCKED.
All 43 estimate candidates remain non-executable. No existing profile replacement,
recipe remapping, new migration, API/UI, AI, Retail or Assembly runtime changes.

Executed on 2026-09-12, with `AI_ENABLED=false` for runtime checks:

- `backend/.venv/bin/python scripts/audit_pr6_ru_food_data.py`: PASS. Actual full
  baseline, all-row preservation, all 183 old seals read before/after, all 185
  final seals read, 60 exact ATOMIC owners/profile pins replayed, no-op second
  seed, clean foreign keys and scope audit. Retained JSON is the final execution.
- `backend/.venv/bin/python scripts/validate_pr6_ru_food_sources.py
  --source-directory /tmp/pr6-ru-research`: PASS, two primary archives and five
  complete retained profile/nutrient/vocabulary/available-derivation extracts.
- Focused `test_ru_food_data.py`: **41 passed in 4.67s**. Identity/name/alias,
  candidate exclusion, package tamper, market panel/form/region/date/status,
  Russian display, exact same-source sparse import/digest/zeros, transactional
  rollback, sealed immutability, current-profile replacement replay and scope.
  An earlier run had 40 passed / 1 failed because the static test used the wrong
  repository parent directory; corrected the test path and reran all 41.
- FoodIngredient domain/application/seed/repository, NutrientVector and registry,
  Composition Core/domain migration, Nutrition domain/application/catalogue:
  **311 passed in 20.45s**.
- Migration lineage/rebuild, backup consistency/audit, FoodIngredient migration
  and persistence migration coexistence: **154 passed in 21.60s**.
- `scripts/validate_pr6_nutrient_vector_a.py --content-only`: PASS.
- `scripts/promote_pr6_data_b2a.py` without write option and
  `scripts/audit_pr6_data_b2a.py`: PASS; accepted artifacts not modified.
- Ruff check and format check: PASS, all eight new Python files.
- Mypy with `--follow-imports=silent --ignore-missing-imports
  --check-untyped-defs --python-executable backend/.venv/bin/python`: PASS,
  all five new runtime files (two domain, service, Core adapter, seed).
  Initial constructor metadata, protocol typing and lint defects were corrected
  before final passing verification and full-suite launch.

Full backend + launcher command:
`AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests launcher/tests`
— **3799 passed in 632.45s (10:32), zero skips**.

Final `git diff --check` passes; 27 relevant local Markdown file links resolve.
A second `git fetch origin main` confirms the exact starting SHA is unchanged.
HTTPS push could not obtain local credentials; SSH returned publickey denial and
`gh` returned HTTP 401. Delivery uses the authenticated GitHub connector instead;
remote blobs are compared to local Git blob hashes before publication.

No production runtime/data/test changes were made after full-suite launch;
remaining edits are documentation and the retained audit result. Delivery uses
only intended files; unrelated local `.DS_Store` is excluded. Stop for review;
no autonomous merge or B2-B2/Recipe Assembly/PR7 start.

Staged review: `git diff --cached --check` PASS; exactly 19 intended files.
No seed CSV/recipe data, old curation, migrations, dependencies, API/UI, private
records or `.DS_Store` are staged. All staged paths and content were reviewed.

Delivery: [PR #28](https://github.com/Mitronomik/family-food-os/pull/28) is OPEN,
not merged, targeting exact main above from `codex/pr6-ru-food-data`.
Implementation commit: `6da0d711d25a172c2b0e5ef308283dd0c698cee6`.
The GitHub API published all 19 reviewed blobs; its tree SHA matched the staged
local tree exactly: `8c519881f45229db6e5a657ed424b53c27e1d6e2`.
Fetched remote branch and advanced the local branch to that identical commit;
only the unrelated `.DS_Store` remained modified. GitHub confirms no merge conflict.
This later delivery receipt changes state documents only; verified runtime,
tests, source package and audit bytes remain unchanged. PR6 remains NOT COMPLETE.

READY FOR PR6-RU-FOOD-DATA FINAL REVIEW

## PR6-DATA-B2-B2-REDESIGNED — implementation and verification

Starting main fetched before editing: `4180297d47d68a0e0d9efbe7a7a27f3900c4f388`.
GitHub independently confirms PR #28 MERGED at that commit. Created requested
`codex/pr6-data-b2-b2-redesigned` from origin/main; unrelated `.DS_Store` preserved.
The complete accepted seed measured 185 foods and migration 0029; all 37 B2-B1
identities and 46 uses re-resolve against this actual database.

[The evidence package](../data/curation/pr6-data-b2-b2-redesigned/README.md)
records two source-backed frozen-form revisions, three SR profile promotions,
PEACH deferral, three exact mass records and complete all-use/assessment review.
There were no prior compositions for the three profile candidates (PR28
NOT_READY): first ATOMIC v1 is the applicable case, while synthetic old-v1 → v2
replay is separately tested. No new FoodIngredient, new policy or schema change.
The explicit populated-0029 data upgrade is atomic/idempotent and has tested
native backup/restore replay. All historical data is preserved except the
allowed 3 profile and 7 assessment current-marker retirements.

Executed with AI_ENABLED=false where applicable:

- `PYTHONPATH=backend:. backend/.venv/bin/python -m pytest -q
  backend/app/tests/test_pr6_data_b2b2.py`: **27 passed in 10.27s**.
  Covers complete production audit, 46-use guards, both immutable remaps,
  six real publication-stage failure injections and retry, sealed profiles,
  all-use reassessments/stale binding, conditional historical composition v2
  replay, deferred/yield/APPLE/estimate boundaries, hash tampering, missing
  frozen composition and changed exact evidence/carry-forward review on rerun.
- `backend/.venv/bin/python scripts/validate_pr6_data_b2b2_sources.py --archive
  /private/tmp/pr6-ru-research/SR-RELEASE.zip`: PASS; 5 complete source/portion
  extracts, 6 CSV member hashes, archive SHA matches accepted SR 2018-04.
- `backend/.venv/bin/python scripts/audit_pr6_data_b2b2.py`: PASS; populated
  0029 upgrade, all historical rows/seals/compositions, no-op second command,
  native backup/restore, integrity/FKs and full report reproducibility.
- `backend/.venv/bin/python scripts/audit_pr6_ru_food_data.py`: PASS; unchanged
  PR28 historical operation reproduces its accepted evidence.
- `backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py --content-only`:
  PASS for unchanged registry/mappings/legacy observations/zero evidence.
- `backend/.venv/bin/python scripts/promote_pr6_data_b2a.py` and
  `scripts/audit_pr6_data_b2a.py`: PASS; immutable correction chain and v3 audit.
- `backend/.venv/bin/python scripts/audit_pr6_nutrient_vector_b.py` and
  `scripts/audit_pr6_composition_core.py`: PASS; historical upgrades/readiness.
- `ruff check` and `ruff format --check`: PASS on all six new Python files.
- `mypy --follow-imports=silent --ignore-missing-imports --check-untyped-defs
  --python-executable backend/.venv/bin/python` on
  `backend/app/domain/b2b2_vector_import.py`, `backend/app/seed/b2b2.py`,
  `backend/app/persistence/sqlalchemy_core/b2b2.py`: PASS (3 source files).

Early task-local checks found wrong environment paths, a repository getter name,
formatting and test comparisons that included the explicitly mutable profile
current marker. These were corrected; actual seal/value/history byte comparisons
remain enforced. A partial full-regression run was interrupted to add the final
mass-evidence and frozen-composition prerequisite checks, and is not claimed as
passing. The final full backend + launcher run passed: **3826 passed in 649.81s (0:10:49)**,
zero skips. This includes FoodIngredient/profile, B1 evidence/assessment, B2-A
immutable revisions, Nutrition catalogue, NutrientVector, Composition Core,
all migration/rebuild/backup/restore/coexistence and PR28 RU regressions:
`AI_ENABLED=false PYTHONPATH=backend:. backend/.venv/bin/python -m pytest -q
backend/app/tests launcher/tests` (local loopback/process access enabled).

Measured readiness: 71 exact / 23 no-conversion / 35 review-required / 60 blocked;
29 INCOMPLETE + 1 CONDITIONAL, zero COMPLETE. Full before/after SHA-256 and all
ten row deltas are retained; only seven assessment statuses improve. Three old
estimate usages gain independent exact authority, while every original estimate
record and the remaining 40 current non-executable usages retain their boundary.
PR6 is NOT COMPLETE. All required checks pass; implementation is review-ready.
Final identity audit: 37 unique target dispositions / 46 complete uses / no UUID
curation keys. All 31 protected inputs and 56 checked local documentation links
pass. Working/staged whitespace and the 19-file scope audit pass; `.DS_Store` is
excluded. Origin/main was fetched again and remains the same verified SHA.
A non-mutating Git push dry-run confirms feature-branch publication access.
Delivery: feature branch pushed normally; [PR #29](https://github.com/Mitronomik/family-food-os/pull/29)
opened into main. Implementation commit `d0a238ce32193d5884d61ee384d5eb7f242bcaed`.
The delivery receipt updates state only; all tested runtime, data, scripts and
tests remain byte-identical. PR6-DATA-B2-B2-REDESIGNED is REVIEW-READY;
**READY FOR PR6-DATA-B2-B2-REDESIGNED FINAL REVIEW**. No merge or next operation.

## PR6-CLOSE — closure verification

Exact main fetched before editing and again before delivery:
`3caa95e636c02e8f34657b1b6c885f646451114c`. Authenticated GitHub metadata confirms
PR #29 MERGED at `2026-09-12T07:42:03Z`, head
`8a80ce26e7155ab17a5623d07294fbfd1124d9bf`. Merge and accepted head full tree:
`f953fb4d3693c4eead77fad301342359dc8bd206`. `git diff --name-only
 d0a238ce32193d5884d61ee384d5eb7f242bcaed 3caa95e636c02e8f34657b1b6c885f646451114c
 -- backend launcher frontend data scripts` is empty. The accepted **3826 passed
with AI_ENABLED=false** is reused historical PR29 evidence; no full rerun.

**PR6 COMPLETE; PR6-CLOSE COMPLETE** under the
[20-criterion closure decision](../docs/family-food/pr6-closure.md).
Measured 30 current recipes / 189 rows / 82 required foods in the inventory;
71 exact, 23 direct-g, 35 review-required, 60 blocked; 29 INCOMPLETE + 1 CONDITIONAL.
No current stale profile links. All 40 estimates, nine rows for five deferred
forms and three named yield cases remain non-executable. All 188 seals / 63
compositions read/replay; 185 old seals / 60 old compositions preserved. All 35
pre-upgrade and 37 final RecipeVersion input/config snapshots replay. Migration
remains `0029_food_composition_core`. No production behavior/schema/data changes.

Exact commands and retained outputs are in
[verification.json](../data/curation/pr6-close/verification.json):

- B2-B2 populated production audit, PR28 RU audit, VECTOR-A content audit,
  VECTOR-B upgrade, Composition Core upgrade and B2-A catalogue/readiness audit:
  **PASS**, each with `AI_ENABLED=false`, using the existing scripts without write flags.
- Nutrition domain/application/catalogue/evidence, target/config and B2-B2 focused
  tests: **178 passed in 11.72s**. Includes adult/child, sex/PAL, age/growth/fiber
  boundaries, missing/unsupported inputs, explicit reference-estimate warnings,
  deterministic precision/config and current/historical authority.
- Composition, NutrientVector and coherent Nutrition read-scope tests:
  **105 passed in 10.67s**. Missing yield/retention, sparse unknowns, corrupt seals,
  immutability, explicit profile pins, stale bindings and history/snapshot behavior.
- New read-only `scripts/audit_pr6_close.py`: **PASS**; independent regeneration
  and comparison of all three measured JSON files. No user database or network.
  Its first development run failed the deferred-form coverage assertion because
  the old artifact stores null new-food fields for deferrals; nine exact reviewed
  row identities replaced the heuristic. Production data/tests were unchanged.
- Ruff check and format check on the audit script: **PASS**.

Legacy zero differences are explicitly reviewed, not hidden: 185 nutrient
occurrences retain v1 uncertainty; normalized composition never substitutes them
for unknown. Distinct accepted result/config contracts provide the boundary;
no new unified API or exact-zero policy is imposed for closure. Sparse food vectors,
optional combinations, Russian consumer/kitchen readiness and Gate 1 remain limited
as documented. Empty milestone blocker register does not erase those limitations.

`gh` metadata access returned HTTP 401; authenticated GitHub connector provided
independent merge verification. Routine fetch succeeded through the required Git
metadata sandbox escalation. Unrelated `.DS_Store` remains excluded.

Final documentation/scope checks: `git diff --check` PASS; **128 local links and
anchors** checked, including every criterion's canonical reference. The check
found an older progress link to a removed handoff anchor; it now points to the
canonical Composition Core contract. Full changed-path allowlist excludes all
production runtime/schema/seed/test paths and unrelated `.DS_Store`. Exact
static results are retained in the closure package.

Staged verification: `git diff --cached --check` PASS; exactly **25 intended
files**, no backend/launcher/frontend/production seed/test changes and no
`.DS_Store`. All 16 package file hashes verified against checksums.json.
READY FOR PR6-CLOSE FINAL REVIEW. No merge or next operation.

Delivery: branch `codex/pr6-close` pushed normally; [PR #30](https://github.com/Mitronomik/family-food-os/pull/30)
opened into `main`, OPEN / not merged. Closure implementation/evidence commit:
`c3590e67bac9d4b884f2f22df6aed7986f988d10`. This delivery receipt changes state
only; measured evidence and verified runtime/data/test bytes remain unchanged.
Stop for final review. RECIPE-ASSEMBLY-A remains NOT STARTED and separately gated.


## RECIPE-ASSEMBLY-A — authorized preflight

2026-09-12: fetched `origin/main` and verified exact SHA
`e8a75e5b828ef935292da593f9f4d5edbd199474`. GitHub connector confirms PR30
MERGED at `2026-09-12T08:32:53Z` with the same merge commit. Created requested
branch `codex/recipe-assembly-a` from that base. PR6 / PR6-CLOSE COMPLETE;
Assembly A explicitly authorized, evidence preflight in progress. Assembly B and
PR7+ NOT STARTED. Ordered migration source head remains 0029.
Local `gh` returned HTTP 401; connected GitHub read succeeded. Git fetch/branch
creation succeeded through the sandbox escalation flow. Unrelated `.DS_Store`
remains excluded. No runtime or production data changes at this point.


### RECIPE-ASSEMBLY-A — blocked preflight result

**BLOCKED / not review-ready / not COMPLETE.** The user's explicit stop condition
was reached: three production families could not be established from the bounded
reviewed evidence. [Evidence package](../data/curation/recipe-assembly-a/README.md)
records all 30 current RecipeVersions screened and three shortlisted families
DEFERRED. Twenty-nine have unavailable required mass; the remaining oats v2
lacks MILK_1_PERCENT composition authority. Kitchen scope, substitution and RU
default eligibility are not inferred. Positive USDA collection testing evidence
and source-access limitations are retained without granting candidate approval.

No runtime/domain/persistence/API/frontend/seed or historical migration changes.
Migration remains 0029; no production templates. 0030 is still required upon
resuming catalogue implementation. Full implementation tests and full
backend/launcher regression NOT RUN because the explicit evidence stop preceded
implementation; those original acceptance gates remain unmet, not waived.

Verification with `AI_ENABLED=false`:

- Existing `audit_pr6_close.measure` on a disposable accepted database reproduces
  recipe-readiness.json and food-readiness.json byte-for-byte. Its old CLI main-head
  guard is unchanged; no actual user database is inspected. Preserved 188 seals,
  63 compositions, 35 old / 37 final captured recipe snapshots; 40 estimates remain
  non-executable and five deferred forms absent.
- `python3 scripts/audit_recipe_assembly_a_preflight.py`: evidence consistency PASS,
  production readiness false; 30 screened / zero carry-forward-ready / three deferred.
- Disposable-copy corruption checks: accepted-input drift and package drift both
  rejected, with no live evidence mutation.
- `ruff check scripts/audit_recipe_assembly_a_preflight.py`: PASS.
- `ruff format --check scripts/audit_recipe_assembly_a_preflight.py`: PASS after
  formatting the new script. Initial format check correctly requested formatting.
- Initial root `.venv` database invocation lacked SQLAlchemy; retry with
  `backend/.venv` passed. Ruff is installed on PATH, not in backend/.venv.
- Affected-runtime mypy is N/A: no runtime files changed.

Draft publication records the blocker; it must not be described as the requested
three-template implementation being ready for review. Assembly B and PR7+ remain
NOT STARTED. No autonomous merge.

Final pre-publication checks: `git diff --check` and staged whitespace PASS;
16-file staged scope excludes runtime, production seed and `.DS_Store`.
Local documentation verification: 71 links/anchors PASS.
The committed auditor also reproduces the temporary baseline with `--database`: PASS.

Draft delivery: [PR #31](https://github.com/Mitronomik/family-food-os/pull/31),
OPEN / DRAFT / not merged. Evidence commit:
`cbccc22ea87a326256891545c715259a0d67e8cf`. This publishes the blocker report,
not a review-ready RecipeTemplate implementation. Stop for evidence review.

## RECIPE-ASSEMBLY-A-R1 — bounded evidence recovery

2026-09-12. Accepted BLOCKED PR31 merged under explicit user authorization;
exact fetched merge/base `3c854f55323c895c1bdc5aabd5f1146fb6514935`.
Branch `codex/recipe-assembly-a-r1` created from that commit.
[Evidence package](../data/curation/recipe-assembly-a-r1/README.md) records 23
screened donors and nine detailed reviews. Thirteen names/cards overlap earlier
PR4 donor research and were re-inspected; ten expand it. The three PR31 deferred
candidates were not privileged. No final three established: **Assembly A BLOCKED;
R1 BLOCKED**, not milestone completion. PR6 COMPLETE; Assembly B / PR7+ NOT STARTED.

Positive evidence: exact source weights and existing compositions for AFRS plain
oatmeal inputs; explicit standardized-card relationships; published optional and
substitution leads. Remaining form/composition, exact mass, verified substitution
and default market gates are retained. No automatic food-data remediation.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r1.py --database`:
  PASS for evidence consistency, not publication readiness. 23 screened / nine deep /
  zero selected; 29 resolved and 24 unresolved mass rows (includes optional/process
  rows; unresolved values are not treated as zero).
- Disposable accepted DB reproduces PR6-CLOSE food/recipe reports byte-for-byte;
  185 foods, 63 compositions, 188 seals; exact natural identities checked.
  Migration head 0029; 40 estimates non-executable; five deferred forms absent;
  three yield blockers and historical replay preserved. Existing PR6-CLOSE CLI
  head guard unchanged; imported measurement function used under the R1 base guard.
- Package SHA-256 inventory, accepted-input hashes, source/provenance review
  completeness, no-float JSON audit, exact-weight/portion arithmetic, FoodIngredient
  resolution, Composition pins/unknowns, market policy and Russian display checks PASS.
- Five disposable-copy negative checks rejected package drift, incorrect source
  weight, JSON float, cross-food portion and missing required terminal input.
  Semantic cases recomputed package checksums before testing rejection.
- `ruff check scripts/audit_recipe_assembly_a_r1.py`: PASS.
- `ruff format --check scripts/audit_recipe_assembly_a_r1.py`: PASS after initial formatting.
- `git diff --check`: PASS. Scope audit allows only R1 evidence/auditor and owning
  docs/state; unrelated `.DS_Store` excluded from delivery.
- Source checks: 12 primary PDF downloads hashed; remaining readable primary/ICN
  sources reviewed through web text, with actual HTML fallback URLs retained.
  Local ICN/military TLS failures, oversized full AFRS PDF, screenshot cache misses
  and search-only third salt-chain evidence remain explicit limitations, not passes.
- Full backend regression NOT RUN, as authorized for research-only scope.

Research PR delivery follows; stop for review, no autonomous merge or implementation.

Delivery: [PR #32](https://github.com/Mitronomik/family-food-os/pull/32), OPEN,
not merged. Evidence commit `4c7f0712875bbb9ad86a1615d6ddb819178b026c`.
Research evidence is ready for review; R1 and Assembly A remain BLOCKED.
Stop for review. No next-phase or merge authorization.

## RECIPE-ASSEMBLY-A-R1-CORRECTION — canonical market semantics

2026-09-12. Continue existing `codex/recipe-assembly-a-r1` / PR32 from reviewed
head `4741e91710e17b86dbc25c5e69ca58ea36c5c635`. Fetched `origin/main` and PR32
base independently match `3c854f55323c895c1bdc5aabd5f1146fb6514935`.
The preceding R1 zero-ready and universal RU_AVAILABLE failure statements are
historical and superseded by this correction.

Corrected R1 to follow canonical localization policy §5 and the composition
contract's existing RU gate. Classification is unchanged and independent of
ordinary retail, exact form, commodity exception, product reason, dependency
risk and actual substitution requirement. Basic table salt remains RU_AVAILABLE
and passes default-use using retained category evidence; no third chain/SKU is
required. Sugar, specific basic oils and named single spices are reviewed
individually. Water's explicit exception remains. Generic oil, unresolved salt
choices and herb blends cannot inherit it. No donor/market search performed.

**R1 BLOCKED; individually ready 1 (R1-21), selected final three 0.** All 23 donor
dispositions recalculated; nine detailed gate records and eight near-misses.
R1-21 passes every individual gate only for the published 100-portion water/oats/
salt variant. No inferred household-scale, substitution or cooked-output authority.
Fourteen screen-only donors retain their non-market failure and explicit
NOT_REVIEWED terminal-level gates; they are not declared unavailable or ready.

Counted residuals among nine deep reviews (overlapping): food/form/composition 7,
exact mass 8, kitchen scope 2, rights 5, familiarity 1, actual form-specific market
evidence 2 (margarine 72% vs retained 80%; olive-oil content of reduced-fat mayo
unconfirmed). Unresolved identities are not counted twice as rare ingredients.
Verified substitution is still a separate final-three feature gap, with zero
providers; it is not an individual market obligation for every RU_AVAILABLE food.

Verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r1.py --database`:
  evidence consistency PASS, R1 BLOCKED / individually ready 1 / selected 0;
  29 exact and 24 unresolved mass rows unchanged. Disposable accepted DB reproduces
  PR6-CLOSE food/recipe reports byte-for-byte: 185 foods / 63 compositions / 188 seals.
  Migration 0029, 40 non-executable estimates, five deferred forms, three yield
  blockers and historical replay unchanged.
- Fourteen re-hashed temporary package mutations rejected: RU_AVAILABLE-only
  refusal; commodity without identity; blanket oils/spices; lost water exception;
  unreasoned substitution; specialty PASS; market repairs to mass/form/composition;
  wrong ready count; omitted terminal; float; cross-food portion.
- Package checksums and accepted-input hashes PASS; no-float audit PASS. Protected
  quantity/Composition/rights/kitchen/familiarity/substitution/baseline/inventory
  evidence equals the reviewed head. No production seed/schema/runtime change.
- Ruff check and format check PASS. Changed/new local file links and anchors: 15 PASS.
- Working and staged whitespace/scope checks performed before delivery. Unrelated
  `.DS_Store` remains excluded. Full backend regression unnecessary and not run.

Deliver correction to existing PR32 and update its body; stop for final re-review.
PR6 COMPLETE; Assembly A BLOCKED; Assembly B / PR7+ NOT STARTED. No merge or
next-phase authorization.


## RECIPE-ASSEMBLY-A-R2 — targeted recovery

2026-09-12. PR32 MERGED, exact fetched main/base
`8730b9fcfdb56cec2215f7e70319241c83431371`; R1 COMPLETE AS BLOCKED RESEARCH,
accepted 1/3. Branch `codex/recipe-assembly-a-r2`, only R1-23/R1-13 reopened.
[R2 evidence](../data/curation/recipe-assembly-a-r2/README.md) derives Outcome A:
2/3 individually ready (fixed R1-21 plus F00400 method 1 / 100 portions),
selected final three = []. Rice rights and garlic mass recovered; exact base
kitchen/process scope unresolved. Substitution and optional-role gates open.
All R1 files remain byte-identical. No production runtime/data/schema/seed
mutation; migration 0029; Assembly A BLOCKED; B/PR7 NOT STARTED.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r2.py --database --adversarial --source-dir <originals>` — PASS; Outcome A, 2/3, selected 0. The source directory held the three exact originals named in the manifest; no production DB path is accepted.
- Disposable accepted DB: PR6-CLOSE food/recipe reports match bytes; 185 foods / 63 compositions / 188 seals / 40 estimate usages; historical replay, five deferred forms and yield rows match the accepted baseline; migration 0029.
- Stable Composition references compare canonical identity/version, INPUT/kind and profile source/version/type/basis. Fresh loader UUIDs and UUID-bearing snapshot hashes differ between disposable DBs; internal snapshot/seal correctness is independently verified by accepted replay, not by equating unrelated DB UUIDs.
- All 19 adversarial cases rejected plus DEFER positive control passed: AP/EP, piece inference, revision mixing, wrong lb constant, garlic food/form/estimate/density, alternative/optional, OR kitchen assumption, incomplete substitution branches/Composition, household claims, unsupported rights and false final-three/count states.
- Full original SHA-256/size, exact AFRS original-to-excerpt pages, source rice/garlic observations, whole-package and frozen R1/accepted-input hashes, no-float, Russian ingredient display and Decimal/rational arithmetic — PASS. Relevant source PDF pages rendered and visually reviewed.
- Local links/anchors — 80 PASS. `ruff check` and `ruff format --check` for the new audit — PASS.
- `git diff --check`, `git diff --cached --check`, staged 25-file scope audit — PASS; `.DS_Store` excluded. Changed scope is R2 evidence, its read-only auditor and five state/canonical documents only.
- Full backend regression was not run: production code/data did not change. Direct local TLS downloads were unavailable; browser downloads supplied the exact source bytes. No original HTML or unavailable Army-PDF byte hashes are invented.

R2 evidence is ready for review. Assembly A remains BLOCKED, not COMPLETE.
Feature branch and PR published; stop for review, with no autonomous merge or follow-up research.


Delivery: [PR #33](https://github.com/Mitronomik/family-food-os/pull/33),
OPEN into main, not merged. Evidence commit:
`bb9254143f2449eeb0e7786ce1f06af91afbe517`.
R2 evidence READY FOR REVIEW; Assembly A BLOCKED. Stop for review.


## RECIPE-ASSEMBLY-A-R3 — Third-Family Closure

2026-09-12. PR33 MERGED at exact fetched main/base
`f2b6bc9015a1b892bb533b5d322d981d5a1782bd`; R1/R2 COMPLETE AS BLOCKED RESEARCH,
accepted ready count 2/3. This supersedes the historical OPEN PR33 delivery
record above. R3 is the current authorized evidence operation on
`codex/recipe-assembly-a-r3`.

[R3 evidence](../data/curation/recipe-assembly-a-r3/README.md): twelve serious
prefilter candidates, none passing, zero deep reviews. R3 BLOCKED; no third
candidate; individually ready 2/3; final three empty. Optional/substitution gates
remain OPEN. Exact published E00100 and F00400 method 1 batches remain frozen;
all bytes of both accepted packages are preserved. No production mutation;
migration 0029, Assembly A BLOCKED, B/PR7+ NOT STARTED.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r3.py --database --adversarial --source-dir <originals>` — PASS; R3 BLOCKED, 2/3, no selected third. After tightening source-weight binding, the affected local semantic/adversarial audit was rerun and passed; production replay inputs were unchanged.
- Disposable accepted DB replay matches PR6-CLOSE food/recipe reports byte-for-byte: 185 FoodIngredients, 63 exact Composition/profile pins, 188 seals, 40 non-executable estimate usages. Historical replay, five deferred forms and yield rows equal the accepted baseline; migration remains 0029.
- Complete R1/R2 package file inventories and SHA-256 match exact merged base. Accepted input hashes and production scope pass; no production truth is published. Stable profile pins compare canonical code, Composition version, INPUT/kind and source/version/type/basis; random disposable UUIDs are not equated.
- Full AFRS and SDSU original SHA-256/size pass. Five retained AFRS pages equal their original pages in the June 2003 system; extracted text equals the retained PDF. N50200 weight/issue alignment was rendered and visually inspected. Missing original hashes for indexed/text-only sources remain explicitly null.
- Package hashes, no-float/Decimal conversions, source weight bindings, optional/group semantics, whole substitution branch rejection, Russian display, corrected market/familiarity policy and local links/anchors (88) — PASS.
- Thirty adversarial cases rejected; complete synthetic positive control passed. Coverage includes missing Composition/mass, alternative-as-optional, processing medium, one-sided/inferred substitution, untested variant/unrelated family, estimates/density/piece/AP, specialty input, English display, household scaling, rights, incomplete branch, frozen bytes, runtime/schema/seed scope and false final-three states. The fixture is a validator test, not an additional donor.
- `ruff check` and `ruff format --check` for the new script — PASS.
- `git diff --check`, `git diff --cached --check` and exact staged 26-file scope audit — PASS; unrelated `.DS_Store` excluded. Scope is the R3 package, read-only auditor and five state/canonical documents only.
- Full backend regression was not run because production code/data did not change. Direct original retrieval was unavailable for several rejected candidates; those sources were never promoted to publication authority.

R3 research evidence READY FOR REVIEW; R3 result and Assembly A remain BLOCKED.
Stop after delivery for review. No merge, follow-up donor search, food-data repair
or migration 0030 is authorized.
