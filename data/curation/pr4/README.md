# PR4 recipe-corpus FoodIngredient coverage

Status: **ready for PR4-DATA review**

This directory is durable curation evidence for `PR4-DATA — Recipe Corpus
FoodIngredient Coverage`. It is a supporting data operation, not production
Recipe seed data, a Recipe model, an ingestion framework, or a runtime resolver.

## Frozen corpus

`recipe-corpus.json` freezes 30 directly published USDA FNS CACFP Family Child
Care six-serving recipe cards. Every record stores a stable curation ID, title,
direct official recipe URL, collection, and source servings.

`ingredient-coverage.csv` transcribes every source ingredient occurrence,
including optional ingredients and source alternatives. Alternatives remain in
`source_ingredient_text`; the selected deterministic concept and canonical
FoodIngredient code are explicit. The Bean Burrito Bowl pico de gallo is
decomposed only because the same USDA source supplies the complete subrecipe;
its structural row and every component row remain represented.

The corrected corpus was frozen on 2026-09-04 after direct review of the USDA
source cards.

## Minimal replacement analysis

The original 30-card union required 126 canonical concepts. Marginal
contribution was calculated as the full union minus the union with each recipe
removed, rather than from total ingredient counts.

The complete original-corpus marginal calculation was:

| Recipe | Marginal unique contribution |
| --- | ---: |
| Asian Tuna Burger | 3 |
| Baked Sweet Potatoes and Apples | 0 |
| Bean Burrito Bowl | 1 |
| Brown Rice Pilaf | 3 |
| Carrot Raisin Salad | 2 |
| Chicken Fajita | 2 |
| Corn and Edamame Blend | 2 |
| Corn Pudding | 2 |
| Creamy Coleslaw | 2 |
| Green Beans with Potatoes and Smoked Turkey | 4 |
| Honey Lime Chicken | 2 |
| Local Harvest Bake | 2 |
| Macaroni Salad | 4 |
| Marinated Black Bean Salad | 1 |
| Orange Glazed Carrots | 0 |
| Pizza Green Beans | 1 |
| Quiche with Self-Forming Crust | 0 |
| Rice Vegetable Casserole | 1 |
| Roasted Potato and Turkey Hash | 6 |
| Ropa Vieja | 3 |
| Sautéed Spinach and Tomatoes | 0 |
| Southwest Tofu Scramble | 3 |
| Spanish Rice | 0 |
| Spiced Oatmeal | 1 |
| Strawberry Smoothie Bowl | 2 |
| Tabbouleh | 3 |
| Tuna Salad Sandwich | 1 |
| Tuscan Grill Cheese Sandwich | 2 |
| Vegetable Chili | 4 |
| Vegetable Frittata | 0 |

The highest marginal was Roasted Potato and Turkey Hash at **6** exclusive
concepts: `APPLESAUCE_UNSWEETENED`, `CAYENNE_PEPPER`, `POTATO`, `SAGE_GROUND`,
`TURKEY_GROUND_93`, and `WHITE_PEPPER`. The best qualified one-card replacement,
Vegetable Frittata Bites, contributes only **1** concept not otherwise required,
`FLOUR_WHEAT`, but a one-for-one change would still leave 121 concepts.

Therefore two replacements were the minimum capable of satisfying the bound:

- removed Roasted Potato and Turkey Hash — marginal **6**;
- removed Brown Rice Pilaf — marginal **3** (`CELERY_SALT`, `CHEESE_PARMESAN`,
  `THYME_FRESH`); this also avoids asserting nutrition for celery salt when the
  allowed Foundation/SR Legacy releases contain no matching item;
- added Vegetable Frittata Bites — contribution **1** (`FLOUR_WHEAT`);
- added Cauliflower Rice — contribution **1** (`CAULIFLOWER`).

The resulting union is `126 - 6 - 3 + 1 + 1 = 119`. The corpus still includes
vegetables, grains/starches, legumes and plant protein, poultry and beef, fish,
eggs and dairy, vegetarian dishes, and breakfast-, side-, salad-, sandwich-, and
main-style preparations.

## Deterministic coverage result

- recipe records: **30**
- matrix source ingredient rows: **363**
- per-recipe canonical occurrences after within-recipe deduplication: **358**
- distinct transcribed source ingredient texts: **310**
- unique canonical FoodIngredient codes required: **119**
- resolved by the accepted PR3 catalogue before expansion: **36**
- added by PR4-DATA: **83**
- unresolved or ambiguous required rows: **0**

`mvp0-food-ingredient-codes.txt` is the exact sorted 119-code Gate 2 subset. It
is deliberately separate from the 183-item global catalogue and satisfies the
unchanged `<=120` fixture constraint.

## FoodIngredient expansion and provenance

Only the 83 missing concepts required by the corrected corpus were added to the
global seed. All have one current USDA FoodData Central profile per 100 g:

- 15 Foundation Foods records from the 2026-04-30 release / FoodData Central
  Version 15.0;
- 68 SR Legacy records from the final 2018-04 release.

Foundation was selected where the release supplies a suitable record with all
required macros and energy; SR Legacy supplies ordinary gaps and exact processed
forms. Source modifiers remain visible in the matrix. Stable catalogue
abstractions are used where the modifier is not a separate canonical food
identity: panko resolves to `BREADCRUMBS`, lime zest to `LIME`, low-sodium salsa
to `SALSA`, low-sodium vegetable broth to `VEGETABLE_BROTH`, and no-salt-added
crushed tomatoes to `TOMATO_CRUSHED`. Materially distinct foods are not merged.

## Candidate and rejection policy

Vegetable Frittata Bites and Cauliflower Rice are direct six-serving USDA
Standardized Recipes Project 2024 cards with complete quantities and no
brand-dependent compound ingredient, unresolved blend, or invented conversion.

Previously rejected recipes remain rejected because their concrete blockers
remain unresolved:

- Orzo Pasta with Green Peas — low-sodium chicken base.
- Winter Greens — low-sodium vegetable base.
- Cuban Black Beans and Rice — low-sodium vegetable base powder/bouillon.
- Ground Turkey and Beef Spanish Rice — low-sodium beef base.
- Minestrone Soup — low-sodium beef base.
- Tomato Soup — low-sodium chicken base.
- Bean Soup — Old Bay seasoning.
- Beef Vegetable Soup — unspecified salt-free seasoning.
- Chicken or Turkey and Rice Soup — Old Bay seasoning and poultry seasoning.

No recipe was replaced merely because it introduced several ordinary reusable
ingredients.

## Reproduction checks

The curation tests require 30 unique six-serving sources, all 363 matrix rows to
be non-empty and resolved, exactly one retained structural subrecipe marker,
exact equality between matrix codes and the sorted 119-code manifest, a manifest
size at or below 120, and authoritative current provenance for all 83 additions.
The global seed-loader and idempotency tests independently validate the complete
183-item catalogue.
