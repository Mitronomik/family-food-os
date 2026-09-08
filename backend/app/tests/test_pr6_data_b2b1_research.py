"""Research integrity and fail-closed boundaries; no network or production writes."""

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "b2b1_validator", ROOT / "scripts/validate_pr6_data_b2b1.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture
def research():
    directory = ROOT / validator.DIRECTORY
    return (
        validator.read_json(directory / "semantic-profile-audit.json"),
        validator.read_json(directory / "source-manifest.json"),
    )


def test_current_coverage_provenance_and_summary(research):
    audit, manifest = research
    summary = validator.validate_content(audit, manifest)
    assert summary == validator.read_json(ROOT / validator.DIRECTORY / "summary.json")
    assert summary["target_issue_occurrence_counts"] == {
        "FOOD_FORM_MISMATCH": 17,
        "IDENTITY_MISMATCH": 1,
        "PROFILE_REPRESENTATIVENESS_REVIEW": 19,
    }
    assert summary["distinct_target_row_count"] == 37
    assert summary["affected_recipe_count"] == 23
    assert summary["affected_food_ingredient_count"] == 19
    assert summary["all_usage_row_count"] == 46
    assert summary["all_usage_recipe_count"] == 25


@pytest.mark.parametrize("fault", ["missing", "duplicate", "historical", "issue"])
def test_coverage_rejects_missing_duplicate_historical_and_dropped_issues(
    research, fault
):
    audit, manifest = research
    if fault == "missing":
        audit["rows"].pop()
    elif fault == "duplicate":
        audit["rows"].append(deepcopy(audit["rows"][0]))
    elif fault == "historical":
        row = next(r for r in audit["rows"] if r["current_recipe_version_number"] == 2)
        row["current_recipe_version_number"] = 1
    else:
        audit["rows"][0]["current_issue_codes"] = []
    with pytest.raises(ValueError):
        validator.validate_content(audit, manifest)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("resolution_code", "NUTRIENTS_CLOSE_ENOUGH"),
        ("conversion_after_semantic_resolution", "ESTIMATE_ACCEPTED"),
        ("stable_row_identity", "historical-or-database-uuid"),
    ],
)
def test_controlled_codes_and_stable_identity(research, field, value):
    audit, manifest = research
    audit["rows"][0][field] = value
    with pytest.raises(ValueError):
        validator.validate_content(audit, manifest)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_source",
        "nutrient",
        "decimal",
        "description",
        "release",
        "original_hash",
        "data_type",
        "release_hash",
    ],
)
def test_selected_primary_source_facts_cannot_be_forged(research, fault):
    audit, manifest = research
    selected = next(s for s in manifest["sources"] if s.get("selected_by_rows"))
    if fault == "missing_source":
        manifest["sources"].remove(selected)
    elif fault == "nutrient":
        selected["profile"]["kcal"] = "9999"
    elif fault == "decimal":
        selected["profile"]["protein_g"] = float("nan")
    elif fault == "description":
        selected["food_description"] = "All forms are equivalent"
    elif fault == "release":
        selected["source_version_or_release"] = "unknown"
    elif fault == "data_type":
        selected["source_data_type"] = "Community estimate"
    elif fault == "release_hash":
        release = next(
            s
            for s in manifest["sources"]
            if s["manifest_id"] == selected["release_manifest_id"]
        )
        release["archive_sha256"] = "0" * 64
    else:
        source = next(
            s for s in manifest["sources"] if s["source_type"] == "ORIGINAL_RECIPE"
        )
        source["reopened_sha256"] = "0" * 64
    with pytest.raises((ValueError, KeyError)):
        validator.validate_content(audit, manifest)


def test_safe_replacement_must_cover_non_target_usages(research):
    audit, manifest = research
    row = next(r for r in audit["rows"] if r["food_ingredient_code"] == "OATS_ROLLED")
    assert len(row["all_current_food_ingredient_usages"]) == 3
    row["global_replacement_compatibility"].pop()
    with pytest.raises(ValueError, match="global replacement misses usages"):
        validator.validate_content(audit, manifest)


def test_shared_food_matrix_cannot_hide_an_incompatible_use(research):
    audit, manifest = research
    audit["food_ingredient_usage_matrix"]["APPLE"].pop()
    with pytest.raises(ValueError, match="incomplete all-usage analysis"):
        validator.validate_content(audit, manifest)


def test_apples_and_yield_cases_are_not_safe_global_swaps(research):
    audit, _ = research
    apples = [r for r in audit["rows"] if r["food_ingredient_code"] == "APPLE"]
    assert not any(r["global_replacement_safe"] for r in apples)
    assert {r["resolution_code"] for r in apples} == {
        "ADD_NUTRITION_RELEVANT_FOOD_INGREDIENT",
        "SOURCE_FORM_AMBIGUOUS",
        "ARCHITECTURE_DECISION_REQUIRED",
    }
    yields = [
        r
        for r in audit["rows"]
        if r["resolution_code"] == "EDIBLE_BASIS_OR_YIELD_REQUIRED"
    ]
    assert {r["food_ingredient_code"] for r in yields} == {
        "CHICKEN_THIGH",
        "BUTTERNUT_SQUASH",
        "POTATO",
    }
    assert all(r["candidate_profile_source_manifest_id"] is None for r in yields)
    assert all(
        r["conversion_after_semantic_resolution"] == "STILL_EDIBLE_YIELD_REQUIRED"
        for r in yields
    )


def test_semantic_resolution_does_not_promote_estimates(research):
    audit, manifest = research
    assert len(audit["estimate_boundary"]["current_non_executable_estimate_rows"]) == 43
    row = next(
        r
        for r in audit["rows"]
        if "CONVERSION_ESTIMATE_NOT_ACCEPTED" in r["current_issue_codes"]
    )
    row["conversion_after_semantic_resolution"] = "ALREADY_EXACT"
    with pytest.raises(ValueError, match="estimate promoted"):
        validator.validate_content(audit, manifest)


@pytest.mark.parametrize(
    "fault", ["decision", "missing_option", "missing_assumptions", "missing_rejection"]
)
def test_architecture_is_complete_but_not_approved(research, fault):
    audit, manifest = research
    architecture = audit["architecture_recommendation"]
    if fault == "decision":
        architecture["label"] = "DECISION"
    elif fault == "missing_option":
        del architecture["options"]["C"]
    elif fault == "missing_assumptions":
        architecture["assumptions"] = []
    else:
        architecture["alternatives_rejected"] = ["B"]
    with pytest.raises(ValueError, match="architecture|alternatives"):
        validator.validate_content(audit, manifest)


def test_summary_is_independent_of_row_order(research):
    audit, _ = research
    expected = validator.summarize(audit)
    audit["rows"].reverse()
    assert validator.summarize(audit) == expected


def test_exact_main_and_audit_hash_are_pinned(research):
    audit, manifest = research
    audit["starting_main"] = "7169" + "0" * 36
    with pytest.raises(ValueError, match="starting-main"):
        validator.validate_content(audit, manifest)
    audit["starting_main"] = validator.BASE
    audit["current_audit_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="B2-A authority"):
        validator.validate_content(audit, manifest)


def test_protected_production_files_equal_exact_accepted_git_objects(research):
    audit, _ = research
    assert validator.validate_protected(audit) == 683


def test_research_cannot_rebaseline_a_protected_hash(research):
    audit, _ = research
    audit["protected_file_sha256"]["data/seed/food_ingredients/nutrition.csv"] = (
        "0" * 64
    )
    with pytest.raises(ValueError, match="differs from accepted main"):
        validator.validate_protected(audit)


def test_production_mutation_detected_without_writing_production(research, monkeypatch):
    audit, _ = research
    original = Path.read_bytes
    protected = ROOT / "data/seed/food_ingredients/nutrition.csv"

    def changed_bytes(path):
        data = original(path)
        return data + b"\n" if path == protected else data

    monkeypatch.setattr(Path, "read_bytes", changed_bytes)
    with pytest.raises(ValueError, match="protected production bytes changed"):
        validator.validate_protected(audit)


@pytest.mark.parametrize("invalid", ["NaN", "Infinity", "-1"])
def test_even_self_consistent_source_extract_rejects_invalid_decimal(research, invalid):
    audit, manifest = research
    source = next(s for s in manifest["sources"] if s["manifest_id"] == "FDC-168173")
    nutrient = next(
        n
        for n in source["source_extract"]["food_nutrient.csv"]
        if n["nutrient_id"] == "1008"
    )
    nutrient["amount"] = invalid
    source["profile"]["kcal"] = invalid
    source["source_extract_sha256"] = validator.digest(
        validator.canonical(source["source_extract"])
    )
    with pytest.raises(ValueError, match="invalid nonnegative kcal"):
        validator.validate_content(audit, manifest)


def test_non_target_addition_needs_explicit_justification(research):
    audit, manifest = research
    row = deepcopy(audit["rows"][0])
    row["ingredient_position"] = 1
    row["stable_row_identity"] = validator.row_id(row)
    audit["rows"].append(row)
    with pytest.raises(ValueError, match="unjustified non-target"):
        validator.validate_content(audit, manifest)


def test_new_migration_is_detected_without_creating_one(research, monkeypatch):
    audit, _ = research
    original = Path.glob

    def migration_inventory(path, pattern):
        result = list(original(path, pattern))
        if path == ROOT / "backend/app/migrations/versions":
            result.append(path / "0028_forbidden.py")
        return iter(result)

    monkeypatch.setattr(Path, "glob", migration_inventory)
    with pytest.raises(ValueError, match="migration head is not 0027"):
        validator.validate_protected(audit)


def test_research_cannot_claim_new_production_authority(research):
    audit, manifest = research
    audit["estimate_boundary"]["new_recipe_versions"] = 1
    with pytest.raises(ValueError, match="production/estimate authority claimed"):
        validator.validate_content(audit, manifest)
