"""Step 9 publication of one inactive School2022 RecipeVersion."""

from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
import shutil
import sqlite3
from types import SimpleNamespace

import pytest
from sqlalchemy import event

from app.db.config import DatabaseConfig
from app.domain.households import HouseholdState
from app.domain.meal_patterns import MealRole
from app.domain.nutrition import NutritionStatus, NutritionValues
from app.domain.planner import PlannerConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.seed.food_recipes import seed_food_recipes
from app.seed.ru_nut_db_step8_butter import seed_ru_nut_db_step8_butter
from app.seed import ru_school2022_step9_recipe as step9
from app.services.food_recipes import (
    RecipeCatalogueConflictError,
    TrustedRecipeSeedDisposition,
)
from app.services.meal_plans import MealPlanNotFoundError
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from app.tests.test_planner import selection, uid

RECIPE_CODE = "SCHOOL2022_53_19Z_BUTTER_PORTION"
SOURCE_TABLES = (
    "recipe_source_documents",
    "recipe_source_cards",
    "recipe_source_card_variants",
    "recipe_source_card_ingredients",
    "recipe_source_declared_nutrients",
)


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    config = DatabaseConfig(
        path=tmp_path_factory.mktemp("step9-base") / "base.sqlite"
    )
    seed_food_recipes(config)
    seed_ru_nut_db_step8_butter(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "step9.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def scalar(config: DatabaseConfig, sql: str, params=()):
    with sqlite3.connect(config.path) as db:
        return db.execute(sql, params).fetchone()[0]


def source_corpus_counts(config: DatabaseConfig) -> dict[str, int]:
    with sqlite3.connect(config.path) as db:
        return {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in SOURCE_TABLES
        }


def existing_catalogue_snapshot(config: DatabaseConfig) -> tuple:
    with sqlite3.connect(config.path) as db:
        recipe_rows = tuple(
            db.execute(
                """
                SELECT id, canonical_code, canonical_name, canonical_name_key,
                       is_active, created_at, updated_at
                FROM food_recipes
                WHERE canonical_code != ?
                ORDER BY canonical_code
                """,
                (RECIPE_CODE,),
            ).fetchall()
        )
        version_rows = tuple(
            db.execute(
                """
                SELECT v.*
                FROM food_recipe_versions v
                JOIN food_recipes r ON r.id = v.recipe_id
                WHERE r.canonical_code != ?
                ORDER BY v.id
                """,
                (RECIPE_CODE,),
            ).fetchall()
        )
        ingredient_rows = tuple(
            db.execute(
                """
                SELECT i.*
                FROM food_recipe_ingredients i
                JOIN food_recipe_versions v ON v.id = i.recipe_version_id
                JOIN food_recipes r ON r.id = v.recipe_id
                WHERE r.canonical_code != ?
                ORDER BY i.id
                """,
                (RECIPE_CODE,),
            ).fetchall()
        )
        step_rows = tuple(
            db.execute(
                """
                SELECT s.*
                FROM food_recipe_steps s
                JOIN food_recipe_versions v ON v.id = s.recipe_version_id
                JOIN food_recipes r ON r.id = v.recipe_id
                WHERE r.canonical_code != ?
                ORDER BY s.id
                """,
                (RECIPE_CODE,),
            ).fetchall()
        )
        equipment_rows = tuple(
            db.execute(
                """
                SELECT e.*
                FROM food_recipe_equipment e
                JOIN food_recipe_versions v ON v.id = e.recipe_version_id
                JOIN food_recipes r ON r.id = v.recipe_id
                WHERE r.canonical_code != ?
                ORDER BY e.recipe_version_id, e.position
                """,
                (RECIPE_CODE,),
            ).fetchall()
        )
    return recipe_rows, version_rows, ingredient_rows, step_rows, equipment_rows


def mutate_package(tmp_path, monkeypatch, mutate):
    package = tmp_path / "package"
    shutil.copytree(step9.PACKAGE, package)
    path = package / "publication.json"
    payload = json.loads(path.read_text())
    mutate(payload)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.write_text(raw)
    monkeypatch.setattr(
        step9, "PUBLICATION_SHA256", hashlib.sha256(raw.encode()).hexdigest()
    )
    return package


def test_package_freezes_inactive_recipe_material_steps_and_institutional_context():
    seed, publication = step9.load_ru_school2022_step9_recipe_seed()
    assert seed.canonical_code == RECIPE_CODE
    assert seed.canonical_name == "Масло сливочное (порциями)"
    assert seed.initial_is_active is False
    assert seed.version.steps == step9.MATERIAL_STEPS
    assert len(seed.version.ingredients) == 1
    ingredient = seed.version.ingredients[0]
    assert ingredient.food_ingredient_code == step9.FOOD_CODE
    assert ingredient.quantity == Decimal("10")
    assert ingredient.unit == "g"
    assert ingredient.optional is False
    assert seed.version.equipment_codes == ()

    context = publication["institutional_context"]
    assert context["process_evidence_id"] == step9.PROCESS_EVIDENCE_ID
    assert context["applicability"] == "institutional_school_catering_only"
    assert context["domestic_applicability"] == "unestablished"
    assert context["not_executable_rule"] is True
    assert context["home_storage_status"] == "not_granted"
    assert context["consumer_recipe_step_promotion"] is False
    assert context["refrigerated_holding_fact"] not in seed.version.steps
    assert all("14" not in value for value in seed.version.steps)
    assert len(publication["lineage"]) == 7


def test_package_pins_exact_source_and_v2_expectations():
    _, publication = step9.load_ru_school2022_step9_recipe_seed()
    source = publication["source"]
    assert source["archive_size_bytes"] == step9.ARCHIVE_SIZE_BYTES
    assert source["archive_sha256"] == step9.ARCHIVE_SHA256
    assert source["source_json_sha256"] == step9.SOURCE_JSON_SHA256
    assert source["pdf_sha256"] == step9.SCHOOL_PDF_SHA256
    assert source["official_url"] == step9.SOURCE_URL
    assert {
        row["canonical_json_sha256"] for row in publication["lineage"]
    } == {row[2] for row in step9.LINEAGE}
    assert publication["nutrition_validation"]["expected_recipe_amounts"] == {
        code: format(value, "f")
        for code, value in step9.EXPECTED_RECIPE_AMOUNTS.items()
    }
    assert publication["nutrition_validation"]["water_state"] == "unknown"
    assert (
        publication["nutrition_validation"]["canonical_total_carbohydrate_state"]
        == "unknown"
    )
    readme = (step9.PACKAGE / "README.md").read_text()
    assert step9.SOURCE_URL in readme
    assert step9.SCHOOL_PDF_SHA256 in readme


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload["recipe"].__setitem__("initial_is_active", True),
        lambda payload: payload["recipe"]["version"]["steps"].append(
            "До раздачи хранить порционированное масло в холодильнике."
        ),
        lambda payload: payload["institutional_context"].__setitem__(
            "domestic_applicability", "established"
        ),
        lambda payload: payload["institutional_context"].__setitem__(
            "home_storage_status", "granted"
        ),
    ],
)
def test_rehashed_semantic_drift_fails_closed(tmp_path, monkeypatch, mutate):
    package = mutate_package(tmp_path, monkeypatch, mutate)
    with pytest.raises(ValueError):
        step9.load_ru_school2022_step9_recipe_seed(package)


def test_changed_package_hash_fails_before_database_creation(tmp_path):
    package = tmp_path / "package"
    shutil.copytree(step9.PACKAGE, package)
    with (package / "publication.json").open("a") as stream:
        stream.write(" ")
    config = DatabaseConfig(path=tmp_path / "should-not-exist.sqlite")

    with pytest.raises(ValueError, match="Изменён"):
        step9.seed_ru_school2022_step9_recipe(config, package=package)

    assert not config.path.exists()


def test_missing_step8_dependency_fails_without_recipe_write(tmp_path):
    config = DatabaseConfig(path=tmp_path / "missing-step8.sqlite")
    seed_food_recipes(config)
    before = db_dump(config)

    with pytest.raises(ValueError, match="Step 8 FoodIngredient"):
        step9.seed_ru_school2022_step9_recipe(config)

    assert db_dump(config) == before
    assert scalar(config, "SELECT COUNT(*) FROM food_recipes") == 30


def test_inactive_step8_dependency_fails_without_recipe_write(database):
    engine = create_sqlite_engine(database)
    try:
        food_service = create_food_catalogue_service(engine)
        food = food_service.get_by_code(step9.FOOD_CODE)
        food_service.deactivate(food.id)
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(ValueError, match="должен быть active"):
        step9.seed_ru_school2022_step9_recipe(database)

    assert db_dump(database) == before
    assert scalar(
        database,
        "SELECT COUNT(*) FROM food_recipes WHERE canonical_code = ?",
        (RECIPE_CODE,),
    ) == 0


def test_fresh_publication_exact_replay_and_activation_preservation(database):
    before_existing = existing_catalogue_snapshot(database)
    before_source = source_corpus_counts(database)
    assert (
        scalar(database, "SELECT COUNT(*) FROM food_recipes WHERE is_active = 1")
        == 30
    )

    first = step9.seed_ru_school2022_step9_recipe(database)
    assert first.recipes_inserted == 1
    assert first.versions_inserted == 1
    assert first.ingredients_inserted == 1
    assert first.steps_inserted == 2
    assert first.equipment_inserted == 0

    engine = create_sqlite_engine(database)
    try:
        service = create_food_recipe_catalogue_service(engine)
        recipe = service.get_by_code(RECIPE_CODE)
        versions = service.list_versions(recipe.id)
        assert recipe.is_active is False
        assert len(versions) == 1
        detail = service.get_version_detail(versions[0].id)
        assert detail.version.version_number == 1
        assert detail.version.source_recipe_id == step9.SOURCE_RECIPE_ID
        assert detail.version.base_servings == Decimal("1.000000")
        assert len(detail.ingredients) == 1
        assert detail.ingredients[0].quantity == Decimal("10.000000")
        assert tuple(item.instruction for item in detail.steps) == step9.MATERIAL_STEPS
        assert detail.equipment == ()
        assert all(item.id != recipe.id for item in service.list_active(limit=200))
        disposition = service.preflight_trusted_seed(
            step9.load_ru_school2022_step9_recipe_seed()[0]
        )
        assert disposition is TrustedRecipeSeedDisposition.EXACT_REPLAY
    finally:
        engine.dispose()

    assert scalar(database, "SELECT COUNT(*) FROM food_recipes") == 31
    assert scalar(database, "SELECT COUNT(*) FROM food_recipe_versions") == 31
    assert scalar(database, "SELECT COUNT(*) FROM food_recipe_ingredients") == 190
    assert scalar(database, "SELECT COUNT(*) FROM food_recipe_steps") == 171
    assert scalar(database, "SELECT COUNT(*) FROM food_recipe_equipment") == 86
    assert (
        scalar(database, "SELECT COUNT(*) FROM food_recipes WHERE is_active = 1")
        == 30
    )
    assert existing_catalogue_snapshot(database) == before_existing
    assert source_corpus_counts(database) == before_source

    before_replay = db_dump(database)
    second = step9.seed_ru_school2022_step9_recipe(database)
    assert second.recipes_inserted == 0
    assert second.versions_inserted == 0
    assert second.ingredients_inserted == 0
    assert second.steps_inserted == 0
    assert second.equipment_inserted == 0
    assert second.recipes_existing == 1
    assert second.versions_existing == 1
    assert db_dump(database) == before_replay

    engine = create_sqlite_engine(database)
    try:
        with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as uow:
            recipe = uow.recipes.get_by_code(RECIPE_CODE)
            assert recipe is not None
            uow.recipes.set_active(
                recipe.id,
                active=True,
                updated_at=datetime(2026, 9, 27, tzinfo=timezone.utc),
            )
            uow.commit()
    finally:
        engine.dispose()

    activated_dump = db_dump(database)
    third = step9.seed_ru_school2022_step9_recipe(database)
    assert third.recipes_existing == 1
    assert third.versions_existing == 1
    assert db_dump(database) == activated_dump

    engine = create_sqlite_engine(database)
    try:
        assert create_food_recipe_catalogue_service(engine).get_by_code(
            RECIPE_CODE
        ).is_active is True
    finally:
        engine.dispose()


def test_unexpected_existing_recipe_history_fails_closed(database):
    seed, _ = step9.load_ru_school2022_step9_recipe_seed()
    wrong = replace(
        seed,
        version=replace(
            seed.version,
            source_recipe_id="ru-school2022:recipe:unexpected",
        ),
    )
    engine = create_sqlite_engine(database)
    try:
        create_food_recipe_catalogue_service(engine).reconcile_seed((wrong,))
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(RecipeCatalogueConflictError, match="lacks the trusted"):
        step9.seed_ru_school2022_step9_recipe(database)

    assert db_dump(database) == before


def test_same_provenance_structural_drift_fails_closed(database):
    seed, _ = step9.load_ru_school2022_step9_recipe_seed()
    wrong = replace(
        seed,
        version=replace(
            seed.version,
            ingredients=(
                replace(seed.version.ingredients[0], quantity=Decimal("9")),
            ),
        ),
    )
    engine = create_sqlite_engine(database)
    try:
        create_food_recipe_catalogue_service(engine).reconcile_seed((wrong,))
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(RecipeCatalogueConflictError, match="Same-provenance"):
        step9.seed_ru_school2022_step9_recipe(database)

    assert db_dump(database) == before


def test_strict_reconcile_rechecks_history_inside_write_uow(database):
    seed, _ = step9.load_ru_school2022_step9_recipe_seed()
    engine = create_sqlite_engine(database)
    try:
        service = create_food_recipe_catalogue_service(engine)
        assert (
            service.preflight_trusted_seed(seed)
            is TrustedRecipeSeedDisposition.FRESH
        )
        wrong = replace(
            seed,
            version=replace(
                seed.version,
                source_recipe_id="ru-school2022:recipe:concurrent",
            ),
        )
        service.reconcile_seed((wrong,))
        before = db_dump(database)
        with pytest.raises(RecipeCatalogueConflictError, match="lacks the trusted"):
            service.reconcile_seed((seed,), strict_history=True)
        assert db_dump(database) == before
    finally:
        engine.dispose()


def test_later_same_provenance_revision_blocks_exact_replay(database):
    seed, _ = step9.load_ru_school2022_step9_recipe_seed()
    engine = create_sqlite_engine(database)
    try:
        service = create_food_recipe_catalogue_service(engine)
        first = service.reconcile_seed((seed,))
        assert first.versions_inserted == 1
        recipe = service.get_by_code(RECIPE_CODE)
        service.append_trusted_version(
            recipe.id,
            replace(
                seed.version,
                change_note="Conflicting same-provenance internal revision.",
            ),
        )
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(RecipeCatalogueConflictError, match="Same-provenance"):
        step9.seed_ru_school2022_step9_recipe(database)

    assert db_dump(database) == before


def test_injected_late_write_failure_rolls_back_complete_recipe_bundle(
    database, monkeypatch
):
    engine = create_sqlite_engine(database)
    before = db_dump(database)

    def fail_on_step(connection, cursor, statement, parameters, context, executemany):
        del connection, cursor, parameters, context, executemany
        if statement.strip().startswith("INSERT INTO food_recipe_steps"):
            raise RuntimeError("injected Step 9 recipe-step failure")

    event.listen(engine, "before_cursor_execute", fail_on_step)
    monkeypatch.setattr(step9, "create_sqlite_engine", lambda config: engine)
    try:
        with pytest.raises(RuntimeError, match="injected Step 9"):
            step9.seed_ru_school2022_step9_recipe(database)
    finally:
        event.remove(engine, "before_cursor_execute", fail_on_step)

    assert db_dump(database) == before


class _Households:
    def __init__(self, household_id, member_id):
        self.household_id = household_id
        self.member_id = member_id

    def get_household(self, household_id):
        assert household_id == self.household_id
        return HouseholdState(
            household=SimpleNamespace(id=self.household_id),
            members=(SimpleNamespace(id=self.member_id, active=True),),
        )


class _MealPlans:
    def __init__(self, household_id, member_id):
        self.selection = selection(member_id, (MealRole.DINNER,))
        object.__setattr__(self.selection.selection, "household_id", household_id)
        self.writes = []

    def get_current_member_pattern(self, household_id, member_id):
        return self.selection

    def get_current_plan(self, household_id, week_start):
        raise MealPlanNotFoundError()

    def create_plan_revision(self, **kwargs):
        self.writes.append(kwargs)
        return SimpleNamespace()


class _Nutrition:
    def member_reference_target(self, household_id, member_id, *, as_of_date):
        return SimpleNamespace(reference_energy_kcal=Decimal("2000"))

    def recipe_version(self, version_id):
        return SimpleNamespace(
            per_base_serving=NutritionValues(kcal=Decimal("500")),
            status=NutritionStatus.COMPLETE,
        )


class _Pantry:
    def list_items(self, household_id):
        return []


def test_inactive_step9_recipe_is_absent_from_authoritative_planner(database):
    step9.seed_ru_school2022_step9_recipe(database)
    engine = create_sqlite_engine(database)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        step9_recipe = recipes.get_by_code(RECIPE_CODE)
        step9_versions = recipes.list_versions(step9_recipe.id)
        assert step9_recipe.is_active is False
        assert len(step9_versions) == 1
        step9_version = step9_versions[0].id
        household_id, member_id = uid(1), uid(2)
        meal_plans = _MealPlans(household_id, member_id)
        planner = PlannerService(
            meal_plans,
            _Households(household_id, member_id),
            recipes,
            _Nutrition(),
            _Pantry(),
            PlannerConfig(max_recipe_repetitions=10),
        )
        command = AuthoritativeGenerationRequest(
            household_id,
            date(2026, 9, 28),
            (GenerationMemberConstraints(member_id),),
        )
        request = planner.compose_authoritative_request(command)
        assert step9_version not in {
            candidate.recipe_version_id for candidate in request.candidates
        }
        assert len(request.candidates) == 30

        result, persisted = planner.generate_authoritative(command)
        assert persisted is not None
        assert meal_plans.writes
        assert all(
            event.recipe_version_id != step9_version
            for event in result.events
            if event.recipe_version_id is not None
        )
    finally:
        engine.dispose()
