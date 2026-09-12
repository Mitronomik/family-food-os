"""Read-only PR6 closure measurements; accepted loaders run only in a temporary DB.

No network, production DB argument or data repair. --write publishes only this
operation's measured JSON. The reviewed decision is a separate, human-owned file.
"""

import argparse
from collections import Counter
from dataclasses import asdict, replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
from app.db.config import DatabaseConfig  # noqa: E402
from app.db.migrations import expected_migration_ids  # noqa: E402
from app.domain.nutrition import calculate_recipe_nutrition  # noqa: E402
from app.domain.nutrition_config import CONFIG, NUTRIENTS  # noqa: E402
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine  # noqa: E402
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork  # noqa: E402
from app.persistence.sqlalchemy_core.food_recipe_composition import (  # noqa: E402
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (  # noqa: E402
    create_nutrition_service,
)
from app.services.food_composition import CompositionCalculator  # noqa: E402
from app.seed.b2b2 import upgrade_b2b2  # noqa: E402
from app.tests.test_nutrition_targets import person, calculate  # noqa: E402
from audit_pr6_data_b2b2 import baseline, preserved  # noqa: E402
from audit_pr6_nutrient_vector_b import snapshot, readiness  # noqa: E402
from audit_pr6_ru_food_data import head  # noqa: E402

PACKAGE = ROOT / "data/curation/pr6-close"
BASE = "3caa95e636c02e8f34657b1b6c885f646451114c"
ACCEPTED_HEAD = "8a80ce26e7155ab17a5623d07294fbfd1124d9bf"
TESTED = "d0a238ce32193d5884d61ee384d5eb7f242bcaed"
VECTOR_CODES = dict(
    zip(
        NUTRIENTS,
        (
            "ENERGY_KCAL",
            "PROTEIN",
            "FAT_TOTAL",
            "CARBOHYDRATE_BY_DIFFERENCE",
            "FIBER_TOTAL_DIETARY",
        ),
        strict=True,
    )
)
DEFERRED = (
    "APPLE_PEELED",
    "LEMON_JUICE",
    "ORANGE_JUICE",
    "PASTA_COOKED",
    "SPINACH_BABY",
)
DEFERRED_ROWS = {
    "HARV6_FRESH_TOMATO_SALSA:v2:2": "APPLE_PEELED",
    "CACFP6_TABBOULEH:v1:12": "LEMON_JUICE",
    "SNAP4_DILLED_FISH_FILLETS:v1:2": "LEMON_JUICE",
    "SNAP6_PEACH_CRISP:v1:7": "LEMON_JUICE",
    "SNAP6_WALDORF_SALAD:v1:7": "LEMON_JUICE",
    "SNAP8_SOMALI_SUMMER_SALAD:v1:2": "LEMON_JUICE",
    "SNAP4_PEAR_ORANGE_SAUCE:v1:2": "ORANGE_JUICE",
    "HARV6_GARDEN_PASTA_SALAD:v1:1": "PASTA_COOKED",
    "SNAP6_SPINACH_APPLE_SALAD:v2:1": "SPINACH_BABY",
}
YIELD_CASES = {
    ("SNAP4_BRAISED_CHICKEN_SPINACH", "CHICKEN_THIGH"),
    ("SNAP4_SPANISH_FRITTATA", "POTATO"),
    ("WIC4_BUTTERNUT_SOUP", "BUTTERNUT_SQUASH"),
}
FORM_ISSUES = {
    "FOOD_FORM_MISMATCH",
    "IDENTITY_MISMATCH",
    "PROFILE_REPRESENTATIVENESS_REVIEW",
}


def encode(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        + "\n"
    )


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def provenance(profile):
    return {
        k: str(getattr(profile, k)) if getattr(profile, k) is not None else None
        for k in (
            "source_name",
            "source_id",
            "source_version",
            "source_data_type",
            "verified_at",
            "basis_grams",
            "estimated",
        )
    }


def all_results(engine):
    recipes = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    return {
        (recipe.canonical_code, version.version_number): (
            recipes.get_version_detail(version.id),
            nutrition.recipe_version(version.id),
        )
        for recipe in recipes.list_active()
        for version in recipes.list_versions(recipe.id)
    }


def replay_captured(detail, result):
    """Replay a retained coherent v1 input snapshot, not a mutable current lookup."""
    rows = result.required_contributions + result.optional_contributions
    return calculate_recipe_nutrition(
        detail,
        {r.row.food_ingredient_id: r.nutrition.ingredient for r in rows},
        {r.row.food_ingredient_id: r.nutrition.profile for r in rows},
        {r.row.id: r.assessment for r in rows if r.assessment},
        {r.measure_evidence.id: r.measure_evidence for r in rows if r.measure_evidence},
        {
            r.assessment_profile.id: r.assessment_profile
            for r in rows
            if r.assessment_profile
        },
    )


def sealed_replay(config):
    engine = create_sqlite_engine(config)
    try:
        with sqlite3.connect(config.path) as db:
            profiles = [
                UUID(r[0])
                for r in db.execute("SELECT profile_id FROM nutrition_vector_seals")
            ]
            compositions = [
                UUID(r[0])
                for r in db.execute("SELECT id FROM food_composition_versions")
            ]
            codes = tuple(
                r[0]
                for r in db.execute(
                    "SELECT code FROM nutrient_definitions ORDER BY code"
                )
            )
        with B2B2UnitOfWork(engine) as uow:
            vectors = {key: uow.nutrient_vectors.get(key) for key in profiles}
            calc = CompositionCalculator(uow.compositions, uow.nutrient_vectors)
            results = {
                key: calc.calculate(key, nutrient_codes=codes) for key in compositions
            }
            assert results == {
                key: calc.calculate(key, nutrient_codes=codes) for key in compositions
            }
        return vectors, results, codes
    finally:
        engine.dispose()


def measure(config):
    baseline(config)
    before = snapshot(config)
    old_vectors, old_compositions, _ = sealed_replay(config)
    engine = create_sqlite_engine(config)
    try:
        historical = all_results(engine)
    finally:
        engine.dispose()
    upgrade_b2b2(config)
    after = snapshot(config)
    marker_retirements = preserved(config, before, after)
    vectors, compositions, registry = sealed_replay(config)
    for key, old in old_vectors.items():
        current = vectors[key]
        assert (
            replace(
                current,
                profile=replace(current.profile, is_current=old.profile.is_current),
            )
            == old
        )
    assert all(compositions[key] == old for key, old in old_compositions.items())
    ready = readiness(config)
    accepted = json.loads(
        (
            ROOT
            / "data/curation/pr6-data-b2-b2-redesigned/implementation-evidence.json"
        ).read_text()
    )
    assert ready == accepted["readiness_after"]
    ru = {
        r["food_code"]: r
        for r in json.loads(
            (ROOT / "data/curation/pr6-ru-food-data/food-readiness.json").read_text()
        )["rows"]
    }
    resolutions = json.loads(
        (
            ROOT / "data/curation/pr6-data-b2-b2-redesigned/row-resolution.json"
        ).read_text()
    )
    reviewed_rows = {r["current_after_identity"]: r for r in resolutions["rows"]}
    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        service = create_nutrition_service(engine)
        current_results = all_results(engine)
        # Full old row/profile/assessment facts were independently reloaded and
        # compared above. Exact captured configs/inputs, including historical
        # selectors, remain replayable after the current pointers advance.
        for key, (detail, result) in historical.items():
            assert current_results[key][0] == detail
            assert replay_captured(detail, result) == result
        for detail, result in current_results.values():
            assert replay_captured(detail, result) == result
        food_usages, recipe_records, estimates, deferred_rows, yield_rows = (
            {},
            [],
            [],
            [],
            [],
        )
        zero_disagreements = []
        with B2B2UnitOfWork(engine) as uow:
            for code in DEFERRED:
                assert uow.ingredients.get_by_code(code) is None
            for recipe in sorted(recipes.list_active(), key=lambda r: r.canonical_code):
                detail = recipes.get_current_verified(recipe.id)
                result = service.recipe_version(detail.version.id)
                assert result == service.recipe_version(detail.version.id)
                contributions = sorted(
                    result.required_contributions + result.optional_contributions,
                    key=lambda r: r.row.position,
                )
                rows = []
                for contribution in contributions:
                    row, nutrition, assessment = (
                        contribution.row,
                        contribution.nutrition,
                        contribution.assessment,
                    )
                    food = nutrition.ingredient
                    key = f"{recipe.canonical_code}:v{detail.version.version_number}:{row.position}"
                    food_usages.setdefault(food.canonical_code, []).append(
                        {"identity": key, "required": not row.optional}
                    )
                    issues = [str(i) for i in assessment.issues]
                    warnings = [str(w.code) for w in nutrition.warnings]
                    assert "NUTRITION_ASSESSMENT_PROFILE_STALE" not in warnings
                    assert assessment.nutrition_profile_id == nutrition.profile.id
                    measure = contribution.measure_evidence
                    vector = vectors[nutrition.profile.id]
                    unknown = [c for c in registry if vector.amount(c) is None]
                    reviewed = reviewed_rows.get(key, {})
                    proposed = DEFERRED_ROWS.get(key)
                    is_yield = (
                        recipe.canonical_code,
                        food.canonical_code,
                    ) in YIELD_CASES
                    record = dict(
                        identity=key,
                        position=row.position,
                        food_code=food.canonical_code,
                        optional=row.optional,
                        assessment_status=assessment.status_code,
                        assessment_version=assessment.assessment_version,
                        issues=issues,
                        warnings=warnings,
                        mass_g=nutrition.mass_g,
                        values=asdict(nutrition.values),
                        profile_provenance=provenance(nutrition.profile),
                        evidence_key=None if measure is None else measure.evidence_key,
                        evidence_estimated=None
                        if measure is None
                        else measure.estimated,
                        normalized_unknown_nutrients=unknown,
                        review_reference=reviewed.get("review_reference"),
                        review_note=assessment.review_note,
                    )
                    rows.append(record)
                    if "CONVERSION_ESTIMATE_NOT_ACCEPTED" in warnings:
                        assert nutrition.mass_g is None and all(
                            v is None for v in asdict(nutrition.values).values()
                        )
                        estimates.append(record)
                    if proposed in DEFERRED:
                        assert (
                            assessment.status_code == "BLOCKED"
                            and nutrition.mass_g is None
                        )
                        assert all(v is None for v in asdict(nutrition.values).values())
                        deferred_rows.append(dict(deferred_form=proposed, **record))
                    if is_yield:
                        assert (
                            "YIELD_EVIDENCE_REQUIRED" in reviewed["remaining_blockers"]
                        )
                        assert (
                            assessment.status_code == "BLOCKED"
                            and nutrition.mass_g is None
                        )
                        assert all(v is None for v in asdict(nutrition.values).values())
                        yield_rows.append(record)
                    for field, nutrient in VECTOR_CODES.items():
                        value = getattr(nutrition.values, field)
                        if value is not None and vector.amount(nutrient) is None:
                            assert value == 0 and getattr(nutrition.profile, field) == 0
                            assert "ESTIMATION_STATUS_UNKNOWN" in warnings
                            zero_disagreements.append(
                                dict(
                                    identity=key,
                                    food_code=food.canonical_code,
                                    optional=row.optional,
                                    nutrient=nutrient,
                                    legacy_value=value,
                                    legacy_profile_value=getattr(
                                        nutrition.profile, field
                                    ),
                                    normalized_amount=None,
                                    warnings=warnings,
                                    recipe_status=result.status,
                                )
                            )
                counts = Counter(r["assessment_status"] for r in rows)
                required_rows = [r for r in rows if not r["optional"]]
                counts_required = Counter(r["assessment_status"] for r in required_rows)
                form = [r["identity"] for r in rows if set(r["issues"]) & FORM_ISSUES]
                mass = [r["identity"] for r in rows if r["mass_g"] is None]
                yields = [
                    r["identity"]
                    for r in rows
                    if (recipe.canonical_code, r["food_code"]) in YIELD_CASES
                ]
                missing_composition = sorted(
                    {
                        r["food_code"]
                        for r in required_rows
                        if uow.compositions.find_version(
                            uow.ingredients.get_by_code(r["food_code"]).id, 1
                        )
                        is None
                    }
                )
                interpretation = "Safe technical evidence; not a downstream nutrition origin: required totals unavailable."
                if result.status != "INCOMPLETE":
                    interpretation = "Usable conditional required-input subtotal under the existing v1 contract only; optional choices excluded. Not a complete selected dish, cooked output or normalized recipe-vector authority."
                recipe_records.append(
                    dict(
                        recipe_code=recipe.canonical_code,
                        current_version=detail.version.version_number,
                        nutrition_status=result.status,
                        required_row_count=len(required_rows),
                        optional_row_count=len(rows) - len(required_rows),
                        approved_exact_count=counts["APPROVED_EXACT"],
                        approved_no_conversion_count=counts["APPROVED_NO_CONVERSION"],
                        review_required_estimate_count=counts[
                            "REVIEW_REQUIRED_ESTIMATE"
                        ],
                        blocked_count=counts["BLOCKED"],
                        required_assessment_counts=dict(counts_required),
                        critical_form_blockers=form,
                        critical_mass_blockers=mass,
                        critical_yield_blockers=yields,
                        unknown_required_nutrients={
                            "legacy_v1_total": [
                                k
                                for k, v in asdict(result.required_total).items()
                                if v is None
                            ],
                            "normalized_required_input_union": sorted(
                                {
                                    c
                                    for r in required_rows
                                    for c in r["normalized_unknown_nutrients"]
                                }
                            ),
                        },
                        composition_authority_status={
                            "recipe_composition_binding": "Not implemented; v1 uses row/profile assessments",
                            "required_foods_without_composition": missing_composition,
                        },
                        ru_food_data_status={
                            r["food_code"]: {
                                "pr28_reviewed_readiness": ru[r["food_code"]][
                                    "final_readiness"
                                ],
                                "pr29_nutrition_update": r["food_code"]
                                in {"MAYONNAISE_LOW_FAT", "OATS_ROLLED", "TOMATO"},
                            }
                            for r in rows
                        },
                        source_provenance={
                            k: getattr(detail.version, k)
                            for k in (
                                "source_name",
                                "source_recipe_id",
                                "source_version",
                                "source_url",
                                "source_document_sha256",
                                "source_retrieved_at",
                            )
                        },
                        source_provenance_status="Retained accepted source/hash; no external re-fetch in closure",
                        required_total=asdict(result.required_total),
                        per_base_serving=asdict(result.per_base_serving),
                        closure_interpretation=interpretation,
                        rows=rows,
                    )
                )
            foods = []
            for code, usages in sorted(food_usages.items()):
                food = uow.ingredients.get_by_code(code)
                profile = uow.nutrition_profiles.get_current(food.id)
                vector = vectors[profile.id]
                direct = service.food_ingredient(food.id, Decimal(100))
                composition = uow.compositions.find_version(food.id, 1)
                prior = ru[code]
                held_codes = [
                    c
                    for f, c in VECTOR_CODES.items()
                    if getattr(direct.values, f) is not None
                    and vector.amount(c) is None
                ]
                if held_codes:
                    assert direct.status == "COMPLETE_WITH_WARNINGS"
                    assert "ESTIMATION_STATUS_UNKNOWN" in [
                        w.code for w in direct.warnings
                    ]
                if composition is not None:
                    by_code = {
                        n.definition.code: n
                        for n in compositions[composition.id].nutrients
                    }
                    assert all(
                        by_code[c].availability == "UNKNOWN"
                        and by_code[c].amount is None
                        for c in held_codes
                    )
                unknown = [c for c in registry if vector.amount(c) is None]
                foods.append(
                    dict(
                        food_code=code,
                        russian_display_present=bool(
                            re.search("[А-Яа-яЁё]", food.canonical_name)
                        ),
                        russian_display=food.canonical_name,
                        usages=usages,
                        required_usage_count=sum(u["required"] for u in usages),
                        current_profile_provenance=provenance(profile),
                        sealed_vector_present=True,
                        vector_value_count=len(vector.values),
                        unknown_nutrient_count=len(unknown),
                        unknown_nutrients=unknown,
                        composition_authority=None
                        if composition is None
                        else composition.kind,
                        composition_version=None
                        if composition is None
                        else composition.version,
                        composition_requested_all_registry_status=None
                        if composition is None
                        else compositions[composition.id].status,
                        composition_profile_matches_current=None
                        if composition is None
                        else composition.profile_id == profile.id,
                        ru_classification=prior["market_classification"],
                        ru_readiness_as_reviewed_pr28=prior["final_readiness"],
                        ru_review_blockers_as_reviewed_pr28=prior["blocking_reasons"],
                        later_nutrition_review="PR29 replacement profile and ATOMIC v1"
                        if code in {"MAYONNAISE_LOW_FAT", "OATS_ROLLED", "TOMATO"}
                        else None,
                        known_blockers=sorted(
                            {
                                i
                                for recipe in recipe_records
                                for r in recipe["rows"]
                                if r["food_code"] == code
                                for i in r["issues"]
                            }
                        ),
                        historical_replay_verified=True,
                        legacy_direct_100g_status=direct.status,
                        legacy_direct_100g_values=asdict(direct.values),
                        legacy_direct_warnings=[w.code for w in direct.warnings],
                        legacy_numeric_normalized_unknown=[
                            c
                            for f, c in VECTOR_CODES.items()
                            if getattr(direct.values, f) is not None
                            and vector.amount(c) is None
                        ],
                    )
                )
    finally:
        engine.dispose()
    assert (
        snapshot(config) == after
    ), "Closure inspection mutated the temporary production truth"
    assert {r["deferred_form"] for r in deferred_rows} == set(DEFERRED)
    assert {r["identity"] for r in deferred_rows} == set(DEFERRED_ROWS)
    assert len(yield_rows) == len(YIELD_CASES)
    assert len(recipe_records) == ready["recipes"]
    assert (
        len(estimates)
        == ready["warning_occurrences"]["CONVERSION_ESTIMATE_NOT_ACCEPTED"]
    )
    assert head(config) == expected_migration_ids()[-1] == "0029_food_composition_core"
    targets = []
    for age, sex, height, weight in (
        (40, "male", "180", "80"),
        (40, "female", "165", "60"),
        (10, "male", "140", "35"),
        (10, "female", "140", "35"),
    ):
        for pal in ("inactive", "low_active", "active", "very_active"):
            member = person(age, sex, pal, height, weight)
            result = calculate(member)
            assert result == calculate(member)
            targets.append(
                dict(
                    age=age,
                    sex=sex,
                    activity=pal,
                    height_cm=height,
                    weight_kg=weight,
                    as_of_date=result.as_of_date,
                    reference_energy_kcal=result.reference_energy_kcal,
                    equation_table=result.equation_table,
                    growth_allowance_kcal=result.growth_allowance_kcal,
                    warnings=[w.code for w in result.warnings],
                    config=asdict(result.config),
                )
            )
    return {
        "recipe-readiness.json": {
            "count_scope": "status and blocker lists include optional rows (flagged); required counts separately retained. The normalized unknown union inventories all 51 registry codes, not a new recipe-required nutrient policy.",
            "recipes": recipe_records,
        },
        "food-readiness.json": {
            "scope": "All current required and optional foods; required usage count identifies required subset",
            "registry_size": len(registry),
            "foods": foods,
        },
        "closure-evidence.json": dict(
            operation="PR6-CLOSE",
            closure_base=BASE,
            measured_readiness={
                k: v
                for k, v in ready.items()
                if k not in {"records", "source_quantity_findings"}
            },
            migration_head=head(config),
            food_catalogue_count=len(after["food_ingredients"]),
            current_food_union_count=len(foods),
            required_food_union_count=sum(f["required_usage_count"] > 0 for f in foods),
            exact_config=asdict(CONFIG),
            member_fixture_results=targets,
            legacy_zero_boundary=dict(
                legacy_results_versioned=True,
                all_legacy_zero_occurrences_have_explicit_source_uncertainty=True,
                normalized_composition_never_falls_back_to_legacy_zero=True,
            ),
            legacy_zero_boundary_counts=dict(
                nutrient_occurrences=len(zero_disagreements),
                row_count=len({r["identity"] for r in zero_disagreements}),
                food_count=len({r["food_code"] for r in zero_disagreements}),
                required_nutrient_occurrences=sum(
                    not r["optional"] for r in zero_disagreements
                ),
            ),
            historical_replay=dict(
                old_seals=len(old_vectors),
                all_seals=len(vectors),
                old_compositions=len(old_compositions),
                all_compositions=len(compositions),
                requested_nutrients=len(registry),
                old_recipe_input_snapshots=len(historical),
                all_recipe_input_snapshots=len(current_results),
                current_marker_retirements=marker_retirements,
                preexisting_facts_preserved=True,
                captured_v1_inputs_replay=True,
                recipe_id_alone_historical_replay=False,
                read_only_inspection_preserved_all_tables=True,
            ),
            estimate_usages_non_executable=estimates,
            deferred_forms_absent=list(DEFERRED),
            deferred_rows=deferred_rows,
            yield_rows=yield_rows,
            legacy_numeric_normalized_unknown_occurrences=zero_disagreements,
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    assert (
        git("rev-parse", "origin/main") == BASE
    ), "Main moved: recompute reviewed closure baseline"
    assert git("rev-parse", f"{BASE}^2") == ACCEPTED_HEAD
    assert git("rev-parse", f"{BASE}^{{tree}}") == git(
        "rev-parse", f"{ACCEPTED_HEAD}^{{tree}}"
    )
    assert not git(
        "diff",
        "--name-only",
        TESTED,
        BASE,
        "--",
        "backend",
        "launcher",
        "frontend",
        "data",
        "scripts",
    )
    with TemporaryDirectory() as directory:
        reports = measure(DatabaseConfig(path=Path(directory) / "closure.sqlite"))
    reports["closure-evidence.json"]["git_baseline"] = dict(
        pr29_merged=True,
        merge_sha=BASE,
        accepted_head=ACCEPTED_HEAD,
        tested_implementation=TESTED,
        accepted_merge_tree=git("rev-parse", f"{BASE}^{{tree}}"),
        tested_runtime_data_tests_scripts_unchanged=True,
        historical_regression="3826 passed with AI_ENABLED=false; reused, not rerun",
        verification_source="GitHub get_pr_info PR29 plus fetched Git merge parent/tree comparison",
    )
    for name, report in reports.items():
        content = encode(report)
        path = PACKAGE / name
        if args.write:
            PACKAGE.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        else:
            assert path.read_text() == content, f"Closure evidence differs: {name}"
    print(encode({name: digest(report) for name, report in reports.items()}), end="")


if __name__ == "__main__":
    main()
