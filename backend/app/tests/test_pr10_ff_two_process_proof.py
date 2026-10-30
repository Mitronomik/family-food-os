"""Issue #268 input pins and fail-closed comparison invariants."""
from copy import deepcopy

import pytest

from scripts import pr10_ff_two_process_proof as proof


def test_frozen_a_b_are_separately_pinned():
    pins, a, b = proof.checked_inputs()
    assert pins["scope"]["expected_meal_events"] == 21
    assert pins["scope"]["expected_servings"] == 42
    assert len(a["publications"]) == 58
    assert len(b["candidate_inputs"]) == len(b["candidate_admissions"]) == 51
    assert all(x["nutrition_status"] == "INCOMPLETE" for x in b["candidate_inputs"])


@pytest.mark.parametrize("which", ["publication_a", "planner_b"])
def test_mutated_pin_is_rejected(monkeypatch, tmp_path, which):
    pins, _, _ = proof.checked_inputs()
    test_dir = tmp_path / "pr10-ff-forward-input-v1"
    test_dir.mkdir()
    pin_dir = tmp_path
    copy = deepcopy(pins)
    for key in ("publication_a", "planner_b"):
        filename = proof.INPUT_DIR / copy["raw_artifacts"][key]["repository_path"].split("/")[-1]
        raw = filename.read_bytes()
        (test_dir / filename.name).write_bytes(raw + (b" " if which == key else b""))
        copy["raw_artifacts"][key]["repository_path"] = str(
            (test_dir / filename.name).relative_to(tmp_path)
        )
    (pin_dir / "pins.json").write_bytes(proof.inputs.canonical_bytes(copy))
    monkeypatch.setattr(proof, "PIN_PATH", pin_dir / "pins.json")
    monkeypatch.setattr(proof, "INPUT_DIR", test_dir)
    monkeypatch.setattr(proof, "ROOT", tmp_path)
    # Invalid independently supplied path must fail before any Planner access.
    with pytest.raises(proof.ProofNoGo):
        proof.checked_inputs()


def test_decimal_portion_contract():
    from decimal import Decimal
    assert proof.portion(Decimal("1.250000")) == "1.250000"
    with pytest.raises(proof.ProofNoGo):
        proof.portion(Decimal("NaN"))
    with pytest.raises(proof.ProofNoGo):
        proof.portion(Decimal(0))
    with pytest.raises(proof.ProofNoGo):
        proof.portion(Decimal("0.1234567"))
