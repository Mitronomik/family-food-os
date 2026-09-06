"""Offline research integrity, not authorization to import curated conversions."""

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "validate_pr6_data_a", ROOT / "scripts/validate_pr6_data_a.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
DIRECTORY = validator.DIRECTORY
DATA_A_MAIN = "60908eb8270ef356eff8552855b4cc5d2aa9ee44"


@pytest.fixture
def evidence():
    return (
        validator.read(DIRECTORY / "conversion-gap-audit.json"),
        validator.read(DIRECTORY / "source-manifest.json"),
    )


def test_complete_stable_corpus_and_source_integrity(evidence):
    audit, manifest = evidence
    assert validator.validate(audit, manifest, protected_revision=DATA_A_MAIN) == []
    assert len(audit["rows"]) == 189
    assert len({r["recipe_canonical_code"] for r in audit["rows"]}) == 30
    assert Counter(r["recipe_unit"] for r in audit["rows"]) == {
        "g": 31,
        "ml": 123,
        "pcs": 35,
    }
    assert all(not r["recipe_source_id"].startswith("000000") for r in audit["rows"])


def test_summary_is_deterministic_and_pinned(evidence):
    audit, _ = evidence
    assert validator.summary(audit["rows"]) == validator.read(
        DIRECTORY / "summary.json"
    )
    assert validator.summary(list(reversed(audit["rows"]))) == validator.summary(
        audit["rows"]
    )


def test_accepted_corpus_without_b1_seed_now_fails_closed(tmp_path, monkeypatch):
    from app.db.config import DatabaseConfig
    from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
    from app.seed.food_recipes import seed_food_recipes
    from app.tests.test_nutrition_catalogue import audit_catalogue

    monkeypatch.setenv("AI_ENABLED", "false")
    config = DatabaseConfig(path=tmp_path / "research-baseline.sqlite")
    seed_food_recipes(config)
    engine = create_sqlite_engine(config)
    try:
        report = audit_catalogue(engine)
        assert report["recipes"] == 30
        assert report["statuses"] == {
            "COMPLETE": 0,
            "COMPLETE_WITH_WARNINGS": 0,
            "CONDITIONAL": 0,
            "INCOMPLETE": 30,
        }
        assert report["warning_occurrences"]["MISSING_NUTRITION_ASSESSMENT"] == 189
        assert report["warning_occurrences"]["MISSING_DENSITY"] == 0
        assert report["warning_occurrences"]["UNSUPPORTED_PIECE_MASS"] == 0
        assert report["warning_occurrences"]["ESTIMATION_STATUS_UNKNOWN"] == 189
        assert all(
            row["mass_g"] is None
            for recipe in report["records"]
            for row in recipe["rows"]
        )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_row",
        "duplicate_row",
        "wrong_identity",
        "missing_provenance",
        "invented_mass",
        "zero_mass",
        "false_exact",
        "false_ready",
        "duplicate_source",
        "unresolved_false_exact",
        "wrong_pr4_selection",
    ],
)
def test_validator_rejects_research_corruption(evidence, mutation):
    audit, manifest = deepcopy(evidence)
    candidate = next(r for r in audit["rows"] if r["implementation_ready"])
    estimated = next(r for r in audit["rows"] if r["estimated"] is True)
    if mutation == "missing_row":
        audit["rows"].pop()
    elif mutation == "duplicate_row":
        audit["rows"][-1] = audit["rows"][0]
    elif mutation == "wrong_identity":
        audit["rows"][0]["recipe_source_version"] = "invented"
    elif mutation == "missing_provenance":
        candidate["source_manifest_ids"] = []
    elif mutation == "invented_mass":
        candidate["candidate_mass_g"] = "999.000000"
    elif mutation == "zero_mass":
        candidate["candidate_mass_g"] = "0"
    elif mutation == "false_exact":
        estimated["estimated"] = False
    elif mutation == "false_ready":
        blocked = next(
            r for r in audit["rows"] if r["semantic_compatibility"] == "FORM_MISMATCH"
        )
        blocked["implementation_ready"] = True
    elif mutation == "duplicate_source":
        manifest["sources"].append(manifest["sources"][0])
    elif mutation == "unresolved_false_exact":
        row = next(
            r
            for r in audit["rows"]
            if r["decision_code"] == "MEASURE_OR_SIZE_AMBIGUOUS"
        )
        row["estimated"] = False
    elif mutation == "wrong_pr4_selection":
        candidate["accepted_pr4_selection"]["quantity_text"] = "invented"
    assert validator.validate(audit, manifest, check_protected=False)


def test_exact_portions_retain_food_form_and_source_measure(evidence):
    audit, manifest = evidence
    sources = {s["manifest_id"]: s for s in manifest["sources"]}
    amounts = {
        "cup": 240,
        "tablespoon": 15,
        "tbsp": 15,
        "teaspoon": 5,
        "tsp": 5,
        "liter": 1000,
    }
    from decimal import Decimal

    for row in audit["rows"]:
        if row["decision_code"] != "FDC_EXACT_PORTION":
            continue
        method = row["conversion_method"]
        source = sources[method["source_manifest_id"]]
        if row["recipe_unit"] == "ml":
            measure = source["measure_description"]
            if measure == "undetermined":
                measure = source["modifier_or_form"].split(",")[0].split(" (")[0]
            assert Decimal(method["portion_input_quantity"]) == (
                Decimal(source["amount"]) * amounts[measure]
            )
        if source["source_id"] == "173647":
            assert row["food_ingredient_code"] == "WATER"
        assert row["review_note"]


def test_source_weight_never_crosses_food_or_alternative_boundary(evidence):
    rows = {
        (r["recipe_canonical_code"], r["ingredient_position"]): r
        for r in evidence[0]["rows"]
    }
    chicken = rows["SNAP4_BRAISED_CHICKEN_SPINACH", 1]
    assert chicken["direct_source_mass_review"]["source_total_g"] == "680.388555"
    assert chicken["direct_source_mass_review"]["edible_as_used"] is False
    assert chicken["candidate_mass_g"] is None
    assert (
        rows["SNAP4_BRAISED_CHICKEN_SPINACH", 10]["piece_review"]["source_object"]
        == "fresh spinach bunch"
    )
    for key in [("HARV6_GARDEN_PASTA_SALAD", 1), ("CACFP6_TABBOULEH", 12)]:
        assert rows[key]["semantic_compatibility"] == "FORM_MISMATCH"
        assert not rows[key]["implementation_ready"]
    assert (
        "SOURCE_ALTERNATIVE_WEIGHT_MISAPPLIED"
        in rows["HARV6_FRESH_TOMATO_SALSA", 1]["additional_blockers"]
    )
    # Accepted fresh cauliflower and all-one-fruit strawberry choices are not
    # rediscovered as unsupported generic/mixed ingredient identity changes.
    assert (
        rows["WIC1_BEYOND_BASIC_GRILLED_CHEESE", 3]["semantic_compatibility"]
        == "ACCEPTED_SUBSTITUTION"
    )
    assert (
        rows["SNAP2_SIMPLE_GREEN_SMOOTHIE", 6]["semantic_compatibility"]
        == "FORM_MISMATCH"
    )


def test_piece_sizes_are_never_silently_chosen(evidence):
    rows = evidence[0]["rows"]
    unspecified = {
        "APPLE",
        "BANANA",
        "PEACH",
        "TOMATO",
        "CUCUMBER",
        "BELL_PEPPER_GREEN",
        "EGG",
        "GINGER",
        "SPINACH",
    }
    for row in rows:
        if row["recipe_unit"] != "pcs":
            continue
        review = row["piece_review"]
        assert review["global_piece_mass_safe"] is False
        if (
            row["food_ingredient_code"] in unspecified
            and review["size_specified"] is None
        ):
            assert row["candidate_g_per_piece"] is None
            assert not row["implementation_ready"]


def test_protected_snapshot_is_exact_accepted_main_and_pr_scope(evidence):
    audit, _ = evidence
    # No network or current database required. The accepted commit is retained
    # in the normal repository checkout; hashes also run without Git in validate.
    protected = audit["protected_file_sha256"]
    for path in [
        "data/seed/recipes/recipes.json",
        "data/seed/recipes/source-manifest.json",
        "data/seed/food_ingredients/ingredients.csv",
        "data/seed/food_ingredients/nutrition.csv",
        "backend/app/tests/test_nutrition_catalogue.py",
    ]:
        blob = subprocess.check_output(
            ["git", "show", f"{validator.BASE}:{path}"], cwd=ROOT
        )
        assert hashlib.sha256(blob).hexdigest() == protected[path]
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", validator.BASE, DATA_A_MAIN], cwd=ROOT, text=True
    ).splitlines()
    allowed = {
        ".DS_Store",
        "backend/app/tests/test_pr6_data_a_research.py",
        "scripts/validate_pr6_data_a.py",
        "docs/family-food/nutrition-data-readiness.md",
        "docs/family-food/nutrition-core.md",
        "docs/family-food/master-roadmap.md",
        "docs/family-food/pantry-core.md",
        "docs/family-food/recipe-localization-and-substitution.md",
        "state/current-focus.md",
        "state/progress.md",
        "state/handoff.md",
    }
    assert all(
        p in allowed or p.startswith("data/curation/pr6-data-a/") for p in changed
    )
    historical_migrations = subprocess.check_output(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            DATA_A_MAIN,
            "backend/app/migrations/versions",
        ],
        cwd=ROOT,
        text=True,
    )
    assert "/0026" not in historical_migrations
