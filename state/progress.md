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
PR4   Recipe Catalogue                     READY FOR REVIEW
PR5   Pantry                               UNAUTHORIZED
```

Canonical implementation order remains `docs/family-food/master-roadmap.md`.

## PR4-DATA2 closure

Supporting PR #13 merged after `PR4-DATA2 FINAL REVIEW: ACCEPT`.

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

The user approved retaining PR #10's useful Recipe Catalogue runtime while
removing obsolete seed/provenance-acquisition assumptions.

Superseded as PR4 hard gates:

- old 119-FI historical seed;
- all-servings-6 assumption;
- old 365 ingredient / 315 step / zero-equipment production counts;
- blanket rights inference;
- exact historical retrieval instant requirement;
- fresh-source acquisition as a prerequisite for publishing the accepted DATA2
  technical corpus.

`source_retrieved_at` is now nullable. Known true instants may be stored;
unknown values stay `NULL`.

## PR4 delivered candidate

PR #10 now contains the required platform Recipe Catalogue runtime:

- `Recipe` and immutable/versioned `RecipeVersion`;
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
- idempotent seed reconciliation.

Production seed counts:

```text
30 Recipe
30 RecipeVersion v1
189 RecipeIngredient
169 RecipeStep
86 RecipeEquipment
34 equipment codes
81 FoodIngredient codes
```

Ordered steps are durably reviewed in
`data/curation/pr4-runtime/recipe-steps.json`. The selected Grilled Fruit variant
has three steps; conditional wooden-skewer soak guidance is not active because
DATA2 selected a non-wood skewer.

## Latest verification

GitHub Actions run `34001179713`: SUCCESS.

- DATA2 validator: PASS;
- DATA2 focused tests: `164 passed`;
- PR4 focused tests: `55 passed`;
- fresh first seed: 30/30/189/169/86 inserts, 0 conflicts;
- second identical seed: 0 inserts; exact existing counts 30/30/189/169/86;
- full backend + launcher: `2983 passed, 2 skipped`;
- Ruff: PASS;
- deterministic seed generation: PASS;
- exact count gate `30 189 169 86 81`: PASS;
- `git diff --check`: PASS;
- temporary workflow/payload/reset/acquisition files removed;
- final `.github/workflows` diff against main: empty.

## Next gate

Perform `PR4 FINAL REVIEW` on the current PR #10 head.

PR4 remains READY FOR REVIEW, not COMPLETE. Do not merge without explicit user
authorization. PR5 remains unauthorized until PR4 is accepted and merged.
