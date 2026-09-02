from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.domain.food_ingredients import (
    FoodIngredient,
    FoodNutritionProfile,
    IngredientAlias,
)
from app.services.food_ingredients import (
    FoodCatalogueService,
    TrustedAliasSeed,
    TrustedFoodIngredientSeed,
    TrustedNutritionSeed,
)

NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)


@dataclass
class Store:
    ingredients: dict[UUID, FoodIngredient] = field(default_factory=dict)
    aliases: dict[str, IngredientAlias] = field(default_factory=dict)
    nutrition: dict[tuple[UUID, str, str, str], FoodNutritionProfile] = field(
        default_factory=dict
    )


class IngredientRepo:
    def __init__(self, values):
        self.values = values

    def add(self, ingredient):
        self.values[ingredient.id] = ingredient

    def get(self, ingredient_id):
        return self.values.get(ingredient_id)

    def get_by_code(self, code):
        return next((x for x in self.values.values() if x.canonical_code == code), None)

    def get_by_name_key(self, key):
        return next(
            (x for x in self.values.values() if x.canonical_name_key == key), None
        )

    def list_active(self, *, limit):
        return sorted(
            (x for x in self.values.values() if x.is_active),
            key=lambda x: (x.canonical_name_key, x.canonical_code),
        )[:limit]

    def search_active(self, key, *, limit):
        return [
            x
            for x in self.list_active(limit=200)
            if key in x.canonical_name_key or key == x.canonical_code.casefold()
        ][:limit]

    def set_active(self, ingredient_id, *, active, updated_at):
        from dataclasses import replace

        self.values[ingredient_id] = replace(
            self.values[ingredient_id], is_active=active, updated_at=updated_at
        )


class AliasRepo:
    def __init__(self, values, *, fail=False):
        self.values = values
        self.fail = fail

    def add(self, alias):
        self.values[alias.alias_key] = alias
        if self.fail:
            raise RuntimeError("simulated alias persistence failure")

    def get_by_key(self, key):
        return self.values.get(key)

    def list_for_ingredient(self, ingredient_id):
        return [
            x for x in self.values.values() if x.food_ingredient_id == ingredient_id
        ]


class NutritionRepo:
    def __init__(self, values):
        self.values = values

    def add(self, profile):
        self.values[profile.provenance_key] = profile

    def get_by_provenance(self, ingredient_id, source_name, source_id, source_version):
        return self.values.get((ingredient_id, source_name, source_id, source_version))

    def get_current(self, ingredient_id):
        return next(
            (
                value
                for value in self.values.values()
                if value.food_ingredient_id == ingredient_id and value.is_current
            ),
            None,
        )

    def clear_current(self, ingredient_id):
        from dataclasses import replace

        for key, value in tuple(self.values.items()):
            if value.food_ingredient_id == ingredient_id and value.is_current:
                self.values[key] = replace(value, is_current=False)


class WriteScope:
    def __init__(self, store, record, *, fail_alias=False):
        self.store = store
        self.record = record
        self.working = Store(
            ingredients=dict(store.ingredients),
            aliases=dict(store.aliases),
            nutrition=dict(store.nutrition),
        )
        self.ingredients = IngredientRepo(self.working.ingredients)
        self.aliases = AliasRepo(self.working.aliases, fail=fail_alias)
        self.nutrition_profiles = NutritionRepo(self.working.nutrition)
        self.completed = False
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        self.record.append(self)
        return self

    def commit(self):
        self.store.ingredients = self.working.ingredients
        self.store.aliases = self.working.aliases
        self.store.nutrition = self.working.nutrition
        self.completed = True
        self.committed = True

    def rollback(self):
        self.completed = True
        self.rolled_back = True

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.completed:
            self.rollback()


class ReadScope:
    def __init__(self, store):
        self.ingredients = IngredientRepo(store.ingredients)
        self.aliases = AliasRepo(store.aliases)
        self.nutrition_profiles = NutritionRepo(store.nutrition)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None


def entry():
    return TrustedFoodIngredientSeed(
        canonical_code="BUCKWHEAT",
        canonical_name="Гречневая крупа",
        category_code="grains",
        default_unit="g",
        density_g_per_ml=None,
        edible_fraction=None,
        allergens_reviewed=False,
        allergen_codes=(),
        storage_profile_code=None,
        aliases=(TrustedAliasSeed("гречка"),),
        nutrition=TrustedNutritionSeed(
            basis_grams=Decimal("100"),
            kcal=Decimal("331.600521"),
            protein_g=Decimal("11.065340"),
            fat_g=Decimal("3.039000"),
            carbohydrates_g=Decimal("71.130660"),
            fiber_g=Decimal("4.046000"),
            source_name="USDA_FDC",
            source_id="2512378",
            source_version="2026-04-30",
            source_data_type="Foundation",
            verified_at=NOW,
            estimated=None,
        ),
    )


def service(store, scopes, *, fail_alias=False):
    return FoodCatalogueService(
        write_scope_factory=lambda: WriteScope(store, scopes, fail_alias=fail_alias),
        read_scope_factory=lambda: ReadScope(store),
        id_factory=uuid4,
        clock=lambda: NOW,
    )


def test_application_adds_complete_catalogue_item_and_commits_explicitly():
    store = Store()
    scopes = []
    application = service(store, scopes)

    created = application.add_trusted_ingredient(entry())

    assert scopes[-1].committed is True
    assert scopes[-1].rolled_back is False
    assert store.ingredients[created.id] == created
    assert store.aliases["гречка"].food_ingredient_id == created.id
    assert next(iter(store.nutrition.values())).food_ingredient_id == created.id
    assert application.get_by_code("BUCKWHEAT") == created


def test_application_failure_rolls_back_complete_multi_repository_command():
    store = Store()
    scopes = []
    application = service(store, scopes, fail_alias=True)

    with pytest.raises(RuntimeError, match="simulated"):
        application.add_trusted_ingredient(entry())

    assert store.ingredients == {}
    assert store.aliases == {}
    assert store.nutrition == {}
    assert scopes[-1].committed is False
    assert scopes[-1].rolled_back is True


@pytest.mark.parametrize("limit", [0, 201, True, 1.5])
def test_application_enforces_bounded_result_limit(limit):
    application = service(Store(), [])
    with pytest.raises(ValueError, match="limit"):
        application.list_active(limit=limit)
