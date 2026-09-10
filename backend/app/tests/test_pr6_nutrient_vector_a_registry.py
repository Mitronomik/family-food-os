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
    assert first["profiles_with_unresolved_component_mapping"] == []


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


def zero_row(artifacts):
    return next(
        r for r in artifacts[2]["rows"] if r["source_value_state"] == "ZERO_REPORTED"
    )


def test_zero_audit_is_reported_not_analytically_exact(artifacts):
    result = v.validate_content(*artifacts)
    audit = result["zero_provenance_audit"]
    assert "known_zero_observations" not in result
    assert audit["source_reported_zero_observations"] == 64
    assert audit["by_dataset"] == {"Foundation": 14, "SR Legacy": 50}
    assert audit["censoring_evidence_partition"] == {
        "EXPLICIT_CENSORED": 0,
        "EXPLICIT_NOT_CENSORED": 0,
        "LOQ_METADATA_PRESENT_STATUS_UNSPECIFIED": 0,
        "NO_CENSORING_METADATA": 64,
    }
    assert audit["zero_resolution_partition"] == {
        "EXACT_ZERO_CONFIRMED": 0,
        "BLOCKED_CENSORED": 0,
        "UNRESOLVED": 64,
    }
    assert len(audit["unresolved_observations"]) == 64
    assert (
        sum(r["source_value_state"] == "NONZERO_REPORTED" for r in artifacts[2]["rows"])
        == 806
    )
    assert (
        sum(r["source_value_state"] == "VALUE_ABSENT" for r in artifacts[2]["rows"])
        == 45
    )


@pytest.mark.parametrize(
    "fault",
    [
        "exact_without_evidence",
        "censored_to_exact",
        "metadata_stripped",
        "numeric_changed",
        "row_hash_forged",
        "absent_to_zero",
        "value_state_unknown",
        "censor_state_unknown",
        "unresolved_counted_exact",
        "source_identity",
        "evidence_link",
        "missing",
        "failed_import",
        "filtered_out",
    ],
)
def test_zero_semantics_fail_closed(artifacts, fault):
    row = zero_row(artifacts)
    if fault == "exact_without_evidence":
        row["zero_resolution"] = "EXACT_ZERO_CONFIRMED"
    elif fault == "censored_to_exact":
        row.update(
            censoring_evidence_state="EXPLICIT_CENSORED",
            zero_resolution="EXACT_ZERO_CONFIRMED",
        )
    elif fault == "metadata_stripped":
        del row["source_observation"]["row"]["footnote"]
    elif fault == "numeric_changed":
        row["source_value"] = "0.01"
    elif fault == "row_hash_forged":
        row["source_observation"]["row_sha256"] = "0" * 64
    elif fault == "absent_to_zero":
        row = next(
            r
            for r in artifacts[2]["rows"]
            if r["legacy_mapping_status"] == "VALUE_ABSENT"
        )
        row["source_value_state"] = "ZERO_REPORTED"
    elif fault == "value_state_unknown":
        row["source_value_state"] = "KNOWN_ZERO"
    elif fault == "censor_state_unknown":
        row["censoring_evidence_state"] = "ASSUME_NOT_CENSORED"
    elif fault == "unresolved_counted_exact":
        row.update(
            censoring_evidence_state="EXPLICIT_NOT_CENSORED",
            zero_resolution="EXACT_ZERO_CONFIRMED",
            exact_zero_evidence_refs=["FDC-DICTIONARY"],
        )
    elif fault == "source_identity":
        row["source_observation"]["row"]["id"] = "1"
    elif fault == "evidence_link":
        row["zero_provenance_ref"] = None
    else:
        row["source_value_state"] = fault.upper()
    with pytest.raises(ValueError):
        v.validate_content(*artifacts)


def test_numeric_loq_is_not_itself_censoring_or_exactness(artifacts):
    # Synthetic release-shape fixture, NOT an assertion about the accepted rows.
    row = zero_row(artifacts)
    evidence = deepcopy(
        next(
            e
            for e in artifacts[3]["zero_provenance_evidence"]["observations"]
            if e["evidence_ref"] == row["evidence_ref"]
        )
    )
    evidence["json_food_nutrient"]["loq"] = "0.03"
    interpreted = v.zero_semantics(evidence)
    assert (
        interpreted["censoring_evidence_state"]
        == "LOQ_METADATA_PRESENT_STATUS_UNSPECIFIED"
    )
    assert interpreted["zero_resolution"] == "UNRESOLVED"
    row.update(interpreted)
    v.validate_observation_semantics(
        row, evidence["csv_row"], {row["evidence_ref"]: evidence}
    )
    # Stripping the classification while raw LOQ remains must fail too, even
    # before the independent immutable-evidence checksum guard is applied.
    row["censoring_evidence_state"] = "NO_CENSORING_METADATA"
    with pytest.raises(ValueError, match="censoring assertion"):
        v.validate_observation_semantics(
            row, evidence["csv_row"], {row["evidence_ref"]: evidence}
        )


@pytest.mark.parametrize(
    "fault",
    ["metadata", "row_hash", "related_result", "json_row", "duplicate", "missing"],
)
def test_zero_evidence_is_immutable_and_complete(artifacts, fault):
    evidence = artifacts[3]["zero_provenance_evidence"]
    entry = evidence["observations"][0]
    if fault == "metadata":
        entry["csv_row"].pop("min")
    elif fault == "row_hash":
        entry["csv_row_sha256"] = "0" * 64
    elif fault == "related_result":
        entry = next(
            e
            for e in evidence["observations"]
            if e["related_csv_rows"].get("sub_sample_result.csv")
        )
        entry["related_csv_rows"]["sub_sample_result.csv"] = []
    elif fault == "json_row":
        entry["json_food_nutrient"] = None
    elif fault == "duplicate":
        evidence["observations"].append(deepcopy(entry))
    else:
        evidence["observations"].pop()
    with pytest.raises(ValueError, match="Zero source evidence"):
        v.validate_content(*artifacts)


@pytest.mark.parametrize(
    "fault", ["foundation_total", "partition", "unresolved_as_exact", "old_known_zero"]
)
def test_zero_summary_cannot_invent_authority_or_drop_observations(artifacts, fault):
    expected = v.validate_content(*artifacts)
    actual = deepcopy(expected)
    audit = actual["zero_provenance_audit"]
    if fault == "foundation_total":
        audit["by_dataset"]["Foundation"] += 1
    elif fault == "partition":
        audit["censoring_evidence_partition"]["NO_CENSORING_METADATA"] -= 1
    elif fault == "unresolved_as_exact":
        audit["zero_resolution_partition"]["UNRESOLVED"] -= 1
        audit["zero_resolution_partition"]["EXACT_ZERO_CONFIRMED"] += 1
    else:
        actual["known_zero_observations"] = 64
    with pytest.raises(ValueError):
        v.validate_summary(actual, expected)


def test_source_replay_requires_exact_pinned_bytes_before_parsing(tmp_path, artifacts):
    (tmp_path / "foundation.zip").write_bytes(b"different release or corrupt archive")
    with pytest.raises(ValueError, match="Pinned source hash mismatch"):
        v.replay_zero_sources(tmp_path, artifacts[2])


@pytest.mark.parametrize(
    "fault", ["migration_0028", "migration_head", "estimate_mass", "estimate_accepted"]
)
def test_protected_migration_and_estimate_guards_use_actual_files(
    tmp_path, monkeypatch, fault
):
    # Preserve real repository files: only a disposable copy is poisoned. Git
    # reports a clean scope so this also exercises the dedicated inventory/data
    # guards independently of the earlier protected-diff guard.
    migration = "backend/app/db/migrations.py"
    audit_path = "data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json"
    for name in [migration, audit_path]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    versions = tmp_path / "backend/app/migrations/versions"
    versions.mkdir(parents=True)
    real_git = v.git
    monkeypatch.setattr(v, "git", lambda _root, *args: real_git(ROOT, *args))
    if fault == "migration_0028":
        (versions / "0028_nutrients.py").write_text("# unauthorized\n")
    elif fault == "migration_head":
        target = tmp_path / migration
        target.write_text(
            target.read_text().replace(v.MIGRATION_HEAD, "0028_nutrients")
        )
    else:
        audit = v.read_json(tmp_path / audit_path)
        row = next(
            r
            for record in audit["records"]
            for r in record["rows"]
            if "CONVERSION_ESTIMATE_NOT_ACCEPTED" in r["issues"]
        )
        if fault == "estimate_mass":
            row["mass_g"] = "1"
        else:
            row["issues"].remove("CONVERSION_ESTIMATE_NOT_ACCEPTED")
        (tmp_path / audit_path).write_bytes(v.canonical(audit))
    with pytest.raises(ValueError, match="Migration|estimate candidates"):
        v.validate_protected(tmp_path)


def test_extra_known_zero_flag_cannot_bypass_controlled_states(artifacts):
    zero_row(artifacts)["known_zero"] = True
    with pytest.raises(ValueError, match="Unrecognized"):
        v.validate_content(*artifacts)


@pytest.mark.parametrize(
    "field,state",
    [
        ("censoring_evidence_state", "NOT_APPLICABLE"),
        ("zero_resolution", "NOT_APPLICABLE"),
    ],
)
def test_zero_partition_rejects_unaccounted_observation(artifacts, field, state):
    zero_row(artifacts)[field] = state
    with pytest.raises(ValueError, match="partition"):
        v.summarize_zeros(artifacts[2]["rows"])


def test_stripped_loq_bytes_fail_even_when_synthetic_snapshot_was_trusted(
    artifacts, monkeypatch
):
    # The real 64-row corpus has no LOQ. This fixture models an independently
    # reviewed snapshot that did contain one, to exercise loss of raw metadata.
    manifest = artifacts[3]
    evidence = manifest["zero_provenance_evidence"]
    entry = next(e for e in evidence["observations"] if e["json_food_nutrient"])
    entry["json_food_nutrient"]["loq"] = "0.03"
    entry["json_row_sha256"] = v.digest(v.canonical(entry["json_food_nutrient"]))
    monkeypatch.setattr(v, "ZERO_EVIDENCE_HASH", v.digest(v.canonical(evidence)))
    v.validate_zero_evidence(manifest)
    del entry["json_food_nutrient"]["loq"]
    # Forging a new row hash does not bypass the independently pinned snapshot.
    entry["json_row_sha256"] = v.digest(v.canonical(entry["json_food_nutrient"]))
    with pytest.raises(ValueError, match="stripped"):
        v.validate_zero_evidence(manifest)
