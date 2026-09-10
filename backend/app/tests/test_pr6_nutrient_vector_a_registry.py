"""Offline VECTOR-A research checks; destructive cases mutate copies only."""

from copy import deepcopy
from dataclasses import replace
from decimal import ROUND_DOWN, localcontext
import importlib.util
from pathlib import Path
import sqlite3

import pytest

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.seed.food_ingredients import seed_food_ingredients, load_seed_entries

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "vector_a_validator", ROOT / "scripts/validate_pr6_nutrient_vector_a.py"
)
v = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v)


@pytest.fixture
def artifacts():
    return [v.read_json(ROOT / v.DIRECTORY / name) for name in v.FILES[:4]]


def test_complete_registry_audit_and_deterministic_summary(artifacts):
    first = v.validate_content(*artifacts)
    with localcontext() as ctx:
        ctx.prec = 3
        ctx.rounding = ROUND_DOWN
        second = v.validate_content(*deepcopy(artifacts))
    assert v.canonical(first) == v.canonical(second)
    assert first == v.read_json(ROOT / v.DIRECTORY / "summary.json")
    assert first["profiles_audited"] == 183
    assert first["legacy_field_observations"] == 915
    assert first["registry_candidate_count"] == 51
    assert first["legacy_mapping_counts"] == {
        "SOURCE_COMPONENT_CONFIRMED": 870,
        "LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE": 0,
        "VALUE_MISMATCH": 0,
        "DEFINITION_AMBIGUOUS": 0,
        "VALUE_ABSENT": 45,
    }
    assert len(first["profiles_with_full_five_field_provenance"]) == 138
    assert first["profiles_with_unresolved_provenance"] == []


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "english",
        "code",
        "mixed",
        "unit",
        "kind",
        "semantic",
        "status",
    ],
)
def test_registry_fails_closed(artifacts, fault):
    doc = artifacts[0]
    r = doc["entries"][0]
    if fault == "missing":
        doc["entries"].pop()
    elif fault == "duplicate":
        doc["entries"].append(deepcopy(r))
    elif fault == "english":
        r["display_name_ru"] = "Alpha-linolenic acid"
    elif fault == "code":
        r["display_name_ru"] = r["canonical_code"]
    elif fault == "mixed":
        r["display_name_ru"] = "Кислота Alpha-linolenic"
    elif fault == "unit":
        r["canonical_unit"] = "IU"
    elif fault == "kind":
        r["definition_kind"] = "MEASURED_EXACT"
    elif fault == "semantic":
        r["definition"] = doc["entries"][1]["definition"]
    else:
        r["status"] = "AUTO_APPROVED"
    with pytest.raises(ValueError):
        v.validate_content(*artifacts)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "fake_id",
        "nbr",
        "name",
        "release",
        "type",
        "unit",
        "conversion",
        "conversion_evidence",
        "definition_evidence",
        "target",
        "status",
    ],
)
def test_source_mappings_require_exact_reviewed_component(artifacts, fault):
    mappings = artifacts[1]["mappings"]
    m = next(m for m in mappings if m["mapping_status"] == "EXACT")
    if fault == "missing":
        mappings.remove(m)
    else:
        field, value = {
            "fake_id": ("source_nutrient_id", "999999999"),
            "nbr": ("source_nutrient_nbr", "made-up"),
            "name": ("source_nutrient_name", "Protein"),
            "release": ("source_release", "2025-04"),
            "type": ("source_data_type", "Branded"),
            "unit": ("source_unit", "MG"),
            "conversion": ("conversion_divisor", "1000"),
            "conversion_evidence": ("conversion_evidence_ref", "GUESSED"),
            "definition_evidence": ("definition_evidence_refs", ["GUESSED"]),
            "target": ("canonical_code", "OMEGA_3_TOTAL"),
            "status": ("mapping_status", "SIMILAR_NAME"),
        }[fault]
        m[field] = value
    with pytest.raises(ValueError):
        v.validate_content(*artifacts)


@pytest.mark.parametrize("fault", ["id", "amount", "hash", "food", "infoods"])
def test_offline_source_evidence_cannot_be_rewritten(artifacts, fault):
    manifest = artifacts[3]
    e = manifest["fdc_selected_extracts"][0]
    if fault == "id":
        e["nutrient_rows"][0]["id"] = "fiction"
    elif fault == "amount":
        e["food_nutrient_rows"][0]["amount"] = "0"
    elif fault == "hash":
        next(s for s in manifest["sources"] if s["id"] == "FDC-FOUNDATION")[
            "content_sha256"
        ] = "0" * 64
    elif fault == "food":
        e["food_rows"][0]["data_type"] = "branded_food"
    else:
        manifest["infoods_selected_identifiers"][0]["tagname"] = "GUESS"
    with pytest.raises(ValueError):
        v.validate_content(*artifacts)


@pytest.mark.parametrize("code,nid", sorted(v.REJECTIONS | v.UNPROVEN))
def test_scientific_collisions_and_unproven_mappings_cannot_be_promoted(
    artifacts, code, nid
):
    m = next(
        m
        for m in artifacts[1]["mappings"]
        if (m["canonical_code"], m["source_nutrient_id"]) == (code, nid)
    )
    m["mapping_status"] = "EXACT"
    with pytest.raises(ValueError, match="semantics"):
        v.validate_content(*artifacts)


def test_scientific_distinctions_are_separate_internal_identities(artifacts):
    entries = {r["canonical_code"]: r for r in artifacts[0]["entries"]}
    groups = [
        ["CARBOHYDRATE_BY_DIFFERENCE", "CARBOHYDRATE_AVAILABLE"],
        ["VITAMIN_A_RAE", "RETINOL", "BETA_CAROTENE"],
        ["FOLATE_TOTAL", "FOLATE_DFE", "FOLIC_ACID"],
        ["FAT_TOTAL", "LINOLEIC_ACID", "ALPHA_LINOLENIC_ACID", "EPA", "DHA"],
    ]
    for codes in groups:
        assert len({entries[c]["definition"] for c in codes}) == len(codes)
        assert len({entries[c]["infoods_tagname"] for c in codes}) == len(codes)
    energies = [
        m
        for m in artifacts[1]["mappings"]
        if m["canonical_code"] == "ENERGY_KCAL"
        and m["source_data_type"] == "Foundation"
    ]
    assert {m["source_nutrient_id"] for m in energies} == {
        "1008",
        "1062",
        "2047",
        "2048",
    }
    assert len({m["mapping_rationale"] for m in energies}) == 4
    assert all(
        m["mapping_status"] == "METHOD_SPECIFIC"
        for m in energies
        if m["source_nutrient_id"] != "1062"
    )


@pytest.mark.parametrize(
    "fault",
    [
        "missing_profile",
        "missing_field",
        "duplicate",
        "uuid",
        "source_id",
        "numeric",
        "ambiguous",
        "value",
    ],
)
def test_legacy_coverage_and_provenance_are_fail_closed(artifacts, fault):
    rows = artifacts[2]["rows"]
    row = next(
        r for r in rows if r["legacy_mapping_status"] == "SOURCE_COMPONENT_CONFIRMED"
    )
    if fault == "missing_profile":
        rows[:] = [
            r for r in rows if r["food_ingredient_code"] != row["food_ingredient_code"]
        ]
    elif fault == "missing_field":
        rows.remove(row)
    elif fault == "duplicate":
        rows.append(deepcopy(row))
    elif fault == "uuid":
        row["audit_identity"] = "e5d89989-4146-4997-8bf0-d3065e5e0c61"
    elif fault == "source_id":
        row["source_nutrient_id"] = None
    elif fault == "numeric":
        row["numeric_comparison"]["equal"] = False
    elif fault == "ambiguous":
        row["legacy_mapping_status"] = "DEFINITION_AMBIGUOUS"
    else:
        row["legacy_value"] = "999"
    with pytest.raises(ValueError):
        v.validate_content(*artifacts)


def test_null_fibre_never_becomes_zero_and_zero_is_retained(artifacts):
    row = next(
        r for r in artifacts[2]["rows"] if r["legacy_mapping_status"] == "VALUE_ABSENT"
    )
    assert row["legacy_field"] == "fiber_g" and row["legacy_value"] is None
    assert v.compare_numeric(None, None)["equal"] is None
    assert v.compare_numeric("0.000000", "0")["equal"] is True
    row["legacy_value"] = "0"
    with pytest.raises(ValueError, match="legacy value"):
        v.validate_content(*artifacts)


@pytest.mark.parametrize("bad", [0.1, True, 1, "NaN", "Infinity", "-1", ""])
def test_numeric_comparison_refuses_non_decimal_inputs(bad):
    with pytest.raises(ValueError):
        v.compare_numeric("1.000000", bad)


def test_exact_representation_comparison_has_no_tolerance():
    assert v.compare_numeric("1.234568", "1.2345675")["equal"] is True
    assert v.compare_numeric("1.234568", "1.2345674")["result"] == "DIFFERENT"
    assert v.compare_numeric("1", None)["result"] == "SOURCE_UNAVAILABLE"


def test_historical_provenance_cannot_be_silently_skipped(artifacts):
    inventory, _, _ = v.profile_inventory()
    key = next(iter(inventory))
    historical = dict(inventory[key], source_version="historical-test-version")
    inventory[v.profile_key(historical)] = historical
    with pytest.raises(ValueError, match="every profile"):
        v.validate_legacy(artifacts[2], inventory, artifacts[3])


def test_all_accepted_seed_history_and_all_database_rows_are_covered(
    tmp_path, artifacts
):
    config = DatabaseConfig(path=tmp_path / "accepted-replay.sqlite3")
    seed_food_ingredients(config)
    with sqlite3.connect(config.path) as connection:
        # Deliberately no is_current WHERE clause: includes historical profiles.
        rows = connection.execute(
            "SELECT f.canonical_code, p.source_name, p.source_id, p.source_version, "
            "p.is_current FROM food_nutrition_profiles p "
            "JOIN food_ingredients f ON f.id = p.food_ingredient_id"
        ).fetchall()
    inventory, history, _ = v.profile_inventory()
    assert {tuple(r[:4]) for r in rows} == set(inventory)
    assert len(rows) == 183 and sum(not r[4] for r in rows) == 0
    assert sorted(h["profile_count"] for h in history) == [100, 183]

    # Prove the existing container keeps a replaced profile. Test-only data;
    # nothing is written to accepted seeds or a developer's database.
    entry = load_seed_entries()[0]
    changed = replace(
        entry,
        nutrition=replace(entry.nutrition, source_version="TEST-HISTORICAL-REPLAY"),
    )
    engine = create_sqlite_engine(config)
    try:
        create_food_catalogue_service(engine).reconcile_seed((changed,))
    finally:
        engine.dispose()
    with sqlite3.connect(config.path) as connection:
        counts = connection.execute(
            "SELECT is_current, count(*) FROM food_nutrition_profiles GROUP BY is_current"
        ).fetchall()
    assert dict(counts) == {0: 1, 1: 183}


def test_protected_production_baseline():
    assert v.validate_protected() >= 900


@pytest.mark.parametrize(
    "path",
    [
        "data/seed/food_ingredients/nutrition.csv",
        "data/seed/food_ingredients/ingredients.csv",
        "backend/app/domain/nutrition.py",
        "backend/app/migrations/versions/0028_nutrients.py",
        "data/curation/pr6-data-b2b1/source-manifest.json",
        "data/seed/nutrition_measure_evidence/assessments.json",
    ],
)
def test_unauthorized_diff_is_rejected(monkeypatch, path):
    real_git = v.git

    def changed_git(root, *args):
        result = real_git(root, *args)
        if args == ("diff", "--name-only", v.BASE):
            return result + path.encode() + b"\n"
        return result

    monkeypatch.setattr(v, "git", changed_git)
    with pytest.raises(ValueError):
        v.validate_protected()
