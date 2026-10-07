"""Planner v0.5 household slot ordering and exact DC4 Fixture 3 proof."""

from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID


from app.db.config import DatabaseConfig
from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
)
from app.domain.nutrition import NutritionStatus
from app.domain.planner import (
    MemberPlannerConstraints,
    PlannerCandidate,
    PlannerConfig,
    PlannerFailure,
    PlannerFailureCode,
    PlannerRequest,
    PlannerSuccess,
    generate_week,
)
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdReadScope
from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.r3d_final_dc3_batch import seed_r3d_final_dc3_batch
from app.services.meal_plans import MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from scripts.gate1a_fixture_spec import GATE1_ROLE_SHAPES

WEEK_START = date(2026, 9, 14)
NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


def uid(number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{number:012d}")


def selection(
    member_id: UUID,
    roles_and_shares: tuple[tuple[MealRole, Decimal], ...],
) -> MemberMealPatternSelectionDetail:
    selection_id = uid(1000 + int(member_id.hex[-2:], 16))
    selected = MemberMealPatternSelection(
        id=selection_id,
        household_id=uid(1),
        member_id=member_id,
        version_number=1,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        program_version_id=None,
        recommender_version=None,
        has_user_overrides=False,
        accepted_at=NOW,
        supersedes_selection_id=None,
        created_at=NOW,
    )
    opportunities = tuple(
        MemberMealPatternOpportunitySnapshot(
            selection_id,
            weekday,
            position,
            role,
            share,
        )
        for weekday in range(1, 8)
        for position, (role, share) in enumerate(roles_and_shares, start=1)
    )
    return MemberMealPatternSelectionDetail(selected, opportunities)


def candidate(number: int, meal_type: MealTypeCode) -> PlannerCandidate:
    return PlannerCandidate(
        uid(number),
        meal_type,
        frozenset(),
        Decimal("500"),
        NutritionStatus.COMPLETE,
        True,
        30,
        False,
        False,
    )


def heterogeneous_request(
    second_roles: tuple[tuple[MealRole, Decimal], ...] = (
        (MealRole.BREAKFAST, Decimal("0.30")),
        (MealRole.DINNER, Decimal("0.25")),
    ),
) -> PlannerRequest:
    first, second, third = uid(2), uid(3), uid(4)
    return PlannerRequest(
        uid(1),
        WEEK_START,
        (
            MemberPlannerConstraints(
                first,
                selection(
                    first,
                    (
                        (MealRole.BREAKFAST, Decimal("0.30")),
                        (MealRole.LUNCH, Decimal("0.35")),
                        (MealRole.DINNER, Decimal("0.25")),
                    ),
                ),
                Decimal("2000"),
            ),
            MemberPlannerConstraints(
                second,
                selection(second, second_roles),
                Decimal("2000"),
            ),
            MemberPlannerConstraints(
                third,
                selection(third, ((MealRole.DINNER, Decimal("0.25")),)),
                Decimal("2000"),
            ),
        ),
        (
            candidate(10, MealTypeCode.BREAKFAST),
            candidate(11, MealTypeCode.MAIN),
        ),
    )


def roles_for_member(result: PlannerSuccess, member_id: UUID) -> tuple[MealRole, ...]:
    return tuple(
        event.role
        for event in result.events
        if event.local_date == WEEK_START
        and member_id in event.participant_member_ids
    )


def test_v05_preserves_every_member_precedence_and_v04_replay_stays_unchanged() -> None:
    request = heterogeneous_request()
    v04 = generate_week(
        request,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=20),
    )
    v05 = generate_week(
        request,
        PlannerConfig(version="planner-v0.5", max_recipe_repetitions=20),
    )
    repeated = generate_week(
        request,
        PlannerConfig(version="planner-v0.5", max_recipe_repetitions=20),
    )

    assert isinstance(v04, PlannerSuccess)
    assert isinstance(v05, PlannerSuccess)
    assert isinstance(repeated, PlannerSuccess)

    first, second, third = (member.member_id for member in request.members)
    assert roles_for_member(v04, first) == (
        MealRole.BREAKFAST,
        MealRole.DINNER,
        MealRole.LUNCH,
    )
    assert roles_for_member(v05, first) == (
        MealRole.BREAKFAST,
        MealRole.LUNCH,
        MealRole.DINNER,
    )
    assert roles_for_member(v05, second) == (
        MealRole.BREAKFAST,
        MealRole.DINNER,
    )
    assert roles_for_member(v05, third) == (MealRole.DINNER,)

    assert [event.role for event in v05.events[:3]] == [
        MealRole.BREAKFAST,
        MealRole.LUNCH,
        MealRole.DINNER,
    ]
    assert v04.trace.config_version == "planner-v0.4"
    assert v05.trace.config_version == "planner-v0.5"
    assert v05.trace.fingerprint == repeated.trace.fingerprint
    assert v05.events == repeated.events
    assert v04.trace.fingerprint != v05.trace.fingerprint


def test_v05_preserves_repeated_role_occurrence_order() -> None:
    first, second = uid(2), uid(3)
    request = PlannerRequest(
        uid(1),
        WEEK_START,
        (
            MemberPlannerConstraints(
                first,
                selection(
                    first,
                    (
                        (MealRole.BREAKFAST, Decimal("0.20")),
                        (MealRole.SNACK, Decimal("0.10")),
                        (MealRole.SNACK, Decimal("0.10")),
                        (MealRole.DINNER, Decimal("0.20")),
                    ),
                ),
                Decimal("2000"),
            ),
            MemberPlannerConstraints(
                second,
                selection(
                    second,
                    (
                        (MealRole.BREAKFAST, Decimal("0.20")),
                        (MealRole.DINNER, Decimal("0.20")),
                    ),
                ),
                Decimal("2000"),
            ),
        ),
        (
            candidate(10, MealTypeCode.BREAKFAST),
            candidate(12, MealTypeCode.SANDWICH),
            candidate(11, MealTypeCode.MAIN),
        ),
    )

    result = generate_week(
        request,
        PlannerConfig(version="planner-v0.5", max_recipe_repetitions=20),
    )

    assert isinstance(result, PlannerSuccess)
    assert roles_for_member(result, first) == (
        MealRole.BREAKFAST,
        MealRole.SNACK,
        MealRole.SNACK,
        MealRole.DINNER,
    )
    assert roles_for_member(result, second) == (
        MealRole.BREAKFAST,
        MealRole.DINNER,
    )


def test_v05_incompatible_member_precedence_fails_closed() -> None:
    first, second = uid(2), uid(3)
    request = PlannerRequest(
        uid(1),
        WEEK_START,
        (
            MemberPlannerConstraints(
                first,
                selection(
                    first,
                    (
                        (MealRole.BREAKFAST, Decimal("0.50")),
                        (MealRole.DINNER, Decimal("0.50")),
                    ),
                ),
                Decimal("2000"),
            ),
            MemberPlannerConstraints(
                second,
                selection(
                    second,
                    (
                        (MealRole.DINNER, Decimal("0.50")),
                        (MealRole.BREAKFAST, Decimal("0.50")),
                    ),
                ),
                Decimal("2000"),
            ),
        ),
        (
            candidate(10, MealTypeCode.BREAKFAST),
            candidate(11, MealTypeCode.MAIN),
        ),
    )

    result = generate_week(
        request,
        PlannerConfig(version="planner-v0.5", max_recipe_repetitions=20),
    )

    assert isinstance(result, PlannerFailure)
    assert result.code is PlannerFailureCode.INCOMPATIBLE_SLOT_ORDER
    assert result.trace.final_events == ()
    assert "cannot be reconciled" in result.message


def meal_plan_service(engine) -> MealPlanService:
    return MealPlanService(
        lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        lambda: SqlAlchemyMealPlanReadScope(engine),
        lambda: SqlAlchemyHouseholdReadScope(engine),
        lambda: SqlAlchemyMealPatternCatalogueReadScope(engine),
    )


def test_v05_exact_dc4_fixture3_persists_21_events_and_42_servings(tmp_path) -> None:
    config = DatabaseConfig(path=tmp_path / "planner-v05-dc4.sqlite")
    seed_r3d_final_dc3_batch(config)
    engine = create_sqlite_engine(config)
    try:
        households = create_household_service(engine)
        meal_plans = meal_plan_service(engine)
        recipes = create_food_recipe_catalogue_service(engine)
        nutrition = create_nutrition_service(engine)
        pantry = create_pantry_service(engine)
        recipe_nutrition = create_recipe_nutrition_v2_service(engine)
        planner = PlannerService(
            meal_plans,
            households,
            recipes,
            nutrition,
            pantry,
            PlannerConfig(version="planner-v0.5", max_recipe_repetitions=3),
            recipe_nutrition=recipe_nutrition,
        )
        food = create_food_catalogue_service(engine)

        household = households.create_household(
            name="DC4 Fixture 3 v0.5",
            timezone_name="Europe/Moscow",
            city="Санкт-Петербург",
        )
        members = []
        selections = {}
        share_by_role = {
            MealRole.BREAKFAST: Decimal("0.30"),
            MealRole.LUNCH: Decimal("0.35"),
            MealRole.DINNER: Decimal("0.25"),
        }
        for index, roles in enumerate(GATE1_ROLE_SHAPES[2], 1):
            member = households.add_household_member(
                household.id,
                name=f"Участник {index}",
                birth_date=date(1990, 1, index),
                sex="female" if index % 2 else "male",
                height_cm=Decimal(170),
                weight_kg=Decimal(65),
                activity_level="active",
                goal="maintain",
            )
            accepted = meal_plans.accept_member_pattern(
                household_id=household.id,
                member_id=member.id,
                source_kind=MemberMealPatternSourceKind.CUSTOM,
                schedule={weekday: roles for weekday in range(1, 8)},
                energy_shares={
                    weekday: tuple(share_by_role[role] for role in roles)
                    for weekday in range(1, 8)
                },
            )
            members.append(member)
            selections[member.id] = accepted

        beef_id = food.get_by_code("BEEF_CATEGORY_1_RAW").id
        command = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(members[0].id),
                GenerationMemberConstraints(members[1].id),
                GenerationMemberConstraints(
                    members[2].id,
                    frozenset({beef_id}),
                ),
            ),
        )

        pure_request = planner.compose_authoritative_request(command)
        pure_first = generate_week(
            pure_request,
            PlannerConfig(version="planner-v0.5", max_recipe_repetitions=3),
        )
        pure_second = generate_week(
            pure_request,
            PlannerConfig(version="planner-v0.5", max_recipe_repetitions=3),
        )
        result, persisted = planner.generate_authoritative(command)

        assert isinstance(pure_first, PlannerSuccess)
        assert isinstance(pure_second, PlannerSuccess)
        assert pure_first.trace.fingerprint == pure_second.trace.fingerprint
        assert isinstance(result, PlannerSuccess)
        assert result.trace.config_version == "planner-v0.5"
        assert persisted is not None
        assert persisted.plan.config_version == "planner-v0.5"
        assert len(persisted.events) == 21
        assert len(persisted.servings) == 42

        participants_by_event = defaultdict(set)
        for serving in persisted.servings:
            participants_by_event[serving.event_id].add(serving.member_id)

        ordered_events = sorted(
            persisted.events,
            key=lambda event: (event.local_date, event.position),
        )
        for member in members:
            expected = selections[member.id].roles_for_weekday(1)
            actual = tuple(
                event.role
                for event in ordered_events
                if event.local_date == WEEK_START
                and member.id in participants_by_event[event.id]
            )
            assert actual == expected

        current_by_version = {
            detail.version.id: detail
            for recipe in recipes.list_active(limit=200)
            for detail in (recipes.get_current_verified(recipe.id),)
        }
        for event in ordered_events:
            if (
                event.local_date != WEEK_START
                or members[2].id not in participants_by_event[event.id]
                or event.recipe_version_id is None
            ):
                continue
            ingredient_ids = {
                row.food_ingredient_id
                for row in current_by_version[event.recipe_version_id].ingredients
            }
            assert beef_id not in ingredient_ids
    finally:
        engine.dispose()
