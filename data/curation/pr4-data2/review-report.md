# PR4-DATA2 — final correction review evidence

PR4-DATA2 — READY FOR REVIEW, not ACCEPTED or COMPLETE (`2026-09-05`).

Issue #12; existing branch `data/pr4-data2-russia-spb-recuration` and
[PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Exact base: `26af749be0f6446de1d88cad2e2e03158a9830a0` (merged governance #9,
historical PR4-DATA #8 and localization #11). Correction begins at reviewed head
`36c0cb82680fbc8a57ab4a78a41f363f3420d39d`; delivered head is the current branch
HEAD, recorded exactly in PR #13 after push, not a self-referential commit hash.

Final: **30 recipes**, **25 retained / 5 replaced in this correction pass**;
relative to historical PR4: **5 retained / 25 replaced**. Both forbidden ICN
cards are absent. **226 source-audit rows / 195 selected rows** (190 required,
4 source-explicit optional, 1 conditional); exact **82 existing FoodIngredient**
union within **80..120**, zero new codes and zero unresolved required rows.
**88 source-backed equipment rows / 32 normalized codes**.

Canonical PR4 meal types: **breakfast 3 / main 6 / side 6 / salad 6 /
sandwich 0 / other 9**. Separate curation roles: **BREAKFAST 3 / MAIN_DISH 6 /
SIDE_DISH 12 / SOUP 2 / DESSERT 3 / SNACK 3 / CONDIMENT 1**.
**8 meal anchors**, **3 soups/substantial one-bowl meals**, **12 pure sides**;
five primary-protein families: **EGG 2 / FISH 2 / LEGUME_TOFU 1 / MEAT 1 /
POULTRY 2** among anchors. Local Harvest is a vegetable side, never a pork main.

**85 non-water purchase forms: 3 RU_MASS_MARKET / 82 RU_AVAILABLE /
0 SPECIALTY_OR_UNCLEAR**. Chain coverage: 71 one-chain, 11 two-chain,
3 three-chain forms. All five baseline chains assessed; Lenta concentration
remains a limitation. Matrix: 185 raw / 177 unique observations, 140 AVAILABLE /
37 UNCERTAIN (includes rejected research). Compatibility is not momentary stock.

All final sources re-audited for name, servings, ingredient concepts, meal role,
diversity, times, equipment and limitations. Exact artifacts/hashes, attribution
and notices retained under the approved narrow direct-FNS project risk posture.
No unresolved selected-source rights blocker; no blanket public-domain or
unrestricted commercial/derivative rights claim.

Verification: final DATA2 validator **PASS**; focused DATA2 **104 passed in 2.54s**;
historical PR4-DATA/FoodIngredient affected suite **82 passed in 2.43s**;
Ruff format **2 files already formatted**, Ruff check **All checks passed!**;
`git diff --check` and staged scope audit **PASS**. Five final artifacts reproduce
byte-for-byte from reviewed source/form inputs. Full runtime suite and PR4
production seed execution are excluded from this isolated curation operation.

Historical `data/curation/pr4/`, global seeds (183 ingredients / 172 aliases /
183 profiles), PR4 runtime, migrations/API/frontend and local development DB
remain unchanged. PR #10 remains at `cd2285802c94735e0c9015042f9f4c0b52d68b85`;
it may consume DATA2 only after ACCEPT + merge. No RetailSKU/retailer production,
Nutrition, Pantry, Planner, Shopping, Auth/PostgreSQL or AI work. PR5 unauthorized.
Next action: project final review, not autonomous merge.

## Five correction-pass replacements

| Removed | Selected | Reason |
| --- | --- | --- |
| TNC6-CORN-ZUCCHINI-PANCAKES | SNAP4-SPANISH-FRITTATA | Replace source-defined snack/side corn pancakes with a substantial six-egg/potato entree. Breakfast is an explicit curator occasion, not a source quotation; no side is relabelled as a main. |
| HARV6-ROASTED-POTATOES | FNS5-BAKED-LENTILS-CASSEROLE | Replace a redundant plain potato side with the source-described hearty lentil, vegetable and cheese dinner in one dish; adds a genuine legume anchor with measured required foods. |
| SNAP1-MICROWAVE-BAKED-POTATO | FNS2-ORANGE-PORK-CHOPS | Replace the single plain potato side with a measured pork-loin-chop main, sweet potato and orange; omit only source-explicit optional dash seasonings. |
| WIC4-ROASTED-CARROTS | SNAP2-SIMPLE-GREEN-SMOOTHIE | Replace a redundant plain roasted vegetable side with a source-defined fruit/greens snack using an explicit single frozen-fruit option. Select frozen strawberries, not the retained cauliflower/oat smoothie composition. This is not a meal anchor; four other new genuine anchors satisfy the guard without role inflation. |
| SNAP8-HOMEMADE-MASHED-POTATOES | FNS4-OVEN-FRIED-FISH | Replace another plain potato side with a second materially different fish preparation: breaded tilapia oven-baked using the measured source butter coating. |

## All final recipes — derived from reviewed artifacts

| Recipe/source ID | Servings | PR4 type / curation role | Anchor / family | Source / selected rows | Equipment rows | Diversity contribution |
| --- | --- | --- | --- | --- | --- | --- |
| CACFP6-CORN-EDAMAME-BLEND — Corn and Edamame Blend | 6 | side / SIDE_DISH | no | 10 / 10 | 2 | Corn and edamame vegetable side; saucepan saute with source-explicit sesame-seed toasting. |
| CACFP6-LOCAL-HARVEST-BAKE — Local Harvest Bake | 6 | side / SIDE_DISH | no | 7 / 7 | 3 | Oven-baked butternut squash, beet and sweet potato vegetable side. |
| CACFP6-TABBOULEH — Tabbouleh | 6 | salad / SIDE_DISH | no | 13 / 13 | 3 | Chilled quinoa and bulgur salad with tomato, cucumber, pepper and fresh herbs. |
| CACFP6-HONEY-LIME-CHICKEN — Honey Lime Chicken | 6 | main / MAIN_DISH | yes / POULTRY | 6 / 6 | 3 | Oven-baked chicken thighs with measured honey, lime juice and zest. |
| CACFP6-CREAMY-COLESLAW — Creamy Coleslaw | 6 | salad / SIDE_DISH | no | 11 / 11 | 1 | Uncooked green and red cabbage/carrot side with yogurt-mayonnaise dressing and dried cranberries. |
| TNC6-EGGS-SPINACH — Scrambled Eggs with Spinach | 6 | breakfast / BREAKFAST | yes / EGG | 12 / 3 | 9 | Two-egg-per-serving scrambled spinach breakfast, prepared in a skillet. |
| TNC6-APPLESAUCE — Applesauce | 6 | other / SNACK | no | 4 / 2 | 7 | Cooked and mashed apples with water; optional cinnamon omitted. |
| SNAP4-SPANISH-FRITTATA — Spanish Frittata | 4 | breakfast / BREAKFAST | yes / EGG | 7 / 6 | 8 | Substantial egg and potato skillet entree, oven-finished and inverted onto a plate; breakfast occasion chosen by the curator. |
| FNS5-BAKED-LENTILS-CASSEROLE — Baked Lentils Casserole | 5 | main / MAIN_DISH | yes / LEGUME_TOFU | 9 / 7 | 3 | Source-described hearty lentil, vegetable and cheddar dinner in one covered casserole; a legume meal anchor. |
| HARV6-FRESH-TOMATO-SALSA — Fresh Tomato Salsa | 6 | other / CONDIMENT | no | 9 / 7 | 1 | Cold tomato/apple salsa with measured lime juice and seasoning; fresh tomato alternative selected. |
| HARV6-GARDEN-PASTA-SALAD — Garden Pasta Salad | 6 | salad / SIDE_DISH | no | 9 / 8 | 1 | Cold cooked-macaroni salad with cucumber, onion, green pepper and vinegar/oil dressing. |
| SNAP6-SPINACH-APPLE-SALAD — Spinach Salad with Apples and Raisins | 6 | salad / SIDE_DISH | no | 7 / 7 | 0 | Uncooked spinach, apple and raisin salad with canola and cider-vinegar dressing. |
| SNAP6-PEACH-CRISP — Peach Crisp | 6 | other / DESSERT | no | 7 / 7 | 4 | Baked fresh-peach dessert with quick-oat, flour and margarine topping. |
| SNAP6-SEARED-GREENS — Seared Greens | 6 | side / SIDE_DISH | no | 7 / 7 | 2 | Kale cooked with garlic in a covered pot, then finished with cider vinegar. |
| SNAP8-SOMALI-SUMMER-SALAD — Somali Summer Salad | 8 | salad / SIDE_DISH | no | 7 / 6 | 1 | Fresh apple, cucumber, tomato and green-pepper salad with olive oil and lemon juice. |
| FNS2-ORANGE-PORK-CHOPS — Orange Pork Chops | 2 | main / MAIN_DISH | yes / MEAT | 7 / 4 | 3 | Pork loin chops browned in a skillet then baked with sweet potato and orange; a meat meal anchor. |
| WIC4-BUTTERNUT-SOUP — Butternut Squash Soup | 4 | other / SOUP | no | 6 / 4 | 7 | Roasted butternut squash blended with milk using the selected immersion-blender method. |
| WIC1-OVERNIGHT-OATS-CINNAMON-APPLE — Overnight Oats - Cinnamon Apple | 1 | breakfast / BREAKFAST | no | 6 / 5 | 5 | No-cook overnight rolled-oat breakfast with the source-quantified apple, cinnamon and plain-yogurt options selected. |
| SNAP2-SIMPLE-GREEN-SMOOTHIE — Simple Green Smoothie | 2 | other / SNACK | no | 8 / 6 | 1 | Cold blended spinach, banana, apple, dairy and source-permitted frozen strawberries; a fruit/greens snack, without the retained smoothie's cauliflower or oats. Not a meal anchor. |
| SNAP3-GRILLED-FRUIT — Grilled Fruit | 3 | other / DESSERT | no | 3 / 3 | 1 | Pineapple, peach and banana skewers grilled or broiled according to source doneness cues. |
| WIC2-SPINACH-CAULIFLOWER-SMOOTHIE — Spinach and Cauliflower Smoothie | 2 | other / SNACK | no | 8 / 7 | 4 | Blended spinach, frozen cauliflower, apple, banana, oats, milk and plain yogurt snack. |
| SNAP4-PEAR-ORANGE-SAUCE — Pear in Orange Sauce | 4 | other / DESSERT | no | 3 / 3 | 1 | Double-boiler pears served with measured orange-juice and sugar sauce. |
| SNAP4-SPRING-VEGETABLE-SAUTE — Spring Vegetable Saute | 4 | side / SIDE_DISH | no | 12 / 12 | 1 | Skillet vegetable saute with small potatoes, carrot, asparagus, green beans and radishes. |
| FNS4-OVEN-FRIED-FISH — Oven Fried Fish | 4 | main / MAIN_DISH | yes / FISH | 7 / 6 | 4 | Breaded tilapia fillets oven-baked in measured butter; a fish main distinct from the retained microwave cod. |
| SNAP8-APPLE-CARROT-SOUP — Apple Carrot Soup | 8 | other / SOUP | no | 7 / 6 | 1 | Long-simmer pork, apple and carrot soup with ginger; not a vegetarian soup. |
| SNAP6-WALDORF-SALAD — Waldorf Salad | 6 | salad / SIDE_DISH | no | 7 / 7 | 2 | Apple, celery and raisin salad with source oven-toasted walnuts and plain nonfat yogurt dressing. |
| SNAP4-BROWN-RICE-PILAF — Brown Rice Pilaf | 4 | side / SIDE_DISH | no | 6 / 6 | 2 | Rice-cooker brown rice with almonds, parsley and measured seasonings. |
| SNAP5-KALE-NUTS-RAISINS — Kale with Nuts and Raisins | 5 | side / SIDE_DISH | no | 6 / 5 | 3 | Leafy kale side with oven-toasted walnuts and raisins, then skillet-cooked. |
| SNAP4-BRAISED-CHICKEN-SPINACH — Braised Chicken Thighs with Spinach | 4 | main / MAIN_DISH | yes / POULTRY | 10 / 10 | 2 | Bone-in chicken thighs browned then braised with herbs and fresh spinach. |
| SNAP4-DILLED-FISH-FILLETS — Dilled Fish Fillets | 4 | main / MAIN_DISH | yes / FISH | 5 / 4 | 3 | Frozen cod fillets cooked by the source microwave method with measured dill and lemon juice. |

## Source collections and rights result

All rows below: REVIEWED_UNDER_ACCEPTED_DIRECT_FNS_RISK_POSTURE. The actual artifact and its notices, not generic USDA branding, are evidence. No broader license is asserted.

- **USDA FNS America's Harvest Cookbook, Budget Stretchers: 3**. [Baked Lentils Casserole](https://fns-prod.azureedge.us/americasharvest/budget/main/lentils-casserole); [Orange Pork Chops](https://fns-prod.azureedge.us/americasharvest/budget/main/orange-porkchops); [Oven Fried Fish](https://fns-prod.azureedge.us/americasharvest/budget/main/fish).
- **USDA FNS CACFP Home Childcare — Main Dishes: 1**. [Honey Lime Chicken](https://fns-prod.azureedge.us/sites/default/files/resource-files/Honey_Lime_Chicken_6_Servings.pdf).
- **USDA FNS CACFP Home Childcare — Side Dishes: 4**. [Corn and Edamame Blend](https://fns-prod.azureedge.us/sites/default/files/resource-files/Corn_Edamame_Blend_6_Servings.pdf); [Local Harvest Bake](https://fns-prod.azureedge.us/sites/default/files/resource-files/Local_Harvest_Bake_6_Servings.pdf); [Tabbouleh](https://fns-prod.azureedge.us/sites/default/files/resource-files/Tabbouleh_6_Servings.pdf); [Creamy Coleslaw](https://fns-prod.azureedge.us/sites/default/files/resource-files/Creamy_Coleslaw_6_Servings.pdf).
- **USDA FNS FDPIR — A Harvest of Recipes with USDA Foods (FNS-430): 2**. [Fresh Tomato Salsa](https://fns-prod.azureedge.us/sites/default/files/resource-files/HarvestofRecipes.pdf); [Garden Pasta Salad](https://fns-prod.azureedge.us/sites/default/files/resource-files/HarvestofRecipes.pdf).
- **USDA FNS MyPlate for My Family handouts, November 2014: 1**. [Spanish Frittata](https://snaped.fns.usda.gov/snap/MPMF/Handouts/HowMuchFoodandPhysicalActivityHandouts.pdf).
- **USDA FNS SNAP-Ed recipe pages: 1**. [Simple Green Smoothie](https://snaped.fns.usda.gov/node/2489).
- **USDA FNS SNAP-Ed — Recipes and seasonal menus: 12**. [Spinach Salad with Apples and Raisins](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes); [Peach Crisp](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/summer-recipes); [Seared Greens](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/spring-recipes); [Somali Summer Salad](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/summer-recipes); [Grilled Fruit](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/grilled-fruit); [Pear in Orange Sauce](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes); [Spring Vegetable Saute](https://snaped.fns.usda.gov/nutrition-education/snap-ed-recipes/spring-recipes); [Apple Carrot Soup](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/apple-carrot-soup); [Waldorf Salad](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/fall-recipes); [Brown Rice Pilaf](https://snaped.fns.usda.gov/resources/recipes-and-menus/healthy-thrifty-holiday-menus/valentines-day); [Kale with Nuts and Raisins](https://snaped.fns.usda.gov/node/1861); [Dilled Fish Fillets](https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/dilled-fish-fillets).
- **USDA FNS Team Nutrition Cooks! — Family Handouts: 2**. [Scrambled Eggs with Spinach](https://fns-prod.azureedge.us/sites/default/files/resource-files/tnc-eggs.pdf); [Applesauce](https://fns-prod.azureedge.us/sites/default/files/resource-files/tnc-applesauce.pdf).
- **USDA FNS WIC Works — Recipes: 3**. [Butternut Squash Soup](https://wicworks.fns.usda.gov/recipe/butternut-squash-soup); [Overnight Oats - Cinnamon Apple](https://wicworks.fns.usda.gov/recipe/overnight-oats-cinnamon-apple); [Spinach and Cauliflower Smoothie](https://wicworks.fns.usda.gov/recipe/spinach-and-cauliflower-smoothie).
- **USDA FNS — Food and Physical Activity Checklist: 1**. [Braised Chicken Thighs with Spinach](https://snaped.fns.usda.gov/sites/default/files/documents/howmuch_foodandphysicalactivitychecklist.pdf).

Exact per-card SHA-256, attribution, notice findings and applicable narrow rights basis are in `recipe-corpus.json` and `source-consistency-audit.json`. New Print/PDF sources retain Wisconsin Extension, Utah State Extension and Colorado State/UC Davis attribution; SNAP smoothie retains NVCSS attribution. No new candidate requires a blanket-public-domain inference.

## Equipment — exact derived codes

`BAKING_DISH`, `BAKING_PAN`, `BAKING_SHEET`, `BLENDER`, `BOWL`, `CASSEROLE_DISH`, `CUTTING_BOARD`, `DOUBLE_BOILER`, `FINE_MESH_STRAINER`, `FORK`, `IMMERSION_BLENDER`, `KNIFE`, `LID`, `MEASURING_CUP`, `MEASURING_SPOON`, `MICROWAVE`, `NONSTICK_SAUCEPAN`, `NONSTICK_SKILLET`, `OVEN`, `PLATE`, `POT`, `POTATO_MASHER`, `RESEALABLE_CONTAINER`, `RICE_COOKER`, `SAUCEPAN`, `SKEWER`, `SKILLET`, `SPATULA`, `SPOON`, `STOCK_POT`, `STOVETOP`, `WHISK`.

88 rows / 32 codes, ordered by first explicit operational use within each recipe; evidence snippet and source section retained for every row.

## Source limitations — final selection

- **CACFP6-HONEY-LIME-CHICKEN**: {'source_fact': 'Source header cook time 30 minutes, oven directions 30–35 minutes. The step 2 Set aside for step 2 reference is a source typo.', 'review_decision': 'PRESERVE_SOURCE_HEADER_AND_STAGE_RANGE_NO_REWRITTEN_STEP'}
- **CACFP6-CREAMY-COLESLAW**: {'source_fact': 'Source header says cooking 10 minutes although directions perform no cooking. Preserve reported field, flag mismatch; do not invent heating.', 'review_decision': 'PRESERVE_SOURCE_AND_DISTINGUISH_CURATED_SELECTION'}
- **SNAP4-SPANISH-FRITTATA**: Header cook time and individual step durations are not reconciled or silently recomputed.; Four 4-ounce servings is retained literally despite apparent yield tension with listed food quantities.; Unquantified potato-boiling water is drained process water, not invented consumed food quantity.
- **FNS5-BAKED-LENTILS-CASSEROLE**: Use this measured 14.5-ounce official version, not the older SNAP-Ed version whose tomato can has no size.; Optional pepper and garlic powder may be retained at their measured quantities or omitted explicitly.; No-salt-added tomatoes are a candidate narrower purchase selection; retailer ingredient evidence must establish the no-salt form without assuming every canned tomato qualifies.
- **HARV6-GARDEN-PASTA-SALAD**: {'source_fact': 'Cooked macaroni input quantity retained; dry purchase amount is not established and must not be generated as ½ cup dry.', 'review_decision': 'PRESERVE_SOURCE_NO_INVENTED_CONVERSION_OR_STEP', 'scope': 'Source evidence is retained verbatim for technical curation. No purchase-weight conversion or missing source step is generated by DATA2; later runtime normalization must review this limitation.'}
- **SNAP6-SPINACH-APPLE-SALAD**: {'source_fact': 'Source spinach says 2/3 package (10 ounces); preserve exact dual notation without inventing package-size conversion.', 'review_decision': 'PRESERVE_SOURCE_NO_INVENTED_CONVERSION_OR_STEP', 'scope': 'Source evidence is retained verbatim for technical curation. No purchase-weight conversion or missing source step is generated by DATA2; later runtime normalization must review this limitation.'}
- **FNS2-ORANGE-PORK-CHOPS**: Retain two chops as a count, not invented grams or yield.; PORK_LOIN is a proposed selection of loin chops within generic pork chops; the market review must support that purchased cut.; Source says cover but does not name a cover type; do not infer foil or a specific lid.; All three dash seasonings are explicitly optional and omitted, not normalized to invented teaspoon fractions.; Brown rice is a separate serving suggestion, not an ingredient added to this recipe.
- **WIC1-OVERNIGHT-OATS-CINNAMON-APPLE**: {'source_fact': 'Source prose says all except oats and liquid optional. Selected apple, yogurt and cinnamon remain quantified choices, but are source-optional selections.', 'review_decision': 'PRESERVE_SOURCE_AND_DISTINGUISH_CURATED_SELECTION'}
- **SNAP2-SIMPLE-GREEN-SMOOTHIE**: Choose frozen strawberry only as explicitly permitted, subject to its separate frozen-form retailer evidence; this is not a mixed-fruit decomposition.; Low-fat plain yogurt is selected as a narrower member of source generic plain yogurt, with exact canonical low-fat market evidence required.; Flax and chia are source-explicit optional omissions. Generic whole flax seeds are not automatically mapped to global ground-flax code.; No preparation or cooking time is supplied; do not invent one.; No count-to-weight or milk/yogurt volume-to-mass conversion proposed.; Source review applies only to the approved narrow direct-FNS project risk posture; original contributor attribution does not establish broad commercial or derivative permission.
- **FNS4-OVEN-FRIED-FISH**: Frozen-and-thawed fillets are explicitly allowed; preserve selected purchase form in market audit.; The pan is coated using the listed tablespoon of butter, not an invented extra cooking spray.; Generic butter may be narrowed to existing unsalted butter without adding salt or changing source quantities.
- **SNAP4-BRAISED-CHICKEN-SPINACH**: {'source_fact': 'Salt and pepper listed but directions omit application; no invented source step.', 'review_decision': 'PRESERVE_SOURCE_NO_INVENTED_CONVERSION_OR_STEP', 'scope': 'Source evidence is retained verbatim for technical curation. No purchase-weight conversion or missing source step is generated by DATA2; later runtime normalization must review this limitation.'}

## Retail evidence

Final forms: 3 RU_MASS_MARKET / 82 RU_AVAILABLE / 0 SPECIALTY_OR_UNCLEAR. Selected row classifications: 9 RU_MASS_MARKET / 178 RU_AVAILABLE / 8 HOUSEHOLD_WATER. Available unique research records by chain: Пятёрочка 4 / Перекрёсток 0 / Лента 120 / О’КЕЙ 0 / Магнит 16. Zero is unproven coverage, not absence. Matrix includes rejected-candidate research; it is not a final-ingredient count.

| New/correction concept | Chain | Official product evidence | Official SPB/LO presence |
| --- | --- | --- | --- |
| TOMATO_CANNED_NO_SALT | LENTA | https://lenta.com/product/tomaty-kusochkami-v-tomatnom-soke-zhb-italiya-400g-542921/ | https://lenta.com/catalog/ovoshchi-146/ |
| BREADCRUMBS | LENTA | https://lenta.com/product/suhari-panirovochnye-lenta-rossiya-200g-638246/ | https://lenta.com/catalog/ovoshchi-146/ |
| TILAPIA_RAW | LENTA | https://lenta.com/product/tilapiya-file-premium-razmorozhennoe-rossiya-474037/ | https://lenta.com/catalog/ovoshchi-146/ |
| TILAPIA_RAW | LENTA | https://lenta.com/product/tilapiya-file-sm-rossiya-500g-428531/ | https://lenta.com/catalog/ovoshchi-146/ |
| LENTILS_DRY | LENTA | https://lenta.com/product/chechevica-zelenaya-prodovolstvennaya-kalibrovannaya-rossiya-450g-440340/ | https://lenta.com/catalog/ovoshchi-146/ |
| LENTILS_DRY | MAGNIT | https://magnit.ru/product/1000108780-chechevitsa_zelenaya_tselaya_td_kholding_400g?shopCode=782972&shopType=1 | https://magnit.ru/product/1000108780-chechevitsa_zelenaya_tselaya_td_kholding_400g?shopCode=782972&shopType=1 |
| TOMATO_CANNED_NO_SALT | MAGNIT | https://magnit.ru/product/1000216768-tomaty_premier_of_taste_rezanye_v_sobstvennom_soku_400g?shopCode=784364&shopType=1 | https://magnit.ru/product/1000216768-tomaty_premier_of_taste_rezanye_v_sobstvennom_soku_400g?shopCode=784364&shopType=1 |
| CHEESE_CHEDDAR | LENTA | https://lenta.com/product/syr-polutverdyjj-chedder-45-brusok-bez-zmzh-belarus-200g-734869/ | https://lenta.com/catalog/ovoshchi-146/ |
| CHEESE_CHEDDAR | PYATEROCHKA | https://5ka.ru/catalog/syr--251C13095/ | https://rabota.x5.ru/dostavka/rabota-v-x5/ |
| PORK_LOIN | LENTA | https://lenta.com/product/svinina-korejjka-premium-polufabrikat-ohlazhdennyjj-rossiya-70099/ | https://lenta.com/catalog/ovoshchi-146/ |
| STRAWBERRY | LENTA | https://lenta.com/product/klubnika-zam-1500g-495854/ | https://lenta.com/catalog/ovoshchi-146/ |
| STRAWBERRY | MAGNIT | https://magnit.ru/product/1499919387-klubnika_zamorozhennaya_v_10?catalogType=1&shopCode=571452&shopType=1 | https://magnit.ru/product/1499919387-klubnika_zamorozhennaya_v_10?catalogType=1&shopCode=571452&shopType=1 |

### Exact one-chain-only forms (71)

| Form ID | Actual purchase concept | Qualifying refs |
| --- | --- | --- |
| ALMONDS_RAW | Plain unroasted unsalted almond kernels; chop/slice as source preparation | research-lenta-okey-v6.json:1 |
| APPLE | Whole fresh apples; washing, peeling where specified, coring and chopping are preparation | research-lenta-okey-v3.json:27 |
| APPLE_CIDER_VINEGAR | Plain apple cider vinegar; source vinegar member selection retained | research-lenta-okey-v3.json:22 |
| ASPARAGUS | Fresh asparagus; wash and trim | research-lenta-okey-v4.json:6 |
| BANANA | Fresh banana; peel and slice | research-lenta-okey-v6.json:2 |
| BELL_PEPPER_GREEN | Fresh sweet green bell pepper; dice/chop | research-lenta-okey-v4.json:13 |
| BELL_PEPPER_RED | Fresh sweet red bell pepper; dice/chop | research-magnit-v2.json:9 |
| BLACK_PEPPER | Ground black pepper | research-lenta-okey-v2.json:34 |
| BUTTER_UNSALTED | Unsalted butter; select explicit butter alternative or narrower member of source-generic butter where reviewed | research-lenta-okey-v4.json:7 |
| BUTTERNUT_SQUASH | Fresh butternut squash; peel, seed and cube as specified | research-lenta-okey-v2.json:7 |
| CABBAGE_RED | Fresh red cabbage; shred/chop | research-x5-v3.json:4 |
| CANOLA_OIL | Plain food-grade rapeseed/canola oil for cold salad dressing only | research-lenta-okey-v6.json:5 |
| CAULIFLOWER__FROZEN | Plain frozen cauliflower florets for smoothie | research-lenta-okey-v7.json:1 |
| CELERY | Fresh celery stalks, not celeriac root; slice/dice | research-lenta-okey-v3.json:13 |
| CHICKEN_THIGH | Raw boneless skinless chicken thigh for Honey Lime Chicken | research-x5-v3.json:3 |
| CHICKEN_THIGH__BONE_IN | Plain raw chilled bone-in chicken thigh; remove skin as source preparation | research-lenta-okey-v7.json:4 |
| CILANTRO | Fresh cilantro leaves; chop | research-lenta-okey-v3.json:12 |
| CINNAMON_GROUND | Ground cinnamon | research-lenta-okey-v2.json:36 |
| COD_ATLANTIC | Plain raw frozen Atlantic cod fillets without skin/bones | research-lenta-okey-v7.json:12 |
| CORIANDER_SEED | Ground coriander seeds; source requires ground spice, not whole seed or leaf | research-lenta-okey-v7.json:2 |
| CORN_SWEET | Plain frozen sweet corn kernels, selected among source fresh/frozen/canned options; thaw/drain where specified | research-lenta-okey-v4.json:18 |
| CRANBERRIES_DRIED | Dried cranberries; ordinary sweetened dried product fits generic source | research-lenta-okey-v3.json:21 |
| CUMIN_GROUND | Ground cumin (zira), not caraway or whole-only seed evidence | research-x5-v3.json:8 |
| DILL_DRIED | Dried dill, selected explicit source alternative to fresh with source dry quantity | research-lenta-okey-v4.json:14 |
| EDAMAME_FROZEN | Plain frozen edamame beans; source requires thawed and drained, then sauteed | research-lenta-okey-v3.json:1 |
| FLOUR_WHEAT | Ordinary refined wheat flour | research-lenta-okey-v4.json:16 |
| GARLIC_POWDER | Plain dried ground garlic powder | research-lenta-okey-v4.json:15 |
| GINGER | Fresh ginger root; peel and slice | research-lenta-okey-v2.json:9 |
| GREEN_BEANS__FROZEN | Plain frozen green beans | research-lenta-okey-v8.json:5 |
| GREEN_ONION | Fresh green onion/scallions; trim/chop | research-lenta-okey-v4.json:11, research-x5-v3.json:5 |
| HONEY | Natural honey | research-lenta-okey-v3.json:7 |
| KALE | Fresh kale leaves; remove stems/chop; selected explicit source leafy-green option | research-lenta-okey-v6.json:9 |
| LEMON | Fresh whole lemons; squeezing juice or grating zest is source preparation | research-lenta-okey-v3.json:9, research-lenta-okey-v7.json:10 |
| LIME | Fresh whole lime for source zest | research-x5-v3.json:6 |
| LIME_JUICE | Fresh-squeezed lime juice prepared from purchased whole limes | research-lenta-okey-v4.json:19, research-x5-v3.json:7 |
| MARGARINE | Ordinary baking margarine; melt where source requires; not butter replacement | research-lenta-okey-v4.json:10 |
| MAYONNAISE_LOW_FAT | Light reduced-fat mayonnaise-family product20%; not full-fat mayonnaise | research-lenta-okey-v2.json:19 |
| MILK_1_PERCENT | Unflavoured cow milk1% fat; exact1% where source fixes it, selected lowfat option otherwise | research-lenta-okey-v2.json:14 |
| MINT_FRESH | Fresh mint leaves, not dried mint or mint tea | research-lenta-okey-v3.json:11 |
| OATS_ROLLED__QUICK | Plain quick-cooking rolled oats for Peach Crisp | research-lenta-okey-v5.json:4 |
| OLIVE_OIL | Pure olive oil; no non-olive blend | research-lenta-okey-v4.json:9, research-x5-v3.json:1 |
| ONION_RED__SWEET_YALTA | Sweet red Yalta onion, raw whole bulbs | research-lenta-okey-v8.json:1 |
| ONION_YELLOW | Fresh ordinary yellow/brown bulb onion; peel/chop | research-magnit-v2.json:2 |
| ORANGE | Raw whole oranges squeezed to prepare 100% pure orange juice | research-lenta-okey-v9.json:2 |
| PARSLEY | Fresh parsley leaves; chop | research-lenta-okey-v2.json:24 |
| PARSLEY_DRIED | Plain dried parsley | research-lenta-okey-v2.json:25 |
| PASTA_DRY | Ordinary dry macaroni; source specifies cooked½cup final ingredient, not½cup dry input | research-lenta-okey-v4.json:5 |
| PEACH | Fresh peaches; slice | research-lenta-okey-v4.json:12 |
| PEAR | Whole raw pears, select four medium; peel/cut during preparation | research-lenta-okey-v9.json:1 |
| PINEAPPLE | Fresh whole raw pineapple, chunk during preparation | research-lenta-okey-v8.json:4 |
| PORK_LOIN | Plain raw boneless pork loin; selected member of generic lean pork and loin chops, source counts and preparation retained | research-lenta-okey-v4.json:24, research-correction-market.json:10 |
| POTATO | Fresh potatoes; peel/cube as specified | research-lenta-okey-v4.json:4 |
| POTATO__YOUNG | Young/new raw potato tubers, select tiny | research-lenta-okey-v8.json:2 |
| QUINOA | Plain dry quinoa; rinse/cook as specified | research-lenta-okey-v2.json:31 |
| RADISH | Fresh raw radish | research-lenta-okey-v8.json:3 |
| RAISINS_GOLDEN | Plain light/golden raisins; source generic raisin member selection | research-lenta-okey-v3.json:3 |
| RICE_BROWN | Dry brown rice | research-lenta-okey-v2.json:32 |
| ROSEMARY_DRIED | Plain dried rosemary | research-lenta-okey-v7.json:6 |
| SALT | Ordinary food table salt; iodized-specific source option separately reviewed | research-lenta-okey-v4.json:17, research-lenta-okey-v7.json:3, research-x5-v3.json:2 |
| SALT__IODIZED | Iodized food salt selected from explicit source kosher-or-iodized alternative | research-lenta-okey-v7.json:3 |
| SESAME_OIL | Pure sesame oil suitable for saute, reviewed ELEYA unrefined 250ml form | research-lenta-okey-v8.json:6 |
| SESAME_SEEDS | Plain raw sesame seeds, toasted at home using explicit source method | research-lenta-okey-v3.json:14 |
| SPINACH | Fresh spinach leaves; rinse/chop as specified | research-lenta-okey-v4.json:2 |
| SUNFLOWER_OIL | Refined sunflower cooking oil, selected source generic vegetable-oil member | research-lenta-okey-v4.json:8 |
| SWEET_POTATO | Fresh sweet potatoes; peel/cube as specified | research-lenta-okey-v2.json:8 |
| THYME_DRIED | Plain dried thyme | research-lenta-okey-v2.json:23 |
| WALNUTS_RAW | Plain unroasted unsalted walnut kernels; chop | research-lenta-okey-v6.json:14 |
| YOGURT_GREEK_NONFAT | Plain nonfat-family Greek yogurt from skim milk, residual0.1% fat; not mathematical zero | research-lenta-okey-v6.json:15 |
| YOGURT_PLAIN_LOW_FAT | Plain unflavoured low-fat yogurt1.5%; no fruit/vanilla/sugar-flavoured alternative | research-lenta-okey-v3.json:4 |
| BREADCRUMBS | Plain dry wheat breadcrumbs for breading, not panko or seasoned coating mix | research-correction-market.json:3 |
| TILAPIA_RAW | Plain frozen raw tilapia fillets, thawed for cooking as explicitly allowed by the source | research-correction-market.json:2 |

## Historical slot replacements (25)

| Removed historical source | Final successor | Reason |
| --- | --- | --- |
| CACFP6-SOUTHWEST-TOFU-SCRAMBLE | SNAP4-BRAISED-CHICKEN-SPINACH | Firm tofu form not cleared; retain a source-backed protein main using ordinary raw chicken thigh and fresh spinach. |
| CACFP6-SPICED-OATMEAL | WIC1-OVERNIGHT-OATS-CINNAMON-APPLE | Trans-fat-free margarine and vanilla requirements not cleared; source-explicit optional vanilla omission in an independently sourced oat breakfast. |
| CACFP6-STRAWBERRY-SMOOTHIE-BOWL | WIC2-SPINACH-CAULIFLOWER-SMOOTHIE | Required frozen strawberry and vanilla forms not cleared; retain a distinct smoothie with evidenced frozen cauliflower and source-specified milk. |
| CACFP6-BAKED-SWEET-POTATOES-APPLES | SNAP4-PEAR-ORANGE-SAUCE | Frozen unsweetened green apples, orange concentrate, trans-fat-free margarine and vanilla not cleared; select quantified fresh-fruit cooked dessert. |
| CACFP6-ORANGE-GLAZED-CARROTS | SNAP2-SIMPLE-GREEN-SMOOTHIE | Frozen carrot, orange concentrate, trans-fat-free margarine and vanilla forms not cleared; fresh whole carrots cut during source preparation need no pre-cut retail product. Correction pass: Replace a redundant plain roasted vegetable side with a source-defined fruit/greens snack using an explicit single frozen-fruit option. Select frozen strawberries, not the retained cauliflower/oat smoothie composition. This is not a meal anchor; four other new genuine anchors satisfy the guard without role inflation. |
| CACFP6-PIZZA-GREEN-BEANS | SNAP4-SPRING-VEGETABLE-SAUTE | Canned no-salt green beans not cleared; independent source permits generic green beans, with reviewed frozen member, sweet red onion and young potato forms. |
| CACFP6-SAUTEED-SPINACH-TOMATOES | SNAP6-SEARED-GREENS | Required trans-fat-free margarine not cleared; retain independently sourced cooked greens without that restriction. |
| CACFP6-SPANISH-RICE | SNAP4-BROWN-RICE-PILAF | Low-sodium beef broth, chili blend and parboiled long-grain brown rice not cleared; independent water-based brown-rice source needs no invented broth substitution. |
| CACFP6-CHICKEN-FAJITA | SNAP4-DILLED-FISH-FILLETS | Cooked frozen chicken strips, ancho, low-sodium salsa and whole-wheat tortilla forms not cleared; introduce a verified frozen-cod main with four quantified ingredients. |
| CACFP6-RICE-VEGETABLE-CASSEROLE | FNS5-BAKED-LENTILS-CASSEROLE | Reduced-fat cheddar, low-moisture part-skim mozzarella, low-sodium broth, trans-fat-free margarine and specified parboiled rice not cleared; independently sourced roasted potato side. Correction pass: Replace a redundant plain potato side with the source-described hearty lentil, vegetable and cheese dinner in one dish; adds a genuine legume anchor with measured required foods. |
| CACFP6-VEGETABLE-CHILI | WIC4-BUTTERNUT-SOUP | Ancho, low-sodium canned kidney beans, no-salt crushed tomato and low-sodium vegetable broth not cleared; select a quantified roast-and-blend vegetable soup. |
| CACFP6-VEGETABLE-FRITTATA | SNAP4-SPANISH-FRITTATA | Reduced-fat cheddar not cleared; independent egg/vegetable pancake source uses ordinary ingredients and an explicit frozen-corn alternative. Correction pass: Replace source-defined snack/side corn pancakes with a substantial six-egg/potato entree. Breakfast is an explicit curator occasion, not a source quotation; no side is relabelled as a main. |
| CACFP6-CARROT-RAISIN-SALAD | SNAP8-SOMALI-SUMMER-SALAD | Unsweetened pineapple canned in 100% juice not cleared; independent fresh-produce salad has explicit optional salt/pepper omission. |
| CACFP6-MACARONI-SALAD | HARV6-GARDEN-PASTA-SALAD | Whole-wheat pasta and canned pimientos not cleared; generic macaroni source preserved, including its cooked-volume quantity rather than invented dry weight. |
| CACFP6-MARINATED-BLACK-BEAN-SALAD | HARV6-FRESH-TOMATO-SALSA | Low-sodium canned black beans/salsa, ancho and reduced-fat cheddar not cleared; fresh tomato salsa provides a distinct condiment/vegetable preparation. |
| CACFP6-QUICHE-SELF-FORMING-CRUST | FNS2-ORANGE-PORK-CHOPS | Frozen liquid whole egg and reduced-fat cheddar not cleared; source-verified whole-potato microwave method adds a short single-serving preparation, not an invented quiche adaptation. Correction pass: Replace the single plain potato side with a measured pork-loin-chop main, sweet potato and orange; omit only source-explicit optional dash seasonings. |
| CACFP6-ROPA-VIEJA | SNAP8-APPLE-CARROT-SOUP | Low-sodium beef broth and parboiled brown rice not cleared; independently sourced long-simmer pork, apple and carrot soup. No beef or nutritional equivalence claimed. |
| CACFP6-CORN-PUDDING | SNAP6-PEACH-CRISP | White whole-grain cornmeal and no-salt cream-style corn not cleared; add a source-backed baked fruit/oat dessert. |
| CACFP6-GREEN-BEANS-POTATOES-SMOKED-TURKEY | SNAP5-KALE-NUTS-RAISINS | Smoked cooked turkey drumstick and trans-fat-free margarine not cleared; frozen green beans were initially unresolved and later evidenced, which alone does not clear the remaining recipe forms. |
| CACFP6-TUNA-SALAD-SANDWICH | SNAP6-WALDORF-SALAD | Whole-wheat roll and canned tuna-in-water forms not cleared; independently sourced apple/walnut salad, not a tuna substitution claim. |
| CACFP6-TUSCAN-GRILL-CHEESE | SNAP3-GRILLED-FRUIT | Whole-wheat bread, low-fat mozzarella and trans-fat-free margarine not cleared; independent grilling method with three ordinary fresh fruits. |
| CACFP6-ASIAN-TUNA-BURGER | SNAP6-SPINACH-APPLE-SALAD | Panko breadcrumbs, whole-wheat roll and low-sodium soy sauce not cleared; independent raw-leaf salad with reviewed cold-use canola oil. |
| CACFP6-BEAN-BURRITO-BOWL | FNS4-OVEN-FRIED-FISH | Low-sodium canned pinto beans, reduced-fat cheddar and parboiled brown rice not cleared; independently sourced boiled-and-mashed potato side. Correction pass: Replace another plain potato side with a second materially different fish preparation: breaded tilapia oven-baked using the measured source butter coating. |
| CACFP6-VEGETABLE-FRITTATA-BITES | TNC6-EGGS-SPINACH | Mandatory exclusion of ICN 2024 card: rights posture not cleared. Direct FNS Team Nutrition source has reviewed provenance and copying statement; no public-domain claim. |
| CACFP6-CAULIFLOWER-RICE | TNC6-APPLESAUCE | Mandatory exclusion of ICN 2024 card: rights posture not cleared. Direct FNS Team Nutrition source has reviewed provenance and copying statement; no public-domain claim. |

## Verification commands and integrity

```sh
backend/.venv/bin/python scripts/validate_pr4_data2.py
backend/.venv/bin/python -m pytest backend/app/tests/test_pr4_data2_research.py -q
backend/.venv/bin/python -m pytest backend/app/tests/test_pr4_data_coverage.py backend/app/tests/test_food_ingredient_domain.py backend/app/tests/test_food_ingredient_application.py backend/app/tests/test_food_ingredient_architecture.py backend/app/tests/test_food_ingredient_seed.py backend/app/tests/test_food_ingredient_migration.py backend/app/tests/persistence/test_food_ingredient_repository.py -q
ruff format --check scripts/validate_pr4_data2.py backend/app/tests/test_pr4_data2_research.py
ruff check scripts/validate_pr4_data2.py backend/app/tests/test_pr4_data2_research.py
git diff --check
git diff --cached --check
git diff --cached --stat
```

Results above are from the corrected artifacts, not the previous reviewed head.
Tests derive counts from source selections and independently reviewed facts;
negative cases cover incompatible enum/roles, hidden sides, false protein claims,
Local Harvest pork/main corruption, guard thresholds, ingredient union/new codes,
source hash/equipment/order mutations and deterministic regeneration of all five
final outputs. No general AI semantic validator or production runtime imports.

Scope audit: only `data/curation/pr4-data2/`, `scripts/validate_pr4_data2.py`,
`backend/app/tests/test_pr4_data2_research.py`, and the three state files changed.
No source binaries, private browser content, credentials, local databases or
unrelated artifacts staged. Global seeds and historical PR4 fixture have no diff
against the exact base. PR #10 and PR5 were not mutated. Await project review.
