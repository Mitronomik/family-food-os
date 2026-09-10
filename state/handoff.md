# Handoff

Updated: `2026-09-10`

PR6-ARCH-COMPOSITION establishes the docs-only architecture contract from exact
main `47299ceb2c740f40f69f3b02359ce71c8be6b1c1` (PR #23), on
`docs/pr6-arch-composition`. No implementation or production data changed.

Option A is now **DECISION / APPROVED**, dated 2026-09-10 in
[Architecture §6.2](../docs/family-food/architecture.md#decision--option-a-approved-2026-09-10).
FoodIngredient is the sole food identity. Different nutrition-relevant forms are
separate foods; no mandatory FoodProductType Nutrition layer.

The [composition contract](../docs/family-food/food-composition-and-assembly.md)
now defines atomic/composite, recursive versioned DAG and one calculation authority
per version. Exact components have exact grams and pinned profile/composition
versions. Declared-only lists lack quantitative composition: use the product's
authoritative direct profile, never infer quantities from ingredient order.

Raw/input/cooked mass differ because preparation/cooking can remove parts or
absorb/lose water and fat. recipe_input_mass_g refers to the actual process input
form; pcs/ml need reviewed mass evidence. Yield and nutrient retention are distinct,
versioned evidence; unknown retention cannot silently become 100%.
NutrientVector extends macros to micronutrients without one SQL column per nutrient,
with nutrient-level provenance and unknown != zero. Nutrition v1 remains valid
current implementation and accepted PR #18 history; the new model is future target.

[Russian-language contract](../docs/family-food/russian-language-contract.md): all
consumer **and admin** product text must be Russian. No English fallback; missing
Russian food/recipe/nutrient/status/error text blocks publication. Machine codes
and exact external provenance identifiers remain intact behind the display boundary.
RU availability and familiarity are independent hard default-recipe gates; the
30 current FNS recipes remain technical evidence, not final consumer catalogue.

**Old PR6-DATA-B2-B2: SUPERSEDED / PENDING REDESIGN.** It cannot run next because
NutrientVector, composition/mass/yield and RU catalogue/display must exist before
redesigned source/profile promotion. PR #23 B2-B1 report, source candidates and
matrices remain unchanged research evidence; architecture approval does not approve
individual candidate values, FNDDS defaults or unresolved source choices.
All 43 estimates remain non-executable. Migration head is still 0027; production
baseline still has 30 current recipes / 189 rows / 30 INCOMPLETE.

[Canonical merge order](../docs/family-food/master-roadmap.md#5-canonical-master-sequence):
PR6-ARCH-COMPOSITION → PR6-NUTRIENT-VECTOR → PR6-COMPOSITION-CORE → PR6-RU-FOOD-DATA
→ PR6-DATA-B2-B2-REDESIGNED → PR6-CLOSE → RECIPE-ASSEMBLY-A → RECIPE-ASSEMBLY-B
→ PR7 MealPlan/Serving → PR8 Planner. Assembly uses verified Russian templates,
exact grams and reproducible trace; deterministic validation does not confer kitchen
verification. PR7 consumes RecipeVersion or validated RecipeAssembly without
replicating Nutrition; Planner consumes valid candidates and does not invent recipes.

PR6 remains **NOT COMPLETE**. The only next logical implementation operation is
**PR6-NUTRIENT-VECTOR — NOT STARTED / requires separate authorization after merge**.
PR7+ remain UNAUTHORIZED. Review readiness or merge grants no next-task permission.
[Progress](progress.md#pr6-arch-composition-verification) records verification;
[current focus](current-focus.md) owns execution authorization.
