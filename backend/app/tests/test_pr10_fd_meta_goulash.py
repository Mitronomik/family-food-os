"""Adversarial integrity tests for research-only finished-dish MealPlan receipt."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.db.config import DatabaseConfig

from scripts.audit_pr10_fd_meta_goulash import (
    GOULASH_CODE,
    build_research_receipt,
    validate_research_receipt,
)


@pytest.fixture(scope="module")
def receipt() -> dict:
    """Never access a user database or production environment."""
    with TemporaryDirectory(prefix="pr10-fd-meta-test-") as tmp:
        yield build_research_receipt(
            DatabaseConfig(path=Path(tmp) / "research.sqlite")
        )


def _validate(receipt: dict) -> None:
    validate_research_receipt(
        receipt,
        trusted_semantic_sha256=receipt["expected_semantic_sha256"],
    )


def test_persisted_research_plan_and_one_recipe_two_events(receipt: dict) -> None:
    _validate(receipt)
    assert receipt["gate_decision"] == "BLOCKED"
    assert receipt["scope"] == "ISOLATED_SYNTHETIC_MEALPLAN_ONLY"
    assert receipt["recipe"]["canonical_code"] == GOULASH_CODE
    assert receipt["recipe"]["freezable"] is None
    assert receipt["recipe"]["batch_friendly"] is None
    assert receipt["recipe"]["storage_days_fridge"] is None
    assert receipt["recipe"]["storage_days_freezer"] is None
    assert receipt["research_plan"]["revision_number"] == 2
    assert len(receipt["research_plan"]["events"]) == 7
    assert len(receipt["candidate_pair"]) == 2
    assert len({
        event["event_id"] for event in receipt["candidate_pair"]
    }) == 2
    assert {
        event["recipe_version_id"] for event in receipt["candidate_pair"]
    } == {receipt["recipe"]["recipe_version_id"]}
    assert receipt["planned_cook_sessions_baseline"] == 2
    assert receipt["planned_cook_sessions_candidate"] == 1
    assert receipt["minutes_or_net_actions_saved"] == "NOT_PROVEN"


@pytest.mark.parametrize(
    "alter",
    [
        lambda r: r.update(gate_decision="READY"),
        lambda r: r["safety"].update(time_authority="DATE_ONLY_CONSERVATIVE"),
        lambda r: r["safety"].update(
            storage_policy_status="ACCEPTED_FAMILYFOODOS_POLICY"
        ),
        lambda r: r["safety"].update(executable_freezer_task=True),
        lambda r: r["safety"].update(confirmed_stock=True),
        lambda r: r["candidate_pair"][1].update(
            event_id=r["candidate_pair"][0]["event_id"]
        ),
        lambda r: r["candidate_pair"][0].update(combined_servings="999"),
        lambda r: r["candidate_pair"][1].update(recipe_version_id="forged"),
        lambda r: r["candidate_pair"][0]["servings"][0].update(
            portion_servings="NaN"
        ),
        lambda r: r["candidate_pair"][0]["servings"][0].update(
            portion_servings="Infinity"
        ),
        lambda r: r["research_plan"]["events"][0].update(
            recipe_version_id="wrong"
        ),
        lambda r: r["research_plan"]["events"][0].update(role="BREAKFAST"),
        lambda r: r["research_plan"]["events"][0]["servings"][0].update(
            member_id="foreign-member"
        ),
        lambda r: r["research_plan"]["events"][0].update(
            event_id=r["research_plan"]["events"][1]["event_id"]
        ),
        lambda r: r["research_plan"]["events"][0].update(
            local_date="2026-09-20"
        ),
        lambda r: r["recipe"].update(
            source_document_sha256="a" * 64
        ),
        lambda r: r["recipe"].update(verification_status="UNVERIFIED"),
        lambda r: r["recipe"].update(rights_review_status="UNKNOWN"),
        lambda r: r["combined_ingredient_demand"][0].update(
            planned_combined_quantity="999"
        ),
        lambda r: r["combined_ingredient_demand"][0].update(
            per_event_sum_quantity="999"
        ),
        lambda r: r["recipe"].update(steps=[]),
    ],
)
def test_forgery_and_unsupported_policy_fail_closed(receipt: dict, alter) -> None:
    tampered = deepcopy(receipt)
    alter(tampered)
    with pytest.raises((ValueError, KeyError, TypeError)):
        _validate(tampered)


def test_outside_semantic_anchor_is_required(receipt: dict) -> None:
    with pytest.raises(ValueError, match="trusted intended"):
        validate_research_receipt(
            receipt,
            trusted_semantic_sha256="f" * 64,
        )


def test_research_quantities_reconcile_exact_decimal(receipt: dict) -> None:
    quantities = receipt["combined_ingredient_demand"]
    assert len(quantities) == 7
    for ingredient in quantities:
        assert (
            ingredient["planned_combined_quantity"]
            == ingredient["per_event_sum_quantity"]
        )
        assert ingredient["unit"] == "g"
