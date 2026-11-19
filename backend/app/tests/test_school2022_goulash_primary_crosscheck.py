"""Independent-card factual reconciliation; never authorizes family portions or Prep."""

import copy
import json
import subprocess
import sys
from decimal import Decimal

import pytest

from scripts.verify_school2022_goulash_source import (
    BLOCKED,
    RECIPE_CODE,
    REPORT_SCHEMA,
    SourceCrosscheckBlocked,
    crosscheck,
    load_sources,
)


@pytest.fixture()
def sources():
    return load_sources()


def test_original_primary_pdf_card_numeric_facts_match_frozen_manifest(sources):
    manifest, witness = sources
    report = crosscheck(manifest=manifest, witness=witness)
    assert report["schema"] == REPORT_SCHEMA
    assert report["recipe_code"] == RECIPE_CODE
    assert report["original_primary_card_portion_g"] == "80"
    assert report["finished_meat_g"] == "46.6"
    assert report["finished_sauce_g"] == "33.4"
    assert Decimal(report["finished_meat_g"]) + Decimal(
        report["finished_sauce_g"]
    ) == Decimal(report["original_primary_card_portion_g"])
    assert report["source_card_energy_kcal"] == "185.6"
    assert report["ingredient_rows_reconciled"] == 7
    assert all(row["amount_matches"] for row in report["ingredient_rows"])
    assert report["source_age_context"] == "7–11 лет"
    assert report["source_text_numeric_facts_match_manifest"] is True
    assert report["prepared_nutrition_available_codes"] == ["ENERGY_KCAL"]
    assert report["prepared_nutrition_unknown_codes"] == 53
    assert report["current_pdf_binary_independently_verified"] is False
    assert report["family_course_suitability"] == "UNKNOWN"
    assert report["family_scaled_edible_mass"] == "UNKNOWN"
    assert report["member_physical_portion_policy"] == "UNKNOWN"
    assert report["source_card_holding_freezing_reheat_permission"] == "NOT_PROVEN"
    assert report["customer_release"] == BLOCKED


def test_cli_prints_deterministic_standalone_read_only_source_receipt(sources):
    manifest, witness = sources
    expected = crosscheck(manifest=manifest, witness=witness)
    cmd = [
        sys.executable,
        "-m",
        "scripts.verify_school2022_goulash_source",
    ]
    a = subprocess.run(cmd, check=True, capture_output=True, text=True)
    b = subprocess.run(cmd, check=True, capture_output=True, text=True)
    assert a.stdout == b.stdout
    assert json.loads(a.stdout) == expected
    assert a.stderr == ""


@pytest.mark.parametrize(
    ("ingredient", "wrong_amount"),
    [
        ("BEEF_CATEGORY_1_RAW", "73"),
        ("ONION_BULB_FRESH", "9.2"),
        ("WATER", "106"),
    ],
)
def test_fails_if_primary_card_net_amount_disagrees_with_publication(
    sources, ingredient, wrong_amount
):
    manifest, witness = copy.deepcopy(sources)
    for row in witness["recipe"]["input_quantities"]:
        if row["canonical_food_code"] == ingredient:
            row["net_g"] = wrong_amount
            break
    with pytest.raises(SourceCrosscheckBlocked, match="contradict card"):
        crosscheck(manifest=manifest, witness=witness)


@pytest.mark.parametrize(
    "name",
    [
        "source_output_g",
        "finished_meat_g",
        "finished_sauce_g",
        "energy_kcal_per_source_card",
    ],
)
def test_fails_if_output_component_or_energy_disagrees(sources, name):
    manifest, witness = copy.deepcopy(sources)
    witness["recipe"][name] = "79"
    with pytest.raises(SourceCrosscheckBlocked):
        crosscheck(manifest=manifest, witness=witness)


def test_fails_if_publication_version_original_base_or_hash_changes(sources):
    manifest, witness = copy.deepcopy(sources)
    entry = manifest["recipes"][RECIPE_CODE]
    entry["trusted_recipe_seed"]["version"]["source_original_servings"] = "2"
    with pytest.raises(SourceCrosscheckBlocked):
        crosscheck(manifest=manifest, witness=witness)

    manifest, witness = copy.deepcopy(sources)
    manifest["recipes"][RECIPE_CODE]["source_receipt"][
        "exact_source_card_sha256"
    ] = "0" * 64
    with pytest.raises(SourceCrosscheckBlocked):
        crosscheck(manifest=manifest, witness=witness)


def test_cannot_promote_transcription_to_new_pdf_binary_receipt(sources):
    manifest, witness = copy.deepcopy(sources)
    witness["publication_context"]["fresh_pdf_sha256_verified"] = True
    with pytest.raises(SourceCrosscheckBlocked, match="новый байтовый"):
        crosscheck(manifest=manifest, witness=witness)


def test_cannot_promote_source_recipe_to_safe_family_portion_or_freezing(sources):
    for unsafe_field in (
        "scaled_family_ready_edible_mass_is_verified",
        "course_SECOND_for_family_is_authorized",
        "individual_age_or_goal_portion_policy_is_verified",
        "finished_cooked_batch_storage_freezing_reheat_is_authorized",
    ):
        manifest, witness = copy.deepcopy(sources)
        witness["interpretation_limits"][unsafe_field] = True
        with pytest.raises(SourceCrosscheckBlocked):
            crosscheck(manifest=manifest, witness=witness)


def test_manifest_payload_must_retain_accepted_exact_git_blob_sha(sources, tmp_path):
    manifest, _ = sources
    path = tmp_path / "modified-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    from scripts.verify_school2022_goulash_source import load_sources

    with pytest.raises(SourceCrosscheckBlocked, match="Git blob"):
        load_sources(manifest_path=path)
