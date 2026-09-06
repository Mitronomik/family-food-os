# Current focus

Updated: `2026-09-06`

## Active milestone

`PR4 — Recipe Catalogue — READY FOR REVIEW`

GitHub PR: `#10` — OPEN, not merged.  
Branch: `migration/pr4-recipe-catalogue`.  
Base/main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.

`PR4-DATA2` is COMPLETE: PR `#13` merged accepted head
`918bf81b5da306fc65a57643de515ca1b3fbd1e4` into main as
`2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.

## Latest approved decision

The user explicitly approved a PR10 scope reset and removed exact historical
retrieval instant as a PR4 hard gate. `source_retrieved_at` is optional: use a
real aware instant when it is known, otherwise persist `NULL`. Never fabricate a
midnight/review/commit/mtime instant.

Accepted DATA2 remains the production recipe-truth handoff for source identity,
URL, accepted source hash, servings, selected ingredient rows, equipment,
rights review and source limitations. Fresh acquisition is not a prerequisite
for PR4 publication after this scope reset.

## PR4 implementation result

PR #10 now implements the platform Recipe Catalogue through:

`Recipe → immutable RecipeVersion → RecipeIngredient → FoodIngredient → ordered RecipeStep / RecipeEquipment`

The retained runtime includes driver-independent domain/application contracts,
synchronous SQLAlchemy Core repositories, Recipe Catalogue Unit of Work,
migration `0024_food_recipe_catalogue`, database immutability guards, exact
Decimal scaling, deactivation/version history and deterministic offline seed
reconciliation.

The production seed is rebuilt from accepted PR4-DATA2, not historical
`data/curation/pr4` assumptions:

- 30 Recipe;
- 30 initial SOURCE_VERIFIED RecipeVersion;
- 189 RecipeIngredient;
- 169 ordered source-derived RecipeStep;
- 86 ordered RecipeEquipment rows / 34 equipment codes;
- exact 81 existing FoodIngredient codes;
- 0 new FoodIngredient;
- 0 unresolved required ingredient rows;
- 0 unresolved required direction-consumables.

The 169-step count is intentional. For `SNAP3-GRILLED-FRUIT`, the wooden-skewer
soak note is excluded from the selected production variant because accepted
DATA2 explicitly selected a non-wood skewer; it is conditional source guidance,
not an active recipe step.

`data/curation/pr4-runtime/recipe-steps.json` is the durable reviewed step
transcription used by the offline compiler. Source binaries and temporary
acquisition workflows are not production/runtime dependencies.

## Verification

Authoritative verification run: GitHub Actions `34001179713`.

- DATA2 validator: PASS;
- DATA2 focused: `164 passed`;
- PR4 focused domain/application/architecture/migration/seed/persistence:
  `55 passed`;
- fresh SQLite first seed: 30 recipes, 30 versions, 189 ingredients, 169 steps,
  86 equipment, 0 conflicts;
- identical second seed: 0 inserts; 30/30/189/169/86 existing; 0 conflicts;
- full backend + launcher: `2983 passed, 2 skipped`;
- Ruff final changed-Python checks: PASS;
- deterministic compiler: two consecutive generations byte-identical;
- `git diff --check`: PASS;
- final `.github/workflows` diff versus main: empty;
- temporary payloads, acquisition evidence files and reset artifacts removed.

## Next action

Perform adversarial `PR4 FINAL REVIEW` on the current PR #10 head. Do not merge
without explicit post-review user authorization. Do not start PR5 before PR4 is
accepted and merged.

`PR5 — UNAUTHORIZED`.
