import sqlite3
from dataclasses import replace

import pytest

from app.db.config import DatabaseConfig
from app.domain.errors import DomainValidationError
from app.domain.meal_patterns import MealPatternEligibilityQuery, MealPatternLifecycle
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_pattern_composition import (
    create_meal_pattern_catalogue_service,
)
from app.seed.meal_patterns import load_seed_entries, seed_meal_patterns
from app.services.meal_patterns import MealPatternNotFoundError


@pytest.fixture
def catalogue(tmp_path):
    config = DatabaseConfig(path=tmp_path / "application.sqlite")
    seed_meal_patterns(config)
    engine = create_sqlite_engine(config)
    try:
        yield config, create_meal_pattern_catalogue_service(engine)
    finally:
        engine.dispose()


def _seed(code):
    return next(item for item in load_seed_entries() if item.code == code)


def test_exact_current_and_adult_eligibility_are_deterministic(catalogue):
    _, service = catalogue
    exact = service.get_exact("ADULT_REGULAR_3", 1)
    current = service.get_current_published("ADULT_REGULAR_3")
    assert current == exact

    child = service.list_eligible(MealPatternEligibilityQuery(age_years=18))
    assert child.programs == ()
    assert child.unsupported_reason == "NO_ELIGIBLE_PUBLISHED_MEAL_PATTERN"

    adult = service.list_eligible(
        MealPatternEligibilityQuery(
            age_years=19,
            context_codes=("GENERAL_WELLNESS_SCHEDULE",),
        )
    )
    assert {item.program.code for item in adult.programs} == {
        "ADULT_REGULAR_3",
        "ADULT_REGULAR_3_PLUS_SNACK",
    }
    assert adult.unsupported_reason is None


def test_deactivate_appends_inactive_version_without_rewriting_published_history(catalogue):
    _, service = catalogue
    original = service.get_exact("ADULT_REGULAR_3", 1)
    inactive = service.deactivate(
        "ADULT_REGULAR_3", change_note="Synthetic deactivation fixture."
    )

    assert inactive.version.version_number == 2
    assert inactive.version.lifecycle is MealPatternLifecycle.INACTIVE
    assert inactive.version.created_from_version_id == original.version.id
    assert service.get_exact("ADULT_REGULAR_3", 1) == original
    with pytest.raises(MealPatternNotFoundError):
        service.get_current_published("ADULT_REGULAR_3")


def test_persistence_allows_repeated_snack_roles_by_position(catalogue):
    _, service = catalogue
    source = _seed("ADULT_REGULAR_3")
    candidate = replace(
        source,
        code="ADULT_REPEATED_SNACK_FIXTURE",
        version=replace(
            source.version,
            opportunity_roles=("BREAKFAST", "SNACK", "SNACK", "DINNER"),
            change_note="Synthetic repeated-role fixture.",
        ),
    )
    created = service.create_trusted(candidate)
    assert [item.role.value for item in created.opportunities] == [
        "BREAKFAST",
        "SNACK",
        "SNACK",
        "DINNER",
    ]


def test_invalid_publication_rolls_back_new_program_atomically(catalogue):
    config, service = catalogue
    source = _seed("ADULT_REGULAR_3")
    invalid = replace(
        source,
        code="INVALID_NO_EVIDENCE",
        version=replace(source.version, evidence=()),
    )
    with pytest.raises(DomainValidationError, match="evidence"):
        service.create_trusted(invalid)

    with sqlite3.connect(config.path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM meal_pattern_programs WHERE program_code=?",
            ("INVALID_NO_EVIDENCE",),
        ).fetchone()[0] == 0
