"""PR10-FF pre-run materialization; no Planner selection or self-approved pin."""

import json
from copy import deepcopy
from decimal import Decimal

import pytest

from scripts import pr10_ff_pre_generation_inputs as inputs


def test_materialization_is_pre_generation_and_caller_pin_is_required(
    tmp_path, monkeypatch
):
    from app.domain import planner as domain_planner
    from app.services import planner as planner_module

    def forbidden(*args, **kwargs):
        pytest.fail("real Planner week generation is forbidden before A/B review")

    monkeypatch.setattr(
        planner_module.PlannerService, "generate_authoritative", forbidden
    )
    monkeypatch.setattr(domain_planner, "generate_week", forbidden)
    destination = tmp_path / "proposals"
    result = inputs.materialize_pre_generation(destination)
    assert result["planner_generation_performed"] == "NO"
    a = json.loads((destination / "publication-A-PROPOSED.json").read_text())
    b = json.loads((destination / "planner-B-PROPOSED.json").read_text())
    assert len(a["publications"]) == 58
    assert len(a["stages"]) == 12
    assert len(b["members"]) == 3
    assert len(b["candidate_inputs"]) == len(b["candidate_admissions"]) == 51
    assert sum(len(row["opportunities"]) for row in b["members"]) == 42
    assert b["pantry"] == b["history"] == b["fixed_events"] == []
    evidence = inputs.validate_externally_pinned_proposals(
        destination,
        expected_a_sha256=result["publication_A_sha256_OBSERVED_NOT_PIN"],
        expected_b_sha256=result["planner_B_sha256_OBSERVED_NOT_PIN"],
        expected_source_commit=inputs.SOURCE_COMMIT,
        expected_stage_membership=a["stages"],
    )
    assert evidence["candidate_count"] == 51
    assert evidence["no_Planner_generation"] is True

    with pytest.raises(inputs.PreflightNoGo, match="external A/B raw SHA"):
        inputs.validate_externally_pinned_proposals(
            destination,
            expected_a_sha256="f" * 64,
            expected_b_sha256=result["planner_B_sha256_OBSERVED_NOT_PIN"],
            expected_source_commit=inputs.SOURCE_COMMIT,
            expected_stage_membership=a["stages"],
        )
    with pytest.raises(inputs.PreflightNoGo, match="output directory must be empty"):
        inputs.materialize_pre_generation(destination)
    with pytest.raises(inputs.PreflightNoGo, match="source commit differs"):
        inputs.materialize_pre_generation(
            tmp_path / "wrong-revision",
            expected_base="0" * 40,
        )


def test_no_unreviewed_profile_or_version_key_is_accepted(tmp_path):
    a, profiles = inputs.build_source_proposal()
    assert list(profiles) == [1, 2, 3]
    assert len(a["publications"]) == 58
    assert sum(len(v) for v in a["stages"].values()) == 58
    assert (
        len([item for item in a["approved_ids"] if item["kind"] == "HOUSEHOLD_MEMBER"])
        == 3
    )
    with pytest.raises(inputs.PreflightNoGo, match="ordinal"):
        inputs._member_profile(4)
    with pytest.raises(inputs.PreflightNoGo, match="nonfinite"):
        inputs._decimal(__import__("decimal").Decimal("NaN"))


@pytest.fixture(scope="module")
def grounded_proposals(tmp_path_factory):
    """Build once from approved source, not a fabricated candidate week."""
    destination = tmp_path_factory.mktemp("pr10_ff_source") / "proposals"
    results = inputs.materialize_pre_generation(destination)
    a = json.loads((destination / "publication-A-PROPOSED.json").read_bytes())
    b = json.loads((destination / "planner-B-PROPOSED.json").read_bytes())
    provider = inputs.load_pinned_publication_manifest(
        destination / "publication-A-PROPOSED.json",
        expected_sha256=results["publication_A_sha256_OBSERVED_NOT_PIN"],
        expected_source_commit=inputs.SOURCE_COMMIT,
        expected_stage_membership=a["stages"],
        correction_path=inputs.dc4.CORRECTIONS_PATH,
        expected_correction_sha256=inputs.CORRECTION_SHA256,
        expected_correction_blob_sha1=inputs.CORRECTION_GIT_BLOB,
    )
    source_candidate_truth, source_admission_truth = (
        inputs._independent_candidate_truth(provider)
    )
    assert b["candidate_inputs"] == source_candidate_truth
    assert b["candidate_admissions"] == source_admission_truth
    return destination, results, a, b, (source_candidate_truth, source_admission_truth)


def _verify_changed_b(tmp_path, source, changed_b):
    """Simulate a new matching *self-supplied* B SHA; semantics must still fail."""
    _, _, a, _, _ = source
    directory = tmp_path / "bad-b"
    directory.mkdir()
    a_bytes = inputs.canonical_bytes(a)
    b_bytes = inputs.canonical_bytes(changed_b)
    (directory / "publication-A-PROPOSED.json").write_bytes(a_bytes)
    (directory / "planner-B-PROPOSED.json").write_bytes(b_bytes)
    return inputs.validate_externally_pinned_proposals(
        directory,
        expected_a_sha256=inputs.sha(a_bytes),
        expected_b_sha256=inputs.sha(b_bytes),
        expected_source_commit=inputs.SOURCE_COMMIT,
        expected_stage_membership=a["stages"],
    )


def test_git_blob_integrity_fails_closed_on_changed_source(monkeypatch):
    expected_path = "backend/app/services/planner.py"
    original_sha = inputs.PINNED_SOURCE_BLOBS[expected_path]
    monkeypatch.setattr(
        inputs,
        "PINNED_SOURCE_BLOBS",
        {expected_path: "0" * 40},
    )
    with pytest.raises(inputs.PreflightNoGo, match="source Git blob drift"):
        inputs._assert_source_integrity()
    assert len(original_sha) == 40


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("planner_config", "PlannerConfig values"),
        ("week_end", "week_end differs"),
        ("candidate_order", "candidate order/source"),
        ("nutrition", "candidate order/source"),
        ("admission", "candidate admission semantics"),
        ("roles", "accepted member pattern"),
        ("shares", "accepted member pattern"),
        ("hidden_pantry", "hidden Pantry"),
        ("hidden_history", "hidden Pantry"),
        ("source_version", "candidate order/source"),
        ("rights", "candidate order/source"),
        ("energy_target", "reference-energy"),
    ],
)
def test_semantic_mutation_is_rejected_even_with_matching_new_sha(
    tmp_path, grounded_proposals, mutation, message, monkeypatch
):
    _, _, _, accepted, source_truth = grounded_proposals
    # One independently re-read SQLite nutrition/source snapshot is sufficient
    # for adversarial comparisons. The production validator still calls the
    # real independent read; only repeated negative tests reuse that witness.
    monkeypatch.setattr(
        inputs, "_independent_candidate_truth",
        lambda _provider: deepcopy(source_truth),
    )
    b = deepcopy(accepted)
    if mutation == "planner_config":
        b["planner_config"]["repetition_weight"] = "0"
    elif mutation == "week_end":
        b["week_end"] = "2026-11-09"
    elif mutation == "candidate_order":
        b["candidate_inputs"][0], b["candidate_inputs"][1] = (
            b["candidate_inputs"][1], b["candidate_inputs"][0]
        )
    elif mutation == "nutrition":
        b["candidate_inputs"][0]["kcal_per_base_serving"] = "999999"
    elif mutation == "admission":
        b["candidate_admissions"][0]["exact_energy_ready"] = False
    elif mutation == "roles":
        b["members"][0]["opportunities"][0]["role"] = "DINNER"
    elif mutation == "shares":
        b["members"][0]["opportunities"][0]["energy_share"] = "0.5"
    elif mutation == "hidden_pantry":
        b["pantry"] = ["HIDDEN_FOOD"]
    elif mutation == "hidden_history":
        b["history"] = ["HIDDEN_PLAN"]
    elif mutation == "source_version":
        b["candidate_inputs"][0]["source_version"] = "UNREVIEWED"
    elif mutation == "rights":
        b["candidate_inputs"][0]["rights_basis"] = "UNREVIEWED NEW RIGHTS"
    elif mutation == "energy_target":
        b["members"][0]["reference_energy_kcal"] = "50000"
    with pytest.raises(inputs.PreflightNoGo, match=message):
        _verify_changed_b(tmp_path, grounded_proposals, b)


def test_mutated_source_manifest_with_self_pinned_new_a_sha_fails(
    tmp_path, grounded_proposals
):
    _, _, approved_a, approved_b, _ = grounded_proposals
    a = deepcopy(approved_a)
    a["publications"][0]["seed_projection"]["source_name"] = "FABRICATED"
    directory = tmp_path / "bad-a"
    directory.mkdir()
    raw_a = inputs.canonical_bytes(a)
    b = deepcopy(approved_b)
    b["publication_manifest_sha256"] = inputs.sha(raw_a)
    raw_b = inputs.canonical_bytes(b)
    (directory / "publication-A-PROPOSED.json").write_bytes(raw_a)
    (directory / "planner-B-PROPOSED.json").write_bytes(raw_b)
    with pytest.raises((inputs.PreflightNoGo, ValueError)):
        inputs.validate_externally_pinned_proposals(
            directory,
            expected_a_sha256=inputs.sha(raw_a),
            expected_b_sha256=inputs.sha(raw_b),
            expected_source_commit=inputs.SOURCE_COMMIT,
            expected_stage_membership=a["stages"],
        )


def test_semantic_decimal_truth_rejects_nonfinite():
    with pytest.raises(inputs.PreflightNoGo, match="nonfinite"):
        inputs._decimal(Decimal("Infinity"))
