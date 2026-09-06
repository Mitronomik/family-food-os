"""Compose existing repositories over one shared read transaction."""

from types import TracebackType

from sqlalchemy.engine import Engine

from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
    SqlAlchemyFoodNutritionProfileRepository,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.household_repositories import (
    SqlAlchemyHouseholdMemberRepository,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_repositories import (
    SqlAlchemyNutritionEvidenceRepository,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyReadOnlyScope


class SqlAlchemyNutritionReadScope:
    def __init__(self, engine: Engine) -> None:
        self._scope = SqlAlchemyReadOnlyScope(engine)

    @property
    def evidence(self) -> SqlAlchemyNutritionEvidenceRepository:
        return SqlAlchemyNutritionEvidenceRepository(self._scope.adapter_connection)

    @property
    def ingredients(self) -> SqlAlchemyFoodIngredientRepository:
        return SqlAlchemyFoodIngredientRepository(self._scope.adapter_connection)

    @property
    def nutrition_profiles(self) -> SqlAlchemyFoodNutritionProfileRepository:
        return SqlAlchemyFoodNutritionProfileRepository(self._scope.adapter_connection)

    @property
    def versions(self) -> SqlAlchemyRecipeVersionRepository:
        return SqlAlchemyRecipeVersionRepository(self._scope.adapter_connection)

    @property
    def members(self) -> SqlAlchemyHouseholdMemberRepository:
        return SqlAlchemyHouseholdMemberRepository(self._scope.adapter_connection)

    def __enter__(self) -> "SqlAlchemyNutritionReadScope":
        self._scope.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._scope.__exit__(exc_type, exc_value, traceback)
