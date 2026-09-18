"""Gate1-A fresh-database audit regression proof."""

from collections import Counter
import json
from pathlib import Path

from app.db.config import DatabaseConfig
from scripts.audit_gate1a_readiness import audit


def test_fresh_current_readiness_matrix(tmp_path) -> None:
    config = DatabaseConfig(path=tmp_path / "gate1a.sqlite")
    result = audit(config)

    assert result["accepted_starting_sha"] == (
        "ce5cf6e2faaf9159e74d8c235f334d47743ab2a0"
    )
    assert result["recipe_count"] == 30
    assert Counter(row["nutrition_status"] for row in result["recipes"]) == {
        "INCOMPLETE": 29,
        "CONDITIONAL": 1,
    }
    assert [
        row["recipe_code"]
        for row in result["recipes"]
        if row["technical_gate1_suitable"]
    ] == ["WIC1_OVERNIGHT_OATS_CINNAMON_APPLE"]
    assert all(not row["consumer_publication_ready"] for row in result["recipes"])


def test_committed_matrix_matches_fresh_current_truth(tmp_path) -> None:
    result = audit(DatabaseConfig(path=tmp_path / "gate1a.sqlite"))
    committed = json.loads(
        (
            Path(__file__).resolve().parents[3]
            / "data/curation/gate1a-data-readiness/current-readiness.json"
        ).read_text(encoding="utf-8")
    )

    # Seed identities are deployment-local UUIDs; all authoritative facts match.
    for document in (result, committed):
        for row in document["recipes"]:
            row.pop("recipe_version_id")
    assert result == committed
