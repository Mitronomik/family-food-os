"""Step 10-A publication of the exact Step 9 RecipeIngredient composition binding."""

import json
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.ru_school2022_step9_recipe import (
    EXPECTED_RECIPE_AMOUNTS,
    FOOD_CODE,
    RECIPE_CODE,
    SCHOOL_PDF_SHA256,
    SOURCE_RECIPE_ID,
    load_ru_school2022_step9_recipe_seed,
)
from app.services.recipe_nutrition_v2 import (
    BindingPublicationResult,
    ReviewedRecipeIngredientBindingSpec,
)

SOURCE_VERSION = f"sha256:{SCHOOL_PDF_SHA256}"

def step10a_binding_spec() -> ReviewedRecipeIngredientBindingSpec:
    trusted_seed, _ = load_ru_school2022_step9_recipe_seed()
    return ReviewedRecipeIngredientBindingSpec(
        trusted_recipe_seed=trusted_seed,
        recipe_code=RECIPE_CODE,
        source_name="ru-school2022",
        source_recipe_id=SOURCE_RECIPE_ID,
        source_version=SOURCE_VERSION,
        recipe_version_number=1,
        ingredient_position=1,
        food_ingredient_code=FOOD_CODE,
        quantity=Decimal("10"),
        unit="g",
        composition_version=1,
        composition_kind="ATOMIC",
        composition_input_state="INPUT",
        expected_available_amounts=tuple(
            (code, EXPECTED_RECIPE_AMOUNTS[code])
            for code in NUTRIENT_CODES
            if code in EXPECTED_RECIPE_AMOUNTS
        ),
        expected_unknown_codes=tuple(
            code for code in NUTRIENT_CODES if code not in EXPECTED_RECIPE_AMOUNTS
        ),
    )


def seed_ru_school2022_step10a_binding(
    config: DatabaseConfig | None = None,
) -> BindingPublicationResult:
    spec = step10a_binding_spec()
    engine = create_sqlite_engine(config)
    try:
        service = create_recipe_nutrition_v2_service(engine)
        return service.publish_binding(spec)
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_ru_school2022_step10a_binding()
    print(
        json.dumps(
            {
                "disposition": result.disposition.value,
                "recipe_ingredient_id": str(result.binding.recipe_ingredient_id),
                "composition_version_id": str(result.binding.composition_version_id),
                "recipe_version_id": str(result.recipe_version_id),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
