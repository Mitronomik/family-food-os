# R1-B — Source Recipe Output / Yield Implementation Contract Gate

**Status:** docs-only Implementation Contract Gate
**Decision date:** 2026-09-27
**Accepted base:** `eb803cda82ce8073443981867291716a0eb0f0ad` (merged PR #101)
**Parent:** #102, #99, #67
**Runtime authorized by this document:** no — merge/review this gate first.

## 1. Goal

R1-B must publish the first ordinary household-suitable Russian RecipeVersions
from the already accepted corpus.

R1-A closed FoodIngredient/form/Nutrition dependencies for five recipes:

| Source | Recipe | Source input mass | Source output |
| --- | --- | ---: | ---: |
| USSR82-453 | Яйца вареные | 40 g | 40 g |
| USSR82-467 | Омлет (натуральный) | 120 g | 110 g |
| USSR82-492 | Сырники из творога | 200 g | 170 g |
| USSR82-1081 | Блины, III — с маслом | 215.5 g | 160 g |
| USSR82-697 | Птица, дичь или кролик отварные с гарниром — selected chicken/main branch | 109 g | 75 g |

The retained corpus also contains source-backed Russian process instructions for
all five.

Current `RecipeVersion` cannot persist the structured output mass of a selected
source variant.

For four of the five recipes source output differs materially from input mass.

R1-B must not hide that truth in `RecipeStep`, `change_note` or free-form
normalization text.

## 2. FACT — why this gate is required

Repository `AGENTS.md` requires a docs-only Implementation Contract Gate before
runtime implementation that changes a persisted identity/version, schema/migration
boundary or another high-coupling immutable contract.

Adding source output/yield truth to immutable `RecipeVersion` changes:

- the domain snapshot;
- SQL persistence;
- trusted recipe seed/replay equality;
- migration behavior;
- future Serving/consumer interpretation.

Therefore R1-B runtime must not start until this gate is reviewed and merged.

## 3. FACT — accepted source evidence for R1-B

The R1 source audit re-read the durable corpus archive:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Archive SHA-256:

`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`

Relevant retained source layers include:

- `russian_normative_recipes_v20_complete_master.xlsx`
  - workbook SHA-256:
    `6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5`;
- v22.13 mass/nutrient evidence
  - workbook SHA-256:
    `5ea78ead82568f8aff019a4076215c6598675783cb81e0d1d5b4f913016de4cc`;
- DC1 accepted recipe/relationship inventory in the repository.

For the five selected recipes the v22.13 coverage layer reports:

- 100% relationship resolution;
- 100% known input mass;
- one selected variant block;
- one ready output scenario;
- zero proxy rows;
- status `READY_RAW`.

`READY_RAW` is evidence/curation state only. It is not automatic authorization
to publish a RecipeVersion or to apply cooked-retention coefficients.

The retained v20 extraction rows are explicitly marked
`UNVERIFIED_LEGACY_EXTRACTION / ready_for_integration=false`.

**DECISION:** R1-B runtime must create a new reviewed, hash-pinned curation package
from the retained source bytes and accepted later mapping decisions. It must not
promote legacy extraction status directly.


### 3.1. DECISION — RecipeVersion source snapshot identity

For this R1-B batch, the retained reviewed source snapshot used by
`RecipeVersion.source_document_sha256` is:

`russian_normative_recipes_v20_complete_master.xlsx`

SHA-256:

`6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5`

R1-B must use:

```text
source_name = reviewed USSR82 corpus identity
source_version = sha256:6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5
source_document_sha256 = 6ac7dfb300844fd996aee6d20b4e7e6aa421dd517367ab1f59120812fee104d5
source_url = exact card URL retained in the reviewed row
source_recipe_id = exact USSR82-* identity
```

The URL identifies the original referenced card. The SHA pins the retained reviewed
snapshot actually used for publication review. Do not hash the URL string and do
not claim the hash belongs to a freshly fetched web response.

The v22.13 workbook SHA
`5ea78ead82568f8aff019a4076215c6598675783cb81e0d1d5b4f913016de4cc`
is supporting curation/mass evidence and must be pinned in the R1-B package
lineage, but it is not substituted for the RecipeVersion source-document hash.

Rights basis follows the accepted
`docs/family-food/ru-normative-recipe-corpus.md` decision: factual normative/base
recipe data explicitly authorized by the user may be published with provenance;
photographs, publisher layout, logos and third-party commentary are outside the
publication.

## 4. FACT — source process/output evidence

Selected source process facts:

### USSR82-453 — Яйца вареные

- selected variant: `selected_1982_variant`;
- input: 40 g edible egg mass;
- output: 40 g;
- process: boil to selected doneness; serve in shell.

### USSR82-467 — Омлет (натуральный)

- selected 1982 variant;
- inputs: 80 g egg, 30 g milk, 5 g margarine, 5 g butter;
- input total: 120 g;
- output: 110 g;
- process: mix egg/milk, cook in fat 5–7 minutes; mass-catering baking
  alternative is source context, not automatically selected R1-B process.

### USSR82-492 — Сырники из творога

- selected variant: `1-й вариант, со сметаной`;
- inputs: 135 g tvorog, 20 g flour, 5 g egg, 15 g sugar,
  5 g table margarine, 20 g sour cream;
- input total: 200 g;
- output: 170 g;
- process: mix, form/bread in flour, fry both sides, finish 5–7 minutes in oven,
  serve with sour cream.

### USSR82-1081 — Блины

- selected variant: `III — с маслом`;
- inputs: 75 g flour, 3 g sugar, 118 g water, 3 g compressed yeast,
  1.5 g salt, 5 g table margarine, 10 g butter;
- input total: 215.5 g;
- output: 160 g;
- process: mix/ferment batter, cook both sides on heated surface, serve with
  butter.

### USSR82-697 — selected chicken/main branch

- exact selected branch:
  `III, курица, основной продукт без гарнира/соуса`;
- inputs: 107 g category-I chicken, 2 g onion;
- input total: 109 g;
- output: 75 g main boiled product;
- process: simmer prepared bird/portion with onion; portion cooked chicken;
- garnish and sauce are excluded from the selected RecipeVersion.

## 5. DECISION — minimal persisted output contract

Add two nullable immutable fields to `RecipeVersion`:

```text
source_output_g: Decimal | None
source_output_text: str | None
```

### source_output_g

Meaning:

> total source-backed output mass represented by this exact RecipeVersion
> ingredient/process variant.

Rules:

- Decimal, never float;
- positive when present;
- grams only in this contract;
- no value is inferred from ingredient sum;
- no value is inferred from a calculated yield ratio;
- null means structured source output mass is unavailable/unsupported;
- historical rows are not backfilled from assumptions.

### source_output_text

Meaning:

> retained source wording needed to preserve output/branch semantics.

Rules:

- optional normalized non-empty text;
- maximum 1000 characters;
- may be present when structured grams are unknown;
- when R1-B has exact output grams, both fields are populated;
- it is evidence/display context, not a calculation authority.

Examples for R1-B:

```text
USSR82-453 → 40 / "выход 40 г"
USSR82-467 → 110 / "выход 110 г"
USSR82-492 → 170 / "выход 170 г"
USSR82-1081 → 160 / "III — с маслом; выход 160 г"
USSR82-697 → 75 / "выход основного отварного продукта 75 г; без гарнира/соуса"
```

## 6. DECISION — source output is not a transformation coefficient

Knowing:

`input_mass_g` and `source_output_g`

does **not** authorize:

```text
yield_factor = output / input
```

as a reusable `YieldModel`, transformation coefficient or retention authority.

Reason:

- source output may include cooking medium loss, evaporation, discarded broth,
  absorbed/released water, fat left in cookware and other process-specific effects;
- one recipe's observed/source output does not automatically generalize to the
  same FoodIngredient in another process.

R1-B may preserve the source output fact without publishing any new numeric
Transformation/Yield/Retention rule.

Step 7 applicability rules remain unchanged.

## 7. DECISION — Recipe Nutrition remains input-composition authoritative

R1-B does not change Step 10-A calculation authority.

Recipe Nutrition remains:

```text
RecipeIngredient exact input grams
→ pinned FoodCompositionVersion
→ deterministic V2 Recipe Nutrition
```

`source_output_g` must not:

- rescale recipe nutrient totals;
- fill unknown nutrients;
- imply cooked-food nutrient equivalence;
- apply implicit retention;
- replace source input grams.

Source-declared recipe nutrition remains reference/review evidence only.

If a recipe requires numeric retention/transformation authority to be considered
safe/usable, it must remain blocked until that authority is separately reviewed.

## 8. DECISION — base serving interpretation

For R1-B selected variants:

```text
base_servings = 1
source_original_servings = 1
```

The selected source output therefore describes one base recipe serving.

A future consumer may derive:

```text
output_g_per_base_serving = source_output_g / base_servings
```

without changing stored recipe truth.

**R1-B does not add Planner/Serving consumption of this value.**

That is a later bounded integration decision, expected in/around R1-C after #100.

## 9. DECISION — migration 0040

The next free migration is reserved for this bounded contract:

`0040_recipe_version_source_output`

Expected columns on `food_recipe_versions`:

```text
source_output_g TEXT NULL
source_output_text TEXT NULL
```

Runtime metadata uses `DecimalText()` for `source_output_g`.

Required SQL/domain checks:

- null allowed;
- numeric value must be > 0;
- text null or non-empty after normalization;
- no destructive rewrite of existing IDs/history.

### Upgrade strategy

Prefer additive nullable columns where the project migration runner/SQLite
compatibility proves safe.

The implementation must preserve:

- immutable recipe/version IDs;
- all child FKs;
- indexes;
- no-update/no-delete triggers;
- historical data;
- existing source/provenance fields.

If additive ALTER semantics cannot preserve accepted constraints/triggers safely,
use the existing foreign-key rebuild pattern instead. Do not silently choose a
different persistence contract.

### Downgrade/restore

Migration verification must include:

- fresh DB;
- upgrade from current main;
- data preservation on a copy;
- downgrade/restore path;
- `PRAGMA foreign_key_check`;
- trigger/index presence.

Historical RecipeVersions receive null output fields. Do not backfill Step 9
butter or legacy FNS recipes in migration 0040.

## 10. DECISION — trusted seed and replay semantics

Extend `TrustedRecipeVersionSeed` and RecipeVersion equality/replay with:

```text
source_output_g
source_output_text
```

Exact replay requires exact equality of both fields.

A same-source/version RecipeVersion whose persisted output differs from reviewed
seed truth must fail closed as a publication conflict.

No update-in-place is allowed.

## 11. DECISION — R1-B publication shape after gate

After this gate is merged and R1-B runtime is separately authorized, publish a
single bounded recipe batch from the five selected source variants.

For each published RecipeVersion the R1-B package must pin:

- source recipe/card ID;
- exact selected variant/branch;
- source URL;
- retained source/workbook hashes;
- ingredient row identity and exact grams;
- FoodIngredient code;
- exact Composition version;
- source process instructions;
- source output grams/text;
- rights basis;
- Russian display name;
- meal type;
- expected deterministic V2 Recipe Nutrition;
- activation disposition.

R1-B may publish fewer than five if process/output/source review exposes a real
blocker.

## 12. DECISION — activation is separate from publication validity

`SOURCE_VERIFIED RecipeVersion` does not automatically imply `Recipe.is_active=true`.

Activation review must additionally confirm:

- household applicability;
- current Planner role compatibility;
- exact positive energy;
- hard ingredient exclusion behavior remains valid;
- no automatic allergen coverage is claimed;
- no unresolved process/portion ambiguity that makes the recipe misleading.

If a RecipeVersion can be preserved as source truth but is not household-suitable,
publish inactive or keep blocked according to the reviewed disposition.

## 13. Preservation matrix

| Surface | Before | After 0040 | Rule |
| --- | --- | --- | --- |
| Historical RecipeVersion | no output fields | output null | no guessed backfill |
| RecipeIngredient | exact quantity/unit | unchanged | output never rewrites inputs |
| RecipeStep | process text | unchanged | output not hidden in steps |
| Step10 binding | RecipeIngredient → Composition | unchanged | no output coupling |
| Recipe Nutrition | input Composition total | unchanged | no output rescaling |
| Planner v0.3 | current candidate contract | unchanged | no R1-B Planner changes |
| Serving | multiplier-based | unchanged | no output consumption yet |
| Step7 transforms | explicit applicability | unchanged | no implicit yield/retention |
| Recipe replay | existing fields | includes output fields | mismatch fails closed |

## 14. Adversarial acceptance tests

Implementation must cover:

### Domain

- reject `source_output_g <= 0`;
- reject float/non-Decimal inputs through trusted domain construction;
- reject blank `source_output_text`;
- allow null/null for historical and source-unknown recipes;
- allow text-only source output when structured grams are unavailable.

### Migration

- fresh 0040 schema;
- upgrade from merged PR101 main;
- all historical recipe IDs/rows preserved;
- child RecipeIngredient/Step/Equipment FKs preserved;
- indexes/triggers preserved;
- FK check clean;
- downgrade/restore proven.

### Catalogue publication

- fresh R1-B seed;
- exact replay = zero writes;
- changed output grams conflicts;
- changed output text conflicts;
- partial batch fails closed;
- failure injection rolls back the full bounded recipe batch.

### Nutrition boundary

- same Recipe Nutrition totals before/after adding source output metadata;
- source output does not fill unknown nutrients;
- no transformation/retention row is created merely from source output.

### R1-B source cases

- 453 output 40 g;
- 467 output 110 g;
- 492 output 170 g;
- 1081 output 160 g;
- 697 output 75 g and garnish/sauce excluded;
- exact source/process/ingredient/hash pins;
- any real source mismatch blocks that recipe.

## 15. Verification tier

Because runtime implementation will change persisted RecipeVersion schema and a
shared catalogue path, required implementation verification is:

- focused domain/service tests;
- migration fresh/upgrade/downgrade tests;
- Recipe Catalogue persistence tests;
- R1-B source/data package validation;
- Step 10 Recipe Nutrition regression;
- Planner application regression for unchanged candidate semantics;
- full backend regression;
- launcher regression;
- docs/DC1 relevant checks.

This gate itself is docs/state only and uses proportional docs/state verification.

## 16. Non-goals

This contract does not authorize:

- generic Yield Engine redesign;
- automatic output-to-yield conversion;
- V2 retention publication;
- Recipe Assembly;
- #100 energy allocation implementation;
- R1-C Planner product proof;
- Shopping/PR9;
- Prep/Freezer;
- Retail;
- consumer API/UI changes;
- Auth/PostgreSQL;
- AI authority;
- publication of R1-A blocked USSR82-364 or USSR82-208.

## 17. Sequence after this gate

```text
PR101 R1-A merged
→ R1-B source-output contract gate
→ explicit R1-B runtime authorization
→ migration 0040 + reviewed five-recipe publication batch
→ review/merge
→ #100 Planner energy allocation
→ R1-C production Planner proof
```

Do not begin the next arrow merely because the previous PR is review-ready.
