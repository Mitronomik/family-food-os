"""Actual-source portion audit: no invented cooked masses or serving thresholds."""

from copy import deepcopy
from datetime import date
from decimal import Decimal
from types import SimpleNamespace as Row
from uuid import uuid4

import pytest
from app.domain.meal_patterns import MealRole

from scripts import pr10_ff_portion_reality as audit


def _sample():
    event_id = uuid4()
    version_id = uuid4()
    member_ids = (uuid4(), uuid4())
    event = Row(
        id=event_id,
        local_date=date(2026, 11, 2),
        position=1,
        role=MealRole.BREAKFAST,
        recipe_version_id=version_id,
    )
    servings = tuple(
        Row(event_id=event_id, member_id=member_id, portion_servings=factor)
        for member_id, factor in zip(
            member_ids, (Decimal("2.000000"), Decimal("6.000000"))
        )
    )
    plan = Row(events=(event,), servings=servings)
    semantic = [
        {
            "date": "2026-11-02",
            "position": 1,
            "role": "BREAKFAST",
            "recipe": {"code": "TEST_SOUP", "version": 1},
            "servings": [
                {"member_ordinal": 1, "portion_servings": "2.000000"},
                {"member_ordinal": 2, "portion_servings": "6.000000"},
            ],
        }
    ]
    detail = Row(
        recipe=Row(canonical_code="TEST_SOUP", canonical_name="Тестовые щи"),
        version=Row(
            id=version_id,
            version_number=1,
            base_servings=Decimal("1.000000"),
            source_original_servings=Decimal("1.000000"),
            source_output_g=None,
        ),
    )
    candidates = [
        {
            "canonical_code": "TEST_SOUP",
            "recipe_version_id": str(version_id),
            "nutrition_status": "INCOMPLETE",
            "exact_energy_ready": True,
            "kcal_per_base_serving": "112",
        }
    ]
    return (
        plan,
        semantic,
        {version_id: detail},
        candidates,
        dict(zip(member_ids, (1, 2))),
    )


def _run(args):
    plan, semantic, details, candidates, ordinals = args
    return audit.inspect(
        plan=plan,
        semantic_events=semantic,
        details=details,
        candidate_inputs=candidates,
        member_ordinals=ordinals,
    )


def test_exact_energy_arithmetic_never_proves_physical_portion():
    result = _run(_sample())
    assert result["status"] == "PHYSICAL_FEASIBILITY_NOT_PROVEN"
    assert result["meal_events"] == 1
    assert result["individual_servings"] == 2
    assert result["factor_min"] == "2.000000"
    assert result["factor_max"] == "6.000000"
    assert result["source_output_missing_events"] == 1
    assert result["physically_reviewed_servings"] == 0
    assert [row["technical_energy_kcal"] for row in result["rows"]] == [
        "224.000",
        "672.000",
    ]
    assert all(row["physical_feasibility"] == "NOT_PROVEN" for row in result["rows"])
    assert "Тестовые щи" in audit.render_markdown(result)
    assert "не рейтинг опасности" in audit.render_markdown(result)


@pytest.mark.parametrize(
    "original_base,expected_status",
    [
        ("1.000000", "RAW_OUTPUT_APPLICABILITY_UNREVIEWED"),
        ("2.000000", "RAW_OUTPUT_DIFFERENT_BASE_UNREVIEWED"),
    ],
)
def test_raw_source_output_is_not_equated_to_cooked_member_mass(
    original_base, expected_status
):
    args = _sample()
    detail = next(iter(args[2].values()))
    detail.version.source_output_g = Decimal(300)
    detail.version.source_original_servings = Decimal(original_base)
    result = _run(args)
    assert result["source_output_present_events"] == 1
    assert all(row["source_output_status"] == expected_status for row in result["rows"])
    assert all(row["physical_feasibility"] == "NOT_PROVEN" for row in result["rows"])


@pytest.mark.parametrize(
    "mutation",
    [
        "orphan_serving",
        "missing_member",
        "duplicate_member_ordinal",
        "duplicate_serving",
        "nonfinite_serving",
        "swapped_frozen_factor",
        "wrong_version",
        "wrong_candidate_pin",
        "invalid_energy",
        "unknown_energy",
        "missing_recipe",
    ],
)
def test_source_or_member_binding_mismatch_is_blocked(mutation):
    plan, semantic, details, candidates, ordinals = _sample()
    member_id = next(iter(ordinals))
    if mutation == "orphan_serving":
        plan.servings = (
            Row(event_id=uuid4(), member_id=member_id, portion_servings=Decimal(2)),
        ) + plan.servings[1:]
    elif mutation == "missing_member":
        del ordinals[member_id]
    elif mutation == "duplicate_member_ordinal":
        ordinals = {mid: 1 for mid in ordinals}
    elif mutation == "duplicate_serving":
        plan.servings += (plan.servings[0],)
    elif mutation == "nonfinite_serving":
        plan.servings = (
            Row(
                event_id=plan.events[0].id,
                member_id=member_id,
                portion_servings=Decimal("NaN"),
            ),
        ) + plan.servings[1:]
    elif mutation == "swapped_frozen_factor":
        semantic[0]["servings"][0]["portion_servings"] = "6.000000"
    elif mutation == "wrong_version":
        semantic[0]["recipe"]["version"] = 2
    elif mutation == "wrong_candidate_pin":
        candidates[0]["recipe_version_id"] = str(uuid4())
    elif mutation == "invalid_energy":
        candidates[0]["kcal_per_base_serving"] = "NaN"
    elif mutation == "unknown_energy":
        candidates[0]["exact_energy_ready"] = False
    elif mutation == "missing_recipe":
        details.clear()
    with pytest.raises(audit.PortionAuditBlocked):
        audit.inspect(
            plan=plan,
            semantic_events=semantic,
            details=details,
            candidate_inputs=candidates,
            member_ordinals=ordinals,
        )


def test_tampered_release_flag_is_rejected():
    result = _run(_sample())
    changed = deepcopy(result)
    changed["physically_reviewed_servings"] = 1
    with pytest.raises(audit.PortionAuditBlocked):
        audit.render_markdown(changed)
    changed = deepcopy(result)
    changed["rows"][0]["physical_feasibility"] = "PASS"
    with pytest.raises(audit.PortionAuditBlocked):
        audit.render_markdown(changed)
