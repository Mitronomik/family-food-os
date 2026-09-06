# Current focus

Updated: `2026-09-06`

## Active milestone

`PR4 — Recipe Catalogue — READY FOR REVIEW`

GitHub PR: `#10` — OPEN, not merged.  
Branch: `migration/pr4-recipe-catalogue`.  
Base/main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.  
Latest fully tested implementation commit: `173b0f5479c7af2dd7095bf54f9393b2ff68ba55`.

`PR4-DATA2` is COMPLETE: PR `#13` merged accepted head
`918bf81b5da306fc65a57643de515ca1b3fbd1e4` into main as
`2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.

PR5 remains UNAUTHORIZED until PR4 final review ACCEPT + explicit merge authorization + merge.

## Authoritative PR4 decisions

The user approved a PR10 scope reset:

- keep PR #10's useful Recipe Catalogue domain/application/persistence runtime;
- use accepted PR4-DATA2 as production recipe truth;
- historical `data/curation/pr4` and old 119-FI/all-servings-6 seed are not production truth;
- exact historical retrieval instant is not a PR4 publication hard gate;
- `source_retrieved_at` is nullable: persist a real aware UTC instant when known, otherwise `NULL`;
- never fabricate retrieval time from review/commit/mtime or an assumed midnight;
- fresh source acquisition is not a PR4 runtime/publication prerequisite;
- deterministic core remains offline and works with `AI_ENABLED=false`.

## Final PR4 candidate

Runtime path:

`Recipe → immutable RecipeVersion → RecipeIngredient → FoodIngredient → ordered RecipeStep / RecipeEquipment`

Delivered:

- platform Recipe identity plus activate/deactivate state;
- immutable/versioned RecipeVersion and immutable ordered children;
- reviewed source/rights/verification metadata;
- exact Decimal serving scaling;
- version history/current verified semantics;
- driver-independent repository contracts;
- synchronous SQLAlchemy Core repositories and Recipe Catalogue UoW/read scope;
- migration `0024_food_recipe_catalogue` after `0023`;
- SQLite UPDATE/DELETE guards for immutable version-owned rows;
- deterministic offline DATA2 compiler and idempotent seed reconciliation.

Production seed:

- 30 Recipe;
- 30 initial SOURCE_VERIFIED RecipeVersion;
- 189 RecipeIngredient = 185 required + 3 optional + 1 conditional;
- 169 ordered source-derived RecipeStep;
- 86 ordered RecipeEquipment rows / 34 equipment codes;
- exact 81 existing FoodIngredient codes;
- 0 new FoodIngredient;
- 0 unresolved required ingredients;
- 0 unresolved required direction-consumables.

The 169-step count is intentional. `SNAP3-GRILLED-FRUIT` uses the accepted non-wood skewer variant; the wooden-skewer soak note is conditional source guidance and is not an active production step.

`data/curation/pr4-runtime/recipe-steps.json` stores reviewed ordered step transcription. `source-manifest.json` preserves accepted DATA2 hash lineage plus step-extraction hash/comparison lineage. Source binaries and temporary acquisition workflows are not production/runtime dependencies.

## Verification

Seed/reset verification run `34001179713`:

- DATA2 validator: PASS;
- DATA2 focused: `164 passed`;
- PR4 focused: `55 passed`;
- fresh SQLite first seed: 30/30/189/169/86 inserts, 0 conflicts;
- identical second seed: 0 inserts; exact existing counts 30/30/189/169/86;
- compiler output reproduced byte-for-byte;
- full backend + launcher: `2983 passed, 2 skipped`;
- Ruff and `git diff --check`: PASS;
- final `.github/workflows` diff versus main: empty.

Adversarial fail-closed hardening run `34002182325`:

- DATA2 validator: PASS;
- DATA2 focused: `164 passed in 3.56s`;
- PR4 focused including new curation-drift negative regressions: `58 passed in 15.56s`;
- full backend + launcher: `2986 passed, 2 skipped, 1 warning in 626.61s`;
- Ruff: PASS;
- `git diff --check` / staged diff: PASS;
- temporary hardening workflow removed before push;
- loader now rejects same-count ingredient mapping drift, equipment-order drift, step-text drift and step-lineage drift.

## Next action

Perform PR4 project final review on the current PR #10 head. If ACCEPT, wait for explicit user merge authorization before merging. Do not start PR5 automatically.
