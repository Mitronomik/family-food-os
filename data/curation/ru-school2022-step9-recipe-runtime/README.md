# School2022 Step 9 RecipeVersion runtime publication

**Status:** reviewed production payload for Russian-data integration Step 9
**Target:** `ru-school2022:recipe:53-19з — Масло сливочное (порциями)`
**Publication JSON SHA-256:** `241bbd0dd2910317be0b65f46586b8e1f40cb06e3fbac1122b4ea1056c26e28f`

This package publishes one inactive technical Recipe and one immutable
`SOURCE_VERIFIED RecipeVersion` through the existing Recipe Catalogue service.

It does not publish a second food, source-corpus row, Planner activation or
general Nutrition integration.

## Source

Official source:

`https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf`

Retained source PDF SHA-256:

`c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`

Durable private corpus:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Archive SHA-256:

`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`

Source package `source.json` SHA-256:

`7de777b9ea0104e00bbb2e8cc98f2868bc6e5eead8a15b139d83706db765409b`

The seven exact normalized source/process records and their canonical JSON hashes
are pinned in `publication.json`.

## Applicability boundary

The retained process-evidence record for refrigerated pre-service holding is:

- `institutional_school_catering_only`;
- `domestic_applicability=unestablished`;
- `not_executable_rule=true`.

Therefore production RecipeSteps are limited to the source-backed material
preparation facts:

1. no thermal treatment;
2. cut the butter into portion pieces.

Refrigerated holding and the 14 °C serving condition remain institutional
source-context evidence. `home_storage_status=not_granted` is preserved.

## Planner boundary

The fresh Step 9 Recipe is inactive.

Step 9 does not activate it and does not modify Planner, general Nutrition or the
current-profile selector. Activation and V2 Planner/general-Nutrition integration
belong to Step 10.

## Nutrition validation

The runtime preflight requires the accepted Step 8
`BUTTER_PEASANT_72_5_UNSALTED` ATOMIC composition v1 under
`RU_NUTRIENT_REGISTRY_V2`.

The 17 available canonical nutrient amounts are validated from the immutable
100 g composition and scaled by exactly 10/100. WATER and canonical total
carbohydrate remain unknown.

School2022 source-declared recipe nutrition is reference-only and is not imported
as production nutrition.
