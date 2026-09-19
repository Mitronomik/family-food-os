"""Gate1-A fresh-database audit regression proof."""

from collections import Counter
import json
from pathlib import Path

import pytest

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from scripts.gate1a_fixture_spec import GATE1_ROLE_SHAPES
from scripts.audit_gate1a_readiness import (
    audit,
    capacity_audit,
    reusable_evidence_compatibility,
)


@pytest.fixture(scope="module")
def current_audit(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("gate1a") / "audit.sqlite")
    return audit(config), config


def test_generic_capacity_uses_one_sandwich_across_breakfast_and_lunch() -> None:
    capacity = capacity_audit()["generic_minimum_capacity"]

    assert capacity == {
        "total": 7,
        "breakfast": 2,
        "main": 4,
        "sandwich": 1,
        "allocation": {"sandwich_breakfast_uses": 1, "sandwich_lunch_uses": 2},
    }


def test_repository_fixture_and_proposed_exclusion_are_separate() -> None:
    capacity = capacity_audit()

    repository = capacity["current_repository_fixture"]
    assert repository["role_shapes"] == [
        [[role.value for role in member] for member in household]
        for household in GATE1_ROLE_SHAPES
    ]
    assert repository["fixed_events"] == []
    assert repository["explicit_hard_exclusions"] == []
    assert [item["total"] for item in repository["capacity_by_household"]] == [3, 6, 7]

    proposed = capacity["proposed_gate1_hard_exclusion_scenario"]
    assert proposed["status"] == "PROPOSED_NOT_CURRENT_REPOSITORY_FIXTURE"
    assert proposed["excluded_food_code"] == "BREAD_WHOLE_WHEAT"
    assert proposed["capacity"] == {
        "total": 8,
        "breakfast": 3,
        "main": 5,
        "sandwich": 0,
        "allocation": {"sandwich_breakfast_uses": 0, "sandwich_lunch_uses": 0},
    }


def test_reusable_evidence_requires_semantic_size_form_and_identity(
    current_audit,
) -> None:
    _, config = current_audit
    engine = create_sqlite_engine(config)
    try:
        with B2B2UnitOfWork(engine) as scope:

            def detail(code):
                recipe = scope.recipes.get_by_code(code)
                return scope.versions.get_current_verified(recipe.id)

            egg_evidence = scope.evidence.get_by_key("FDC-PORTION-193781:exact")
            deviled = detail("SNAP6_HEAVENLY_DEVILED_EGGS")
            deviled_row = deviled.ingredients[0]
            deviled_assessment = scope.evidence.get_current_assessment(deviled_row.id)
            assert reusable_evidence_compatibility(
                deviled_row, "EGG", deviled_assessment, egg_evidence
            ) == (False, "SOURCE_SIZE_QUALIFIER_NOT_ESTABLISHED")

            frittata = detail("SNAP4_SPANISH_FRITTATA")
            large_egg_row = frittata.ingredients[1]
            large_egg_assessment = scope.evidence.get_current_assessment(
                large_egg_row.id
            )
            assert reusable_evidence_compatibility(
                large_egg_row, "EGG", large_egg_assessment, egg_evidence
            ) == (True, "COMPATIBLE_EXACT_AUTHORITY")

            pepper_evidence = scope.evidence.get_by_key("FDC-PORTION-87560:exact")
            pepper_row = frittata.ingredients[5]
            pepper_assessment = scope.evidence.get_current_assessment(pepper_row.id)
            assert reusable_evidence_compatibility(
                pepper_row, "BLACK_PEPPER", pepper_assessment, pepper_evidence
            ) == (True, "COMPATIBLE_EXACT_AUTHORITY")

            cheese_evidence = scope.evidence.get_by_key("FDC-PORTION-119620:exact")
            sandwich = detail("WIC1_BEYOND_BASIC_GRILLED_CHEESE")
            cheese_row = sandwich.ingredients[1]
            cheese_assessment = scope.evidence.get_current_assessment(cheese_row.id)
            assert reusable_evidence_compatibility(
                cheese_row, "CHEESE_CHEDDAR", cheese_assessment, cheese_evidence
            ) == (False, "TARGET_FOOD_IDENTITY_NOT_EXPLICIT")
    finally:
        engine.dispose()


def test_fresh_current_readiness_matrix(current_audit) -> None:
    result, _ = current_audit

    assert result["accepted_starting_sha"] == (
        "ce5cf6e2faaf9159e74d8c235f334d47743ab2a0"
    )
    assert result["recipe_count"] == 30
    assert Counter(row["nutrition_status"] for row in result["recipes"]) == {
        "INCOMPLETE": 29,
        "CONDITIONAL": 1,
    }
    assert [
        row["recipe_code"]
        for row in result["recipes"]
        if row["technical_gate1_suitable"]
    ] == ["WIC1_OVERNIGHT_OATS_CINNAMON_APPLE"]
    assert all(not row["consumer_publication_ready"] for row in result["recipes"])
    assert [
        row["recipe_code"] for row in result["recipes"] if row["planner_eligible"]
    ] == ["WIC1_OVERNIGHT_OATS_CINNAMON_APPLE"]

    blockers = [
        blocker
        for row in result["recipes"]
        for blocker in row["blocking_ingredient_positions"]
    ]
    classes = {blocker["repair_class"] for blocker in blockers}
    assert "NEW_PRIMARY_EVIDENCE_REQUIRED" in classes
    assert "ALREADY_ACCEPTED_EVIDENCE_REBIND" in classes
    assert any(
        blocker["reusable_exact_evidence_keys"]
        for blocker in blockers
        if blocker["accepted_repository_evidence_resolves"]
    )
    assert all(
        blocker["new_external_primary_evidence_required"]
        == (blocker["repair_class"] == "NEW_PRIMARY_EVIDENCE_REQUIRED")
        for blocker in blockers
    )
    assert Counter(blocker["repair_class"] for blocker in blockers) == {
        "NEW_PRIMARY_EVIDENCE_REQUIRED": 70,
        "IMMUTABLE_RECIPE_REVISION_REQUIRED": 16,
        "ALREADY_ACCEPTED_EVIDENCE_REBIND": 7,
        "PROFILE_OR_FORM_DATA_REPAIR": 1,
    }
    reusable = [
        (row["recipe_code"], blocker["position"], blocker["food_code"])
        for row in result["recipes"]
        for blocker in row["blocking_ingredient_positions"]
        if blocker["accepted_repository_evidence_resolves"]
    ]
    assert len(reusable) == 7
    assert {food_code for _, _, food_code in reusable} == {"BLACK_PEPPER"}

    plan = result["repair_plan"]
    assert plan["generic_minimum_repair_gap"] == 6
    assert plan["generic_target_selection_status"] == (
        "TARGET_SELECTION_BLOCKED_PENDING_PRIMARY_EVIDENCE_REVIEW"
    )
    assert len(plan["generic_minimum_cost_candidate_sets"][0]) == 6
    assert plan["proposed_exclusion_authority"]["occurs_in_recipe_codes"] == [
        "WIC1_BEYOND_BASIC_GRILLED_CHEESE"
    ]


def test_committed_matrix_matches_fresh_current_truth(current_audit) -> None:
    result, _ = current_audit
    committed = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "data/curation/gate1a-data-readiness/current-readiness.json"
        ).read_text(encoding="utf-8")
    )

    def without_local_ids(value):
        if isinstance(value, dict):
            return {
                key: without_local_ids(item)
                for key, item in value.items()
                if key not in {"id", "profile_id", "recipe_version_id"}
            }
        if isinstance(value, list):
            return [without_local_ids(item) for item in value]
        return value

    # Seed UUIDs are deployment-local; all semantic/provenance facts match.
    assert without_local_ids(result) == without_local_ids(committed)
