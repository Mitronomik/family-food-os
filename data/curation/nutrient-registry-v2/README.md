# Nutrient Registry V2 — Russian definition compatibility

This package is a reviewed definition/method contract, not a food-data publication.

- Base registry: `PR6_NUTRIENT_VECTOR_A_V1` (immutable).
- New registry: `RU_NUTRIENT_REGISTRY_V2`.
- All V1 codes are copied into a new version; V1 stored rows are not edited.
- `CARBOHYDRATE_AVAILABLE` becomes method-independent in V2. The source/derivation method is carried separately by the adapter contract.
- `VITAMIN_A_RE`, `NIACIN_EQUIVALENT` and
  `VITAMIN_E_TOCOPHEROL_EQUIVALENT` are distinct concepts.
- Equal units never establish RE=RAE, NE=niacin, or tocopherol-equivalent=alpha-tocopherol.
- No component-to-equivalent conversion formula is introduced in this step.
- `folates_source_unspecified` remains unsupported for automatic mapping.

This package publishes no Russian food values, no target table and no Planner/API/UI default.
