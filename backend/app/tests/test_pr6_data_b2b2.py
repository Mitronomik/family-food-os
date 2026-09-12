"""Adversarial proof for the bounded 0029 data upgrade, using disposable databases."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
import shutil
import sqlite3
from uuid import uuid4

import pytest
from sqlalchemy import event

from app.db.config import DatabaseConfig
from app.domain.b2b2_vector_import import prepare_reviewed_source
from app.domain.food_composition import (
    FoodCompositionVersion,
    CompositionKind,
    CompositionProvenance,
    MassState,
)
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.seed.b2b2 import (
    PACKAGE,
    PROMOTED,
    REMAPS,
    load_package,
    upgrade_b2b2,
    reconcile,
    detail_facts,
    _revision,
)
from scripts.audit_pr6_data_b2b2 import baseline as seed_baseline, measure, replay
from scripts.audit_pr6_nutrient_vector_b import snapshot, readiness


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("b2b2-base") / "base.sqlite")
    seed_baseline(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "test.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


@pytest.fixture
def docs():
    return load_package()


def test_full_upgrade_audit_history_readiness_backup_and_idempotency(tmp_path):
    result = measure(DatabaseConfig(path=tmp_path / "audit.sqlite"))
    assert result == json.loads((PACKAGE / "implementation-evidence.json").read_text())
    assert result["food_count_before"] == result["food_count_after"] == 185
    assert result["old_seals_read_unchanged"] == 185
    assert result["old_compositions_replayed_unchanged"] == 60
    assert result["first_run"] == dict(
        recipe_versions=2,
        profiles=3,
        nutrient_values=100,
        vector_seals=3,
        compositions=3,
        evidence=3,
        assessments=20,
    )
    assert result["readiness_after"]["assessment_status_counts"] == {
        "APPROVED_EXACT": 71,
        "APPROVED_NO_CONVERSION": 23,
        "REVIEW_REQUIRED_ESTIMATE": 35,
        "BLOCKED": 60,
    }
    assert len(result["row_delta"]) == 10
    assert (
        result["readiness_after"]["warning_occurrences"][
            "CONVERSION_ESTIMATE_NOT_ACCEPTED"
        ]
        == 40
    )


@pytest.mark.parametrize("code", list(REMAPS))
def test_only_position_six_changes_and_source_metadata_steps_preserved(database, code):
    engine = create_sqlite_engine(database)
    try:
        with B2B2UnitOfWork(engine) as u:
            parent = u.versions.get_current_verified(u.recipes.get_by_code(code).id)
            facts = detail_facts(u, parent)
            expected = _revision(u, parent, REMAPS[code])
            revised = detail_facts(u, expected)
            assert revised["recipe"] == facts["recipe"]
            assert (
                revised["steps"] == facts["steps"]
                and revised["equipment"] == facts["equipment"]
            )
            for key, value in facts["version"].items():
                if key not in {"version_number", "change_note"}:
                    assert revised["version"][key] == value
            assert revised["ingredients"][:5] == facts["ingredients"][:5]
            assert revised["ingredients"][6:] == facts["ingredients"][6:]
            assert revised["ingredients"][5] == dict(
                facts["ingredients"][5], food_code=REMAPS[code]
            )
        before = snapshot(database)
        upgrade_b2b2(database)
        after = snapshot(database)
        for table in [
            "food_recipe_versions",
            "food_recipe_ingredients",
            "food_recipe_steps",
            "food_recipe_equipment",
        ]:
            assert after[table][: len(before[table])] == before[table]
        with sqlite3.connect(database.path) as db:
            row = db.execute(
                "SELECT f.canonical_code FROM food_recipe_ingredients i JOIN food_recipe_versions v ON v.id=i.recipe_version_id JOIN food_recipes r ON r.id=v.recipe_id JOIN food_ingredients f ON f.id=i.food_ingredient_id WHERE r.canonical_code='WIC1_BEYOND_BASIC_GRILLED_CHEESE' AND i.position=3"
            ).fetchall()
            assert row == [("CAULIFLOWER",)]
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE food_nutrition_profiles SET is_current",
        "INSERT INTO nutrient_values",
        "INSERT INTO nutrition_vector_seals",
        "INSERT INTO food_composition_versions",
        "INSERT INTO food_recipe_versions",
        "INSERT INTO recipe_ingredient_nutrition_assessments",
    ],
)
def test_failure_after_actual_publication_rolls_back_entire_operation(
    database, monkeypatch, statement
):
    import app.seed.b2b2 as module

    before = snapshot(database)
    factory = module.create_sqlite_engine
    fired = []

    def engine_factory(config):
        engine = factory(config)

        def fail(conn, cursor, sql, params, context, many):
            if sql.startswith(statement):
                fired.append(sql)
                raise RuntimeError("injected B2B2 failure")

        event.listen(engine, "after_cursor_execute", fail)
        return engine

    with monkeypatch.context() as patch:
        patch.setattr(module, "create_sqlite_engine", engine_factory)
        with pytest.raises(RuntimeError, match="injected B2B2"):
            upgrade_b2b2(database)
    assert fired and snapshot(database) == before
    assert upgrade_b2b2(database)["profiles"] == 3
    after = snapshot(database)
    assert not any(upgrade_b2b2(database).values()) and snapshot(database) == after


@pytest.mark.parametrize(
    "filename",
    [
        "manifest.json",
        "plan.json",
        "source-manifest.json",
        "row-resolution.json",
        "profile-decisions.json",
    ],
)
def test_changed_review_package_fails_before_opening_database(tmp_path, filename):
    folder = tmp_path / "package"
    shutil.copytree(PACKAGE, folder)
    with (folder / filename).open("a") as stream:
        stream.write(" ")
    config = DatabaseConfig(path=tmp_path / "absent.sqlite")
    with pytest.raises(ValueError, match="Измен"):
        upgrade_b2b2(config, package=folder)
    assert not config.path.exists()


@pytest.mark.parametrize("food_code", list(PROMOTED))
def test_profile_all_use_review_old_seal_and_explicit_stale_bindings(
    database, food_code
):
    engine = create_sqlite_engine(database)
    try:
        with B2B2UnitOfWork(engine) as u:
            food = u.ingredients.get_by_code(food_code)
            old = u.nutrition_profiles.get_current(food.id)
            old_vector = u.nutrient_vectors.get(old.id)
        upgrade_b2b2(database)
        with B2B2UnitOfWork(engine) as u:
            current = u.nutrition_profiles.get_current(food.id)
            assert current.source_id == PROMOTED[food_code] and current.id != old.id
            historical = u.nutrition_profiles.get_nutrition_profile_by_id(old.id)
            assert historical == replace(old, is_current=False)
            assert u.nutrient_vectors.get(old.id) == replace(
                old_vector, profile=replace(old, is_current=False)
            )
            assert u.nutrient_vectors.get(current.id).values
            assert u.compositions.find_version(food.id, 1).profile_id == current.id
            usages = [
                (d, r)
                for d in u.current_details()
                for r in d.ingredients
                if r.food_ingredient_id == food.id
            ]
            assert (
                len(usages)
                == {"MAYONNAISE_LOW_FAT": 2, "OATS_ROLLED": 3, "TOMATO": 3}[food_code]
            )
            for d, row in usages:
                assert (
                    u.evidence.get_current_assessment(row.id).nutrition_profile_id
                    == current.id
                )
            # Deliberately introduce a different current profile in this fixture.
            u.nutrition_profiles.clear_current(food.id)
            u.nutrition_profiles.add(
                replace(current, id=uuid4(), source_id="synthetic-stale-profile")
            )
            u.commit()
        service = create_nutrition_service(engine)
        for d, row in usages:
            result = service.recipe_version(d.version.id)
            contribution = next(
                r
                for r in result.required_contributions + result.optional_contributions
                if r.row.id == row.id
            )
            assert "NUTRITION_ASSESSMENT_PROFILE_STALE" in [
                w.code for w in contribution.nutrition.warnings
            ]
            assert contribution.nutrition.mass_g is None
    finally:
        engine.dispose()


def test_existing_atomic_v1_replay_uses_old_profile_when_v2_is_appended(database, docs):
    engine = create_sqlite_engine(database)
    try:
        with B2B2UnitOfWork(engine) as u:
            for code in PROMOTED:
                food = u.ingredients.get_by_code(code)
                profile = u.nutrition_profiles.get_current(food.id)
                version = FoodCompositionVersion(
                    id=uuid4(),
                    food_ingredient_id=food.id,
                    version=1,
                    kind=CompositionKind.ATOMIC,
                    input_state=MassState.INPUT,
                    profile_id=profile.id,
                    provenance=CompositionProvenance(
                        "SYNTHETIC-TEST", "1", "fixture", "fixture"
                    ),
                )
                u.compositions.add_versions((version,))
            u.commit()
        old_vectors, old_compositions = replay(database)
        # Simulate the task's conditional existing-v1 population, separate from
        # actual main where these three foods have zero composition versions.
        docs = deepcopy(docs)
        docs["plan.json"]["composition_versions"] = {c: 2 for c in PROMOTED}
        with B2B2UnitOfWork(engine) as u:
            reconcile(u, docs)
            u.commit()
        new_vectors, new_compositions = replay(database)
        assert all(
            replace(
                new_vectors[k],
                profile=replace(
                    new_vectors[k].profile, is_current=v.profile.is_current
                ),
            )
            == v
            for k, v in old_vectors.items()
        )
        assert all(new_compositions[k] == v for k, v in old_compositions.items())
        with B2B2UnitOfWork(engine) as u:
            for code in PROMOTED:
                food = u.ingredients.get_by_code(code)
                v1 = u.compositions.find_version(food.id, 1)
                v2 = u.compositions.find_version(food.id, 2)
                assert v1.profile_id != v2.profile_id
                assert v2.profile_id == u.nutrition_profiles.get_current(food.id).id
    finally:
        engine.dispose()


def test_deferred_forms_apple_yield_and_estimates_do_not_gain_authority(database):
    before = snapshot(database)
    upgrade_b2b2(database)
    after = snapshot(database)
    assert before["food_ingredients"] == after["food_ingredients"]
    with sqlite3.connect(database.path) as db:
        codes = {
            r[0] for r in db.execute("SELECT canonical_code FROM food_ingredients")
        }
        assert not codes & {
            "APPLE_PEELED",
            "LEMON_JUICE",
            "ORANGE_JUICE",
            "PASTA_COOKED",
            "SPINACH_BABY",
            "APPLE_WITH_SKIN",
        }
        assert db.execute("SELECT count(*) FROM food_yield_models").fetchone()[0] == 0
        assert (
            db.execute("SELECT count(*) FROM food_transformations").fetchone()[0] == 0
        )
    report = readiness(database)
    remaining = []
    for d in report["records"]:
        for row in d["rows"]:
            if row["evidence_key"] and row["evidence_key"].endswith(":estimate"):
                assert row["mass_g"] is None
                assert row["assessment"] in {"BLOCKED", "REVIEW_REQUIRED_ESTIMATE"}
                remaining.append(row)
            if (d["recipe"], row["position"]) in {
                ("SNAP4_BRAISED_CHICKEN_SPINACH", 1),
                ("SNAP4_SPANISH_FRITTATA", 1),
                ("WIC4_BUTTERNUT_SOUP", 1),
                ("WIC2_SPINACH_CAULIFLOWER_SMOOTHIE", 6),
            }:
                assert row["assessment"] == "BLOCKED" and row["mass_g"] is None
    assert len(remaining) == 40
    # Original estimate evidence is never relabelled or overwritten.
    assert (
        after["nutrition_measure_evidence"][: len(before["nutrition_measure_evidence"])]
        == before["nutrition_measure_evidence"]
    )


def test_incomplete_or_additional_all_use_population_fails_before_profile_switch(
    database, docs
):
    engine = create_sqlite_engine(database)
    try:
        with B2B2UnitOfWork(engine) as u:
            detail = next(
                d
                for d in u.current_details()
                if d.recipe.canonical_code == "WIC1_OVERNIGHT_OATS_CINNAMON_APPLE"
            )
            # Non-target oat use: a new unreviewed immutable revision must block.
            key = uuid4()
            revised = replace(
                detail,
                version=replace(
                    detail.version,
                    id=key,
                    version_number=3,
                    created_from_version_id=detail.version.id,
                ),
                ingredients=tuple(
                    replace(r, id=uuid4(), recipe_version_id=key)
                    for r in detail.ingredients
                ),
                steps=tuple(
                    replace(r, id=uuid4(), recipe_version_id=key) for r in detail.steps
                ),
                equipment=tuple(
                    replace(r, recipe_version_id=key) for r in detail.equipment
                ),
            )
            u.versions.add_detail(revised)
            u.commit()
        before = snapshot(database)
        with pytest.raises(ValueError):
            upgrade_b2b2(database)
        assert snapshot(database) == before
    finally:
        engine.dispose()


@pytest.mark.parametrize("sid", ["173594", "173904", "170457"])
def test_bounded_positive_sparse_import_unknown_zero_and_same_authority(docs, sid):
    mappings = json.loads(
        (PACKAGE.parent / "pr6-nutrient-vector-a/source-mappings.json").read_text()
    )["mappings"]
    source = docs["source-manifest.json"]["profiles"][sid]
    legacy, values, observations = prepare_reviewed_source(source, mappings)
    assert all(isinstance(v["amount"], Decimal) and v["amount"] > 0 for v in values)
    assert len(values) == len({v["nutrient_code"] for v in values}) < 51
    if sid == "173594":
        assert legacy["fiber_g"] is None
        assert "FIBER_TOTAL_DIETARY" not in {v["nutrient_code"] for v in values}
        assert "UNRESOLVED_ZERO" in observations
    bad = deepcopy(source)
    bad["source_id"] = "2709249"
    bad["source_data_type"] = "Survey (FNDDS)"
    with pytest.raises(ValueError):
        prepare_reviewed_source(bad, mappings)
    with pytest.raises(ValueError):
        prepare_reviewed_source(source, [])
    bad = deepcopy(source)
    bad["food_nutrients"][0]["fdc_id"] = "different-food"
    with pytest.raises(ValueError):
        prepare_reviewed_source(bad, mappings)
    bad = deepcopy(source)
    bad["food_nutrients"].append(bad["food_nutrients"][0])
    with pytest.raises(ValueError):
        prepare_reviewed_source(bad, mappings)


def test_relabelled_estimate_remains_non_executable(database):
    upgrade_b2b2(database)
    engine = create_sqlite_engine(database)
    try:
        with B2B2UnitOfWork(engine) as u:
            detail = next(
                d
                for d in u.current_details()
                if d.recipe.canonical_code == "SNAP2_SIMPLE_GREEN_SMOOTHIE"
            )
            row = detail.ingredients[0]
            old = u.evidence.get_current_assessment(row.id)
            assert u.evidence.get_evidence(old.measure_evidence_id).estimated
            u.evidence.add_assessment(
                replace(
                    old,
                    id=uuid4(),
                    assessment_version=old.assessment_version + 1,
                    status_code="APPROVED_EXACT",
                    issues=(),
                )
            )
            u.commit()
        result = create_nutrition_service(engine).recipe_version(detail.version.id)
        item = next(r for r in result.required_contributions if r.row.id == row.id)
        assert item.nutrition.mass_g is None
        assert "CONVERSION_ESTIMATE_NOT_ACCEPTED" in {
            w.code for w in item.nutrition.warnings
        }
        with pytest.raises(ValueError):
            upgrade_b2b2(database)
    finally:
        engine.dispose()


def test_second_run_checks_carried_forward_non_target_assessments(database):
    upgrade_b2b2(database)
    engine = create_sqlite_engine(database)
    try:
        with B2B2UnitOfWork(engine) as u:
            detail = next(
                d
                for d in u.current_details()
                if d.recipe.canonical_code == "SNAP2_SIMPLE_GREEN_SMOOTHIE"
            )
            milk = detail.ingredients[2]
            old = u.evidence.get_current_assessment(milk.id)
            u.evidence.add_assessment(
                replace(
                    old,
                    id=uuid4(),
                    assessment_version=old.assessment_version + 1,
                    review_note="Synthetic later review",
                )
            )
            u.commit()
        before = snapshot(database)
        with pytest.raises(ValueError, match="Опубликованная оценка"):
            upgrade_b2b2(database)
        assert snapshot(database) == before
    finally:
        engine.dispose()


def test_missing_frozen_composition_fails_before_any_profile_switch(
    database, monkeypatch
):
    from app.persistence.sqlalchemy_core.ru_food_data import RuCompositionRepository

    before = snapshot(database)
    monkeypatch.setattr(RuCompositionRepository, "find_version", lambda *args: None)
    with pytest.raises(ValueError, match="состава замороженной"):
        upgrade_b2b2(database)
    assert snapshot(database) == before


def test_second_run_rechecks_exact_mass_contents_not_only_keys(database, monkeypatch):
    from app.persistence.sqlalchemy_core.nutrition_evidence_repositories import (
        SqlAlchemyNutritionEvidenceRepository,
    )

    upgrade_b2b2(database)
    before = snapshot(database)
    original = SqlAlchemyNutritionEvidenceRepository.get_by_key

    def corrupted(self, key):
        result = original(self, key)
        return (
            replace(result, gram_weight=Decimal("999"))
            if key.startswith("B2B2:")
            else result
        )

    monkeypatch.setattr(SqlAlchemyNutritionEvidenceRepository, "get_by_key", corrupted)
    with pytest.raises(ValueError, match="Доказательство массы"):
        upgrade_b2b2(database)
    assert snapshot(database) == before
