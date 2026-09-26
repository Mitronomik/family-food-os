"""Step 10-A publication of the exact Step 9 RecipeIngredient composition binding."""

import json
from decimal import Decimal

from app.db.config import DatabaseConfig
from app.domain.nutrition import NutritionStatus
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES, RecipeNutritionV2Status
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
)
from app.services.recipe_nutrition_v2 import (
    BindingPublicationResult,
    ReviewedRecipeIngredientBindingSpec,
)

SOURCE_VERSION = f"sha256:{SCHOOL_PDF_SHA256}"

STEP10A_BINDING_SPEC = ReviewedRecipeIngredientBindingSpec(
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
)


def seed_ru_school2022_step10a_binding(
    config: DatabaseConfig | None = None,
) -> BindingPublicationResult:
    engine = create_sqlite_engine(config)
    try:
        service = create_recipe_nutrition_v2_service(engine)
        result = service.publish_binding(STEP10A_BINDING_SPEC)
        canonical = service.calculate(result.recipe_version_id)
        if canonical.status is not RecipeNutritionV2Status.PARTIAL:
            raise RuntimeError("Step 10-A canonical Step 9 status изменён.")
        known = {
            item.code: item.amount
            for item in canonical.required_total
            if item.amount is not None
        }
        if known != EXPECTED_RECIPE_AMOUNTS:
            raise RuntimeError("Step 10-A canonical Step 9 nutrient values изменены.")
        if len(canonical.required_total) != len(NUTRIENT_CODES):
            raise RuntimeError("Step 10-A canonical request set изменён.")
        projection = service.consumption_projection(result.recipe_version_id)
        if (
            projection.legacy_status is not NutritionStatus.INCOMPLETE
            or projection.required_total.kcal != Decimal("66.090000")
            or projection.required_total.protein_g != Decimal("0.080000")
            or projection.required_total.fat_g != Decimal("7.250000")
            or projection.required_total.fiber_g != Decimal("0.000000")
            or projection.required_total.carbohydrates_g is not None
        ):
            raise RuntimeError("Step 10-A legacy compatibility projection изменена.")
        return result
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
