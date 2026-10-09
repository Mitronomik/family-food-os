import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.db.config import DatabaseConfig
from app.domain.food_recipes import MealTypeCode, RightsReviewStatus, VerificationStatus
from app.services.recipe_nutrition_v2 import RecipeNutritionV2UnavailableError

from scripts.audit_dc4_corpus_readiness_rerun import _audit_active_catalogue, audit


def test_dc4_rerun_reproducible_corpus_and_gate1_evidence(tmp_path: Path) -> None:
    result = audit(DatabaseConfig(path=tmp_path / "dc4.sqlite"))

    catalogue = result["catalogue"]
    supply = result["planner_supply"]
    fixtures = result["fixtures"]
    bounded = result["bounded_infeasibility"]

    assert catalogue["active_count"] >= 51
    assert len(catalogue["recipes"]) == catalogue["active_count"]
    assert all(
        row["disposition"] in {"PASS", "BLOCKED"} for row in catalogue["recipes"]
    )

    assert supply["eligible_count"] == 51
    assert supply["meal_type_counts"] == {
        "breakfast": 17,
        "main": 33,
        "sandwich": 1,
    }
    assert supply["matches_accepted_baseline"] is True

    assert [row["member_count"] for row in fixtures] == [1, 2, 3]
    assert [row["event_count"] for row in fixtures] == [7, 14, 21]
    assert all(row["planned_success"] for row in fixtures)
    assert all(row["deterministic"] for row in fixtures)
    assert all(row["selected_exclusions_respected"] for row in fixtures)
    assert all(not row["selected_exclusion_violations"] for row in fixtures)
    assert all(row["planner_version"] == "planner-v0.5" for row in fixtures)
    assert fixtures[1]["hard_exclusion_rejections"] > 0

    assert all(row["success"] for row in fixtures)
    assert [row["serving_count"] for row in fixtures] == [7, 21, 42]
    assert all(row["persistence_error"] is None for row in fixtures)
    assert "GATE1_FIXTURE_FAILURE" not in result["blockers"]

    prepared = [
        row
        for row in catalogue["recipes"]
        if row["nutrition_authority_kind"] == "PREPARED_OUTPUT_V1"
    ]
    assert prepared
    assert all(
        row["unknown_nutrient_count"] + row["available_nutrient_count"] == 54
        for row in prepared
    )
    assert all("UNKNOWN_PROMOTED_TO_NUMERIC" not in row["issues"] for row in prepared)

    assert bounded["is_failure"] is True
    assert bounded["returned_persisted_plan"] is False
    assert bounded["partial_plan_exists"] is False
    assert bounded["hard_exclusion_rejections"] > 0
    assert bounded["max_repetition_rejections"] > 0

    assert result["planner_version"] == "planner-v0.5"
    assert result["migration_head"] == "0043_shopping_engine"
    assert result["migration_ok"] is True
    assert result["ai_enabled_required"] is False

    assert catalogue["active_count"] == 51
    assert catalogue["blocked_count"] == 0
    assert catalogue["blocked_recipe_codes"] == []
    assert all(row["disposition"] == "PASS" for row in catalogue["recipes"])
    assert result["blockers"] == []
    assert result["overall_status"] == "PASS"

    summary_path = (
        Path(__file__).resolve().parents[3]
        / "data/curation/dc4-corpus-readiness/rerun-summary.json"
    )
    frozen = json.loads(summary_path.read_text(encoding="utf-8"))
    receipt = frozen["audit"]
    assert receipt["overall_status"] == result["overall_status"]
    assert receipt["blockers"] == result["blockers"]
    assert receipt["planner_version"] == result["planner_version"]
    assert receipt["catalogue"]["active_count"] == catalogue["active_count"]
    assert receipt["catalogue"]["blocked_count"] == catalogue["blocked_count"]
    assert receipt["planner_supply"]["eligible_count"] == supply["eligible_count"]
    assert receipt["planner_supply"]["meal_type_counts"] == supply["meal_type_counts"]
    assert [
        (row["fixture"], row["event_count"], row["serving_count"], row["success"])
        for row in receipt["fixtures"]
    ] == [
        (row["fixture"], row["event_count"], row["serving_count"], row["success"])
        for row in fixtures
    ]

    reused = frozen["reused_evidence"]
    assert reused["verification_freeze_sha"] == (
        "3e5139283c557f75e59f2dd23dd219902b0a4840"
    )
    assert reused["full_backend_workflow"]["status"] == "SUCCESS"
    assert reused["secondary_full_backend_workflow"]["status"] == "SUCCESS"
    requirements = {row["requirement"]: row for row in reused["requirements"]}
    assert set(requirements) == {
        "MEAL_PATTERN_1_2_3_5_6_OPPORTUNITIES",
        "MEAL_PATTERN_SEVEN_OPPORTUNITY_BOUNDARY",
        "MEAL_PATTERN_ACCEPTANCE_PERSISTENCE",
        "MEAL_TYPE_DISTINCT_FROM_MEAL_ROLE",
        "MEAL_SOURCE_KIND_BOUNDARIES_NO_FABRICATION",
        "PROVENANCE_TAMPER_AND_PROCESS_DRIFT_FAIL_CLOSED",
        "NO_GATE_ONLY_AUTHORITY",
    }
    assert all(row["status"] == "SUCCESS" for row in requirements.values())
    assert requirements["NO_GATE_ONLY_AUTHORITY"]["execution_path"].startswith(
        "scripts/audit_dc4_corpus_readiness_rerun.py::audit"
    )


def test_dc4_rerun_is_deterministic_at_gate_level(tmp_path: Path) -> None:
    first = audit(DatabaseConfig(path=tmp_path / "first.sqlite"))
    second = audit(DatabaseConfig(path=tmp_path / "second.sqlite"))

    assert first["catalogue"]["active_count"] == second["catalogue"]["active_count"]
    assert (
        first["catalogue"]["blocked_recipe_codes"]
        == second["catalogue"]["blocked_recipe_codes"]
    )
    assert (
        first["planner_supply"]["eligible_count"]
        == second["planner_supply"]["eligible_count"]
    )
    assert (
        first["planner_supply"]["meal_type_counts"]
        == second["planner_supply"]["meal_type_counts"]
    )
    assert [
        (
            row["fixture"],
            row["planned_success"],
            row["success"],
            row["event_count"],
            row["serving_count"],
            row["persistence_error"],
            row["selected_exclusions_respected"],
        )
        for row in first["fixtures"]
    ] == [
        (
            row["fixture"],
            row["planned_success"],
            row["success"],
            row["event_count"],
            row["serving_count"],
            row["persistence_error"],
            row["selected_exclusions_respected"],
        )
        for row in second["fixtures"]
    ]
    assert first["overall_status"] == second["overall_status"]
    assert first["blockers"] == second["blockers"]


def test_dc4_missing_required_nutrition_authority_is_blocked() -> None:
    recipe_id = uuid4()
    version_id = uuid4()
    ingredient_id = uuid4()
    recipe = SimpleNamespace(
        id=recipe_id,
        canonical_code="EVIDENCE_MISSING_NUTRITION",
        canonical_name="Яйцо отварное",
        is_active=True,
    )
    version = SimpleNamespace(
        id=version_id,
        meal_type_code=MealTypeCode.BREAKFAST,
        verification_status=VerificationStatus.SOURCE_VERIFIED,
        rights_review_status=RightsReviewStatus.REVIEWED,
        rights_basis="Проверенное право использования",
        source_name="test",
        source_recipe_id="test-1",
        source_url="https://example.org/recipe",
        source_document_sha256="a" * 64,
    )
    detail = SimpleNamespace(
        version=version,
        ingredients=(SimpleNamespace(food_ingredient_id=ingredient_id),),
        steps=(SimpleNamespace(instruction="Сварить яйцо"),),
    )
    recipes = SimpleNamespace(
        list_all=lambda: (recipe,),
        get_current_verified=lambda _recipe_id: detail,
    )
    food = SimpleNamespace(
        get=lambda _ingredient_id: SimpleNamespace(is_active=True, canonical_code="EGG")
    )

    def missing_authority(_version_id):
        raise RecipeNutritionV2UnavailableError("Missing authority")

    nutrition = SimpleNamespace(neutral_consumption_projection=missing_authority)
    result = _audit_active_catalogue(recipes, food, nutrition)
    assert result["active_count"] == 1
    assert result["blocked_count"] == 1
    assert result["recipes"][0]["disposition"] == "BLOCKED"
    assert "NUTRITION_AUTHORITY_UNAVAILABLE" in result["recipes"][0]["issues"]
