# Progress

Updated: `2026-09-06`

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
PR5   Pantry                               READY FOR REVIEW
```

Canonical implementation order remains `docs/family-food/master-roadmap.md`.

## PR5 implementation evidence

- Base: `main` / `b7fb609fc28dc46fa5891fc677272b6d21b58b58`.
- Branch: `migration/pr5-pantry`; PR creation follows final regression.
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

### PR5 checks

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

Final project review and explicit merge permission are required; PR5 is not
COMPLETE, and PR6 remains unauthorized.

## PR4-DATA2 closure

PR #13 merged after `PR4-DATA2 FINAL REVIEW: ACCEPT`.

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

PR4 is COMPLETE and merged. PR5 is READY FOR REVIEW on
`migration/pr5-pantry` from `b7fb609fc28dc46fa5891fc677272b6d21b58b58`.
Final Pantry review/acceptance is the next gate. PR6 and every later milestone
remain unauthorized.
