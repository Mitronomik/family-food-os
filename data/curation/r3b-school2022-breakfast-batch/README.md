# R3-B School2022 breakfast batch

Issue #149. Docs/data/source-authority Contract Gate only.

Accepted base: `69c68f4153b25ac4e51cbe9ff54fb080201f08bd`.

This package freezes exactly ten School2022 BREAKFAST cards for one future R3-B
runtime PR. It does not publish runtime data.

## Selection

1. `ru-school2022:recipe:54-2о` — Омлет с зеленым горошком — 150 g / 153.5 kcal
2. `ru-school2022:recipe:54-3о` — Омлет с морковью — 150 g / 201 kcal
3. `ru-school2022:recipe:54-4о` — Омлет с сыром — 150 g / 316.0 kcal
4. `ru-school2022:recipe:54-2т` — Запеканка из творога с морковью — 150 g / 249.5 kcal
5. `ru-school2022:recipe:54-3т` — Суфле из моркови с творогом — 150 g / 200.9 kcal
6. `ru-school2022:recipe:54-1к` — Каша жидкая молочная кукурузная — 200 g / 207.9 kcal
7. `ru-school2022:recipe:54-6к` — Каша вязкая молочная пшенная — 200 g / 274.9 kcal
8. `ru-school2022:recipe:54-16к` — Каша «Дружба» — 200 g / 168.9 kcal
9. `ru-school2022:recipe:54-21к` — Каша вязкая молочная ячневая — 200 g / 249.1 kcal
10. `ru-school2022:recipe:54-23к` — Каша жидкая молочная пшеничная — 200 g / 208.3 kcal

The first five were present in superseded PR #145 but are independently
revalidated here against the current merged source boundary. No #145 contract or
state is reused as authority.

## New identity-only demand

- `CHEESE_SEMI_HARD_UNSPECIFIED` — Сыр полутвердый;
- `CORN_GROATS` — Крупа кукурузная;
- `MILLET_GROATS` — Крупа пшенная;
- `BARLEY_GROATS` — Крупа ячневая;

No NutritionProfile or Composition authority is granted.

## Source receipt

- Library file id: `libfile_26d95a7a50108191944b97db85a5c008`;
- archive size: 206692075 bytes;
- archive SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- embedded PDF size: 4102547 bytes;
- PDF SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- independent materialize/hash verification: 2026-10-04 — PASS.

## Process decisions

- source-declared ingredient totals remain authoritative;
- explicit source ratios may be retained without inventing per-step grams;
- `54-16к` exact 70 g water total has UNKNOWN per-groat split;
- `54-23к` exact 68 g water is source input, while retained water/yield is UNKNOWN;
- unquantified wash/rinse/scald water is process-resource context, not a new RecipeIngredient;
- `54-22к` is deferred because the card quantifies butter without placing it in technology.

## Future runtime

Reuse the merged R3-A batch runtime seam in one PR:

`identity reconcile → per-recipe inactive atomic publication → exact batch preflight → one-UoW activation`.

No recipe-by-recipe PR split and no separate activation PR.
