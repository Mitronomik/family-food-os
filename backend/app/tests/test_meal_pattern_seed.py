import json
import sqlite3
from dataclasses import asdict

import pytest

from app.db.config import DatabaseConfig
from app.seed.meal_patterns import (
    DEFAULT_EVIDENCE_PATH,
    DEFAULT_SEED_PATH,
    MealPatternSeedError,
    load_seed_entries,
    seed_meal_patterns,
)


def test_checked_in_seed_is_bounded_adult_wellness_corpus_with_reviewable_evidence():
    entries = load_seed_entries()
    assert {entry.code for entry in entries} == {
        "ADULT_REGULAR_3",
        "ADULT_REGULAR_3_PLUS_SNACK",
    }
    assert all(entry.version.lifecycle == "PUBLISHED" for entry in entries)
    assert all(entry.version.scope == "WELLNESS_SCHEDULE" for entry in entries)
    assert all(entry.version.min_age_years == 19 for entry in entries)
    assert all(len(entry.version.evidence) == 2 for entry in entries)
    assert all(entry.version.display_name_ru for entry in entries)
    assert all(entry.version.explanation_ru for entry in entries)

    explanations = " ".join(entry.version.explanation_ru for entry in entries)
    assert "не утверждает" in explanations
    assert "не приписывает" in explanations

    evidence = json.loads(DEFAULT_EVIDENCE_PATH.read_text(encoding="utf-8"))["sources"]
    assert {row["code"] for row in evidence} == {
        "USDA_NESR_DGAC2025_SR09",
        "USDA_NESR_DGAC2025_SR10",
    }
    assert all(row["source_url"].startswith("https://nesr.usda.gov/") for row in evidence)
    assert {row["evidence_scope"] for row in evidence} == {
        "FREQUENCY_OUTCOME_UNCERTAINTY"
    }


def test_seed_is_atomic_idempotent_and_has_expected_bounded_counts(tmp_path):
    config = DatabaseConfig(path=tmp_path / "seed.sqlite")
    first = seed_meal_patterns(config)
    second = seed_meal_patterns(config)
    assert asdict(first) == {
        "programs_inserted": 2,
        "programs_existing": 0,
        "versions_inserted": 2,
        "versions_existing": 0,
    }
    assert asdict(second) == {
        "programs_inserted": 0,
        "programs_existing": 2,
        "versions_inserted": 0,
        "versions_existing": 2,
    }
    with sqlite3.connect(config.path) as connection:
        counts = tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "meal_pattern_programs",
                "meal_pattern_program_versions",
                "meal_pattern_opportunities",
                "meal_pattern_tags",
                "meal_pattern_evidence",
            )
        )
    assert counts == (2, 2, 7, 2, 4)


def test_loader_rejects_unreviewed_catalogue_expansion(tmp_path):
    payload = json.loads(DEFAULT_SEED_PATH.read_text(encoding="utf-8"))
    extra = json.loads(json.dumps(payload["programs"][0]))
    extra["code"] = "UNREVIEWED_EXTRA"
    payload["programs"].append(extra)
    changed = tmp_path / "programs.json"
    changed.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(MealPatternSeedError, match="reviewed bounded corpus"):
        load_seed_entries(changed, DEFAULT_EVIDENCE_PATH)
