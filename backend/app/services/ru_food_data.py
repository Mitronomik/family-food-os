"""One transactional reconciliation of the reviewed RU food-data operation."""

from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import datetime, timezone
from typing import Any, Protocol, Self
from uuid import UUID, uuid4

from app.domain.food_composition import (
    CompositionKind,
    CompositionProvenance,
    FoodCompositionVersion,
    MassState,
)
from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    normalize_unicode_search_key,
)
from app.domain.units import UnitCode
from app.domain.nutrient_vector_backfill_v1 import value_set_digest
from app.services.food_ingredient_contracts import (
    FoodIngredientRepository,
    FoodNutritionProfileRepository,
    IngredientAliasRepository,
)
from app.services.food_composition_contracts import CompositionWriter
from app.services.nutrient_vector_contracts import NutrientVectorReader
from app.services.food_composition import CompositionCalculator


class RuCompositionWriter(CompositionWriter, Protocol):
    def find_version(
        self, food_id: UUID, version: int
    ) -> FoodCompositionVersion | None: ...


class RuFoodUnitOfWork(Protocol):
    @property
    def ingredients(self) -> FoodIngredientRepository: ...

    @property
    def aliases(self) -> IngredientAliasRepository: ...

    @property
    def nutrition_profiles(self) -> FoodNutritionProfileRepository: ...

    @property
    def compositions(self) -> RuCompositionWriter: ...

    @property
    def nutrient_vectors(self) -> NutrientVectorReader: ...

    def publish_vector(
        self,
        profile: FoodNutritionProfile,
        values: list[dict[str, Any]],
        observations: str,
    ) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, *args: Any) -> bool | None: ...
    def commit(self) -> None: ...


def reconcile_ru_food_data(
    factory: Callable[[], RuFoodUnitOfWork], entries: tuple[dict[str, Any], ...]
) -> dict[str, int]:
    counts = {
        k: 0
        for k in (
            "ingredients",
            "profiles",
            "nutrient_values",
            "vector_seals",
            "atomic_compositions",
        )
    }
    with factory() as uow:
        for entry in entries:
            row = entry["row"]
            code = row["food_code"]
            ingredient = uow.ingredients.get_by_code(code)
            newly_created = ingredient is None
            if ingredient is None:
                if row["decision"] != "PROMOTE":
                    raise ValueError("Отсутствует исходный продукт каталога.")
                key = normalize_unicode_search_key(row["canonical_name_ru"])
                if uow.ingredients.get_by_name_key(key) or uow.aliases.get_by_key(key):
                    raise ValueError("Название нового продукта уже занято.")
                now = datetime.now(timezone.utc)
                ingredient = FoodIngredient(
                    id=uuid4(),
                    canonical_code=code,
                    canonical_name=row["canonical_name_ru"],
                    canonical_name_key=key,
                    category_code=entry["category_code"],
                    default_unit=UnitCode.GRAM,
                    density_g_per_ml=None,
                    edible_fraction=None,
                    allergens_reviewed=False,
                    allergen_codes=(),
                    storage_profile_code=None,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                uow.ingredients.add(ingredient)
                counts["ingredients"] += 1
            if (
                ingredient.canonical_name != row["canonical_name_ru"]
                or not ingredient.is_active
            ):
                raise ValueError(
                    "Название или доступность продукта каталога изменились."
                )
            expected = FoodNutritionProfile(
                id=uuid4(),
                food_ingredient_id=ingredient.id,
                **entry["profile"],
                is_current=True,
                created_at=datetime.now(timezone.utc),
            )
            # Exact provenance lookup, deliberately never get_current().
            profile = uow.nutrition_profiles.get_by_provenance(
                ingredient.id,
                expected.source_name,
                expected.source_id,
                expected.source_version,
            )
            if profile is None:
                if row["decision"] != "PROMOTE" or not newly_created:
                    raise ValueError("Отсутствует закреплённый профиль продукта.")
                # Existing unrelated profiles cannot be retired by this operation.
                if uow.nutrition_profiles.get_current(ingredient.id) is not None:
                    raise ValueError("Замена существующего профиля запрещена.")
                profile = expected
                uow.nutrition_profiles.add(profile)
                uow.publish_vector(profile, entry["values"], entry["observations"])
                counts["profiles"] += 1
                counts["nutrient_values"] += len(entry["values"])
                counts["vector_seals"] += 1
            if profile.snapshot_values() != expected.snapshot_values():
                raise ValueError(
                    "Закреплённый профиль не совпадает с проверенным источником."
                )
            vector = uow.nutrient_vectors.get(profile.id)
            if vector.observations_json != entry["observations"]:
                raise ValueError(
                    "История наблюдений вектора не совпадает с проверенной."
                )
            actual_values = [
                {
                    "nutrient_code": v.definition.code,
                    "amount": v.amount,
                    "provenance_json": v.provenance.evidence_json,
                }
                for v in vector.values
            ]
            if (
                value_set_digest(actual_values)
                != row["vector_reference"]["value_sha256"]
                or len(actual_values) != row["vector_reference"]["value_count"]
            ):
                raise ValueError(
                    "Снимок нутриентов не соответствует проверенному набору."
                )
            version = uow.compositions.find_version(ingredient.id, 1)
            expected_version = FoodCompositionVersion(
                id=uuid4(),
                food_ingredient_id=ingredient.id,
                version=1,
                kind=CompositionKind.ATOMIC,
                input_state=MassState(row["mass_state"]),
                profile_id=profile.id,
                provenance=CompositionProvenance(
                    "PR6-RU-FOOD-DATA",
                    "1",
                    f"data/curation/pr6-ru-food-data/food-readiness.json#{code}",
                    row["review_reference"],
                ),
            )
            if version is None:
                version = expected_version
                uow.compositions.add_versions((version,))
                counts["atomic_compositions"] += 1
            elif asdict(version) != asdict(replace(expected_version, id=version.id)):
                raise ValueError(
                    "Существующая версия состава отличается от проверенной."
                )
            CompositionCalculator(uow.compositions, uow.nutrient_vectors).calculate(
                version.id,
                nutrient_codes=("ENERGY_KCAL", "PROTEIN", "CALCIUM"),
            )
        uow.commit()
    return counts
