"""PR10-FF pre-run materialization; no Planner selection or self-approved pin."""

import json

import pytest

from scripts import pr10_ff_pre_generation_inputs as inputs


def test_materialization_is_pre_generation_and_caller_pin_is_required(
    tmp_path, monkeypatch
):
    from app.domain import planner as domain_planner
    from app.services import planner as planner_module

    def forbidden(*args, **kwargs):
        pytest.fail("real Planner week generation is forbidden before A/B review")

    monkeypatch.setattr(planner_module.PlannerService, "generate_authoritative", forbidden)
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
    assert len([item for item in a["approved_ids"] if item["kind"] == "HOUSEHOLD_MEMBER"]) == 3
    with pytest.raises(inputs.PreflightNoGo, match="ordinal"):
        inputs._member_profile(4)
    with pytest.raises(inputs.PreflightNoGo, match="nonfinite"):
        inputs._decimal(__import__("decimal").Decimal("NaN"))
