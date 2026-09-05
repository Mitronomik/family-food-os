"""Research integrity is not authorization or acceptance of a final corpus."""

from collections import Counter
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/validate_pr4_data2.py"
SPEC = importlib.util.spec_from_file_location("validate_pr4_data2", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
DIRECTORY = validator.DIRECTORY


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture
def research_copy(tmp_path):
    target = tmp_path / "research"
    shutil.copytree(DIRECTORY, target)
    return target


@pytest.fixture
def synthetic_final(research_copy):
    """Schema exercise only: never written to the repository or called curated."""
    recipes = [
        {
            "recipe_source_id": f"TEST-ONLY-{i:02}",
            "recipe_name": f"Synthetic test recipe {i}",
            "source_url": f"https://example.invalid/source/{i}",
            "source_collection": "Synthetic test collection, not research evidence",
            "source_sha256": "a" * 64,
            "source_servings": 6,
            "source_ingredient_rows": 1,
            "selected_ingredient_rows": 1,
            "distinct_food_ingredient_codes": ["SALT"],
            "equipment": [],
            "source_attribution": "Synthetic fixture",
            "meal_type": "TEST_ONLY",
            "diversity_contribution": "Synthetic fixture",
            "source_times": {"test_only": True},
            "selection": {"decision": "REPLACE", "reason": "Schema test fixture only"},
            "market_summary": {
                "required_concepts": 1,
                "RU_MASS_MARKET": 0,
                "RU_AVAILABLE": 1,
                "SPECIALTY_OR_UNCLEAR": 0,
                "household_water": 0,
            },
            "rights_review": {
                "status": "REVIEWED",
                "basis": "Synthetic fixture; not a real rights assertion",
                "evidence_url": "https://example.invalid/fixture-only",
            },
        }
        for i in range(30)
    ]
    write_json(
        research_copy / "recipe-corpus.json",
        {
            "schema_version": 1,
            "status": "READY_FOR_REVIEW",
            "recipes": recipes,
        },
    )
    write_json(
        research_copy / "draft-ingredient-coverage.json",
        {
            "recipes": [
                {
                    "source_recipe_id": recipe["recipe_source_id"],
                    "source_url": recipe["source_url"],
                    "rows": [
                        {
                            "position": 1,
                            "source_text": "Salt",
                            "selected_codes": ["SALT"],
                            "selection": "SELECTED_REQUIRED",
                            "quantity_text": "1 teaspoon",
                            "normalization_reason": "Synthetic fixture quantity",
                        }
                    ],
                }
                for recipe in recipes
            ]
        },
    )
    with (research_copy / "ingredient-coverage.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "source_recipe_id",
                "source_ingredient_text",
                "normalized_concept",
                "existing_food_ingredient_code",
                "resolution_status",
                "missing_reason",
            ]
        )
        for recipe in recipes:
            writer.writerow(
                [
                    recipe["recipe_source_id"],
                    "Salt",
                    "salt",
                    "SALT",
                    "RESOLVED_EXISTING",
                    "",
                ]
            )
    (research_copy / "mvp0-food-ingredient-codes.txt").write_text("SALT\n")
    rows = []
    for line, recipe in enumerate(recipes, 2):
        rows.append(
            {
                "coverage_line": line,
                "source_recipe_id": recipe["recipe_source_id"],
                "food_ingredient_code": "SALT",
                "purchase_concept": "food salt",
                "review_status": "REVIEWED",
                "source_position": 1,
                "source_quantity_text": "1 teaspoon",
                "ingredient_selection": "SELECTED_REQUIRED",
                "normalization_reason": "Synthetic fixture quantity",
                "evidence_matches": [
                    {
                        "observation_id": "research-x5-v3.json:2",
                        "purchase_concept": "food salt",
                        "form_match_reviewed": True,
                        "rationale": "Test record explicitly matches food salt, not dishwasher salt",
                    }
                ],
                "ordinary_retail_plausibility": True,
                "market_classification": "RU_AVAILABLE",
                "retention_reason": "Test-only ordinary food-salt concept",
                "chain_review": {
                    chain: {
                        "status": "AVAILABLE" if chain == "LENTA" else "UNCERTAIN",
                        "basis": "Synthetic panel fixture",
                    }
                    for chain in validator.CHAINS
                },
            }
        )
    write_json(
        research_copy / "purchase-form-review.json",
        {
            "schema_version": 1,
            "status": "REVIEWED",
            "rows": rows,
        },
    )
    write_json(
        research_copy / "draft-purchase-form-review.json",
        {
            "rows": [
                {
                    "review_id": "TEST-ONLY-SALT",
                    "food_ingredient_code": "SALT",
                    "purchase_form": "food salt",
                    "recipe_ids": [r["recipe_source_id"] for r in recipes],
                    "qualifying_refs": ["research-x5-v3.json:2"],
                    "ordinary_retail_plausibility": "Test-only ordinary food salt",
                    "classification": "RU_AVAILABLE",
                    "retention_reason": "Test-only ordinary food-salt concept",
                    "review_notes": "Test fixture explicitly reviews food salt",
                    "five_chain_review": {
                        chain: {
                            "status": "AVAILABLE" if chain == "LENTA" else "UNCERTAIN",
                            "note": "Synthetic panel fixture",
                        }
                        for chain in validator.CHAINS
                    },
                }
            ]
        },
    )
    for filename, content in validator.build_final_evidence(research_copy).items():
        (research_copy / filename).write_text(content, encoding="utf-8")
    write_json(
        research_copy / "source-downloads.json",
        {
            "documents": [
                {"source_url": r["source_url"], "sha256": r["source_sha256"]}
                for r in recipes
            ]
        },
    )
    write_json(
        research_copy / "source-equipment-audit.json",
        {
            "recipes": [
                {
                    "recipe_source_id": r["recipe_source_id"],
                    "source_url": r["source_url"],
                    "source_sha256": r["source_sha256"],
                    "equipment": [],
                }
                for r in recipes
            ]
        },
    )
    corpus = validator.read_json(research_copy / "recipe-corpus.json")
    corpus["counts"] = validator.corpus_counts(
        recipes, validator.selected_source_rows(research_copy), research_copy
    )
    write_json(research_copy / "recipe-corpus.json", corpus)
    return research_copy


def test_current_research_integrity_and_final_gate_are_separate():
    assert validator.research_errors() == []
    if (DIRECTORY / "recipe-corpus.json").exists():
        assert validator.final_errors() == []
    else:
        assert validator.final_errors()


def test_final_evidence_is_exact_and_reproducible_without_runtime():
    generated = validator.build_final_evidence()
    assert generated == validator.build_final_evidence()
    for filename, content in generated.items():
        assert (DIRECTORY / filename).read_text(encoding="utf-8") == content
    rows = validator.selected_source_rows()
    assert len(rows) == 193
    assert len({r["source_recipe_id"] for r in rows}) == 30
    assert len({r["existing_food_ingredient_code"] for r in rows}) == 79
    assert Counter(r["ingredient_selection"] for r in rows) == {
        "SELECTED_REQUIRED": 191,
        "SELECTED_OPTIONAL": 1,
        "SELECTED_CONDITIONAL": 1,
    }
    matrix = json.loads(generated["retailer-evidence-matrix.json"])
    assert len(matrix["final_source_forms"]) == 82
    assert matrix["final_source_form_classification_counts"] == {
        "RU_MASS_MARKET": 3,
        "RU_AVAILABLE": 79,
    }


def test_final_corpus_exact_96_equipment_33_codes_and_preserved_catalogue():
    import hashlib

    corpus = validator.read_json(DIRECTORY / "recipe-corpus.json")
    assert corpus["counts"] == validator.corpus_counts(
        corpus["recipes"], validator.selected_source_rows(), DIRECTORY
    )
    assert corpus["counts"]["equipment_rows"] == 96
    assert corpus["counts"]["distinct_equipment_codes"] == 33
    corn = next(
        r
        for r in corpus["recipes"]
        if r["recipe_source_id"] == "CACFP6-CORN-EDAMAME-BLEND"
    )
    assert [e["equipment_code"] for e in corn["equipment"]] == [
        "NONSTICK_SAUCEPAN",
        "STOCK_POT",
    ]
    assert corn["equipment"][1]["selection_reason"]
    assert (
        hashlib.sha256(
            (ROOT / "data/seed/food_ingredients/ingredients.csv").read_bytes()
        ).hexdigest()
        == "55058e511e3db14c97382e295e2a617a5a156041e49d2a7ab9772811bd06aaf3"
    )


def test_final_form_join_cannot_fall_back_to_code_only(research_copy):
    path = research_copy / "draft-purchase-form-review.json"
    document = validator.read_json(path)
    document["rows"][0]["recipe_ids"] = []
    write_json(path, document)
    with pytest.raises(ValueError, match="Missing/ambiguous source-form"):
        validator.build_final_evidence(research_copy)


def test_final_source_metadata_exact_equipment_and_hash_registry():
    draft = validator.read_json(DIRECTORY / "draft-ingredient-coverage.json")
    ids = {r["source_recipe_id"] for r in draft["recipes"]}
    historical = validator.read_json(DIRECTORY / "source-equipment-audit.json")
    old = [r for r in historical["recipes"] if r["recipe_source_id"] in ids]
    new = validator.read_json(DIRECTORY / "recipe-review-metadata.json")["recipes"]
    assert len(old) == 5
    assert len(new) == 25
    assert {r["recipe_source_id"] for r in old + new} == ids
    assert sum(len(r["equipment"]) for r in old) == 11
    assert sum(len(r["equipment"]) for r in new) == 84
    documents = validator.read_json(DIRECTORY / "source-downloads.json")["documents"]
    urls = {r["source_url"] for r in documents}
    for recipe in old + new:
        equipment = recipe["equipment"]
        assert [e["position"] for e in equipment] == list(range(1, len(equipment) + 1))
        assert len({e["equipment_code"] for e in equipment}) == len(equipment)
        assert json.loads(json.dumps(equipment)) == equipment
        assert all(e.get("evidence_snippet", e.get("source_words")) for e in equipment)
    for recipe in new:
        assert recipe["source_url"] in urls
        assert recipe["source_attribution"]
        assert recipe["rights_basis"]
        assert recipe["source_time_facts"]


def test_final_form_join_rejects_two_competing_form_assignments(research_copy):
    path = research_copy / "draft-purchase-form-review.json"
    document = validator.read_json(path)
    document["rows"].append(document["rows"][0])
    write_json(path, document)
    with pytest.raises(ValueError, match="Missing/ambiguous source-form"):
        validator.build_final_evidence(research_copy)


def test_explicit_candidate_revision_is_required(research_copy):
    path = research_copy / "candidate-review-v5.json"
    document = validator.read_json(path)
    document.pop("supersedes")
    write_json(path, document)
    assert "Duplicate candidate without explicit reviewed revision" in (
        validator.research_errors(research_copy)
    )


@pytest.mark.parametrize("quantity", ["", "to taste", "as needed"])
def test_selected_food_quantity_cannot_become_qualitative(research_copy, quantity):
    path = research_copy / "draft-ingredient-coverage.json"
    document = validator.read_json(path)
    document["recipes"][0]["rows"][0]["quantity_text"] = quantity
    write_json(path, document)
    with pytest.raises(ValueError, match="explicit source quantity"):
        validator.selected_source_rows(research_copy)


def test_absent_final_successor_always_fails_closed(research_copy):
    (research_copy / "recipe-corpus.json").unlink(missing_ok=True)
    assert validator.final_errors(research_copy) == [
        "No accepted DATA2 successor: exact final 30 and union not established"
    ]


def test_matrix_is_exact_deterministic_and_round_trips():
    matrix = validator.build_matrix()
    assert matrix == validator.build_matrix()
    assert json.loads(json.dumps(matrix)) == matrix
    assert matrix["status"] == "RESEARCH_EVIDENCE_NOT_ACCEPTED_CORPUS"
    assert matrix["counts"] == {
        "raw_observations": 172,
        "observations": 166,
        "duplicate_observations": 6,
        "available": 129,
        "uncertain": 37,
        "available_by_chain": {
            "PYATEROCHKA": 3,
            "PEREKRESTOK": 0,
            "LENTA": 113,
            "OKEY": 0,
            "MAGNIT": 13,
        },
    }
    for observation in matrix["observations"]:
        filename, index = observation["observation_id"].rsplit(":", 1)
        raw = validator.read_json(DIRECTORY / filename)["observations"][int(index) - 1]
        assert observation["food_ingredient_code"] == raw.get(
            "code", raw.get("food_ingredient_code")
        )
        assert observation["stock_claim"] is False
        assert observation["source_observation_ids"] == [
            source["observation_id"] for source in observation["source_observations"]
        ]
        assert observation["aliases"] == observation["source_observation_ids"][1:]


def test_deduplication_preserves_every_raw_id_and_evidence_note():
    raw = validator.normalized_observations()
    matrix = validator.build_matrix()
    preserved = [
        source
        for observation in matrix["observations"]
        for source in observation["source_observations"]
    ]

    def by_id(records):
        return {r["observation_id"]: r for r in records}

    assert by_id(preserved) == by_id(raw)
    assert len(preserved) == len(raw)
    keys = [
        (o["food_ingredient_code"], o["retailer_chain"], o["evidence_url"])
        for o in matrix["observations"]
    ]
    assert len(keys) == len(set(keys))


def test_duplicate_alias_remains_usable_for_explicit_form_review():
    raw = {o["observation_id"]: o for o in validator.normalized_observations()}
    matches = [
        {
            "observation_id": ref,
            "purchase_concept": "fresh green onion",
            "form_match_reviewed": True,
            "rationale": "Both exact original records retain the same product form",
        }
        for ref in ("research-x5-v3.json:5", "research-lenta-okey-v4.json:11")
    ]
    assert validator.form_qualified_chains(
        "GREEN_ONION", "fresh green onion", matches, raw
    ) == {"LENTA"}


def test_mixed_generic_and_critical_form_claims_are_not_promoted_by_deduplication():
    curry = next(
        o
        for o in validator.build_matrix()["observations"]
        if o["observation_id"] == "research-lenta-okey-v3.json:19"
    )
    assert curry["source_statuses"] == ["AVAILABLE", "UNCERTAIN"]
    assert curry["status"] == "UNCERTAIN"
    assert curry["source_observations"][0]["status"] == "AVAILABLE"
    assert curry["source_observations"][1]["status"] == "UNCERTAIN"
    assert "mild" in curry["source_observations"][1]["notes"]


def test_v7_exact_frozen_form_is_present_without_invented_global_code():
    raw = {o["observation_id"]: o for o in validator.normalized_observations()}
    cauliflower = raw["research-lenta-okey-v7.json:1"]
    spinach = raw["research-lenta-okey-v7.json:7"]
    assert cauliflower["food_ingredient_code"] == "CAULIFLOWER"
    assert spinach["food_ingredient_code"] == "SPINACH"
    assert cauliflower["status"] == spinach["status"] == "AVAILABLE"
    assert "frozen" in cauliflower["notes"]
    assert "frozen" in spinach["notes"]


@pytest.mark.parametrize(
    "chains,ordinary,expected",
    [
        (set(), True, "SPECIALTY_OR_UNCLEAR"),
        ({"LENTA"}, True, "RU_AVAILABLE"),
        ({"LENTA"}, False, "SPECIALTY_OR_UNCLEAR"),
        ({"LENTA", "MAGNIT"}, True, "RU_AVAILABLE"),
        ({"LENTA", "MAGNIT", "PYATEROCHKA"}, False, "RU_MASS_MARKET"),
    ],
)
def test_market_thresholds_count_distinct_panel_chains(chains, ordinary, expected):
    assert validator.classify_market(chains, ordinary) == expected


def test_non_panel_chain_cannot_qualify():
    with pytest.raises(ValueError, match="Non-panel"):
        validator.classify_market({"SPECIALTY_SHOP"}, True)


def test_same_chain_multiple_products_do_not_become_mass_market():
    observations = {o["observation_id"]: o for o in validator.normalized_observations()}
    refs = [
        o["observation_id"]
        for o in observations.values()
        if o["food_ingredient_code"] == "SALT" and o["status"] == "AVAILABLE"
    ]
    assert len(refs) >= 2
    matches = [
        {
            "observation_id": ref,
            "purchase_concept": "food salt",
            "form_match_reviewed": True,
            "rationale": "Food salt form reviewed",
        }
        for ref in refs
    ]
    chains = validator.form_qualified_chains("SALT", "food salt", matches, observations)
    assert chains == {"LENTA"}
    assert validator.classify_market(chains, True) == "RU_AVAILABLE"


def test_shell_egg_code_cannot_automatically_clear_frozen_liquid_egg():
    observations = {o["observation_id"]: o for o in validator.normalized_observations()}
    ref = "research-magnit-v2.json:4"
    assert observations[ref]["food_ingredient_code"] == "EGG"
    assert observations[ref]["purchase_concept"] == "shell chicken egg"
    with pytest.raises(ValueError, match="same-form"):
        validator.form_qualified_chains(
            "EGG", "frozen whole liquid egg", [{"observation_id": ref}], observations
        )
    reviewed_shell = [
        {
            "observation_id": ref,
            "purchase_concept": "shell chicken egg",
            "form_match_reviewed": True,
            "rationale": "Source explicitly allows shell eggs",
        }
    ]
    assert validator.form_qualified_chains(
        "EGG", "shell chicken egg", reviewed_shell, observations
    ) == {"MAGNIT"}
    with pytest.raises(ValueError, match="same-form"):
        validator.form_qualified_chains(
            "EGG", "frozen whole liquid egg", reviewed_shell, observations
        )


def test_historical_form_audit_preserves_exact_96_and_classes():
    audit = validator.read_json(DIRECTORY / "research-candidates.json")
    checks = [c for r in audit["all_recipe_form_audit"] for c in r["form_checks"]]
    assert len(checks) == 96
    assert Counter(c["form_class"] for c in checks) == {
        "PURCHASE_FORM_CRITICAL": 77,
        "PREPARATION_ONLY_OR_NOT_RETAIL_FORM": 19,
    }
    assert len(audit["all_recipe_form_audit"]) == 30


def test_historical_equipment_exact_count_order_and_quiche_attachment():
    audit = validator.read_json(DIRECTORY / "source-equipment-audit.json")
    assert json.loads(json.dumps(audit)) == audit
    recipes = audit["recipes"]
    assert len(recipes) == 30
    assert sum(len(r["equipment"]) for r in recipes) == 80
    assert sum(len(r["conditional_equipment"]) for r in recipes) == 4
    for recipe in recipes:
        assert [e["position"] for e in recipe["equipment"]] == list(
            range(1, len(recipe["equipment"]) + 1)
        )
        assert all(
            e["evidence_snippet"]
            and 1 <= e["source_page"] <= recipe["source_page_count"]
            for e in recipe["equipment"]
        )
    quiche = next(
        r
        for r in recipes
        if r["recipe_source_id"] == "CACFP6-QUICHE-SELF-FORMING-CRUST"
    )
    assert [e["equipment_code"] for e in quiche["equipment"]] == [
        "OVEN",
        "MIXER",
        "WIRE_WHIP_ATTACHMENT",
        "BOWL",
        "BAKING_PAN",
    ]
    assert (quiche["source_preparation_time"], quiche["source_cooking_time"]) == (
        "20 minutes",
        "45 minutes",
    )


def test_known_code_only_form_exclusions_cannot_be_promoted(research_copy):
    path = research_copy / "original-corpus-market-review.json"
    data = validator.read_json(path)
    quiche = next(
        r
        for r in data["recipes"]
        if r["recipe_source_id"] == "CACFP6-QUICHE-SELF-FORMING-CRUST"
    )
    quiche["matching_evidence_by_code"]["EGG"] = ["research-magnit-v2.json:4"]
    write_json(path, data)
    assert (
        "Unresolved critical form cannot be cleared by code-only evidence"
        in validator.research_errors(research_copy)
    )


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("stock_claim", True, "Curation must not imply momentary stock"),
        ("checked_at", "2026-99-99", "Invalid check date"),
        ("region_evidence_url", "https://", "Missing reviewable region_evidence_url"),
    ],
)
def test_raw_evidence_defects_are_not_normalized_away(
    research_copy, field, value, error
):
    path = research_copy / "research-x5-v3.json"
    data = validator.read_json(path)
    data["observations"][0][field] = value
    write_json(path, data)
    assert error in validator.research_errors(research_copy)


def test_missing_observation_input_fails_research(research_copy):
    (research_copy / "research-x5-v3.json").unlink()
    assert "Missing research input: research-x5-v3.json" in validator.research_errors(
        research_copy
    )


def test_missing_v7_input_fails_research(research_copy):
    (research_copy / "research-lenta-okey-v7.json").unlink()
    assert "Missing research input: research-lenta-okey-v7.json" in (
        validator.research_errors(research_copy)
    )


@pytest.mark.parametrize("observations", [[], None, ["not an object"], [{}]])
def test_malformed_v7_observations_return_explicit_research_error(
    research_copy, observations
):
    path = research_copy / "research-lenta-okey-v7.json"
    data = validator.read_json(path)
    data["observations"] = observations
    write_json(path, data)
    assert any(
        "Invalid research input research-lenta-okey-v7.json" in error
        for error in validator.research_errors(research_copy)
    )


def test_new_v4_candidate_must_use_actual_global_catalogue(research_copy):
    path = research_copy / "candidate-review-v4.json"
    data = validator.read_json(path)
    data["candidates"][0]["selected_required_codes"].append("SPINACH_FROZEN")
    write_json(path, data)
    assert "Candidate adds global ingredient" in validator.research_errors(
        research_copy
    )


def test_duplicate_source_form_record_is_rejected(research_copy):
    path = research_copy / "research-candidates.json"
    data = validator.read_json(path)
    data["all_recipe_form_audit"][0]["form_checks"][1] = data["all_recipe_form_audit"][
        0
    ]["form_checks"][0]
    write_json(path, data)
    assert "Duplicate historical form check" in validator.research_errors(research_copy)


def test_equipment_position_mutation_is_rejected(research_copy):
    path = research_copy / "source-equipment-audit.json"
    data = validator.read_json(path)
    data["recipes"][0]["equipment"][0]["position"] = 2
    write_json(path, data)
    assert "Equipment order" in validator.research_errors(research_copy)


@pytest.mark.parametrize(
    "value", [None, [], {"recipes": []}, {"recipes": [{"recipe_source_id": []}]}]
)
def test_malformed_final_json_fails_closed(research_copy, value):
    write_json(research_copy / "recipe-corpus.json", value)
    assert validator.final_errors(research_copy)


def test_more_than_120_actual_union_codes_fail_final_gate(synthetic_final):
    with (ROOT / "data/seed/food_ingredients/ingredients.csv").open() as handle:
        codes = sorted(row["canonical_code"] for row in csv.DictReader(handle))[:121]
    # Retain all30 source IDs, but put a genuinely oversized union in coverage.
    with (synthetic_final / "ingredient-coverage.csv").open("a", newline="") as handle:
        writer = csv.writer(handle)
        for code in codes:
            writer.writerow(
                ["TEST-ONLY-00", code, code.lower(), code, "RESOLVED_EXISTING", ""]
            )
    union = sorted(set(codes) | {"SALT"})
    (synthetic_final / "mvp0-food-ingredient-codes.txt").write_text(
        "\n".join(union) + "\n"
    )
    assert any(
        "union <=120" in error for error in validator.final_errors(synthetic_final)
    )


def test_final_gate_rejects_empty_placeholder_files(research_copy):
    write_json(
        research_copy / "recipe-corpus.json",
        {
            "schema_version": 1,
            "status": "READY_FOR_REVIEW",
            "recipes": [{"recipe_source_id": f"FAKE-{i}"} for i in range(30)],
        },
    )
    for filename in [
        "ingredient-coverage.csv",
        "mvp0-food-ingredient-codes.txt",
        "purchase-form-review.json",
    ]:
        (research_copy / filename).write_text("")
    assert validator.final_errors(research_copy)


def test_complete_synthetic_schema_is_not_research_acceptance(synthetic_final):
    assert validator.final_errors(synthetic_final) == []
    assert all(
        r["recipe_source_id"].startswith("TEST-ONLY-")
        for r in validator.read_json(synthetic_final / "recipe-corpus.json")["recipes"]
    )
    assert not any(
        r["source_recipe_id"].startswith("TEST-ONLY-")
        for r in validator.selected_source_rows(DIRECTORY)
    )


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("rights", "Missing source-specific reviewed rights"),
        ("forbidden", "Forbidden ICN recipe"),
        ("duplicate", "Exactly 30 unique"),
        ("unresolved", "Unresolved or empty"),
        ("manifest", "exact sorted nonempty union"),
        ("form", "same-form"),
        ("panel", "full five-chain"),
        ("specialty", "fails market classification"),
        ("quantity", "quantity/optionality crosswalk"),
        ("optionality", "quantity/optionality crosswalk"),
        ("source_order", "exact selected source audit rows/order"),
        ("equipment", "Equipment order/code/source evidence invalid"),
        ("hash", "Source hash/URL is not the reviewed artifact"),
        ("summary", "Recipe market summary disagrees with forms"),
        ("ingredient_summary", "Recipe ingredient summary disagrees with audit"),
    ],
)
def test_final_gate_rejects_acceptance_shortcuts(synthetic_final, mutation, expected):
    corpus_path = synthetic_final / "recipe-corpus.json"
    corpus = validator.read_json(corpus_path)
    form_path = synthetic_final / "purchase-form-review.json"
    form = validator.read_json(form_path)
    if mutation == "rights":
        corpus["recipes"][0].pop("rights_review")
    elif mutation == "forbidden":
        corpus["recipes"][0]["recipe_source_id"] = "CACFP6-CAULIFLOWER-RICE"
    elif mutation == "duplicate":
        corpus["recipes"][0] = corpus["recipes"][1]
    elif mutation == "unresolved":
        path = synthetic_final / "ingredient-coverage.csv"
        path.write_text(path.read_text().replace("RESOLVED_EXISTING", "UNRESOLVED", 1))
    elif mutation == "manifest":
        (synthetic_final / "mvp0-food-ingredient-codes.txt").write_text("SALT\nSALT\n")
    elif mutation == "form":
        form["rows"][0]["evidence_matches"][0].pop("form_match_reviewed")
    elif mutation == "panel":
        form["rows"][0]["chain_review"].pop("MAGNIT")
    elif mutation == "specialty":
        form["rows"][0]["ordinary_retail_plausibility"] = False
    elif mutation == "quantity":
        form["rows"][0]["source_quantity_text"] = "100 g invented"
    elif mutation == "optionality":
        form["rows"][0]["ingredient_selection"] = "SELECTED_OPTIONAL"
    elif mutation == "source_order":
        path = synthetic_final / "ingredient-coverage.csv"
        lines = path.read_text().splitlines()
        lines[1], lines[2] = lines[2], lines[1]
        path.write_text("\n".join(lines) + "\n")
    elif mutation == "equipment":
        corpus["recipes"][0]["equipment"] = [
            {
                "position": 2,
                "equipment_code": "BOWL",
                "evidence_snippet": "test bowl",
                "source_section": "test section",
            }
        ]
    elif mutation == "hash":
        corpus["recipes"][0]["source_sha256"] = "b" * 64
    elif mutation == "summary":
        corpus["recipes"][0]["market_summary"]["RU_MASS_MARKET"] = 1
    elif mutation == "ingredient_summary":
        corpus["recipes"][0]["selected_ingredient_rows"] = 999
    write_json(corpus_path, corpus)
    write_json(form_path, form)
    assert any(expected in error for error in validator.final_errors(synthetic_final))


def test_command_default_checks_final_gate_not_only_research():
    research = subprocess.run(
        [sys.executable, str(SCRIPT), "--research"],
        capture_output=True,
        text=True,
        check=False,
    )
    final = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False
    )
    assert research.returncode == 0
    assert research.stdout.strip() == "PASS: research integrity only"
    if validator.final_errors():
        assert final.returncode == 1
        assert "PASS: final" not in final.stdout
    else:
        assert final.returncode == 0
        assert final.stdout.strip() == "PASS: final DATA2 gates"
