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
        filename = (
            proof.INPUT_DIR
            / copy["raw_artifacts"][key]["repository_path"].split("/")[-1]
        )
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


def _synthetic_comparison_receipt():
    """Adversarial compare contract: no real plan forged as positive evidence."""
    from scripts import pr10_ff_proof_evidence as evidence

    pins, _, _ = proof.checked_inputs()
    events = [
        {
            "date": f"2026-11-{2 + i // 3:02d}",
            "position": i % 3 + 1,
            "role": ("BREAKFAST", "LUNCH", "DINNER")[i % 3],
            "recipe": {"code": f"TEST_RECIPE_{i}", "version": 1},
            "servings": [{"member_ordinal": 1, "portion_servings": "1.000000"}],
        }
        for i in range(21)
    ]
    source = [{"event": i, "source_name": f"TEST_SOURCE_{i}"} for i in range(21)]
    request = {"members": [1, 2, 3], "candidate_codes": ["A", "B"]}
    uuid_order = {
        "candidate_input_uuid_order": ["version-A", "version-B"],
        "candidate_tie_uuid_order": ["version-A", "version-B"],
        "candidate_tie_code_order": ["A", "B"],
        "member_request_uuid_order": ["member1", "member2", "member3"],
        "member_request_ordinal_order": [1, 2, 3],
        "selection_id_by_member_ordinal": {"1": "s1", "2": "s2", "3": "s3"},
        "food_ingredient_id_to_code": [
            {"id": "f1", "code": "FOOD_1"},
            {"id": "f2", "code": "FOOD_2"},
        ],
    }
    receipt = {
        "schema": "PR10_FF_TWO_PROCESS_PROOF_RECEIPT_V1",
        "input_sha256": {
            "A": pins["raw_artifacts"]["publication_a"]["raw_sha256"],
            "B": pins["raw_artifacts"]["planner_b"]["raw_sha256"],
        },
        "input_parity_with_B": True,
        "semantic_events": events,
        "semantic_sha256": proof.digest(proof.inputs.canonical_bytes(events)),
        "actual_request_normalized_v2": request,
        "request_normalized_sha256_v2": proof.digest(
            proof.inputs.canonical_bytes(request)
        ),
        "provenance_semantic_v2": source,
        "provenance_sha256_v2": proof.digest(proof.inputs.canonical_bytes(source)),
        "uuid_order_witness_v2": uuid_order,
        "planner_request_fingerprint": "opaque-run-1",
        "planner_trace_fingerprint": "opaque-trace-1",
    }
    assert evidence.compare_evidence(receipt, deepcopy(receipt), pin=pins)
    return pins, receipt


@pytest.mark.parametrize(
    "mutation",
    [
        "recipe_version",
        "role",
        "event_order",
        "member",
        "portion",
        "input",
        "provenance",
        "candidate_uuid_order",
        "candidate_tie_order",
        "selection_id_collision",
        "food_id_collision",
    ],
)
def test_cross_process_adversarial_change_is_no_go(mutation):
    from scripts import pr10_ff_proof_evidence as evidence

    pins, first = _synthetic_comparison_receipt()
    second = deepcopy(first)
    if mutation == "recipe_version":
        second["semantic_events"][0]["recipe"]["version"] = 2
    elif mutation == "role":
        second["semantic_events"][0]["role"] = "DINNER"
    elif mutation == "event_order":
        second["semantic_events"][0], second["semantic_events"][1] = (
            second["semantic_events"][1],
            second["semantic_events"][0],
        )
    elif mutation == "member":
        second["semantic_events"][0]["servings"][0]["member_ordinal"] = 2
    elif mutation == "portion":
        second["semantic_events"][0]["servings"][0]["portion_servings"] = "2.000000"
    elif mutation == "input":
        second["actual_request_normalized_v2"]["candidate_codes"][0] = "TAMPERED"
    elif mutation == "provenance":
        second["provenance_semantic_v2"][0]["source_name"] = "TAMPERED"
    elif mutation == "candidate_uuid_order":
        second["uuid_order_witness_v2"]["candidate_input_uuid_order"].reverse()
    elif mutation == "candidate_tie_order":
        second["uuid_order_witness_v2"]["candidate_tie_code_order"].reverse()
    elif mutation == "selection_id_collision":
        second["uuid_order_witness_v2"]["selection_id_by_member_ordinal"]["2"] = "s1"
    elif mutation == "food_id_collision":
        second["uuid_order_witness_v2"]["food_ingredient_id_to_code"][1]["id"] = "f1"
    for field, key in (
        ("semantic_events", "semantic_sha256"),
        ("actual_request_normalized_v2", "request_normalized_sha256_v2"),
        ("provenance_semantic_v2", "provenance_sha256_v2"),
    ):
        # Even a recomputed matching internal digest does not launder differences.
        second[key] = proof.digest(proof.inputs.canonical_bytes(second[field]))
    with pytest.raises(evidence.EvidenceNoGo):
        evidence.compare_evidence(first, second, pin=pins)


def test_run_local_uuid_changes_are_explicit_and_do_not_fake_input_equality():
    from scripts import pr10_ff_proof_evidence as evidence

    pins, first = _synthetic_comparison_receipt()
    second = deepcopy(first)
    second["uuid_order_witness_v2"]["selection_id_by_member_ordinal"]["1"] = "new-s1"
    second["uuid_order_witness_v2"]["food_ingredient_id_to_code"][0]["id"] = "new-f1"
    findings = evidence.compare_evidence(first, second, pin=pins)
    assert findings["run_local_uuid_difference_categories"] == [
        "selection_id_by_member_ordinal",
        "food_ingredient_id_to_code",
    ]


def test_failed_child_process_creates_stable_no_go_report(tmp_path, monkeypatch):
    import json
    import subprocess

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, ["worker"])

    monkeypatch.setattr(proof.subprocess, "run", fail)
    output = tmp_path / "evidence"
    assert proof.compare(output) == 1
    receipt = json.loads((output / "comparison.json").read_bytes())
    assert receipt["status"] == "NO_GO_FORWARD_FIXTURE_UNSTABLE"
    assert receipt["PR10_FF_FIXTURE_REPRODUCIBLE"] == "NOT_PROVEN"
    assert receipt["worker_receipts_present"] == [False, False]
    assert receipt["failure_class"] == "CalledProcessError"
