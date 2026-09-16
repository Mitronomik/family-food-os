# V22-13-MAP-A — identity mapping and recipe-candidate classification

**Status:** research/data curation; no production publication
**Reviewed:** 2026-09-16
**Accepted base:** `a852b169323cd4061c150107d7b75aebd67a9bc7` (PR #38 merged)
**Source checkpoint SHA-256:** `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`

## Goal

Map all 363 external v22.13 ingredient/reference identities against the current
FamilyFoodOS `FoodIngredient` catalogue and classify all 350 recipe candidates
without changing production identity, Nutrition, Composition, RecipeVersion,
RecipeTemplate or RecipeAssembly truth.

This operation consumes the accepted preflight in
`docs/research/russian-normative-recipes-v22-13-preflight-2026-09-16.md`.

## Scope and invariants

The operation is classification only.

- `FoodIngredient` remains the sole canonical food identity.
- External `ING-*` / `V21-*` IDs remain external evidence identifiers.
- A name match does not promote an external nutrient profile.
- Raw/input/cooked/process forms are not interchangeable.
- Composite/semi-finished/process outputs are not flattened into atomic foods.
- `READY_RAW` / scenario `READY` remain external checkpoint statuses only.
- Missing or ambiguous identity remains unresolved rather than guessed.
- No source-listed alternative is treated as verified substitution.
- No Recipe Assembly A gate is closed by mapping alone.

## Ingredient mapping states

| State | Meaning |
| --- | --- |
| `EXACT_EXISTING` | normalized source name matches an existing FamilyFoodOS identity |
| `ALIAS_EXISTING` | source wording is a reviewed alias of an existing identity |
| `NEW_FOOD_CANDIDATE` | a specific food identity appears absent and needs a separate Food Catalogue review |
| `FORM_SPLIT_CANDIDATE` | a related current food exists, but form/state/specification cannot safely share identity without review |
| `COMPOSITE_OR_PROCESS_OUTPUT` | recipe-derived, semi-finished or process-dependent identity; must use producer/composition/process truth |
| `UNRESOLVED` | grouped, alternative or under-specified source identity; fail closed |
| `REJECT_TECHNICAL` | bookkeeping/technical row that must not become a canonical food |

Every one of the **363 / 363** external ingredient/reference identities is
classified across `ingredient-mapping-part1.csv` … `ingredient-mapping-part4.csv`.

### Result

| Mapping state | Identities |
| --- | ---: |
| `EXACT_EXISTING` | 25 |
| `ALIAS_EXISTING` | 27 |
| `NEW_FOOD_CANDIDATE` | 103 |
| `FORM_SPLIT_CANDIDATE` | 68 |
| `COMPOSITE_OR_PROCESS_OUTPUT` | 114 |
| `UNRESOLVED` | 25 |
| `REJECT_TECHNICAL` | 1 |

The **52** `EXACT_EXISTING` + `ALIAS_EXISTING` identities are identity mappings
only. Their v22.13 nutrient rows do not replace the current FamilyFoodOS
Nutrition/Composition authority. This is explicit even where the external
reference tier is `A_REFERENCE`.

Across the 6,177 nutrient-input-eligible contribution rows:

- existing FamilyFoodOS identity mappings (`EXACT_EXISTING` + `ALIAS_EXISTING`):
  **2,591 / 6,177
  = 41.95%** of rows;
- by represented input mass, the same identity mappings cover
  **386274.014 / 777592.011 g
  = 49.68%**.

This is a mapping-coverage metric, not a nutrition-authority metric.

## Recipe classification

Every one of the **350 / 350** recipes is classified across
`recipe-candidates-part1.csv` … `recipe-candidates-part4.csv`.

| Class | Recipes | Meaning |
| --- | ---: | --- |
| `DIRECT_EXISTING_MAP_LEAD` | 3 | raw/reference layer passes the strict mapping screen using existing identities only |
| `CATALOGUE_EXTENSION_LEAD` | 65 | raw/reference layer is usable for mapping but needs new/form identity work |
| `PROCESS_REVIEW` | 88 | process/composite/output/yield/retention mapping is required |
| `IDENTITY_REVIEW` | 134 | at least one ingredient identity is ambiguous or unresolved |
| `RAW_EVIDENCE_REVIEW` | 60 | external raw/reference evidence is incomplete before FamilyFoodOS mapping can progress |

The strict raw-data preflight filter from PR #38 still yields **64** recipes.
After FamilyFoodOS identity mapping, those 64 decompose as:

- **3** `DIRECT_EXISTING_MAP_LEAD`;
- **42** `CATALOGUE_EXTENSION_LEAD`;
- **12** `PROCESS_REVIEW`;
- **7** `IDENTITY_REVIEW`.

The three direct identity-map leads are:

1. `USSR82-323` — `Картофель отварной`;
2. `USSR82-442` — `Макаронные изделия отварные`;
3. `USSR82-453` — `Яйца вареные`.

They are **not production-ready recipes**. Rights/source review, kitchen
verification, output/yield/retention semantics, RU familiarity where required and
RecipeTemplate/RecipeVersion publication gates remain separate.

## Recipe Assembly A impact

Assembly A remains **BLOCKED**.

### `family_count` — OPEN

There are now **45** strict-raw mapping leads that are either
`DIRECT_EXISTING_MAP_LEAD` or `CATALOGUE_EXTENSION_LEAD`:

- 3 use current identities only;
- 42 need bounded catalogue extension/form review.

This materially improves the candidate funnel, but it does not establish the
third production-ready RecipeTemplate family.

Lowest identity-extension debt begins with:

- `USSR82-323` — `Картофель отварной` — 0 extension rows;
- `USSR82-442` — `Макаронные изделия отварные` — 0;
- `USSR82-453` — `Яйца вареные` — 0;
- `USSR82-263` — `Суп молочный с картофельными клецками` — 1;
- `USSR82-59` — `Салат из свежих помидоров и огурцов` — 1;
- `USSR82-95` — `Салат из моркови или моркови с яблоками, финиками или черносливом` — 1.

These are triage order, not acceptance order.

### `optional_role` — OPEN

Seven externally `READY_RAW` recipes contain explicit optional rows, but **none**
passes the strict 64-recipe raw/evidence screen without additional debt.

The leading optional-role evidence is
`USSR82-317 — Суп из плодов или ягод сушеных` with 17 optional rows, but it also
contains 17 proxy rows and requires catalogue-extension work.

Therefore optional-source evidence is now concrete, but the FamilyFoodOS
candidate-specific source/identity/rights/kitchen gate is not satisfied.

### `verified_substitution` — OPEN

Fifteen strict-raw recipes contain one or more explicit `ChoiceGroup` values.
Useful leads include:

- `USSR82-374` — `Картофель, запеченный с яйцом и помидорами` — 2 choice groups;
- `USSR82-414` — `Каша вязкая с морковью` — 2;
- `USSR82-412` — `Каша вязкая с тыквой` — 2;
- `USSR82-413` — `Каша вязкая с черносливом` — 2;
- `USSR82-459` — `Яичница глазунья (натуральная)` — 1.

A source choice group proves only that the source lists alternatives. It does not
prove that FamilyFoodOS has a tested substitution rule with exact forms, masses,
Composition, kitchen behavior and applicability. The gate remains open.

## Manual semantic-review examples

The mapping deliberately avoids several tempting shortcuts:

- `Крупа пшенная` is **not** mapped to current `MILLET / Просо цельное`; groats
  are a processed cereal form and remain `FORM_SPLIT_CANDIDATE`.
- generic `Крупа рисовая` does not prove current `RICE_WHITE` long-grain identity;
  it remains `FORM_SPLIT_CANDIDATE`.
- generic `Говядина`, `Свинина (мякоть)`, `Индейка` and `Треска` do not choose
  among the current cut/species-specific identities; they remain unresolved or
  separate candidates.
- `Петрушка (корень)` is not current fresh parsley leaf.
- Russian `творог` is not silently equated with current grainy cottage-cheese
  identity.
- `Рафинадная пудра` may reuse `SUGAR` as nutrition identity because grinding
  does not change sucrose identity; measure/form evidence remains separate.
- source recipe outputs such as sauces, purées, porridges and fried-potato
  components remain producer/process identities rather than atomic foods.

## Files

- `ingredient-mapping-part1.csv` … `ingredient-mapping-part4.csv` — all 363 external identities, sharded only for repository transport/review; each external identity appears exactly once across the four parts;
- `recipe-candidates-part1.csv` … `recipe-candidates-part4.csv` — all 350 recipes with mapping debt and Assembly-A lead flags; each source recipe appears exactly once across the four parts;
- `summary.json` — machine-readable counts, coverage and shortlists;
- `checksums.json` — integrity pins for this curation package.

The original XLSX/ZIP files are not committed.

## Verification

This operation must satisfy:

- exactly 363 ingredient mapping rows with unique external IDs;
- exactly 350 recipe candidate rows with unique source recipe IDs;
- every nutrient-input-eligible row resolves to one classified external identity;
- no row has `production_ready=YES`;
- no mapped identity promotes external Nutrition/Composition truth;
- all checksums match;
- `git diff --check`;
- staged-scope / docs-link verification under the repository policy.

No backend regression is required because runtime/domain/schema/migration/seed
behavior is not changed.

## Next bounded research operation

The next useful operation after review is **not bulk publication**.

A bounded `V22-13-CANDIDATE-A` should take a small candidate set from this map and
attempt to close **one** Assembly-A evidence objective at a time:

1. one low-debt family candidate for `family_count`;
2. one optional-role candidate;
3. one source-choice candidate for `verified_substitution`.

It must perform source-lineage/rights review, exact FoodIngredient/form mapping,
exact quantity authority, Composition readiness, kitchen verification, RU
familiarity and substitution applicability where relevant.

No Assembly B, PR7, RecipeTemplate publication or production Nutrition promotion
starts automatically from this mapping package.
