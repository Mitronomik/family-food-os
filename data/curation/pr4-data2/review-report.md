# PR4-DATA2 — Final review evidence

Status: **READY FOR REVIEW**, not ACCEPTED or COMPLETE. Reviewed `2026-09-05`.

[Issue #12](https://github.com/Mitronomik/family-food-os/issues/12) · [existing PR #13](https://github.com/Mitronomik/family-food-os/pull/13). Branch `data/pr4-data2-russia-spb-recuration`; exact base `main@26af749be0f6446de1d88cad2e2e03158a9830a0`. The pushed commit SHA is recorded in PR #13; this report travels with that reviewed commit. No new branch/PR, no history rewrite, no merge.

## Outcome

Exactly **30 recipes**, **5 retained / 25 replaced**, **223 source-audit rows**, **193 selected food rows** (191 required, 1 optional, 1 conditional), **79 existing FoodIngredient codes <=120**, **0 new codes / 0 unresolved required code rows**, **96 equipment rows / 33 codes**. Global 183 FoodIngredients, 172 aliases and 183 nutrition profiles are unchanged. Historical PR4 fixture remains 30 / 363 / 119 and is not overwritten. These are curation counts, not production RecipeVersion/step/seed counts.

Both forbidden ICN cards are excluded. All original 30 cards and 363 source rows were audited. The 96 flagged exact source/code/text pairs remain preserved: 77 PURCHASE_FORM_CRITICAL and 19 PREPARATION_ONLY_OR_NOT_RETAIL_FORM. Six old cards have full market evidence; one is independently ICN-rights-excluded, leaving five eligible keepers.

## All 30 selected recipes

Food rows are selected coverage rows, not distinct ingredients. Market M/A/? counts distinct required non-water source forms (M = RU_MASS_MARKET, A = RU_AVAILABLE). Full literal ingredient quantities, source limitations, times and equipment excerpts remain in the JSON/CSV artifacts.

| Source ID and primary source | Meal type | Source servings | Food rows | Equipment rows | Market M/A/? |
| --- | --- | ---: | ---: | ---: | --- |
| [CACFP6-CORN-EDAMAME-BLEND](https://fns-prod.azureedge.us/sites/default/files/resource-files/Corn_Edamame_Blend_6_Servings.pdf) — Corn and Edamame Blend | SIDE_DISH | 6 | 10 | 2 | 0/10/0 |
| [CACFP6-LOCAL-HARVEST-BAKE](https://fns-prod.azureedge.us/sites/default/files/resource-files/Local_Harvest_Bake_6_Servings.pdf) — Local Harvest Bake | MAIN_DISH | 6 | 7 | 3 | 0/6/0 |
| [CACFP6-TABBOULEH](https://fns-prod.azureedge.us/sites/default/files/resource-files/Tabbouleh_6_Servings.pdf) — Tabbouleh | SIDE_DISH | 6 | 13 | 3 | 0/12/0 |
| [CACFP6-HONEY-LIME-CHICKEN](https://fns-prod.azureedge.us/sites/default/files/resource-files/Honey_Lime_Chicken_6_Servings.pdf) — Honey Lime Chicken | MAIN_DISH | 6 | 6 | 3 | 0/6/0 |
| [CACFP6-CREAMY-COLESLAW](https://fns-prod.azureedge.us/sites/default/files/resource-files/Creamy_Coleslaw_6_Servings.pdf) — Creamy Coleslaw | SIDE_DISH | 6 | 11 | 1 | 0/11/0 |
| [TNC6-EGGS-SPINACH](https://fns-prod.azureedge.us/sites/default/files/resource-files/tnc-eggs.pdf) — Scrambled Eggs with Spinach | BREAKFAST | 6 | 3 | 9 | 1/2/0 |
| [TNC6-APPLESAUCE](https://fns-prod.azureedge.us/sites/default/files/resource-files/tnc-applesauce.pdf) — Applesauce | SNACK | 6 | 2 | 7 | 0/1/0 |
| [TNC6-CORN-ZUCCHINI-PANCAKES](https://www.fns.usda.gov/sites/default/files/resource-files/tnc-pancakes.pdf) — Corn and Zucchini Pancakes | BREAKFAST | 6 | 8 | 12 | 1/7/0 |
| [HARV6-ROASTED-POTATOES](https://fns-prod.azureedge.us/sites/default/files/resource-files/HarvestofRecipes.pdf) — Roasted Potatoes | SIDE_DISH | 6 | 7 | 3 | 0/7/0 |
| [HARV6-FRESH-TOMATO-SALSA](https://fns-prod.azureedge.us/sites/default/files/resource-files/HarvestofRecipes.pdf) — Fresh Tomato Salsa | CONDIMENT | 6 | 7 | 1 | 0/7/0 |
| [HARV6-GARDEN-PASTA-SALAD](https://fns-prod.azureedge.us/sites/default/files/resource-files/HarvestofRecipes.pdf) — Garden Pasta Salad | SIDE_DISH | 6 | 8 | 1 | 0/8/0 |
| [SNAP6-SPINACH-APPLE-SALAD](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes) — Spinach Salad with Apples and Raisins | SIDE_DISH | 6 | 7 | 0 | 1/6/0 |
| [SNAP6-PEACH-CRISP](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/summer-recipes) — Peach Crisp | DESSERT | 6 | 7 | 4 | 1/6/0 |
| [SNAP6-SEARED-GREENS](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/spring-recipes) — Seared Greens | SIDE_DISH | 6 | 7 | 2 | 0/6/0 |
| [SNAP8-SOMALI-SUMMER-SALAD](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/summer-recipes) — Somali Summer Salad | SIDE_DISH | 8 | 6 | 1 | 0/6/0 |
| [SNAP1-MICROWAVE-BAKED-POTATO](https://snaped.fns.usda.gov/snap/recipes/Microwave_Baked_Potato.pdf) — Microwave Baked Potato | SIDE_DISH | 1 | 1 | 3 | 0/1/0 |
| [WIC4-BUTTERNUT-SOUP](https://wicworks.fns.usda.gov/recipe/butternut-squash-soup) — Butternut Squash Soup | SOUP | 4 | 4 | 7 | 0/4/0 |
| [WIC1-OVERNIGHT-OATS-CINNAMON-APPLE](https://wicworks.fns.usda.gov/recipe/overnight-oats-cinnamon-apple) — Overnight Oats with Cinnamon Apple | BREAKFAST | 1 | 5 | 5 | 1/4/0 |
| [WIC4-ROASTED-CARROTS](https://wicworks.fns.usda.gov/recipe/roasted-carrots-3-ways) — Roasted Carrots — standard version | SIDE_DISH | 4 | 5 | 7 | 0/5/0 |
| [SNAP3-GRILLED-FRUIT](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/grilled-fruit) — Grilled Fruit | DESSERT | 3 | 3 | 1 | 0/3/0 |
| [WIC2-SPINACH-CAULIFLOWER-SMOOTHIE](https://wicworks.fns.usda.gov/recipe/spinach-and-cauliflower-smoothie) — Spinach and Cauliflower Smoothie | SNACK | 2 | 7 | 4 | 1/6/0 |
| [SNAP4-PEAR-ORANGE-SAUCE](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes) — Pear in Orange Sauce | DESSERT | 4 | 3 | 1 | 1/2/0 |
| [SNAP4-SPRING-VEGETABLE-SAUTE](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/spring-recipes) — Spring Vegetable Saute | SIDE_DISH | 4 | 12 | 1 | 0/11/0 |
| [SNAP8-HOMEMADE-MASHED-POTATOES](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/homemade-mashed-potatoes) — Homemade Mashed Potatoes | SIDE_DISH | 8 | 6 | 2 | 0/5/0 |
| [SNAP8-APPLE-CARROT-SOUP](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/apple-carrot-soup) — Apple Carrot Soup | SOUP | 8 | 6 | 1 | 0/5/0 |
| [SNAP6-WALDORF-SALAD](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes) — Waldorf Salad | SIDE_DISH | 6 | 7 | 2 | 1/6/0 |
| [SNAP4-BROWN-RICE-PILAF](https://snaped.fns.usda.gov/resources/recipes-and-menus/healthy-thrifty-holiday-menus/valentines-day) — Brown Rice Pilaf | SIDE_DISH | 4 | 6 | 2 | 0/5/0 |
| [SNAP5-KALE-NUTS-RAISINS](https://snaped.fns.usda.gov/node/1861) — Kale with Nuts and Raisins | SIDE_DISH | 5 | 5 | 3 | 0/5/0 |
| [SNAP4-BRAISED-CHICKEN-SPINACH](https://snaped.fns.usda.gov/sites/default/files/documents/howmuch_foodandphysicalactivitychecklist.pdf) — Braised Chicken Thighs with Spinach | MAIN_DISH | 4 | 10 | 2 | 0/9/0 |
| [SNAP4-DILLED-FISH-FILLETS](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/dilled-fish-fillets) — Dilled Fish Fillets | MAIN_DISH | 4 | 4 | 3 | 0/4/0 |

## All 25 replacements

Pairs identify technical corpus slots, **not** nutrition-equivalent servings or consumer substitutions. Failure means evidence did not clear the required form in the reviewed panel, not a claim that no Russian shop sells it.

| Removed source ID | Selected source ID | Decision evidence |
| --- | --- | --- |
| CACFP6-SOUTHWEST-TOFU-SCRAMBLE | SNAP4-BRAISED-CHICKEN-SPINACH | Firm tofu form not cleared; retain a source-backed protein main using ordinary raw chicken thigh and fresh spinach. |
| CACFP6-SPICED-OATMEAL | WIC1-OVERNIGHT-OATS-CINNAMON-APPLE | Trans-fat-free margarine and vanilla requirements not cleared; source-explicit optional vanilla omission in an independently sourced oat breakfast. |
| CACFP6-STRAWBERRY-SMOOTHIE-BOWL | WIC2-SPINACH-CAULIFLOWER-SMOOTHIE | Required frozen strawberry and vanilla forms not cleared; retain a distinct smoothie with evidenced frozen cauliflower and source-specified milk. |
| CACFP6-BAKED-SWEET-POTATOES-APPLES | SNAP4-PEAR-ORANGE-SAUCE | Frozen unsweetened green apples, orange concentrate, trans-fat-free margarine and vanilla not cleared; select quantified fresh-fruit cooked dessert. |
| CACFP6-ORANGE-GLAZED-CARROTS | WIC4-ROASTED-CARROTS | Frozen carrot, orange concentrate, trans-fat-free margarine and vanilla forms not cleared; fresh whole carrots cut during source preparation need no pre-cut retail product. |
| CACFP6-PIZZA-GREEN-BEANS | SNAP4-SPRING-VEGETABLE-SAUTE | Canned no-salt green beans not cleared; independent source permits generic green beans, with reviewed frozen member, sweet red onion and young potato forms. |
| CACFP6-SAUTEED-SPINACH-TOMATOES | SNAP6-SEARED-GREENS | Required trans-fat-free margarine not cleared; retain independently sourced cooked greens without that restriction. |
| CACFP6-SPANISH-RICE | SNAP4-BROWN-RICE-PILAF | Low-sodium beef broth, chili blend and parboiled long-grain brown rice not cleared; independent water-based brown-rice source needs no invented broth substitution. |
| CACFP6-CHICKEN-FAJITA | SNAP4-DILLED-FISH-FILLETS | Cooked frozen chicken strips, ancho, low-sodium salsa and whole-wheat tortilla forms not cleared; introduce a verified frozen-cod main with four quantified ingredients. |
| CACFP6-RICE-VEGETABLE-CASSEROLE | HARV6-ROASTED-POTATOES | Reduced-fat cheddar, low-moisture part-skim mozzarella, low-sodium broth, trans-fat-free margarine and specified parboiled rice not cleared; independently sourced roasted potato side. |
| CACFP6-VEGETABLE-CHILI | WIC4-BUTTERNUT-SOUP | Ancho, low-sodium canned kidney beans, no-salt crushed tomato and low-sodium vegetable broth not cleared; select a quantified roast-and-blend vegetable soup. |
| CACFP6-VEGETABLE-FRITTATA | TNC6-CORN-ZUCCHINI-PANCAKES | Reduced-fat cheddar not cleared; independent egg/vegetable pancake source uses ordinary ingredients and an explicit frozen-corn alternative. |
| CACFP6-CARROT-RAISIN-SALAD | SNAP8-SOMALI-SUMMER-SALAD | Unsweetened pineapple canned in 100% juice not cleared; independent fresh-produce salad has explicit optional salt/pepper omission. |
| CACFP6-MACARONI-SALAD | HARV6-GARDEN-PASTA-SALAD | Whole-wheat pasta and canned pimientos not cleared; generic macaroni source preserved, including its cooked-volume quantity rather than invented dry weight. |
| CACFP6-MARINATED-BLACK-BEAN-SALAD | HARV6-FRESH-TOMATO-SALSA | Low-sodium canned black beans/salsa, ancho and reduced-fat cheddar not cleared; fresh tomato salsa provides a distinct condiment/vegetable preparation. |
| CACFP6-QUICHE-SELF-FORMING-CRUST | SNAP1-MICROWAVE-BAKED-POTATO | Frozen liquid whole egg and reduced-fat cheddar not cleared; source-verified whole-potato microwave method adds a short single-serving preparation, not an invented quiche adaptation. |
| CACFP6-ROPA-VIEJA | SNAP8-APPLE-CARROT-SOUP | Low-sodium beef broth and parboiled brown rice not cleared; independently sourced long-simmer vegetable/fruit soup. No beef or nutritional equivalence claimed. |
| CACFP6-CORN-PUDDING | SNAP6-PEACH-CRISP | White whole-grain cornmeal and no-salt cream-style corn not cleared; add a source-backed baked fruit/oat dessert. |
| CACFP6-GREEN-BEANS-POTATOES-SMOKED-TURKEY | SNAP5-KALE-NUTS-RAISINS | Smoked cooked turkey drumstick and trans-fat-free margarine not cleared; frozen green beans were initially unresolved and later evidenced, which alone does not clear the remaining recipe forms. |
| CACFP6-TUNA-SALAD-SANDWICH | SNAP6-WALDORF-SALAD | Whole-wheat roll and canned tuna-in-water forms not cleared; independently sourced apple/walnut salad, not a tuna substitution claim. |
| CACFP6-TUSCAN-GRILL-CHEESE | SNAP3-GRILLED-FRUIT | Whole-wheat bread, low-fat mozzarella and trans-fat-free margarine not cleared; independent grilling method with three ordinary fresh fruits. |
| CACFP6-ASIAN-TUNA-BURGER | SNAP6-SPINACH-APPLE-SALAD | Panko breadcrumbs, whole-wheat roll and low-sodium soy sauce not cleared; independent raw-leaf salad with reviewed cold-use canola oil. |
| CACFP6-BEAN-BURRITO-BOWL | SNAP8-HOMEMADE-MASHED-POTATOES | Low-sodium canned pinto beans, reduced-fat cheddar and parboiled brown rice not cleared; independently sourced boiled-and-mashed potato side. |
| CACFP6-VEGETABLE-FRITTATA-BITES | TNC6-EGGS-SPINACH | Mandatory exclusion of ICN 2024 card: rights posture not cleared. Direct FNS Team Nutrition source has reviewed provenance and copying statement; no public-domain claim. |
| CACFP6-CAULIFLOWER-RICE | TNC6-APPLESAUCE | Mandatory exclusion of ICN 2024 card: rights posture not cleared. Direct FNS Team Nutrition source has reviewed provenance and copying statement; no public-domain claim. |

Keep unchanged source identities: `CACFP6-CORN-EDAMAME-BLEND`, `CACFP6-LOCAL-HARVEST-BAKE`, `CACFP6-TABBOULEH`, `CACFP6-HONEY-LIME-CHICKEN`, `CACFP6-CREAMY-COLESLAW`.

Other screened candidates and their exact failures remain in `candidate-review-v2.json` through `v5`. Required unquantified seasoning, non-existing global codes (e.g. WATERMELON), materially different unverified forms and source-access/notice gaps were not patched by invention. Optional omissions and source-explicit alternatives are separately recorded.

## Market evidence and exact one-chain forms

Method: current official neutral/chain-wide product or category plus official SPB/LO chain presence; current indexed official wording remains reviewable when live access fails. A regional delivery listing qualifies only when actual retailer, region and product/form are identified. No momentary stock claim. No other-city SKU, expired flyer, access-block-as-absence or wrong-form evidence qualifies. See [methodology](market-methodology.md) and the [Orchestrator clarification](https://github.com/Mitronomik/family-food-os/issues/12#issuecomment-5550629546).

All five baseline chains are represented in each form review. **82 non-water forms: 3 RU_MASS_MARKET, 79 RU_AVAILABLE, 0 SPECIALTY_OR_UNCLEAR.** Chain counts: **72 one-chain / 7 two-chain / 3 three-chain**. One/two-chain forms retain explicit ordinary-retail plausibility and remain RU_AVAILABLE.

The research ledger contains **172 raw observations / 166 unique code-chain-URL records**, **129 AVAILABLE / 37 UNCERTAIN**, with 6 duplicate aliases retained. AVAILABLE research observations by chain: Пятёрочка 3, Перекрёсток 0, Лента 113, О'КЕЙ 0, Магнит 13. This includes rejected candidates; it is not a final-corpus SKU count. Zero positive evidence does not mean product absence. Evidence is heavily concentrated in Lenta, an explicit limitation.

Conservative code-level roll-up (the least-supported selected form wins): **2 RU_MASS_MARKET / 76 RU_AVAILABLE / 1 household WATER exemption**. Code-level roll-up must not erase separately reviewed purchase forms.

The following **72 rows are the exact one-retailer-only forms**. Links are the underlying official product/category evidence, paired with SPB/LO presence in the linked research record and matrix. Full wording, date, caveats and source applicability are preserved there.

| FoodIngredient / review form ID | Actual purchase form | Only qualifying chain | Official evidence |
| --- | --- | --- | --- |
| ALMONDS_RAW / ALMONDS_RAW | Plain unroasted unsalted almond kernels; chop/slice as source preparation | LENTA | [research-lenta-okey-v6.json:1](https://lenta.com/product/mindal-sushenyjj-ves-60374/) |
| APPLE / APPLE | Whole fresh apples; washing, peeling where specified, coring and chopping are preparation | LENTA | [research-lenta-okey-v3.json:27](https://lenta.com/catalog/yabloki-18244) |
| APPLE_CIDER_VINEGAR / APPLE_CIDER_VINEGAR | Plain apple cider vinegar; source vinegar member selection retained | LENTA | [research-lenta-okey-v3.json:22](https://lenta.com/product/uksus-yablochnyjj-ispaniya-250ml-479839/) |
| ASPARAGUS / ASPARAGUS | Fresh asparagus; wash and trim | LENTA | [research-lenta-okey-v4.json:6](https://lenta.com/product/sparzha-svezhaya-ves-714874/) |
| BAKING_POWDER / BAKING_POWDER | Baking powder, not baking soda | LENTA | [research-lenta-okey-v3.json:24](https://lenta.com/product/razryhlitel-testa-rossiya-10-gr-427560/) |
| BANANA / BANANA | Fresh banana; peel and slice | LENTA | [research-lenta-okey-v6.json:2](https://lenta.com/product/011230/) |
| BELL_PEPPER_GREEN / BELL_PEPPER_GREEN | Fresh sweet green bell pepper; dice/chop | LENTA | [research-lenta-okey-v4.json:13](https://lenta.com/product/perec-zelenyjj-ves-41206/) |
| BELL_PEPPER_RED / BELL_PEPPER_RED | Fresh sweet red bell pepper; dice/chop | MAGNIT | [research-magnit-v2.json:9](https://magnit.ru/product/1444282020-perets_krasnyy?shopCode=690101&shopType=1) |
| BLACK_PEPPER / BLACK_PEPPER | Ground black pepper | LENTA | [research-lenta-okey-v2.json:34](https://lenta.com/product/priprava-perec-chernyjj-molotyjj-vetnam-20g-611678/) |
| BUTTER_UNSALTED / BUTTER_UNSALTED | Unsalted butter; choose explicit source butter alternative where offered | LENTA | [research-lenta-okey-v4.json:7](https://lenta.com/product/maslo-slivochnoe-nesolenoe-825-bez-zmzh-rossiya-100g-673176/) |
| BUTTERNUT_SQUASH / BUTTERNUT_SQUASH | Fresh butternut squash; peel, seed and cube as specified | LENTA | [research-lenta-okey-v2.json:7](https://lenta.com/catalog/ovoshchi-146/) |
| CABBAGE_RED / CABBAGE_RED | Fresh red cabbage; shred/chop | LENTA | [research-x5-v3.json:4](https://lenta.com/product/kapusta-krasnokochannaya-ves-31723/) |
| CANOLA_OIL / CANOLA_OIL | Plain food-grade rapeseed/canola oil for cold salad dressing only | LENTA | [research-lenta-okey-v6.json:5](https://lenta.com/product/maslo-rapsovoe-neraf-st-rossiya-250ml-707922/) |
| CAULIFLOWER / CAULIFLOWER__FROZEN | Plain frozen cauliflower florets for smoothie | LENTA | [research-lenta-okey-v7.json:1](https://lenta.com/product/kapusta-cvetnaya-zam-400g-645567/) |
| CELERY / CELERY | Fresh celery stalks, not celeriac root; slice/dice | LENTA | [research-lenta-okey-v3.json:13](https://lenta.com/product/029126-29126/) |
| CHICKEN_THIGH / CHICKEN_THIGH | Raw boneless skinless chicken thigh for Honey Lime Chicken | LENTA | [research-x5-v3.json:3](https://lenta.com/product/file-bedra-cb-bez-kozhi-ohl-ves-rossiya-696329/) |
| CHICKEN_THIGH / CHICKEN_THIGH__BONE_IN | Plain raw chilled bone-in chicken thigh; remove skin as source preparation | LENTA | [research-lenta-okey-v7.json:4](https://lenta.com/product/bedro-kurinoe-nk-ohl-fas-ves-rossiya-199548/) |
| CILANTRO / CILANTRO | Fresh cilantro leaves; chop | LENTA | [research-lenta-okey-v3.json:12](https://lenta.com/product/kinza-svezhaya-up-50g-582308/) |
| CINNAMON_GROUND / CINNAMON_GROUND | Ground cinnamon | LENTA | [research-lenta-okey-v2.json:36](https://lenta.com/product/korica-lenta-molotaya-rossiya-15g-550705/) |
| COD_ATLANTIC / COD_ATLANTIC | Plain raw frozen Atlantic cod fillets without skin/bones | LENTA | [research-lenta-okey-v7.json:12](https://lenta.com/product/treska-file-atlanticheskaya-bk-zam-rossiya-400g-889794/) |
| CORIANDER_SEED / CORIANDER_SEED | Ground coriander seeds; source requires ground spice, not whole seed or leaf | LENTA | [research-lenta-okey-v7.json:2](https://lenta.com/product/pryanost-koriandr-molotyjj-rossiya-10g-721265/) |
| CORN_SWEET / CORN_SWEET | Plain frozen sweet corn kernels, selected among source fresh/frozen/canned options; thaw/drain where specified | LENTA | [research-lenta-okey-v4.json:18](https://lenta.com/product/kukuruza-morozko-green-v-zernah-rossiya-400g-549203/) |
| CRANBERRIES_DRIED / CRANBERRIES_DRIED | Dried cranberries; ordinary sweetened dried product fits generic source | LENTA | [research-lenta-okey-v3.json:21](https://lenta.com/product/640069-640069/) |
| CUMIN_GROUND / CUMIN_GROUND | Ground cumin (zira), not caraway or whole-only seed evidence | LENTA | [research-x5-v3.json:8](https://lenta.com/product/kumin-zira-molotaya-umnaya-pokupka-indiya-10g-454150/) |
| DILL_DRIED / DILL_DRIED | Dried dill, selected explicit source alternative to fresh with source dry quantity | LENTA | [research-lenta-okey-v4.json:14](https://lenta.com/product/ukrop-sushenyjj-rossiya-10g-177336/) |
| EDAMAME_FROZEN / EDAMAME_FROZEN | Plain frozen edamame beans; source requires thawed and drained, then sauteed | LENTA | [research-lenta-okey-v3.json:1](https://lenta.com/product/boby-edamame-zam-rossiya-400g-909897/) |
| FLOUR_WHEAT / FLOUR_WHEAT | Ordinary refined wheat flour | LENTA | [research-lenta-okey-v4.json:16](https://lenta.com/product/muka-makfa-vs-rossiya-1kg-073012-73012/) |
| FLOUR_WHOLE_WHEAT / FLOUR_WHOLE_WHEAT | Whole-wheat flour, not ordinary refined flour | LENTA | [research-lenta-okey-v3.json:10](https://lenta.com/product/muka-pshenichnaya-celnozernovaya-rossiya-1000g-888176) |
| GARLIC_POWDER / GARLIC_POWDER | Plain dried ground garlic powder | LENTA | [research-lenta-okey-v4.json:15](https://lenta.com/product/chesnok-sushenyjj-molotyjj-rossiya-10g-561764/) |
| GINGER / GINGER | Fresh ginger root; peel and slice | LENTA | [research-lenta-okey-v2.json:9](https://lenta.com/catalog/ovoshchi-146/) |
| GREEN_BEANS / GREEN_BEANS__FROZEN | Plain frozen green beans | LENTA | [research-lenta-okey-v8.json:5](https://lenta.com/product/fasol-struchkovaya-zam-400g-173144/) |
| GREEN_ONION / GREEN_ONION | Fresh green onion/scallions; trim/chop | LENTA | [research-lenta-okey-v4.json:11](https://lenta.com/product/luk-zelenyjj-svezhijj-up-50g-584159/), [research-x5-v3.json:5](https://lenta.com/product/luk-zelenyjj-svezhijj-up-50g-584159/) |
| HONEY / HONEY | Natural honey | LENTA | [research-lenta-okey-v3.json:7](https://lenta.com/product/med-naturalnyjj-cvetochnyjj-dikorosy-rossiya-700g-916746/) |
| KALE / KALE | Fresh kale leaves; remove stems/chop; selected explicit source leafy-green option | LENTA | [research-lenta-okey-v6.json:9](https://lenta.com/product/salat-kejjl-rossiya-50g-663970/) |
| LEMON / LEMON | Fresh whole lemons; squeezing juice or grating zest is source preparation | LENTA | [research-lenta-okey-v3.json:9](https://lenta.com/product/limony-ves-94429), [research-lenta-okey-v7.json:10](https://lenta.com/product/limony-ves-94429) |
| LIME / LIME | Fresh whole lime for source zest | LENTA | [research-x5-v3.json:6](https://lenta.com/product/lajjm-3sht-771025/) |
| LIME_JUICE / LIME_JUICE | Fresh-squeezed lime juice prepared from purchased whole limes | LENTA | [research-lenta-okey-v4.json:19](https://lenta.com/product/lajjmy-ves-32365/), [research-x5-v3.json:7](https://lenta.com/product/lajjm-3sht-771025/) |
| MARGARINE / MARGARINE | Ordinary baking margarine; melt where source requires; not butter replacement | LENTA | [research-lenta-okey-v4.json:10](https://lenta.com/product/margarin-dvypechki-72-rossiya-200g-686419/) |
| MAYONNAISE_LOW_FAT / MAYONNAISE_LOW_FAT | Light reduced-fat mayonnaise-family product20%; not full-fat mayonnaise | LENTA | [research-lenta-okey-v2.json:19](https://lenta.com/product/sous-majjoneznyjj-legkijj-20-dojj-pak-s-doz-rossiya-400g-214314/) |
| MILK_1_PERCENT / MILK_1_PERCENT | Unflavoured cow milk1% fat; exact1% where source fixes it, selected lowfat option otherwise | LENTA | [research-lenta-okey-v2.json:14](https://lenta.com/product/moloko-1-pet-bez-zmzh-rossiya-900g-565966/) |
| MINT_FRESH / MINT_FRESH | Fresh mint leaves, not dried mint or mint tea | LENTA | [research-lenta-okey-v3.json:11](https://lenta.com/product/myata-svezhaya-up-50g-582274/) |
| OATS_ROLLED / OATS_ROLLED__QUICK | Plain quick-cooking rolled oats for Peach Crisp | LENTA | [research-lenta-okey-v5.json:4](https://lenta.com/product/hlopya-gerkules-rossiya-400g-339042/) |
| OLIVE_OIL / OLIVE_OIL | Pure olive oil; no non-olive blend | LENTA | [research-lenta-okey-v4.json:9](https://lenta.com/product/maslo-olivkovoe-clasico-nraf-stb-ispaniya-250ml-153995/), [research-x5-v3.json:1](https://lenta.com/product/maslo-olivkovoe-neraf-extra-virgin-ispaniya-250ml-906830/) |
| ONION_RED / ONION_RED__SWEET_YALTA | Sweet red Yalta onion, raw whole bulbs | LENTA | [research-lenta-okey-v8.json:1](https://lenta.com/product/luk-yaltinskijj-ves-300672/) |
| ONION_YELLOW / ONION_YELLOW | Fresh ordinary yellow/brown bulb onion; peel/chop | MAGNIT | [research-magnit-v2.json:2](https://magnit.ru/product/9072651204-luk_repchatyy?shopCode=781202&shopType=1) |
| ORANGE / ORANGE | Raw whole oranges squeezed to prepare 100% pure orange juice | LENTA | [research-lenta-okey-v9.json:2](https://lenta.com/product/apelsiny-dlya-soka-713677/) |
| PARSLEY / PARSLEY | Fresh parsley leaves; chop | LENTA | [research-lenta-okey-v2.json:24](https://lenta.com/product/petrushka-zl-ves-590476/) |
| PARSLEY_DRIED / PARSLEY_DRIED | Plain dried parsley | LENTA | [research-lenta-okey-v2.json:25](https://lenta.com/catalog/maslo-sousy-specii-20824/page/15/) |
| PASTA_DRY / PASTA_DRY | Ordinary dry macaroni; source specifies cooked½cup final ingredient, not½cup dry input | LENTA | [research-lenta-okey-v4.json:5](https://lenta.com/product/makarony-rozhki-rossiya-450g-117841/) |
| PEACH / PEACH | Fresh peaches; slice | LENTA | [research-lenta-okey-v4.json:12](https://lenta.com/product/persik-otbornyjj-2sht-879014) |
| PEAR / PEAR | Whole raw pears, select four medium; peel/cut during preparation | LENTA | [research-lenta-okey-v9.json:1](https://lenta.com/product/grusha-konferenc-ves-44185/) |
| PINEAPPLE / PINEAPPLE | Fresh whole raw pineapple, chunk during preparation | LENTA | [research-lenta-okey-v8.json:4](https://lenta.com/product/ananas-ves-422644/) |
| PORK_LOIN / PORK_LOIN | Plain raw boneless pork loin, selected lean pork member; cut into chunks | LENTA | [research-lenta-okey-v4.json:24](https://lenta.com/product/svinina-korejjka-beskostnaya-polufabrikat-ohlazhdennyjj-fasovka-rossiya-56030/) |
| POTATO / POTATO | Fresh potatoes; peel/cube as specified | LENTA | [research-lenta-okey-v4.json:4](https://lenta.com/product/kartofel-belyjj-mytyjj-ves-118887/) |
| POTATO / POTATO__YOUNG | Young/new raw potato tubers, select tiny | LENTA | [research-lenta-okey-v8.json:2](https://lenta.com/product/kartofel-molodojj-belyjj-ves-rossiya-45520/) |
| QUINOA / QUINOA | Plain dry quinoa; rinse/cook as specified | LENTA | [research-lenta-okey-v2.json:31](https://lenta.com/product/kinoa-premium-club-bezhevaya-rossiya-400g-717713/) |
| RADISH / RADISH | Fresh raw radish | LENTA | [research-lenta-okey-v8.json:3](https://lenta.com/product/redis-500g-172378/) |
| RAISINS_GOLDEN / RAISINS_GOLDEN | Plain light/golden raisins; source generic raisin member selection | LENTA | [research-lenta-okey-v3.json:3](https://lenta.com/product/izyum-svetlyjj-ves-099410/) |
| RICE_BROWN / RICE_BROWN | Dry brown rice | LENTA | [research-lenta-okey-v2.json:32](https://lenta.com/catalog/krupy-bobovye-27/page/4) |
| ROSEMARY_DRIED / ROSEMARY_DRIED | Plain dried rosemary | LENTA | [research-lenta-okey-v7.json:6](https://lenta.com/product/priprava-rozmarin-rossiya-10g-667009/) |
| SALT / SALT | Ordinary food table salt; iodized-specific source option separately reviewed | LENTA | [research-lenta-okey-v4.json:17](https://lenta.com/product/sol-ekstra-pishchevaya-banka-pet-rossiya-500g-627142/), [research-lenta-okey-v7.json:3](https://lenta.com/product/sol-jjodirovannaya-pishchevaya-pomol-1-vs-rossiya-1000g-86051/), [research-x5-v3.json:2](https://lenta.com/product/sol-pomol-1-kup-rossiya-1kg-491061/) |
| SALT / SALT__IODIZED | Iodized food salt selected from explicit source kosher-or-iodized alternative | LENTA | [research-lenta-okey-v7.json:3](https://lenta.com/product/sol-jjodirovannaya-pishchevaya-pomol-1-vs-rossiya-1000g-86051/) |
| SESAME_OIL / SESAME_OIL | Pure sesame oil suitable for saute, reviewed ELEYA unrefined 250ml form | LENTA | [research-lenta-okey-v8.json:6](https://lenta.com/product/maslo-kunzhutnoe-neraf-st-rossiya-250ml-730027/) |
| SESAME_SEEDS / SESAME_SEEDS | Plain raw sesame seeds, toasted at home using explicit source method | LENTA | [research-lenta-okey-v3.json:14](https://lenta.com/product/496341-496341/) |
| SPINACH / SPINACH | Fresh spinach leaves; rinse/chop as specified | LENTA | [research-lenta-okey-v4.json:2](https://lenta.com/product/shpinat-svezhijj-zl-ves-590447/) |
| SUNFLOWER_OIL / SUNFLOWER_OIL | Refined sunflower cooking oil, selected source generic vegetable-oil member | LENTA | [research-lenta-okey-v4.json:8](https://lenta.com/product/maslo-podsolnechnoe-raf-dezodor-vysshijj-sort-rossiya-1000ml-62861/) |
| SWEET_POTATO / SWEET_POTATO | Fresh sweet potatoes; peel/cube as specified | LENTA | [research-lenta-okey-v2.json:8](https://lenta.com/catalog/ovoshchi-146/) |
| THYME_DRIED / THYME_DRIED | Plain dried thyme | LENTA | [research-lenta-okey-v2.json:23](https://lenta.com/product/timyan-chabrec-izmelchennyjj-polsha-7g-657638/) |
| WALNUTS_RAW / WALNUTS_RAW | Plain unroasted unsalted walnut kernels; chop | LENTA | [research-lenta-okey-v6.json:14](https://lenta.com/product/greckijj-oreh-rossiya-200g-431488/) |
| YOGURT_GREEK_NONFAT / YOGURT_GREEK_NONFAT | Plain nonfat-family Greek yogurt from skim milk, residual0.1% fat; not mathematical zero | LENTA | [research-lenta-okey-v6.json:15](https://lenta.com/product/jjogurt-grecheskijj-obezzhirennyjj-01-rossiya-130g-584769/) |
| YOGURT_PLAIN_LOW_FAT / YOGURT_PLAIN_LOW_FAT | Plain unflavoured low-fat yogurt1.5%; no fruit/vanilla/sugar-flavoured alternative | LENTA | [research-lenta-okey-v3.json:4](https://lenta.com/product/jjogurt-naturalnyjj-15-st-bez-zmzh-rossiya-200g-212269/) |
| ZUCCHINI / ZUCCHINI | Fresh zucchini/courgette; trim/shred as specified | LENTA | [research-lenta-okey-v4.json:3](https://lenta.com/product/kabachki-cukkini-ves-55647/) |

### Multi-chain forms

| Form ID | Classification | Qualifying chains |
| --- | --- | --- |
| BEET | RU_AVAILABLE | LENTA, MAGNIT |
| BULGUR | RU_AVAILABLE | LENTA, MAGNIT |
| CABBAGE_GREEN | RU_AVAILABLE | LENTA, MAGNIT |
| CARROT | RU_AVAILABLE | LENTA, MAGNIT |
| CUCUMBER | RU_AVAILABLE | LENTA, MAGNIT |
| EGG | RU_MASS_MARKET | PYATEROCHKA, LENTA, MAGNIT |
| GARLIC | RU_AVAILABLE | LENTA, MAGNIT |
| OATS_ROLLED | RU_MASS_MARKET | PYATEROCHKA, LENTA, MAGNIT |
| SUGAR | RU_MASS_MARKET | PYATEROCHKA, LENTA, MAGNIT |
| TOMATO | RU_AVAILABLE | LENTA, MAGNIT |

## Rights and provenance by source collection

Each exact selected document/recipe section was reviewed with attribution, notice findings and a downloaded-artifact SHA-256. This applies the **already-approved direct-FNS project risk classification** in issue #12 and the localization policy. It does **not** infer public domain from a .gov address/USDA branding, or unrestricted commercial/derivative rights from downloadability. No selected unresolved rights restriction was found in the reviewed source documents; this is not a new legal opinion. No source photos, logos or trademarks are imported as product assets.

| Direct-FNS source collection | Recipes | Reviewable example (each recipe has its own evidence) |
| --- | ---: | --- |
| USDA FNS CACFP Home Childcare — Side Dishes | 4 | [Corn and Edamame Blend](https://fns-prod.azureedge.us/sites/default/files/resource-files/Corn_Edamame_Blend_6_Servings.pdf) |
| USDA FNS CACFP Home Childcare — Main Dishes | 1 | [Honey Lime Chicken](https://fns-prod.azureedge.us/sites/default/files/resource-files/Honey_Lime_Chicken_6_Servings.pdf) |
| USDA FNS Team Nutrition Cooks! — Family Handouts | 3 | [Scrambled Eggs with Spinach](https://fns-prod.azureedge.us/sites/default/files/resource-files/tnc-eggs.pdf) |
| USDA FNS FDPIR — A Harvest of Recipes with USDA Foods (FNS-430) | 3 | [Roasted Potatoes](https://fns-prod.azureedge.us/sites/default/files/resource-files/HarvestofRecipes.pdf) |
| USDA FNS SNAP-Ed — Recipes and seasonal menus | 13 | [Spinach Salad with Apples and Raisins](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes) |
| USDA FNS SNAP-Ed — Recipe Cards for Educators | 1 | [Microwave Baked Potato](https://snaped.fns.usda.gov/snap/recipes/Microwave_Baked_Potato.pdf) |
| USDA FNS WIC Works — Recipes | 4 | [Butternut Squash Soup](https://wicworks.fns.usda.gov/recipe/butternut-squash-soup) |
| USDA FNS — Food and Physical Activity Checklist | 1 | [Braised Chicken Thighs with Spinach](https://snaped.fns.usda.gov/sites/default/files/documents/howmuch_foodandphysicalactivitychecklist.pdf) |

Team Nutrition Cooks! explicitly permits downloading and copying; that statement is not widened into an unlimited commercial grant. Harvest acknowledgments and WIC/SNAP contributors are preserved; the educator card retains Montana State attribution. Detailed review classes, multiple evidence URLs and notice findings are in `recipe-corpus.json` and `recipe-review-metadata.json`. Both ICN 2024 cards remain excluded, regardless of market status. **No unresolved selected-source rights blocker.**

## Equipment

**96 rows, 33 normalized codes**, deterministic first explicit selected-use order per recipe. Evidence excerpts and source page/step positions are retained. Corn/edamame selects the source-explicit raw-sesame home-toasting alternative, adding STOCK_POT. Named preparation tools in recipe-specific supporting directions qualify; inferred tools, serving-only utensils and disposable supplies do not.

`BAKING_PAN`, `BAKING_SHEET`, `BLENDER`, `BOWL`, `COLANDER`, `CUTTING_BOARD`, `DOUBLE_BOILER`, `FINE_MESH_STRAINER`, `FORK`, `GRATER`, `IMMERSION_BLENDER`, `KNIFE`, `LID`, `MEASURING_CUP`, `MEASURING_SPOON`, `MICROWAVE`, `MICROWAVE_SAFE_PLATE`, `NONSTICK_SAUCEPAN`, `OVEN`, `PLATE`, `POT`, `POTATO_MASHER`, `RESEALABLE_CONTAINER`, `RICE_COOKER`, `SAUCEPAN`, `SKEWER`, `SKILLET`, `SPATULA`, `SPOON`, `STOCK_POT`, `STOVETOP`, `VEGETABLE_PEELER`, `WHISK`.

## Source limitations and handback boundaries

- Garden Pasta Salad retains ½ cup **cooked** macaroni, never ½ cup dry or an invented raw/cooked yield.
- Spinach/Apple Salad retains literal `2/3 package (10 ounces)`; package-to-grams normalization is not invented.
- Braised Chicken lists quantified salt and pepper but omits their application in the directions; no step is fabricated. Source time headers remain distinct from individual timed stages.
- TNC pancakes supplementary directions mention extra oil if needed without a quantity; no additional mandatory quantity is invented.
- Generic green beans may select the evidenced plain frozen member where the source does not require fresh; no claim that the source explicitly says frozen, and no invented thawing time.
- Source-specified prepared citrus juice maps to existing whole-fruit purchase concepts, retaining juice volume without fabricated fruit counts or extraction yields.
- Standard Roasted Carrots allows generic vegetable oil; olive oil is a selected member, not a false claim that standard directions require the spicy variant.
- Some recipe timings are unknown; nulls/stage times are not manufactured into total or active times.
- This is an ingestion/source fixture, not a balanced weekly plan, cost estimate, tested taste/menu, health claim or storage/freezer recommendation. Later PR4 must review production quantity normalization without inventing authority.

## Verification

| Check | Exact result |
| --- | --- |
| `backend/.venv/bin/python scripts/validate_pr4_data2.py` | PASS: final DATA2 gates |
| DATA2 + historical PR4-DATA coverage tests | 66 passed in 1.26s |
| Historical PR4-DATA + FoodIngredient affected regressions | 82 passed in 1.77s |
| `ruff format --check` on changed Python files | 2 files already formatted |
| `ruff check` on changed Python files | All checks passed |
| `git diff --check` | Passed |

Focused command:

```sh
backend/.venv/bin/python -m pytest backend/app/tests/test_pr4_data2_research.py backend/app/tests/test_pr4_data_coverage.py -q
```

Affected regression command:

```sh
backend/.venv/bin/python -m pytest backend/app/tests/test_pr4_data_coverage.py backend/app/tests/test_food_ingredient_domain.py backend/app/tests/test_food_ingredient_application.py backend/app/tests/test_food_ingredient_architecture.py backend/app/tests/test_food_ingredient_seed.py backend/app/tests/test_food_ingredient_migration.py backend/app/tests/persistence/test_food_ingredient_repository.py -q
```

Ruff command uses installed `ruff` (the backend virtualenv has no separate Ruff executable):

```sh
ruff format --check scripts/validate_pr4_data2.py backend/app/tests/test_pr4_data2_research.py
ruff check scripts/validate_pr4_data2.py backend/app/tests/test_pr4_data2_research.py
git diff --check
```

Tests verify deterministic byte-rebuilding of four final artifacts, exact 30/79/193/96 counts, existing global catalogue digest, preserved historical source text, five-chain/form evidence joins, rejected wrong forms/duplicate promotion, selected rights/provenance, forbidden-source exclusion and equipment evidence/order. Offline checks validate review structure and consistency, not the truth of arbitrary fabricated human claims; primary sources remain part of final review.

Full backend/launcher runtime suite and production seed execution: **not run / outside this DATA2 task contract**. Issue #12 specifically excludes a full runtime suite for isolated curation. Existing FoodIngredient seed tests were run in the affected suite above. No runtime seed or new production rows are introduced.

## Scope audit and review gate

Only `data/curation/pr4-data2/`, `scripts/validate_pr4_data2.py`, `backend/app/tests/test_pr4_data2_research.py` and the three `state/` execution files change. Global seeds and historical PR4 curation are byte-unchanged. No source PDFs/HTML snapshots, local SQLite DB, credentials, virtualenv or unrelated artifacts belong in the commit. No runtime/model/schema/migration/API/frontend/retailer integration/AI changes.

PR #10 remains untouched and may consume this successor only after DATA2 **ACCEPT + merge**. PR5 remains unauthorized. Review readiness is not project acceptance or permission to merge.

**PR4-DATA2 — READY FOR REVIEW**
