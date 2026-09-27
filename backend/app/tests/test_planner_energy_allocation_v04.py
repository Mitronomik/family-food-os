import json
import shutil
import sqlite3
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from uuid import UUID

import pytest

from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import (
    MealSourceKind,
    MemberMealPatternOpportunitySnapshot,
    MemberMealPatternSelection,
    MemberMealPatternSelectionDetail,
    MemberMealPatternSourceKind,
)
from app.domain.nutrition import NutritionStatus
from app.domain.planner import (
    FixedPlannerEvent,
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
from app.persistence.sqlalchemy_core.meal_pattern_composition import (
    create_meal_pattern_catalogue_service,
)
from app.persistence.sqlalchemy_core.meal_pattern_repositories import (
    SqlAlchemyMealPatternVersionRepository,
)
from app.seed.meal_patterns import seed_meal_patterns
from app.seed.planner_energy_allocation_v04 import (
    DEFAULT_PACKAGE,
    PlannerEnergyAllocationSeedError,
    load_planner_energy_allocation_seeds,
    seed_planner_energy_allocation_v04,
)
from app.services.meal_patterns import MealPatternCatalogueConflictError

NOW = datetime(2026, 9, 27, tzinfo=timezone.utc)
WEEK_START = date(2026, 9, 28)


def uid(number: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{number:012d}")


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def migrate_through_0040(config: DatabaseConfig) -> None:
    original = list(migrations.MIGRATION_MODULES)
    cutoff = next(
        index
        for index, module in enumerate(original)
        if module.endswith("0040_recipe_version_source_output")
    )
    try:
        migrations.MIGRATION_MODULES[:] = original[: cutoff + 1]
        migrations.apply_migrations(config)
    finally:
        migrations.MIGRATION_MODULES[:] = original


def selection(
    member_id: UUID,
    roles_and_shares: tuple[tuple[MealRole, Decimal | None], ...],
    *,
    source_kind: MemberMealPatternSourceKind = MemberMealPatternSourceKind.CUSTOM,
    program_version_id: UUID | None = None,
    has_user_overrides: bool = False,
) -> MemberMealPatternSelectionDetail:
    selection_id = uid(1000 + int(member_id.hex[-2:], 16))
    selected = MemberMealPatternSelection(
        id=selection_id,
        household_id=uid(1),
        member_id=member_id,
        version_number=1,
        source_kind=source_kind,
        program_version_id=program_version_id,
        recommender_version=None,
        has_user_overrides=has_user_overrides,
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


def candidate(
    number: int,
    meal_type: MealTypeCode,
    *,
    kcal: str = "500",
    ingredients: frozenset[UUID] = frozenset(),
) -> PlannerCandidate:
    return PlannerCandidate(
        uid(number),
        meal_type,
        ingredients,
        Decimal(kcal),
        NutritionStatus.COMPLETE,
        True,
        20,
        False,
    )


def test_0041_upgrade_preserves_history_triggers_and_rolls_back_mid_migration(
    tmp_path, monkeypatch
):
    config = DatabaseConfig(path=tmp_path / "upgrade.sqlite")
    migrate_through_0040(config)

    program_id = uid(10).hex
    version_id = uid(11).hex
    household_id = uid(12).hex
    member_id = uid(13).hex
    selection_id = uid(14).hex
    with sqlite3.connect(config.path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "INSERT INTO meal_pattern_programs (id, program_code, created_at) "
            "VALUES (?, 'HISTORICAL_PATTERN', ?)",
            (program_id, NOW.isoformat()),
        )
        db.execute(
            """INSERT INTO meal_pattern_program_versions (
                id, program_id, version_number, lifecycle, scope_code,
                display_name_ru, explanation_ru, min_age_years, max_age_years,
                review_status, reviewed_at, published_at, created_from_version_id,
                change_note, created_at
            ) VALUES (?, ?, 1, 'PUBLISHED', 'WELLNESS_SCHEDULE',
                      'Исторический режим', 'Исторический режим питания.', 19, NULL,
                      'REVIEWED', ?, ?, NULL, 'historical', ?)""",
            (version_id, program_id, NOW.isoformat(), NOW.isoformat(), NOW.isoformat()),
        )
        db.execute(
            "INSERT INTO meal_pattern_opportunities "
            "(version_id, position, role_code) VALUES (?, 1, 'DINNER')",
            (version_id,),
        )
        db.execute(
            """INSERT INTO households
            (id, name, timezone, city, default_weekly_budget,
             default_cooking_profile, created_at, updated_at)
            VALUES (?, 'Home', 'Europe/Moscow', NULL, NULL, NULL, ?, ?)""",
            (household_id, NOW.isoformat(), NOW.isoformat()),
        )
        db.execute(
            """INSERT INTO household_members
            (id, household_id, name, active, birth_date, sex, height_cm, weight_kg,
             activity_level, goal, created_at, updated_at)
            VALUES (?, ?, 'Anna', 1, '1990-05-20', 'female', '168', '62',
                    'moderate', 'maintain', ?, ?)""",
            (member_id, household_id, NOW.isoformat(), NOW.isoformat()),
        )
        db.execute(
            """INSERT INTO member_meal_pattern_selections
            (id, household_id, member_id, version_number, source_kind,
             program_version_id, recommender_version, has_user_overrides,
             accepted_at, supersedes_selection_id, created_at)
            VALUES (?, ?, ?, 1, 'CUSTOM', NULL, NULL, 0, ?, NULL, ?)""",
            (selection_id, household_id, member_id, NOW.isoformat(), NOW.isoformat()),
        )
        db.execute(
            "INSERT INTO member_meal_pattern_opportunities "
            "(selection_id, weekday, position, role_code) "
            "VALUES (?, 1, 1, 'DINNER')",
            (selection_id,),
        )
        db.commit()
    before = db_dump(config)

    module = import_module(
        "app.migrations.versions.0041_meal_pattern_energy_allocation"
    )
    original_upgrade = module.upgrade

    def fail_after_first(connection):
        connection.execute(
            "ALTER TABLE meal_pattern_opportunities ADD COLUMN energy_share TEXT"
        )
        raise RuntimeError("injected 0041 failure")

    monkeypatch.setattr(module, "upgrade", fail_after_first)
    with pytest.raises(RuntimeError, match="injected 0041 failure"):
        migrations.apply_migrations(config)

    assert "0041_meal_pattern_energy_allocation" not in migrations.current_migrations(
        config
    )
    with sqlite3.connect(config.path) as db:
        assert "energy_share" not in {
            row[1] for row in db.execute("PRAGMA table_info(meal_pattern_opportunities)")
        }
        assert "energy_share" not in {
            row[1]
            for row in db.execute(
                "PRAGMA table_info(member_meal_pattern_opportunities)"
            )
        }
    assert db_dump(config) == before

    monkeypatch.setattr(module, "upgrade", original_upgrade)
    assert migrations.apply_migrations(config) == [
        "0041_meal_pattern_energy_allocation"
    ]
    with sqlite3.connect(config.path) as db:
        assert db.execute(
            "SELECT energy_share FROM meal_pattern_opportunities WHERE version_id=?",
            (version_id,),
        ).fetchone() == (None,)
        assert db.execute(
            "SELECT energy_share FROM member_meal_pattern_opportunities "
            "WHERE selection_id=?",
            (selection_id,),
        ).fetchone() == (None,)
        for table in (
            "meal_pattern_opportunities",
            "member_meal_pattern_opportunities",
        ):
            triggers = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?",
                    (table,),
                )
            }
            assert any(name.endswith("no_update") for name in triggers)
            assert any(name.endswith("no_delete") for name in triggers)
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_reviewed_program_publication_is_bounded_exact_and_zero_write_replay(tmp_path):
    config = DatabaseConfig(path=tmp_path / "programs.sqlite")
    first = seed_planner_energy_allocation_v04(config)
    assert first.programs_existing == 2
    assert first.versions_inserted == 2
    assert first.versions_existing == 0

    engine = create_sqlite_engine(config)
    try:
        service = create_meal_pattern_catalogue_service(engine)
        three = service.get_exact("ADULT_REGULAR_3", 2)
        snack = service.get_exact("ADULT_REGULAR_3_PLUS_SNACK", 2)
        assert tuple(item.energy_share for item in three.opportunities) == (
            Decimal("0.300000"),
            Decimal("0.350000"),
            Decimal("0.250000"),
        )
        assert tuple(item.energy_share for item in snack.opportunities) == (
            Decimal("0.300000"),
            Decimal("0.350000"),
            Decimal("0.100000"),
            Decimal("0.250000"),
        )
        assert three.version.created_from_version_id == service.get_exact(
            "ADULT_REGULAR_3", 1
        ).version.id
    finally:
        engine.dispose()

    before = db_dump(config)
    replay = seed_planner_energy_allocation_v04(config)
    assert replay.versions_inserted == 0
    assert replay.versions_existing == 2
    assert db_dump(config) == before


def test_program_publication_conflict_and_second_program_failure_roll_back(
    tmp_path, monkeypatch
):
    config = DatabaseConfig(path=tmp_path / "rollback.sqlite")
    migrations.apply_migrations(config)
    seed_meal_patterns(config)
    before = db_dump(config)

    seeds = load_planner_energy_allocation_seeds()
    changed = replace(
        seeds[0],
        version=replace(
            seeds[0].version,
            opportunity_energy_shares=(
                Decimal("0.29"),
                Decimal("0.35"),
                Decimal("0.25"),
            ),
        ),
    )
    engine = create_sqlite_engine(config)
    try:
        service = create_meal_pattern_catalogue_service(engine)
        service.reconcile_target_versions(seeds)
        with pytest.raises(MealPatternCatalogueConflictError):
            service.reconcile_target_versions((changed, seeds[1]))
    finally:
        engine.dispose()

    # Fresh database proves the whole two-program publication is one transaction.
    config2 = DatabaseConfig(path=tmp_path / "rollback-fresh.sqlite")
    migrations.apply_migrations(config2)
    seed_meal_patterns(config2)
    before2 = db_dump(config2)
    original = SqlAlchemyMealPatternVersionRepository.add_detail
    state = {"calls": 0}

    def fail_second(self, detail):
        state["calls"] += 1
        if state["calls"] == 2:
            raise RuntimeError("injected second program failure")
        return original(self, detail)

    monkeypatch.setattr(SqlAlchemyMealPatternVersionRepository, "add_detail", fail_second)
    with pytest.raises(RuntimeError, match="injected second program failure"):
        seed_planner_energy_allocation_v04(config2)
    assert state["calls"] == 2
    assert db_dump(config2) == before2


def test_package_rejects_unexplained_or_inconsistent_residual(tmp_path):
    payload = json.loads(DEFAULT_PACKAGE.read_text(encoding="utf-8"))
    payload["programs"][0]["residual_share"] = "0.11"
    changed = tmp_path / "programs.json"
    changed.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(PlannerEnergyAllocationSeedError, match="must equal one"):
        load_planner_energy_allocation_seeds(changed)


def test_v04_dinner_only_uses_opportunity_share_and_v03_replay_is_unchanged():
    member_id = uid(2)
    accepted = selection(
        member_id,
        ((MealRole.DINNER, Decimal("0.25")),),
    )
    request = PlannerRequest(
        uid(1),
        WEEK_START,
        (MemberPlannerConstraints(member_id, accepted, Decimal("2000")),),
        (candidate(10, MealTypeCode.MAIN),),
    )

    v04 = generate_week(
        request,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=10),
    )
    assert isinstance(v04, PlannerSuccess)
    assert {portion for event in v04.events for _, portion in event.portions} == {
        Decimal("1.000000")
    }
    assert {
        residual for _, _, residual in v04.trace.member_daily_residual_shares
    } == {Decimal("0.750000")}
    assert len(v04.trace.allocations) == 7
    assert all(item.allocated_kcal == Decimal("500.000000") for item in v04.trace.allocations)

    v03 = generate_week(
        request,
        PlannerConfig(version="planner-v0.3", max_recipe_repetitions=10),
    )
    assert isinstance(v03, PlannerSuccess)
    assert {portion for event in v03.events for _, portion in event.portions} == {
        Decimal("4.000000")
    }
    assert v03.trace.allocations == ()
    assert v03.trace.member_daily_residual_shares == ()


def test_v04_mixed_fixed_source_reserves_share_without_crediting_nutrition():
    member_id = uid(2)
    accepted = selection(
        member_id,
        (
            (MealRole.LUNCH, Decimal("0.35")),
            (MealRole.DINNER, Decimal("0.25")),
        ),
    )
    fixed = FixedPlannerEvent(
        WEEK_START,
        MealRole.LUNCH,
        1,
        MealSourceKind.EAT_OUT,
        "решение пользователя",
        frozenset({member_id}),
        ((member_id, Decimal("1")),),
    )
    request = PlannerRequest(
        uid(1),
        WEEK_START,
        (MemberPlannerConstraints(member_id, accepted, Decimal("2000")),),
        (candidate(10, MealTypeCode.MAIN),),
        fixed_events=(fixed,),
    )
    result = generate_week(
        request,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=10),
    )
    assert isinstance(result, PlannerSuccess)
    monday = [event for event in result.events if event.local_date == WEEK_START]
    assert [event.source_kind for event in monday] == [
        MealSourceKind.EAT_OUT,
        MealSourceKind.COOK_RECIPE,
    ]
    dinner = monday[1]
    assert dict(dinner.portions)[member_id] == Decimal("1.000000")
    fixed_trace = next(
        item
        for item in result.trace.allocations
        if item.local_date == WEEK_START
        and item.role is MealRole.LUNCH
        and item.member_id == member_id
    )
    assert fixed_trace.allocated_kcal == Decimal("700.000000")
    assert fixed_trace.recipe_kcal_per_base_serving is None
    assert "fixed_non_recipe_nutrition_unknown_allocation_reserved" in result.trace.warnings


def test_v04_heterogeneous_members_keep_individual_shares_on_shared_event():
    first, second = uid(2), uid(3)
    members = (
        MemberPlannerConstraints(
            first,
            selection(first, ((MealRole.DINNER, Decimal("0.25")),)),
            Decimal("2000"),
        ),
        MemberPlannerConstraints(
            second,
            selection(second, ((MealRole.DINNER, Decimal("0.30")),)),
            Decimal("2500"),
        ),
    )
    result = generate_week(
        PlannerRequest(uid(1), WEEK_START, members, (candidate(10, MealTypeCode.MAIN),)),
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=10),
    )
    assert isinstance(result, PlannerSuccess)
    monday = next(event for event in result.events if event.local_date == WEEK_START)
    assert dict(monday.portions) == {
        first: Decimal("1.000000"),
        second: Decimal("1.500000"),
    }
    repeated = generate_week(
        PlannerRequest(uid(1), WEEK_START, members, (candidate(10, MealTypeCode.MAIN),)),
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=10),
    )
    assert isinstance(repeated, PlannerSuccess)
    assert repeated.events == result.events
    assert repeated.trace.fingerprint == result.trace.fingerprint


def test_v04_missing_allocation_fails_before_any_partial_plan():
    member_id = uid(2)
    accepted = selection(member_id, ((MealRole.DINNER, None),))
    result = generate_week(
        PlannerRequest(
            uid(1),
            WEEK_START,
            (MemberPlannerConstraints(member_id, accepted, Decimal("2000")),),
            (candidate(10, MealTypeCode.MAIN),),
        ),
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=10),
    )
    assert isinstance(result, PlannerFailure)
    assert result.code is PlannerFailureCode.MISSING_ENERGY_ALLOCATION
    assert result.trace.final_events == ()
