# R1-F — Cooked-Nutrition Authority Implementation Contract Gate

**Status:** docs-only implementation contract gate
**Decision date:** 2026-09-30
**Accepted base:** `becc00f0e94c927598f930140c385f84f80aa21d` (merged PR #115)
**Parent:** #116, #114, #100, #99
**Runtime/data publication authorized by this document before merge:** no

## 1. Goal

Define the minimum truthful runtime/data contract needed to move the first mixed
R1 cooked pilot toward ordinary production Planner eligibility:

- R1-E closure target USSR82-453 → source-neutral production Recipe
  `HARD_BOILED_EGG_40G` — breakfast;
- R1-E closure target USSR82-697 → source-neutral production Recipe
  `BOILED_CHICKEN_PORTION_75G` — main.

The implementation target after this gate is merged is:

`source-backed RecipeVersion → exact prepared-output ENERGY_KCAL → active Recipe → ordinary Planner admission`

with no raw→cooked fallback, no invented retention and no LLM numeric authority.

R1-F is an authority pilot, not sufficient final R1-C catalogue capacity. Planner
still requires later expansion because `max_recipe_repetitions=3`.

## 2. FACT — current runtime cannot represent prepared-output Recipe Nutrition

Current Recipe Nutrition authority kinds are:

- `LEGACY_V1`;
- `COMPOSITION_V2`.

Current `RECIPE_COMPOSITION_NUTRITION_V1` requires every required ingredient row
to have an INPUT-state Composition binding and rejects transformed output.

Current NutrientVector persistence is owned by `FoodNutritionProfile`; it is not
a RecipeVersion-level prepared-dish authority.

Therefore source-published cooked-dish Nutrition cannot be truthfully stored as:

- a FoodIngredient Nutrition profile;
- a fake INPUT Composition;
- a legacy fallback;
- an implicit retention result.

**DECISION:** R1-F requires a distinct RecipeVersion-level prepared-output
Nutrition authority.

## 3. FACT — Planner only needs exact positive energy to admit an incomplete vector

Planner rejects Nutrition when energy is missing/non-positive, or when Nutrition
is INCOMPLETE and `exact_energy_ready=false`.

An INCOMPLETE projection with exact positive `ENERGY_KCAL` and
`exact_energy_ready=true` is permitted by the current Planner contract.

**DECISION:** the R1-F pilot will publish only source fields whose canonical
semantics are explicitly reviewed. `ENERGY_KCAL` is mandatory. Unreviewed
nutrients remain UNKNOWN; no zero placeholders are allowed.

This keeps the pilot focused on Planner eligibility without pretending that a
complete 54-nutrient cooked vector has been established.

## 4. FACT — USSR82-453 source branch and prepared-output authority

USSR82 recipe 453 allows three cooked outcomes:

- soft-boiled;
- medium/"in the bag";
- hard-boiled.

The R1 retained normalization has a 40 g edible serving/output, but a generic
"boiled egg" authority would be ambiguous across the three cooking modes.

A separate Russian normative source, МР 2.4.0162-19 Appendix 5,
Technology Card 4.1, publishes an exact hard-boiled branch:

- chicken egg: 40 g;
- hard-boiled for 8–10 minutes;
- finished output: 40 g / one egg;
- source-published energy: 63 kcal per portion.

Public locators reviewed for this gate:

- https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/bliuda-iz-iaits/tekhnologicheskaia-karta-n-4.1/
- https://base.garant.ru/73535214/

**DECISION:** USSR82-453 remains closure/source evidence, but production does not
create a source-coded USSR82 Recipe identity.

Publish a new source-neutral Recipe:

- canonical code: `HARD_BOILED_EGG_40G`;
- canonical Russian name: `Яйцо куриное вкрутую, 40 г`;
- RecipeVersion source: `RU_MR_2_4_0162_19 / APPENDIX_5_CARD_4_1`;
- meal type: `breakfast`;
- required ingredient: canonical EGG FoodIngredient, 40 g;
- source output: 40 g.

The prepared-output Nutrition authority comes from the **same exact source card**
as the RecipeVersion, so R1-F does not create a cross-source RecipeVersion/Nutrition
equivalence.

Applicability is exact for:

- ingredient identity: chicken egg;
- edible amount/output: 40 g;
- process: hard-boiled 8–10 minutes;
- output state: peeled cooked egg;
- serving basis: one 40 g portion.

Any different egg cooking mode must fail applicability.

## 5. FACT — the 1986 row 697/824 is not authority for the current 75 g chicken-only output

The 1986 USSR vocational-food order publishes:

- `697/824`;
- `Куры отварные`;
- `курица II категории`;
- output `50/50`;
- 144 kcal.

Recipe 824 in the 1982 collection is `Соус красный основной`.

Recipe 697 itself shows, for its III column:

- 107 g net chicken;
- 75 g cooked poultry;
- 150 g garnish;
- 50 g sauce.

Therefore the 1986 `50/50` nutrient row is a chicken + sauce combination, not
the current immutable R1-B 75 g chicken-only output.

**DECISION:** do not scale 144 kcal to 75 g and do not attach it to the existing
USSR82-697 RecipeVersion.

## 6. FACT — exact 75 g prepared-output evidence exists for boiled chicken

The 1988 reference `Рецептура блюд диетического питания`
(Жангабылов А. К. et al., Алма-Ата: Казахстан, 1988, ISBN 5-615-00164-X)
publishes recipe 303 `Курица отварная`.

Variant III states:

- chicken: 155 g gross / 107 g net;
- finished output: 75 g;
- protein: 12.6 g;
- fat: 12.8 g;
- carbohydrate: 0.5 g;
- source-published energy: **167.7 kcal**;
- process: whole chicken boiled.

Public source locator reviewed for this gate:

- https://ru.djvu.online/file/tnrwaYeNtWZjj

The previously accepted USSR82 authority review independently established that
the 155 g gross / 107 g net source path aligns with category-II chicken.

The historical USSR82-697 RecipeVersion contains an additional 2 g onion cooking
input and must remain immutable.

**DECISION:** do not mutate, rename, reinterpret or append a foreign-source
version to the existing source-coded Recipe
`USSR82_697_BOILED_CHICKEN / Курица отварная`.

That historical Recipe and its v1 remain immutable and inactive.

Publish a **separate source-neutral canonical Recipe**:

- canonical code: `BOILED_CHICKEN_PORTION_75G`;
- canonical Russian name: `Курица отварная, порция 75 г`;
- RecipeVersion source: `DIETETIC_RECIPES_1988 / 303_VARIANT_III`;
- required FoodIngredient: `CHICKEN_CATEGORY_2_RAW`;
- required input: 107 g;
- source output: 75 g;
- prepared-output energy: 167.7 kcal.

This avoids making the external USSR82 id a hidden domain invariant and avoids a
Recipe-code rename/alias migration.

The new Recipe is a distinct canonical product identity because its exact source,
ingredient set and process/output truth differ from the historical USSR82-697
version. R1-F closes the **Planner-capacity target** originally represented by
USSR82-697; it does not claim the two source cards are one immutable RecipeVersion
lineage.

## 7. DECISION — authority mode

### Mode A — current identity-preserving V1

Rejected for both pilot recipes as the cooked authority path.

Both outputs are thermally prepared, so INPUT Composition cannot be presented as
consumed output merely because mass or serving size is known.

### Mode B — transformed Composition

Not selected for R1-F.

The reviewed sources do not currently provide an accepted exact ENERGY_KCAL
retention contract sufficient to calculate these two cooked outputs. USDA
retention tables may corroborate process-specific retention for some
micronutrients, but they do not by themselves provide the exact ENERGY_KCAL
authority required by this pilot.

### Mode C — source-backed prepared-output Recipe Nutrition

**Selected.**

R1-F will introduce a narrow versioned authority:

`RECIPE_PREPARED_OUTPUT_NUTRITION_V1`

with authority kind:

`PREPARED_OUTPUT_V1`.

The authority is valid only when source output identity, process, serving/output
mass and RecipeVersion identity satisfy the reviewed publication spec.

## 8. Persistence contract

**DECISION:** migration `0042_recipe_prepared_output_nutrition` is required.

Do not overload FoodNutritionProfile/NutrientVector ownership.

Add immutable RecipeVersion-level persistence.

### Header

`recipe_prepared_nutrition_authorities`

Required fields:

- recipe_version_id — PK/FK to RecipeVersion;
- registry_version — `RU_NUTRIENT_REGISTRY_V2`;
- nutrient_set_version — `RECIPE_V2_NUTRIENT_SET_V1`;
- recipe_calculation_version — `RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- output_mass_g — positive Decimal;
- source_name;
- source_id;
- source_version;
- source_locator;
- source_document_sha256;
- source_data_type;
- rights_review_status;
- rights_basis;
- review_reference;
- value_count;
- value_sha256;
- created_at.

### Sparse values

`recipe_prepared_nutrient_values`

Primary key:

`(recipe_version_id, nutrient_code)`

Required fields:

- amount — non-negative Decimal;
- provenance_json — canonical source evidence;
- registry-version + nutrient-code FK to the frozen registry.

Rows not present in this table project as UNKNOWN, never zero.

Both tables are append-only / immutable under the repository's established
history rules.

## 9. Source artifact rule

The implementation PR must retain or otherwise pin independently retrievable
source artifacts before publishing authority.

Minimum runtime-publication pins:

### 453

- exact MR 2.4.0162-19 source artifact or independently reproducible official
  document snapshot;
- SHA-256;
- exact card locator 4.1;
- source retrieval timestamp.

### chicken main

- exact 1988 source artifact for recipe 303;
- SHA-256;
- bibliographic identity including ISBN;
- exact recipe/variant locator;
- source retrieval timestamp.

If a source artifact cannot be durably retained and hash-verified, production
publication for that recipe remains blocked.

Prepared-output publication also requires an explicit accepted rights/use
disposition for the exact source artifact. Public availability is not a rights
receipt. For each authority source the runtime package must pin:

- rights_review_status;
- rights_basis / receipt reference;
- allowed project use scope.

An unresolved rights disposition keeps that recipe blocked.

Public web text/search snippets are research evidence, not the immutable runtime
source receipt.

## 10. Publication specs

Introduce a reviewed spec dedicated to prepared-output authority.

Minimum spec fields:

- trusted Recipe/RecipeVersion seed identity;
- expected recipe code;
- expected source provenance/version;
- expected output mass;
- prepared source name/id/version/locator/hash;
- expected available nutrient values;
- expected UNKNOWN nutrient codes;
- require Recipe inactive.

The publisher must:

1. resolve the exact RecipeVersion;
2. verify SOURCE_VERIFIED status;
3. verify exact source/output identity;
4. verify output mass equality;
5. verify registry definitions;
6. verify exact reviewed source values;
7. reject unsupported nutrients rather than infer them;
8. reject an existing conflicting prepared authority;
9. exact-replay an identical authority;
10. persist header + sparse values atomically.

## 11. Nutrition projection precedence

`neutral_consumption_projection(recipe_version_id)` must classify authority
fail-closed.

Order:

1. if a prepared-output authority exists:
   - any required Composition binding on the same RecipeVersion is a conflict;
   - project `PREPARED_OUTPUT_V1`;
2. otherwise preserve current behavior:
   - zero required V2 bindings → legacy path;
   - partial required V2 bindings → unavailable;
   - all required V2 bindings → `COMPOSITION_V2`.

There is no silent precedence between prepared-output and Composition authority.

This rule prevents double retention/double calculation.

## 12. Prepared-output projection

Prepared authority projects a canonical 54-code tuple:

- persisted reviewed values → AVAILABLE;
- every other frozen nutrient code → UNKNOWN.

For this R1-F pilot, `ENERGY_KCAL` must be present, finite and positive.

`exact_energy_ready=true` iff per-base-serving ENERGY_KCAL is finite and > 0.

Legacy NutritionStatus may remain INCOMPLETE because other fields are UNKNOWN.
The current Planner contract already accepts exact energy in that state.

No prepared value is divided by or multiplied by output mass unless the source
authority explicitly uses a different reviewed basis and the calculation version
supports it. R1-F V1 uses exact source-portion values; no scaling is authorized.

## 13. Recipe publication / activation order

### 453 breakfast

1. publish the exact hard-boiled RecipeVersion inactive;
2. keep canonical EGG ingredient identity for exclusions/Shopping;
3. publish prepared-output authority from MR card 4.1;
4. require exact 63 kcal projection;
5. require Planner admission to have no Nutrition blocker;
6. activate the Recipe.

### boiled-chicken main

1. preserve historical USSR82-697 v1 unchanged/inactive;
2. publish/resolve exact category-II chicken FoodIngredient identity;
3. append the exact 1988 recipe-303 Variant III RecipeVersion inactive under the
   same canonical boiled-chicken Recipe;
4. publish prepared-output authority for 75 g / 167.7 kcal;
5. require Planner admission to have no Nutrition blocker;
6. activate the canonical Recipe so the new current verified version is selected.

If any step before activation fails, the safe state is inactive. No destructive
rollback of immutable history is required; corrected work appends/replays.

## 14. Ingredient truth is preserved independently from Nutrition authority

Prepared-output Nutrition does not replace RecipeIngredient truth.

RecipeIngredient rows remain authoritative for:

- member FoodIngredient exclusions;
- future Shopping aggregation;
- Pantry linkage;
- provenance/explainability.

A recipe-specific prepared nutrient value must never erase, synthesize or hide an
ingredient.

## 15. Adversarial acceptance

The runtime PR must prove at least:

1. soft-boiled/medium egg cannot consume the hard-boiled 453 authority;
2. 453 output mass other than 40 g is rejected;
3. raw EGG Composition cannot masquerade as cooked output;
4. historical USSR82-697 v1 remains byte/semantic immutable and inactive;
5. category-I chicken cannot satisfy the new main version;
6. 1986 `697/824 50/50, 144 kcal` cannot satisfy the 75 g chicken-only authority;
7. recipe-303 output other than 75 g is rejected;
8. missing/zero/negative ENERGY_KCAL cannot activate;
9. unsupported nutrients remain UNKNOWN, not zero;
10. prepared authority + Composition binding on the same RecipeVersion fails
    closed;
11. duplicate identical publication exact-replays;
12. conflicting duplicate publication rejects without partial writes;
13. failure between RecipeVersion publication and authority publication leaves the
    Recipe inactive;
14. failure before activation leaves the Recipe inactive;
15. neutral consumption projection reports `PREPARED_OUTPUT_V1`;
16. Planner admission reports exact-energy-ready for both successful pilot
    versions;
17. normal authoritative Planner candidate loading sees both after activation;
18. ingredient exclusion still rejects the corresponding RecipeVersion;
19. `AI_ENABLED=false` throughout.

## 16. Planner/product boundary

R1-F completion target after runtime implementation:

- at least one active exact-energy-ready breakfast;
- at least one active exact-energy-ready main;
- both sourced through ordinary Recipe Catalogue + RecipeNutrition service;
- no synthetic candidates;
- no test-only nutrition.

This is still not sufficient for final R1-C full-week success because the Planner
hard repetition limit is three uses per RecipeVersion.

After the pilot proves the authority path, the immediate expansion batch remains:

- USSR82-467;
- USSR82-492;
- USSR82-1081;

plus additional MAIN candidates as required for a complete week.

## 17. Rollback and failure policy

Migration rollback during development may remove only the new empty R1-F tables
before production use.

After a prepared authority has been published, historical authority is immutable.
Correction is append-only through a new RecipeVersion/authority, never UPDATE of
historical source truth.

Activation is the final reversible flag. Deactivation is the operational rollback
when a later issue is found.

## 18. Non-goals

This gate does not authorize before merge:

- runtime code;
- migration execution/publication;
- Recipe activation;
- arbitrary prepared-output imports;
- generic retention engine;
- automatic cross-source equivalence;
- Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- R2/R3.

## 19. DECISION

R1-F runtime implementation after this gate merges will use:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`

for the two pilot targets.

It will not use raw-input energy, inferred 100% retention, the incompatible 1986
697/824 50/50 value, or mutation of the historical USSR82-697 RecipeVersion.

The implementation should be one bounded runtime/data PR if migration + authority
publisher + the two exact pilot publications can remain one coherent transaction
boundary. If that PR reveals another high-coupling immutable contract not defined
here, stop and amend this gate rather than improvising.
