# Step 5 — reviewed Russian reference table runtime package

This package is the bounded production publication for:

`RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`.

It was curated from the pinned source transport in
`FamilyFoodOS-corpus-0.3.0-2026-09-20.zip` (SHA-256
`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`).

The raw ~197 MiB corpus archive is **not** republished in Git. A durable private
operator copy is retained at:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

The runtime package retains only the 48 reviewed factual scalar claims required
by the merged Step 5 contract.

## Immutable pins

- `publication.json` Git blob SHA-1:
  `1f55158725c338f16715f2c2e2f285d183caf779`;
- pinned `RU_NUTRIENT_REGISTRY_V2` Git blob SHA-1:
  `db9d4d3b7e913447ff0c0a87b0e28f3085094409`.

The runtime loader verifies both byte identities before constructing a table.

## Frozen scope

- source: `МР 2.3.1.0253-21`;
- tables 11/12 men + 16/17 women;
- exact source header `Старше 18 лет` → completed age 19+;
- KFA-independent;
- 24 definitions × 2 sexes = 48 rows;
- source status `ready_source_group_lookup` only;
- exact source Decimal literals;
- exact source claim/page/table/row/column identities;
- no tables 9/10/13/14/15/18;
- no Vitamin D, Calcium, folate, Vitamin K, fluoride, cobalt, silicon or vanadium.

`BETA_CAROTENE` deliberately keeps the source/reference unit `mg/day` while
the pinned V2 registry canonical unit remains `µg`. This is same-definition
mass-unit compatibility; the source value is not rewritten.

## Source transport pins

The runtime payload records and the loader validates the accepted hashes for:

- source PDF;
- normalized population input;
- independent QA report;
- population-reference groups/nutrients/values;
- quality/validation reports;
- population-reference manifest;
- the full corpus archive.

The 48 exact `source_claim_id` values were selected from the pinned
`population-reference/normalized/values.jsonl` transport under the merged
contract. No claim identifier is synthesized at runtime.

## Runtime behavior

`backend/app/seed/russian_reference_table_step5.py`:

- verifies the exact Git blob of `publication.json`;
- verifies the pinned V2 nutrient registry Git blob;
- validates the 24 source-definition mappings and unit compatibility;
- validates every source claim locator and frozen applicability;
- constructs the existing immutable `ReviewedRussianReferenceTable`;
- exposes a fail-closed explicit provider for the existing
  `NutritionService.russian_member_group_reference` injection seam;
- performs no DB write and consumes no migration.

Unknown methodology versions fail closed. NASEM, Planner/API/UI defaults and
persisted methodology selection remain unchanged.
