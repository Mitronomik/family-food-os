"""Adversarial integrity tests for research-only finished-dish MealPlan receipt."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest
from app.db.config import DatabaseConfig

from scripts import audit_pr10_fd_meta_goulash
from scripts.audit_pr10_fd_meta_goulash import (
    GOULASH_CODE,
    build_research_receipt,
    validate_research_receipt,
)


@pytest.fixture(scope="module")
def proof() -> tuple[dict, str, str]:
    """Trusted source and intended semantic hashes are separate from receipt data."""
    return build_research_receipt()


@pytest.fixture(scope="module")
def receipt(proof: tuple[dict, str, str]) -> dict:
    return proof[0]


def _validate(receipt: dict, proof: tuple[dict, str, str]) -> None:
    validate_research_receipt(
        receipt,
        trusted_semantic_sha256=proof[1],
        trusted_source_sha256=proof[2],
    )


def test_persisted_research_plan_and_one_recipe_two_events(
    receipt: dict, proof: tuple[dict, str, str]
) -> None:
    _validate(receipt, proof)
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
    assert len({event["event_id"] for event in receipt["candidate_pair"]}) == 2
    assert {event["recipe_version_id"] for event in receipt["candidate_pair"]} == {
        receipt["recipe"]["recipe_version_id"]
    }
    assert {
        row["servings"][0]["portion_servings"] for row in receipt["candidate_pair"]
    } == {"2.000000", "2.500000"}
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
        lambda r: r["candidate_pair"][0]["servings"][0].update(portion_servings="NaN"),
        lambda r: r["candidate_pair"][0]["servings"][0].update(
            portion_servings="Infinity"
        ),
        lambda r: r["research_plan"]["events"][0].update(recipe_version_id="wrong"),
        lambda r: r["research_plan"]["events"][0].update(role="BREAKFAST"),
        lambda r: r["research_plan"]["events"][0]["servings"][0].update(
            member_id="foreign-member"
        ),
        lambda r: r["research_plan"]["events"][0].update(
            event_id=r["research_plan"]["events"][1]["event_id"]
        ),
        lambda r: r["research_plan"]["events"][0].update(local_date="2026-09-20"),
        lambda r: r["recipe"].update(source_document_sha256="a" * 64),
        lambda r: r["recipe"].update(verification_status="UNVERIFIED"),
        lambda r: r["recipe"].update(rights_review_status="UNKNOWN"),
        lambda r: r["combined_ingredient_demand"][0].update(
            planned_combined_quantity="999"
        ),
        lambda r: r["combined_ingredient_demand"][0].update(
            per_event_sum_quantity="999"
        ),
        lambda r: r["recipe"].update(steps=[]),
        lambda r: r["recipe"]["steps"][0].update(instruction_sha256="a" * 64),
    ],
)
def test_forgery_and_unsupported_policy_fail_closed(
    receipt: dict, proof: tuple[dict, str, str], alter
) -> None:
    tampered = deepcopy(receipt)
    alter(tampered)
    with pytest.raises((ValueError, KeyError, TypeError)):
        _validate(tampered, proof)


def test_outside_semantic_anchor_is_required(
    receipt: dict, proof: tuple[dict, str, str]
) -> None:
    with pytest.raises(ValueError, match="trusted intended"):
        validate_research_receipt(
            receipt,
            trusted_semantic_sha256="f" * 64,
            trusted_source_sha256=proof[2],
        )


def test_outside_source_anchor_is_required(
    receipt: dict, proof: tuple[dict, str, str]
) -> None:
    with pytest.raises(ValueError, match="independent trusted source"):
        validate_research_receipt(
            receipt,
            trusted_semantic_sha256=proof[1],
            trusted_source_sha256="f" * 64,
        )


def test_research_quantities_reconcile_exact_decimal(receipt: dict) -> None:
    quantities = receipt["combined_ingredient_demand"]
    assert len(quantities) == 7
    for ingredient in quantities:
        assert Decimal(ingredient["planned_combined_quantity"]) == Decimal(
            ingredient["per_event_sum_quantity"]
        )
        assert ingredient["unit"] == "g"


@pytest.mark.parametrize("use_keyword", [False, True])
def test_arbitrary_user_sqlite_rejected_before_seeding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, use_keyword: bool
) -> None:
    """The public generator owns its SQLite file; an external path is impossible."""
    user_db = tmp_path / "user.sqlite"
    original_bytes = b"existing-user-database-must-not-change"
    user_db.write_bytes(original_bytes)
    attempted_seed = []

    def forbidden_seed(*args, **kwargs) -> None:
        attempted_seed.append((args, kwargs))
        raise AssertionError("Seed must not run for rejected caller config")

    monkeypatch.setattr(
        audit_pr10_fd_meta_goulash,
        "seed_dc4_a3_russian_step_corrections",
        forbidden_seed,
    )
    config = DatabaseConfig(path=user_db)
    with pytest.raises(TypeError):
        if use_keyword:
            build_research_receipt(config=config)
        else:
            build_research_receipt(config)
    assert attempted_seed == []
    assert user_db.read_bytes() == original_bytes


@pytest.mark.parametrize(
    ("target", "value"),
    [
        ("card", "a" * 64),
        ("recipe_ingredient_id", "forged-recipe-ingredient"),
        ("food_ingredient_id", "forged-food-ingredient"),
        ("unit", "ml"),
        ("source_quantity", "900"),
        ("process_sha256", "f" * 64),
        ("baseline_count", 1),
        ("candidate_count", 2),
        ("claimed_savings", "ONE_ACTION_SAVED"),
    ],
)
def test_source_and_cook_count_forgery_rejected(
    receipt: dict, proof: tuple[dict, str, str], target: str, value: object
) -> None:
    forged = deepcopy(receipt)
    if target == "card":
        forged["recipe"]["source_card_sha256"] = value
    elif target in {"recipe_ingredient_id", "food_ingredient_id", "unit", "source_quantity"}:
        forged["combined_ingredient_demand"][0][target] = value
    elif target == "process_sha256":
        forged["recipe"]["process_sha256"] = value
    elif target == "baseline_count":
        forged["planned_cook_sessions_baseline"] = value
    elif target == "candidate_count":
        forged["planned_cook_sessions_candidate"] = value
    else:
        forged["minutes_or_net_actions_saved"] = value
    with pytest.raises((ValueError, TypeError, KeyError)):
        _validate(forged, proof)


def test_recomputed_self_fingerprint_cannot_override_independent_source(
    receipt: dict, proof: tuple[dict, str, str]
) -> None:
    """A forged source snapshot with an updated internal hash still fails."""
    forged = deepcopy(receipt)
    forged["recipe"]["source_card_sha256"] = "a" * 64
    forged["combined_ingredient_demand"][0]["food_ingredient_id"] = "forged"
    forged["source_fingerprint_sha256"] = audit_pr10_fd_meta_goulash._sha(
        audit_pr10_fd_meta_goulash._source_pins(
            forged["recipe"], forged["combined_ingredient_demand"]
        )
    )
    with pytest.raises(ValueError, match="independent trusted source"):
        _validate(forged, proof)
