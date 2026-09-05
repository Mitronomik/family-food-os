# FamilyFoodOS — Russia Recipe Localization & Substitution Policy

**Status:** canonical product/data policy  
**Approved:** 2026-09-05  
**Initial market:** Russia, Saint Petersburg  
**Sequence impact:** none; `docs/family-food/master-roadmap.md` continues to control milestone order.

## 1. Purpose

FamilyFoodOS is not merely a catalogue of recipes. The production catalogue must support realistic weekly planning for households in Russia, initially Saint Petersburg, using ingredients that people can actually buy in mainstream local grocery retail.

The system must also support individualized food preferences and exclusions without duplicating every possible combination as a separate recipe.

The governing product shape is:

```text
verified base RecipeVersion
+ Household/member preferences and exclusions
+ deterministic nutrition and culinary constraints
+ Pantry / Shopping context
+ later Retail availability and price enrichment
→ validated recipe adaptation / replacement choices
```

This policy clarifies recipe curation, market compatibility, catalogue growth and future substitution behavior. It does not authorize implementation of Retail connectors, Planner, Nutrition or a new substitution bounded context inside PR4.

## 2. Source-of-truth boundaries

The following existing architecture remains unchanged:

```text
FoodIngredient != RetailSKU
Recipe != Serving
AI_ENABLED=false remains valid
```

A RecipeVersion stores verified culinary/source truth. It must not become a snapshot of one retailer's assortment or one brand's SKU.

Retail evidence may be used during data curation to determine whether a recipe is appropriate for the target market, but production RecipeVersion rows must remain expressed through platform `FoodIngredient` references.

Later Retail logic may map:

```text
FoodIngredient → RetailSKU → Price / Availability Snapshot
```

without changing recipe identity.

## 3. Target-market decision

### DECISION

The active recipe catalogue for the Russia MVP must be practical for ordinary households shopping in major grocery chains represented in Saint Petersburg.

Recipes should favor:

- ordinary mass-market ingredients;
- forms and package types commonly sold in Russian grocery retail;
- familiar cooking equipment;
- realistic household preparation methods;
- ingredients that do not require specialist ethnic, restaurant-supply or import-only shopping;
- ingredients for which useful validated replacements can eventually be offered.

International dishes are allowed when their required ingredients are realistically available in mainstream Saint Petersburg retail. Russian optimization is an availability/usability requirement, not a requirement that every dish be traditional Russian cuisine.

## 4. Saint Petersburg retailer evidence panel

The current curation baseline is the following mass-market panel:

1. **Пятёрочка** — X5;
2. **Перекрёсток** — X5;
3. **Лента**;
4. **О'КЕЙ**;
5. **Магнит**.

`ВкусВилл` may be used as secondary evidence, but a core recipe must not depend on VkusVill-only or another specialty/premium-only product.

This panel is curation evidence, not a Retail architecture dependency.

### Current external evidence reviewed on 2026-09-05

- X5 identifies `Пятёрочка` and `Перекрёсток` as its grocery networks and has current Saint Petersburg / Leningrad Region activity:  
  `https://www.x5.ru/ru/news/x5-dogovorilas-o-sotrudnichestve-s-11-rossijskimi-regionami/`
- X5 describes regional assortment adaptation for `Перекрёсток`, specifically mentioning Saint Petersburg:  
  `https://www.x5.ru/ru/publication/restajling-dostavka-i-kafe-kak-razvivaetsya-perekryostok/`
- Lenta exposes Saint Petersburg / Leningrad Region stores and a broad grocery catalogue:  
  `https://lenta.com/allmarkets/?citykey=spb&withRedirect=true`  
  `https://lenta.com/catalog/`
- O'KEY official materials list a large set of Saint Petersburg hypermarkets. Current source used in the decision record:  
  `https://www.okmarket.ru/`
- Magnit currently operates stores in Saint Petersburg and exposes an online grocery catalogue:  
  `https://rabota.magnit.ru/sankt-peterburg`  
  `https://magnit.ru/`
- VkusVill currently lists multiple Saint Petersburg stores and is secondary evidence only:  
  `https://vkusvill.ru/shops/`

Retailer presence and assortment change over time. Evidence used for curation must record retrieval date and region and must be refreshed for later Retail-program decisions.

## 5. Ingredient market-compatibility classification

For recipe curation, required ingredients are classified independently of RetailSKU persistence.

### `RU_MASS_MARKET`

A required `FoodIngredient` has current Saint Petersburg / Leningrad Region catalogue evidence in at least **3 of the 5** baseline mass-market chains above.

This is the preferred class for base recipes.

### `RU_AVAILABLE`

The ingredient is evidenced in fewer than 3 baseline chains but is still available in ordinary non-specialist retail.

It may appear in the broader catalogue only when the recipe has a validated mass-market substitution path or there is a specific product reason to retain it.

### `SPECIALTY_OR_UNCLEAR`

Availability depends on specialist/import stores, evidence is weak/stale, or the ingredient form does not map cleanly to Russian retail reality.

It must not be required by the technical/core recipe corpus unless an explicit later decision approves it.

### Exceptions

Tap water does not require retailer evidence. Basic salt/sugar/oil/spice commodities should still be represented by valid `FoodIngredient` concepts, but their curation evidence may be category-level when SKU-level proof adds no useful information.

Availability classification is not permanent truth. It is a timestamped curation assessment until the Retail Program provides real availability snapshots.

## 6. PR4 / PR4-DATA2 immediate corpus decision

### FACT

The current PR4 corpus contains 30 recipe sources. Two sources are ICN-hosted 2024 cards:

- `CACFP6-VEGETABLE-FRITTATA-BITES`;
- `CACFP6-CAULIFLOWER-RICE`.

They do not meet the current project rights-evidence gate for the intended commercial/product reuse.

### DECISION

Those two sources are authorized for replacement.

The supporting correction is no longer only a two-row swap. It must also audit the **entire 30-recipe technical corpus** against this Russia/Saint-Petersburg market-compatibility policy.

Any current recipe that materially depends on `SPECIALTY_OR_UNCLEAR` ingredients must be replaced or explicitly escalated. Do not preserve an unsuitable recipe merely to avoid re-curation work.

### Replacement-source preference for this bounded correction

To avoid opening a new rights/licensing programme inside PR4, replacement candidates should prefer direct official USDA/FNS six-serving recipe cards whose rights evidence passes the current project review.

For direct USDA/FNS material used under the current project risk classification:

- preserve source attribution;
- preserve exact source URL/document hash/retrieval evidence;
- do not import USDA logos, photos or trademarks as product assets;
- reject a candidate if the card contains a third-party copyright/licensing notice that is not independently cleared.

A later Data Program should prioritize Russian/right-cleared editorial, licensed and internally tested recipes so the catalogue becomes culturally and operationally stronger than the initial FNS technical corpus.

### Hard PR4-DATA2 bounds

The corrected technical corpus must remain:

- exactly `30` active technical recipes;
- fully source/provenance reviewable;
- completely resolved to existing `FoodIngredient` records;
- no new `FoodIngredient` added merely to rescue a recipe candidate;
- Gate 2 fixture subset `<=120 FoodIngredient` codes;
- all required ingredients market-audited for Saint Petersburg;
- no unresolved required ingredient;
- no silent source substitution or invented quantity;
- source-backed equipment retained when explicitly present.

The global FoodIngredient catalogue may remain larger than the Gate 2 fixture. Removing a recipe from the fixture does not require deleting an otherwise valid global FoodIngredient.

### Selection score for replacement candidates

Among candidates that pass all hard gates, prefer higher score on:

1. `RU_MASS_MARKET` ingredient coverage;
2. lower marginal FoodIngredient count in the bounded Gate 2 fixture;
3. ordinary household equipment;
4. shorter active cooking time;
5. child/family usability;
6. budget friendliness;
7. batch/reheat usefulness where source-supported;
8. contribution to corpus diversity (meal type, protein, grain/vegetable profile, cooking method);
9. useful future substitution opportunities.

Do not optimize only for the smallest ingredient union if that produces an unrealistic or repetitive catalogue.

## 7. Catalogue size is not the same as useful variety

The technical `30 verified recipes` is a vertical-slice fixture, not a product-size target.

Existing product targets remain minimum stages, not caps:

- technical slice: `30` verified base recipes;
- Data Readiness / closed-MVP stage: `50–80+` verified base recipes;
- commercial-beta stage: approximately `120–150` carefully normalized base recipes;
- later Data Program: continuous expansion when provenance, quality, market compatibility and coverage remain acceptable.

The long-term objective is not to create thousands of near-duplicate RecipeVersion rows. Useful variety comes from both:

```text
more verified base recipes
+
validated adaptation/substitution paths
+
Planner combinations across the week
+
individual Serving sizes
```

Catalogue quality and coverage outrank raw recipe count.

## 8. Recipe families and variants

A verified source change, editorial correction or independently reviewed recipe variant may create a new immutable RecipeVersion according to the Recipe Catalogue contract.

A user's one-off ingredient preference change must **not** silently rewrite or version the authoritative base recipe.

Conceptually:

```text
RecipeVersion (authoritative base)
        ↓
validated substitution/adaptation decisions
        ↓
Recipe Adaptation / Variant Plan (derived)
```

The exact future schema/name is intentionally not frozen by PR4. The important contract is that derived personalization references the immutable base version and records the applied changes.

## 9. Required future substitution capability

### DECISION

FamilyFoodOS must eventually allow the user to request replacement of any ingredient or combination of ingredients.

This does **not** mean every arbitrary replacement is guaranteed to be valid.

The UX contract is:

> the user may request any change; the system returns validated alternatives, a compatible recipe replacement, or an explicit explanation that the requested adaptation cannot be made reliably.

The system must never claim that an arbitrary substitution is safe or culinarily equivalent when it has not been validated.

### Typical substitution intents

- taste preference;
- excluded ingredient;
- allergen/restriction avoidance;
- vegetarian or other supported food preference;
- cheaper ingredient;
- pantry-first use;
- ingredient unavailable;
- retailer availability later;
- easier preparation;
- nutrition-target adjustment when Nutrition Core exists.

Medical treatment/therapeutic claims remain out of scope.

## 10. Deterministic substitution architecture

The core substitution path must work with `AI_ENABLED=false`.

A future deterministic engine should reason over explicit data such as:

- source/base `RecipeVersion`;
- `FoodIngredient` identity;
- culinary/functional role in the recipe;
- allowed substitution candidates;
- quantity/unit transformation rules;
- allergen/exclusion compatibility;
- preparation/cooking-step compatibility;
- Nutrition Core recalculation;
- Household/member preferences;
- Pantry context;
- budget context;
- later Retail availability and price evidence.

Useful future ingredient-role metadata may include concepts such as:

- primary protein;
- starch/grain base;
- vegetable base;
- fat;
- liquid;
- binder;
- thickener;
- leavener;
- acid;
- sweetener;
- aromatic/seasoning;
- garnish.

These are future data requirements, not authorization to add a new PR4 schema today.

## 11. Multi-ingredient adaptation

Independent one-for-one substitutions cannot simply be composed blindly.

When several ingredients change together, the engine must validate the resulting recipe as a whole. For example, changing a protein, binder and liquid simultaneously may require different quantities or cooking instructions.

A future adaptation result should therefore retain enough information to explain and reproduce:

```text
base RecipeVersion
requested changes
applied substitution rules
quantity transformations
step changes, if reviewed/authorized
validation result
nutrition recalculation/version
warnings
availability/cost evidence when applicable
```

If no validated multi-change path exists, replacing the entire recipe is preferable to inventing a fragile combination.

## 12. AI boundary

AI may later help interpret a request such as:

> «замени курицу, молоко и грибы чем-нибудь подходящим»

or propose candidate replacements.

AI may not be the final authority for:

- allergen safety;
- exact quantities;
- nutrition values;
- retailer availability;
- cost;
- cooking feasibility;
- whether multiple substitutions remain a valid recipe.

All accepted adaptations must pass deterministic validation against current authoritative data.

## 13. Relationship to Planner, Shopping and Retail

### Planner

Before a substitution engine exists, Planner may satisfy preferences/exclusions by selecting a different verified RecipeVersion from the catalogue.

Later, validated recipe adaptations can enlarge the candidate space without turning Planner into a recipe generator.

### Shopping

Shopping consumes the final selected ingredient set after recipe/adaptation validation. Shopping must not invent ingredient substitutions on its own.

### Retail

Generic substitution must not depend on a retailer connector.

Later Retail may rank otherwise-valid substitutions using real:

- SKU availability;
- package fit;
- price;
- preferred retailer.

If a preferred SKU is unavailable, the system should first try an alternative SKU for the same FoodIngredient, then an allowed ingredient substitution, then a recipe replacement. Retail failure must not corrupt the base recipe catalogue.

## 14. Coverage metrics for a useful catalogue

Do not measure recipe quality only by `COUNT(Recipe)`.

Track coverage across dimensions such as:

- breakfast / main / side / soup / snack where supported;
- major protein families;
- vegetarian options;
- grains/starches;
- vegetables;
- cooking methods;
- active preparation time;
- ordinary-equipment requirement;
- budget level;
- child/family suitability;
- batch/reheat/freezer suitability when source-supported;
- market compatibility in Saint Petersburg;
- common exclusion/preference replacement coverage;
- recent repetition pressure in Planner.

Future substitution quality should also be measured, for example:

- share of common excluded ingredients with at least one validated alternative;
- share of popular base recipes with useful substitution paths;
- success rate of multi-ingredient adaptation requests;
- rate of fallback from ingredient adaptation to full recipe replacement;
- percent of generated weeks requiring manual recipe replacement.

## 15. Research/data evidence discipline

Market availability is time-sensitive.

For bounded curation evidence, record at minimum:

- `FoodIngredient` code;
- retailer chain;
- region/city;
- evidence URL or source identifier;
- observed product/category wording;
- checked_at;
- status (`AVAILABLE`, `NOT_FOUND`, `UNCERTAIN`);
- notes on seasonality/form/packaging when relevant.

Do not store one observation as permanent availability truth. The later Retail Program owns timestamped production availability snapshots.

## 16. Scope discipline

This policy is required product/data direction, but it does not authorize premature implementation.

PR4 remains responsible for verified Recipe Catalogue truth and the corrected 30-recipe technical corpus.

Do **not** add to PR4 solely because this document exists:

- RetailSKU;
- retailer connectors/parsers;
- price snapshots;
- Planner;
- Nutrition Engine;
- Household-specific recipe variants;
- AI-generated recipes;
- a full Substitution Engine.

Substitution implementation should be introduced only as a later bounded capability after its dependencies and acceptance tests are explicitly authorized. The core weekly loop remains the priority.

## 17. Immediate next data operation

After this policy is accepted in `main`, authorize a bounded supporting operation:

`PR4-DATA2 — Russia/SPB Recipe Corpus Re-curation`

It should:

1. audit all current 30 recipes for Russia/Saint-Petersburg ingredient compatibility;
2. remove the two uncleared ICN sources;
3. replace every recipe that fails the agreed market-compatibility gate;
4. keep exactly 30 technical recipes;
5. keep the bounded manifest at `<=120 FoodIngredient` codes;
6. use only existing global FoodIngredient records unless a separate data decision explicitly authorizes expansion;
7. preserve provenance/rights evidence;
8. produce retailer-availability evidence as curation data, not RetailSKU production truth;
9. hand the accepted corpus back to PR4 for seed regeneration, equipment curation, tests and final review.

PR5 remains unauthorized until PR4 is corrected, accepted and merged.
