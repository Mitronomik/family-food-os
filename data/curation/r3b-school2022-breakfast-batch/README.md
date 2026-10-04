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
5. `ru-school2022:recipe:54-1к` — Каша жидкая молочная кукурузная — 200 g / 207.9 kcal
6. `ru-school2022:recipe:54-2к` — Каша вязкая молочная кукурузная — 200 g / 287.8 kcal
7. `ru-school2022:recipe:54-6к` — Каша вязкая молочная пшенная — 200 g / 274.9 kcal
8. `ru-school2022:recipe:54-16к` — Каша «Дружба» — 200 g / 168.9 kcal
9. `ru-school2022:recipe:54-23к` — Каша жидкая молочная пшеничная — 200 g / 208.3 kcal
10. `ru-school2022:recipe:54-24к` — Каша жидкая молочная пшенная — 200 g / 274.9 kcal

Adversarial process audit removed `54-3т` and `54-21к` because quantified sugar has no technology placement. They are replaced in the same ten-card gate by source-clean `54-2к` and `54-24к`. `54-22к` remains deferred because quantified butter has no technology placement.

## New identity-only demand

- `CHEESE_SEMI_HARD_UNSPECIFIED` — Сыр полутвердый;
- `CORN_GROATS` — Крупа кукурузная;
- `MILLET_GROATS` — Крупа пшенная.

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
- `54-2к` exact 65 g water is quantified cooking input; wash water remains process-resource context;
- `54-24к` exact 52 g water is the source `по расчету рецептуры` cooking input after unquantified wash/scald/drain operations;
- `54-3т`, `54-21к` and `54-22к` are deferred because a quantified table ingredient lacks technology placement.

## Future runtime

Reuse the merged R3-A batch runtime seam in one PR:

`identity reconcile → per-recipe inactive atomic publication → exact batch preflight → one-UoW activation`.

No recipe-by-recipe PR split and no separate activation PR.


## Review corrections

- Consumer Recipe Steps for `54-23к` and `54-24к` contain Russian display text only; internal authority/inference terminology remains in engineering receipts, not user-facing steps.
- Omelets `54-2о/3о/4о` explicitly publish the oven branch `180–200 °C / 8–10 минут`; the alternative steam branch `25–30 минут` remains provenance-only.
- All ten R3-B recipes depend on `MILK_2_5`. Future runtime acceptance must prove that exact hard exclusion rejects all ten while preserving the existing three-candidate milk-free breakfast-compatible set and its repetition capacity 9.
