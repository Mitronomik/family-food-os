from datetime import date
from uuid import uuid4

import pytest

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_composition import create_household_service
from app.persistence.sqlalchemy_core.reference_methodology_composition import (
    create_reference_methodology_service,
)
from app.services.reference_methodology import (
    BASELINE_NUTRITION_CONFIG_VERSION,
    RUSSIAN_GROUP_REFERENCE_VERSION,
    ReferenceMethodologyConflictError,
)


def test_real_sqlite_service_persists_baseline_and_russian_selection(tmp_path):
    config = DatabaseConfig(path=tmp_path / "step6a-integration.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        households = create_household_service(engine)
        references = create_reference_methodology_service(engine)
        home = households.create_household(
            name="Home",
            timezone_name="Europe/Moscow",
        )
        person = households.add_household_member(
            home.id,
            name="Anna",
            activity_level="moderate",
            goal="maintain",
            birth_date=date(1990, 5, 20),
            sex="female",
        )

        baseline = references.accept_member_selection(
            household_id=home.id,
            member_id=person.id,
            acceptance_request_id=uuid4(),
            expected_current_selection_id=None,
            nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version=None,
        )
        russian = references.accept_member_selection(
            household_id=home.id,
            member_id=person.id,
            acceptance_request_id=uuid4(),
            expected_current_selection_id=baseline.id,
            nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version=RUSSIAN_GROUP_REFERENCE_VERSION,
        )

        assert baseline.version_number == 1
        assert russian.version_number == 2
        assert russian.supersedes_selection_id == baseline.id
        assert references.get_current_selection(home.id, person.id) == russian
        assert references.get_selection_history(home.id, person.id) == (
            baseline,
            russian,
        )
    finally:
        engine.dispose()


def test_request_id_reuse_across_member_scope_fails_even_on_same_bundle_noop(
    tmp_path,
):
    config = DatabaseConfig(path=tmp_path / "step6a-request-scope.sqlite")
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        households = create_household_service(engine)
        references = create_reference_methodology_service(engine)
        home = households.create_household(
            name="Home",
            timezone_name="Europe/Moscow",
        )
        first_member = households.add_household_member(
            home.id,
            name="Anna",
            activity_level="moderate",
            goal="maintain",
        )
        second_member = households.add_household_member(
            home.id,
            name="Boris",
            activity_level="moderate",
            goal="maintain",
        )
        reused_request_id = uuid4()
        references.accept_member_selection(
            household_id=home.id,
            member_id=first_member.id,
            acceptance_request_id=reused_request_id,
            expected_current_selection_id=None,
            nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version=None,
        )
        second_current = references.accept_member_selection(
            household_id=home.id,
            member_id=second_member.id,
            acceptance_request_id=uuid4(),
            expected_current_selection_id=None,
            nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
            group_reference_methodology_version=None,
        )

        with pytest.raises(
            ReferenceMethodologyConflictError,
            match="another Household/member scope",
        ):
            references.accept_member_selection(
                household_id=home.id,
                member_id=second_member.id,
                acceptance_request_id=reused_request_id,
                expected_current_selection_id=second_current.id,
                nutrition_config_version=BASELINE_NUTRITION_CONFIG_VERSION,
                group_reference_methodology_version=None,
            )

        assert references.get_current_selection(
            home.id, second_member.id
        ) == second_current
    finally:
        engine.dispose()
