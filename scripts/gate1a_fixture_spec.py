"""Current repository Gate 1 fixture schedules shared with audit tests."""

from app.domain.meal_patterns import MealRole

GATE1_ROLE_SHAPES = (
    ((MealRole.DINNER,),),
    ((MealRole.BREAKFAST, MealRole.DINNER), (MealRole.DINNER,)),
    (
        (MealRole.BREAKFAST, MealRole.LUNCH, MealRole.DINNER),
        (MealRole.BREAKFAST, MealRole.DINNER),
        (MealRole.DINNER,),
    ),
)
