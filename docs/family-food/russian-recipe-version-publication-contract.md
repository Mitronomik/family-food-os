# Step 9 — Russian RecipeVersion Publication Contract

**Status:** Implementation Contract Gate / docs-only
**Decision date:** 2026-09-26
**Accepted base:** `88a22a3cdfdd13d5481875dcd499abf06939582c` (merged PR #91 / accepted Step 8 runtime)
**Bounded step:** Russian-data integration Step 9 — executable Russian RecipeVersion publication
**Runtime/data publication authorized by this document:** no — review/merge this gate first

## 1. Goal

Step 9 publishes one immutable, source-backed Russian `RecipeVersion` that is
materially executable from accepted FamilyFoodOS food/composition truth without
inventing ingredient identity, mass, culinary transformation, storage duration,
meal-slot eligibility or nutrition.

The selected vertical slice remains:

```text
School2022 53-19з — «Масло сливочное (порциями)»
→ exact source card / source variant / execution route
→ BUTTER_PEASANT_72_5_UNSALTED
→ exact 10 g INPUT
→ immutable SOURCE_VERIFIED RecipeVersion
→ deterministic RU_NUTRIENT_REGISTRY_V2 composition calculation
```

Step 9 publishes the recipe catalogue object only. Planner consumption is Step 10.

## 2. FACT — sequencing and accepted prerequisites

The approved order remains:

```text
Step 8 recipe-dependency food batch
→ Step 9 executable Russian RecipeVersion
→ Step 10 Planner integration
```

PR91 merged Step 8 runtime into `main` at
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Accepted main already contains:

- `BUTTER_PEASANT_72_5_UNSALTED`;
- FIC RU-NUT-DB code 1417 / DB/533 profile;
- a sealed 17-value `RU_NUTRIENT_REGISTRY_V2` vector;
- ATOMIC composition v1 / INPUT for that exact food;
- immutable Recipe / RecipeVersion / RecipeIngredient / RecipeStep catalogue tables;
- transactional Recipe Catalogue service/UoW;
- same-source immutable revision support from migration 0027;
- migration head `0038_transformation_applicability`.

Reserved `0033_recipe_template_catalogue` remains unconsumed.

## 3. FACT — durable source artifact

The retained private corpus remains:

```text
private-library:/FamilyFoodOS/source-artifacts/
FamilyFoodOS-corpus-0.3.0-2026-09-20.zip
```

Archive identity:

```text
bytes:
206692075

SHA-256:
c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea
```

Pinned School2022 PDF:

```text
title:
Сборник рецептур блюд и типовых меню для организации питания обучающихся
1—4-х классов в общеобразовательных организациях: Пособие

publisher:
Федеральный центр гигиены и эпидемиологии Роспотребнадзора

year:
2022

source id:
ru-school2022

official URL:
https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf

PDF SHA-256:
c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d
```

The retained School2022 `source.json` has SHA-256:

`7de777b9ea0104e00bbb2e8cc98f2868bc6e5eead8a15b139d83706db765409b`.

No raw PDF/layout/image asset is committed by Step 9.

## 4. FACT — exact source-card lineage

Step 9 is not allowed to construct a recipe from a title plus memory.

The exact retained source lineage is:

| Record | Exact identity | Canonical JSON SHA-256 |
| --- | --- | --- |
| School2022 normalized card | `ru-school2022:recipe:53-19з` | `9090bb6d28ad83808acdaef124ae79208fd280316452409f12249bad83c73f9c` |
| source variant | `ru-school2022:recipe:53-19з:source-variant:1` | `9a7e02487b9bd3d2b7fdac68c90f717701708ed68d0e7c421ad1631cbcae8f42` |
| ingredient demand | `ru-school2022:recipe:53-19з:row:1:demand:1` | `f27dd3a8e156eb7c07cac9dd5460a29f0eda2b4a2efecc8b1c900ecacc71e164` |
| source process | `ru-school2022:recipe:53-19з:source-process` | `b9f4975ed8ed330464ed03fa8fffc713109dc5f10f6112695ee5e9cbc31c4f4e` |
| executable selection | `ru-school2022:recipe:53-19з:source-variant:1:selection:86446b0c327de7f405fe` | `f0a235291eba3b04e370b39bb758b9f8e34d60dc9870c90e4b6798e47829bdbc` |
| resolved execution route | `ru-school2022:recipe:53-19з:source-variant:1:selection:86446b0c327de7f405fe:closure:route:4f53cda18c2baa0c0354bb5f` | `a92d315561553a44b7f5ec6dd57d621aff73a8c471873eac5b1d7dbb89723a46` |

The runtime package must pin these identities/hashes or an equivalent stronger
exact-source receipt.

## 5. FACT — exact material recipe facts

The target card is:

```text
source recipe code:
53-19з

title:
Масло сливочное (порциями)

age/source scope:
7–11 years institutional school catering

PDF page:
18
```

The source variant has:

```text
basis.kind = published_single_food_portion
basis.mass_g = 10
clinical_scope = false
choice groups = []
ingredient source rows = [row:1]
```

The ingredient demand establishes:

```text
source label: масло сливочное
gross mass: 10 g
net mass: 10 g
unit: g
mass state: source_net_before_recipe_process
required: yes
```

The resolved route establishes:

- exactly one selected ingredient;
- recipe input mass = 10 g;
- gross purchase mass = 10 g;
- output mass = 10 g;
- material execution ready = true;
- procurement mass ready = true;
- zero material blockers;
- zero process choices;
- zero unquantified process inputs.

The process evidence establishes:

- no thermal treatment;
- butter is cut into pieces;
- portioned butter is held refrigerated before service;
- serving temperature is 14 °C.

## 6. FACT / DECISION — historical v0.3 blockers are adjudicated, not ignored

The v0.3 reconciliation record historically carried
`publication_ready=false`.

That historical state had two material causes relevant here:

1. food/nutrition closure was incomplete, including the unresolved FIC
   `carbh` definition;
2. production rights were intentionally a separate gate.

Step 9 does not silently relabel that old row as ready.

### DECISION — food/nutrition blocker

Step 8 now supplies the exact food identity and accepted V2 composition.

The FIC `carbh` definition remains ambiguous and remains non-canonical.
Step 9 does not invent or import canonical total carbohydrate.

Therefore the old `carbh` blocker is resolved only in the sense that Step 9
can calculate all **available canonical V2 nutrients** without requiring
carbohydrate completion.

### DECISION — rights blocker

The later canonical project decision in
`docs/family-food/ru-normative-recipe-corpus.md` explicitly allows normative
and base recipe cards authorized by the project user to be stored and published
as factual recipe data without a separate rights gate per card.

That decision does not extend to:

- photographs;
- publisher layout;
- logos/trademarks;
- third-party author commentary;
- decorative or expressive source copy unrelated to the factual recipe.

Step 9 therefore publishes a narrow factual derivative with exact attribution
and provenance. It does not publish source PDF bytes or reproduce the source
page/layout.

## 7. DECISION — exact Recipe identity

Step 9 freezes one new active Recipe:

```text
canonical_code:
SCHOOL2022_53_19Z_BUTTER_PORTION

canonical_name:
Масло сливочное (порциями)

is_active:
true
```

This technical vertical slice does not establish Planner default eligibility.

If the canonical code or normalized name is already owned by a different Recipe,
publication fails closed.

## 8. DECISION — exact RecipeVersion shape

The first immutable version is:

```text
version_number = 1
base_servings = 1
meal_type_code = other

prep_time_minutes = null
cook_time_minutes = null
total_time_minutes = null
difficulty_code = null
batch_friendly = null
freezable = null
storage_days_fridge = null
storage_days_freezer = null

verification_status = SOURCE_VERIFIED
verified_at = 2026-09-26T00:00:00Z

source_name = ru-school2022
source_recipe_id = ru-school2022:recipe:53-19з
source_url =
https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf
source_version =
sha256:c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d
source_retrieved_at = null
source_document_sha256 =
c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d
source_original_servings = 1

rights_review_status = REVIEWED
created_from_version_id = null
```

`source_retrieved_at` stays null because the retained source package supplies
an acquisition date, not a trustworthy exact instant. The runtime package keeps
the acquisition date separately rather than inventing a timestamp.

### Meal-type interpretation

`other` is a neutral technical catalogue classification because the current
Recipe enum has no exact `cold dish / institutional portion` member.

It does not mean breakfast/lunch/dinner eligibility and does not grant any
Planner slot.

### Unknown metadata

“No thermal treatment” does not mean a measured cook duration of zero.
Therefore time fields remain null.

Refrigerated holding before service does not establish a safe home storage
duration. Storage-day fields remain null.

No source fact establishes batch friendliness, freezer suitability or difficulty.
Those fields remain null.

## 9. DECISION — rights_basis

The persisted `rights_basis` must record the narrow project authority, for
example:

```text
Нормативная рецептурная карта публикуется как фактические рецептурные данные
по пользовательскому решению, зафиксированному в
docs/family-food/ru-normative-recipe-corpus.md; сохраняются источник, версия,
URL и SHA-256; фотографии, издательская вёрстка, логотипы и сторонние
авторские комментарии не публикуются.
```

Runtime may whitespace-normalize this exact reviewed meaning, but must not replace
it with a blanket public-domain or unrestricted-commercial-rights assertion.

## 10. DECISION — exact ingredient row

Step 9 publishes exactly one required RecipeIngredient:

```text
food_ingredient_code:
BUTTER_PEASANT_72_5_UNSALTED

quantity:
10

unit:
g

optional:
false
```

The reviewed factual source amount text is:

`масло сливочное: брутто 10 г; нетто 10 г`.

The normalization note must preserve that:

- recipe input uses the source net 10 g;
- gross = net = 10 g;
- exact 72.5% unsalted form was closed by Step 8.

No density, edible fraction, piece conversion or estimate is used.

## 11. DECISION — process steps are factual derivatives

Step 9 must not copy publisher layout or unnecessary expressive prose.

The reviewed Russian execution steps are factual derivatives of the pinned source
process:

1. `Термическая обработка не требуется.`
2. `Нарезать сливочное масло на порционные кусочки.`
3. `До раздачи хранить порционированное масло в холодильнике.`
4. `Подавать при температуре 14 °C.`

The source organoleptic description is not required for this execution slice and
is not copied into production RecipeVersion steps.

All `stage_code` values remain null unless the current domain requires a
pre-existing reviewed code; Step 9 does not invent a new stage taxonomy.

## 12. DECISION — no equipment rows

Current Recipe equipment taxonomy has no exact refrigerator/cold-holding code.

Step 9 publishes zero `RecipeEquipment` rows rather than inventing a new code or
misusing `resealable_container`.

The refrigerated-holding source fact remains in the execution step.

## 13. DECISION — source-declared nutrition is reference-only

School2022 prints recipe nutrient totals on the card.

Step 9 does not persist or use those totals as FamilyFoodOS food/recipe nutrition
authority.

In particular, it must not use the School2022 carbohydrate value to fill the
unresolved FIC carbohydrate definition.

School2022 nutrient totals may be retained in the review package only as
cross-check/reference evidence.

## 14. FACT — Step 8 deterministic V2 nutrition input

Step 8 publishes the exact food composition on a 100 g basis.

For the 10 g recipe input, deterministic canonical V2 values are the Step 8
values scaled by exactly `10 / 100`:

| Nutrient | 10 g amount |
| --- | ---: |
| ENERGY_KCAL | 66.09 kcal |
| PROTEIN | 0.08 g |
| FAT_TOTAL | 7.25 g |
| FATTY_ACIDS_SATURATED_TOTAL | 4.71 g |
| STARCH | 0.00 g |
| SUGARS_TOTAL | 0.13 g |
| FIBER_TOTAL_DIETARY | 0.00 g |
| VITAMIN_A_RE | 45.00 µg |
| THIAMIN | 0.001 mg |
| RIBOFLAVIN | 0.012 mg |
| VITAMIN_C | 0.00 mg |
| SODIUM | 1.50 mg |
| POTASSIUM | 3.00 mg |
| CALCIUM | 2.40 mg |
| PHOSPHORUS | 3.00 mg |
| IRON | 0.02 mg |
| MAGNESIUM | 0.05 mg |

WATER remains unknown. Canonical total carbohydrate remains unavailable.

## 15. DECISION — deterministic nutrition acceptance path

Step 9 must prove recipe nutrition through the exact Step 8 composition:

```text
RecipeIngredient 10 g
→ BUTTER_PEASANT_72_5_UNSALTED
→ FoodCompositionVersion v1 / INPUT
→ RU_NUTRIENT_REGISTRY_V2
→ ApplicabilityAwareCompositionCalculator
→ scale exact 100 g composition result by 10 / 100
```

This is a validation/calculation operation; Step 9 does not persist a duplicate
recipe-nutrition table.

The accepted result is deterministic **partial V2 nutrition**: all available
canonical V2 nutrients are exact, while unsupported concepts remain unknown.

## 16. DECISION — legacy NutritionService is not changed in Step 9

The existing legacy `NutritionService.recipe_version()` reads the current
FoodNutritionProfile and its B1 assessment contract treats a non-current pin as
stale.

The Step 8 FIC profile is intentionally `is_current=false`.

Therefore Step 9 must not:

- mark the Step 8 profile current;
- clear or replace the existing generic butter current profile;
- create a fake B1 assessment to bypass current-profile semantics;
- change legacy `NutritionService.recipe_version()` to consume V2 composition;
- claim legacy complete-macro Nutrition for this recipe.

General V2 Composition integration into Planner/Nutrition consumption belongs to
Step 10 or a separately reviewed integration contract.

## 17. DECISION — “executable RecipeVersion” meaning

For Step 9, executable means all of the following:

- immutable active Recipe/RecipeVersion exists;
- exact source identity/version/hash is retained;
- one required ingredient is resolved to the exact canonical FoodIngredient;
- recipe input quantity is exact 10 g;
- ordered execution steps are source-backed factual derivatives;
- no unresolved material/process choice remains;
- deterministic V2 composition calculation succeeds for every available canonical
  nutrient;
- unknown nutrients remain unknown.

It does **not** mean:

- Planner eligible;
- default meal candidate;
- family-serving optimized;
- legacy `NutritionService` complete;
- carbohydrate complete;
- freezer/storage verified;
- retailer available.

## 18. DECISION — reuse existing Recipe Catalogue persistence

Step 9 reuses:

- `TrustedRecipeSeed`;
- `TrustedRecipeVersionSeed`;
- `TrustedRecipeIngredientSeed`;
- `FoodRecipeCatalogueService`;
- existing SQLAlchemy Core Recipe Catalogue UoW/repositories.

No new Recipe table or alternate recipe model is authorized.

Expected runtime shape is a narrow hash-pinned Step 9 package/loader, for example:

- `data/curation/ru-school2022-step9-recipe-runtime/README.md`;
- `publication.json`;
- package checksums/source-record receipts;
- `backend/app/seed/ru_school2022_step9_recipe.py`;
- focused production-publication tests.

## 19. DECISION — narrow preflight wraps reconcile_seed

Existing `reconcile_seed()` correctly handles exact historical replay, but when
a Recipe identity already exists without the requested provenance it may append a
new version.

Step 9 is a one-shot `CREATE_REVIEWED` publication and must not silently append
to unexpected prior history.

Before calling the existing transactional reconcile path, the Step 9 loader must
enforce:

### Fresh

- Recipe code absent;
- normalized Recipe name absent;
- exact Step 8 FoodIngredient active;
- exact Step 8 ATOMIC v1 / V2 composition readable;
- deterministic 10 g V2 calculation passes.

Then existing Recipe Catalogue transaction creates Recipe + Version + children
and commits once.

### Exact replay

Allowed only when:

- Recipe code/name identity matches;
- the exact Step 9 source provenance exists;
- every persisted version/ingredient/step/equipment fact matches the reviewed
  bundle.

Replay performs zero writes and preserves IDs.

Later unrelated RecipeVersion history may coexist only if the exact Step 9
historical version remains unchanged; replay never rewrites history.

### Conflict

Fail closed if:

- Recipe code or normalized name is occupied by another identity;
- Recipe exists but exact Step 9 provenance is absent;
- same provenance exists with different immutable facts;
- ingredient quantity/form differs;
- source/process/package hash changes;
- Step 8 dependency is missing/inactive or its exact V2 composition is absent;
- the reviewed source package is incomplete/tampered.

Do not append a new version merely to “make the seed work”.

## 20. FACT / DECISION — transaction boundary

Recipe + RecipeVersion + RecipeIngredient + RecipeStep children are written by the
existing Recipe Catalogue UoW in one transaction.

Step 8 Composition is pre-existing immutable history: migration 0029 forbids
update/delete/replacement of the accepted composition snapshot.

Therefore Step 9 does not require a new cross-context write transaction.

The Step 8 dependency is validated before publication and the active
FoodIngredient is resolved again inside the Recipe Catalogue write transaction.

Injected failure after any attempted Recipe Catalogue write must roll back the
whole Step 9 recipe bundle.

## 21. DECISION — no source-corpus persistence expansion

Step 9 does not add a new `SourceDocument` / `SourceCard` row to migration
0030 source-corpus tables.

The exact source lineage is retained in:

- the durable private corpus;
- the Step 9 reviewed publication package;
- RecipeVersion source/version/URL/hash fields.

Adding a School2022 source-corpus ingestion path would be separate source-corpus
scope and is not required to prove this one RecipeVersion vertical slice.

## 22. DECISION — no schema migration

Step 9 requires no schema change.

Existing tables already represent:

- Recipe identity;
- immutable RecipeVersion;
- ingredient rows;
- ordered steps;
- optional equipment;
- source provenance;
- rights review;
- exact FoodIngredient dependency.

Migration head remains `0038_transformation_applicability`.
Reserved `0033_recipe_template_catalogue` remains unconsumed.

If runtime implementation proves schema/shared immutable semantics must change,
**STOP and amend this Contract Gate before implementation continues.**

## 23. Preservation matrix

| Accepted truth | Step 9 requirement |
| --- | --- |
| migrations 0001–0038 | unchanged |
| reserved 0033 | unchanged / unconsumed |
| existing Recipe catalogue/history | unchanged |
| existing 30 technical seed RecipeVersions | unchanged |
| source-corpus tables/data | unchanged |
| Step 8 FoodIngredient/profile/vector | unchanged |
| Step 8 ATOMIC v1 | unchanged |
| generic BUTTER_UNSALTED current USDA profile | unchanged |
| current-profile selector semantics | unchanged |
| legacy NutritionService | unchanged |
| B1 nutrition assessment semantics | unchanged |
| transformations/applicability | unchanged |
| source-declared School2022 nutrition | reference-only |
| Planner/API/UI defaults | unchanged |
| AI_ENABLED=false | supported |

## 24. Adversarial acceptance tests frozen by this gate

Step 9 runtime publication must prove at least:

1. accepted main is `88a22a3cdfdd13d5481875dcd499abf06939582c` or a descendant containing merged PR91;
2. migration head remains 0038;
3. reserved 0033 remains unconsumed;
4. durable corpus archive size/hash matches the accepted receipt;
5. School2022 PDF hash matches;
6. source recipe identity is exactly `53-19з`;
7. normalized-card canonical record hash matches;
8. source-variant canonical record hash matches;
9. ingredient-demand canonical record hash matches;
10. source-process canonical record hash matches;
11. executable-selection canonical record hash matches;
12. resolved-route canonical record hash matches;
13. historical `publication_ready=false` is explicitly adjudicated, not ignored;
14. project rights basis is the canonical normative-recipe factual-publication decision;
15. no PDF/layout/photo/logo asset is copied into production package;
16. Recipe code/name are exactly the frozen identity;
17. Recipe is active;
18. version number is 1 for fresh publication;
19. base/source servings are exactly 1;
20. meal type is `other` and grants no Planner eligibility;
21. time/difficulty/batch/freezer/storage unknowns stay null;
22. source provenance/version/URL/PDF hash are exact;
23. source retrieval instant remains null rather than invented;
24. rights status is REVIEWED with the narrow reviewed basis;
25. exactly one RecipeIngredient is created;
26. ingredient is exactly `BUTTER_PEASANT_72_5_UNSALTED`;
27. quantity is exactly 10 g and optional=false;
28. gross/net/source amount evidence is retained;
29. no density/piece/edible-fraction conversion is used;
30. exact four reviewed factual process steps are published in order;
31. zero equipment rows are created;
32. source organoleptic prose is not required/copied;
33. School2022 nutrient totals do not populate production nutrition;
34. no canonical carbohydrate value is invented;
35. exact Step 8 ATOMIC v1 / INPUT is required;
36. deterministic V2 calculation succeeds for all 17 available canonical nutrients;
37. 10 g scaled values match the frozen table in §14;
38. WATER remains unknown;
39. legacy NutritionService behavior is unchanged;
40. Step 8 profile remains non-current;
41. no fake B1 assessment is created;
42. fresh publication commits once;
43. exact replay is zero-write and preserves IDs;
44. unexpected existing Recipe history without exact Step 9 provenance fails closed;
45. same-provenance structural drift fails closed;
46. source/package/hash tamper fails before publication;
47. injected late write failure rolls back Recipe + Version + children;
48. existing Recipe catalogue rows are unchanged except the one new Step 9 bundle;
49. source-corpus persisted rows are unchanged;
50. no Step 10 Planner integration occurs;
51. AI is not involved.

## 25. Verification tier

Step 9 is authoritative production RecipeVersion publication over accepted food
and composition truth.

Required review-ready evidence:

- exact private corpus retrieval/hash receipt;
- exact six-record source-lineage hash audit;
- rights/provenance audit;
- source factual-derivative/process wording audit;
- exact Step 8 dependency/composition check;
- deterministic 17-nutrient V2 / 10 g calculation audit;
- fresh publication;
- exact replay / zero-write;
- identity/provenance/structure conflict tests;
- package/source tamper tests;
- injected rollback;
- preservation of existing Recipe catalogue and source-corpus data;
- migration head/0033 preservation;
- `AI_ENABLED=false`;
- focused Recipe Catalogue + Step 8/V2 composition regressions;
- full backend + launcher exact-runtime-head regression;
- Docs/DC1;
- exact-head scope/whitespace audit.

A later state/docs-only receipt after runtime freeze does not invalidate
byte-identical runtime evidence.

## 26. Step 10 handoff boundary

After Step 9 runtime/data publication is reviewed and merged, stop.

Step 10 may separately integrate the new RecipeVersion/V2 Composition path into
Planner and the general Nutrition consumption flow.

Step 10 must not infer from Step 9 that:

- `meal_type=other` is a preferred meal slot;
- the recipe is automatically Planner-default;
- missing carbohydrate/WATER may be filled;
- old current-profile semantics may be silently replaced.

## 27. Explicit non-goals

Step 9 does not authorize:

- another Recipe or RecipeVersion;
- another food publication;
- source-corpus bulk import;
- new Recipe schema;
- migration 0033 or any other migration;
- current-profile selector changes;
- legacy NutritionService rewrite;
- persisted recipe-nutrition cache/table;
- carbohydrate inference;
- source-declared nutrition as production truth;
- new equipment taxonomy;
- storage/freezer claims;
- Planner integration;
- Shopping/Prep/Retail;
- API/UI;
- Auth/PostgreSQL;
- AI authority.

## 28. Stop boundary

This PR is the Step 9 Implementation Contract Gate only.

No Recipe, RecipeVersion, RecipeIngredient, RecipeStep, source-corpus row,
runtime seed, migration, Planner change or production write belongs in the gate
PR.

After gate review/merge:

1. stop;
2. Step 9 runtime/data publication requires separate explicit authorization;
3. after Step 9 runtime review/merge, stop before Step 10.
