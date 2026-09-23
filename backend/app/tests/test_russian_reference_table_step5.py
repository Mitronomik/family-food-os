"""Step 5 production Russian reference-table publication tests."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import replace
from datetime import date
from decimal import Decimal
import json
import shutil
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.domain.reference_comparison import (
    DailyNutrientAmount,
    compare_daily_reference,
)
from app.domain.russian_reference_targets import (
    ReferenceSelectionStatus,
    select_russian_reference_targets,
)
from app.seed.russian_reference_table_step5 import (
    METHODOLOGY_VERSION,
    PACKAGE,
    REGISTRY_PATH,
    load_reviewed_russian_reference_table,
    reviewed_russian_reference_table_digest,
    russian_reference_table_provider,
)
from app.services.nutrition import NutritionService
from app.tests.test_household_domain import member


def test_runtime_table_has_exact_frozen_shape_and_claim_provenance():
    table = load_reviewed_russian_reference_table()

    assert table.methodology_version == METHODOLOGY_VERSION
    assert table.review_reference == "STEP5_RU_REFERENCE_TABLE_V1"
    assert len(table.rows) == 48
    assert Counter(row.sex for row in table.rows) == {"male": 24, "female": 24}
    assert set(Counter(row.definition_code for row in table.rows).values()) == {2}
    assert all(row.age_min_years == 19 for row in table.rows)
    assert all(row.age_max_years_exclusive is None for row in table.rows)
    assert all(row.physical_activity_coefficient is None for row in table.rows)
    assert all(row.life_stage == "adult" for row in table.rows)
    assert all(row.basis == "group_reference_daily" for row in table.rows)
    assert all(row.applicability == "wellness" for row in table.rows)

    locators = [json.loads(row.locator) for row in table.rows]
    assert {locator["table_number"] for locator in locators} == {
        "11",
        "12",
        "16",
        "17",
    }
    assert all(locator["column"] == 2 for locator in locators)
    assert len({locator["source_claim_id"] for locator in locators}) == 48
    assert all(
        locator["source_claim_id"].startswith(
            "RU-NEEDS-MR-2.3.1.0253-21:"
        )
        for locator in locators
    )


def test_exact_source_values_and_beta_carotene_unit_are_preserved():
    table = load_reviewed_russian_reference_table()
    rows = {(row.sex, row.definition_code): row for row in table.rows}

    assert rows["male", "IRON"].value == Decimal("10")
    assert rows["female", "IRON"].value == Decimal("18")
    assert rows["male", "VITAMIN_A_RE"].value == Decimal("900")
    assert rows["female", "VITAMIN_A_RE"].value == Decimal("800")
    assert rows["male", "SELENIUM"].value == Decimal("70")
    assert rows["female", "SELENIUM"].value == Decimal("55")

    beta = rows["male", "BETA_CAROTENE"]
    assert beta.value == Decimal("5.0")
    assert beta.unit == "mg/day"
    assert (
        json.loads(beta.locator)["source_claim_id"]
        == "RU-NEEDS-MR-2.3.1.0253-21:p42:t1:r9:c2:population"
    )
    comparison = compare_daily_reference(
        DailyNutrientAmount(
            "BETA_CAROTENE",
            "µg/day",
            Decimal("5000"),
            "test-v1",
            ("test-source",),
        ),
        beta,
    )
    assert comparison.status == "COMPARABLE_GROUP_REFERENCE"
    assert comparison.percent_of_group_reference == Decimal("100.000000")


def test_age_18_is_unsupported_and_age_19_works_with_explicit_kfa():
    table = load_reviewed_russian_reference_table()

    age_18 = select_russian_reference_targets(
        table,
        age_years=18,
        sex="male",
        physical_activity_coefficient=Decimal("1.9"),
        life_stage="adult",
        definition_codes=("IRON",),
    )
    age_19 = select_russian_reference_targets(
        table,
        age_years=19,
        sex="male",
        physical_activity_coefficient=Decimal("1.9"),
        life_stage="adult",
        definition_codes=("IRON",),
    )

    assert age_18.status == ReferenceSelectionStatus.UNSUPPORTED
    assert age_19.status == ReferenceSelectionStatus.COMPLETE
    assert age_19.rows[0].value == Decimal("10")
    assert age_19.rows[0].physical_activity_coefficient is None


def test_deferred_definitions_are_absent():
    codes = {
        row.definition_code
        for row in load_reviewed_russian_reference_table().rows
    }
    assert codes.isdisjoint(
        {
            "CALCIUM",
            "FLUORIDE",
            "FOLATE_DFE",
            "FOLATE_TOTAL",
            "VITAMIN_D_D2_D3",
            "VITAMIN_K_PHYLLOQUINONE",
        }
    )


def test_unknown_methodology_fails_closed():
    with pytest.raises(LookupError, match="Неизвестная версия"):
        russian_reference_table_provider("UNKNOWN_RU_TABLE")


def test_exact_replay_returns_equal_table_and_digest():
    first = load_reviewed_russian_reference_table()
    second = load_reviewed_russian_reference_table()

    assert first == second
    assert (
        reviewed_russian_reference_table_digest(first)
        == reviewed_russian_reference_table_digest(second)
    )


def test_tampered_runtime_package_is_rejected(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    with (package / "publication.json").open("a", encoding="utf-8") as stream:
        stream.write(" ")

    with pytest.raises(ValueError, match="Изменён"):
        load_reviewed_russian_reference_table(package)


def test_tampered_registry_is_rejected(tmp_path):
    registry = tmp_path / "registry.json"
    shutil.copyfile(REGISTRY_PATH, registry)
    with registry.open("a", encoding="utf-8") as stream:
        stream.write(" ")

    with pytest.raises(ValueError, match="Изменён"):
        load_reviewed_russian_reference_table(registry_path=registry)


def test_payload_pins_source_transport_and_exact_claim_count():
    payload = json.loads((PACKAGE / "publication.json").read_text())

    assert payload["source"]["archive_sha256"] == (
        "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
    )
    assert payload["source"]["transport"]["values_sha256"] == (
        "ff9b21599797355ca47af6af5db9e920705cfa233cdaecd173d0c0a07cbf4b3f"
    )
    assert len(payload["rows"]) == 48
    assert len({row["source_claim_id"] for row in payload["rows"]}) == 48
    assert {
        row["source_status"]
        for row in payload["rows"]
    } == {"ready_source_group_lookup"}
    assert all(isinstance(row["source_value"], str) for row in payload["rows"])


def test_existing_nutrition_service_uses_explicit_reviewed_provider():
    household_id = uuid4()
    household_member = replace(
        member(household_id),
        birth_date=date(2000, 1, 1),
        sex="male",
    )

    def get_member(requested_household_id, member_id):
        if (
            requested_household_id == household_member.household_id
            and member_id == household_member.id
        ):
            return household_member
        return None

    @contextmanager
    def read_scope():
        yield SimpleNamespace(
            members=SimpleNamespace(get_member=get_member)
        )

    service = NutritionService(
        read_scope,
        russian_reference_tables=russian_reference_table_provider,
    )
    result = service.russian_member_group_reference(
        household_member.household_id,
        household_member.id,
        as_of_date=date(2026, 1, 1),
        methodology_version=METHODOLOGY_VERSION,
        physical_activity_coefficient=Decimal("1.4"),
        definition_codes=("IRON",),
    )

    assert result.status == ReferenceSelectionStatus.COMPLETE
    assert result.rows[0].value == Decimal("10")
    assert result.individualized is False
