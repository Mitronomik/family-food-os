import re
import shutil
import sqlite3
from collections import Counter
from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest
from app.db import migrations
from app.db.config import DatabaseConfig
from app.domain.food_recipes import MealTypeCode
from app.domain.meal_patterns import MealRole
from app.domain.meal_plans import MemberMealPatternSourceKind
from app.domain.planner import (
    ROLE_COMPATIBILITY_V1,
    PlannerConfig,
    PlannerRejectionCode,
    PlannerSuccess,
)
from app.domain.recipe_nutrition_v2 import NUTRIENT_CODES
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeRepository,
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.household_composition import (
    create_household_service,
)
from app.persistence.sqlalchemy_core.household_uow import SqlAlchemyHouseholdReadScope
from app.persistence.sqlalchemy_core.meal_pattern_uow import (
    SqlAlchemyMealPatternCatalogueReadScope,
)
from app.persistence.sqlalchemy_core.meal_plan_uow import (
    SqlAlchemyMealPlanReadScope,
    SqlAlchemyMealPlanUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_composition import (
    create_nutrition_service,
)
from app.persistence.sqlalchemy_core.pantry_composition import create_pantry_service
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyPreparedRecipeNutritionRepository,
    create_recipe_nutrition_v2_service,
)
from app.seed.r3b_school2022_breakfast_batch import (
    MILK_UNAFFECTED_BREAKFAST_CODES,
)
from app.seed.r3b_school2022_breakfast_batch import RECIPE_CODES as R3B_RECIPE_CODES
from app.seed.r3c_school2022_main_batch import RECIPE_CODES as R3C_RECIPE_CODES
from app.seed.r3c_school2022_main_batch import seed_r3c_school2022_main_batch
from app.seed.r3d_final_dc3_batch import (
    BEEF_FOOD_CODE,
    CHICKEN_FOOD_CODES,
    FISH_FOOD_CODES,
    FROZEN_BATCH_PATH,
    IDENTITY_ONLY_FOOD_CODES,
    MILK_FOOD_CODE,
    MR_BUNDLE_PATH,
    PACKAGE,
    RECIPE_CODES,
    SUMMARY_PATH,
    _load_contract,
    _recipe_seeds_and_specs,
    _review_commitment,
    activate_r3d_final_dc3_batch,
    publish_r3d_final_dc3_batch,
    seed_r3d_final_dc3_batch,
)
from app.services.food_ingredients import (
    FoodCatalogueConflictError,
    FoodIngredientNotFoundError,
    TrustedFoodIngredientIdentitySeed,
)
from app.services.meal_plans import MealPlanService
from app.services.planner import (
    AuthoritativeGenerationRequest,
    GenerationMemberConstraints,
    PlannerService,
)
from app.services.prepared_recipe_activation import PreparedRecipeActivationError
from app.services.recipe_nutrition_v2 import RecipeNutritionV2ConflictError

WEEK_START = date(2026, 10, 5)


@pytest.fixture(scope="session")
def baseline(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("r3d-base") / "base.sqlite")
    seed_r3c_school2022_main_batch(config)
    return config


@pytest.fixture
def database(baseline, tmp_path):
    config = DatabaseConfig(path=tmp_path / "r3d.sqlite")
    shutil.copyfile(baseline.path, config.path)
    return config


def db_dump(config: DatabaseConfig) -> str:
    with sqlite3.connect(config.path) as db:
        return "\n".join(db.iterdump())


def r3d_recipe_states(config: DatabaseConfig) -> dict[str, int]:
    placeholders = ",".join("?" for _ in RECIPE_CODES)
    with sqlite3.connect(config.path) as db:
        rows = db.execute(
            f"""
            SELECT canonical_code, is_active
            FROM food_recipes
            WHERE canonical_code IN ({placeholders})
            ORDER BY canonical_code
            """,
            RECIPE_CODES,
        ).fetchall()
    return {code: active for code, active in rows}


def r3d_counts(config: DatabaseConfig) -> dict[str, int]:
    placeholders = ",".join("?" for _ in RECIPE_CODES)
    with sqlite3.connect(config.path) as db:
        recipe_ids = tuple(
            row[0]
            for row in db.execute(
                f"""
                SELECT id FROM food_recipes
                WHERE canonical_code IN ({placeholders})
                """,
                RECIPE_CODES,
            ).fetchall()
        )
        if not recipe_ids:
            return {"recipes": 0, "authorities": 0, "values": 0}
        recipe_placeholders = ",".join("?" for _ in recipe_ids)
        version_ids = tuple(
            row[0]
            for row in db.execute(
                f"""
                SELECT id FROM food_recipe_versions
                WHERE recipe_id IN ({recipe_placeholders})
                """,
                recipe_ids,
            ).fetchall()
        )
        version_placeholders = ",".join("?" for _ in version_ids)
        authorities = db.execute(
            f"""
            SELECT COUNT(*) FROM recipe_prepared_nutrition_authorities
            WHERE recipe_version_id IN ({version_placeholders})
            """,
            version_ids,
        ).fetchone()[0]
        values = db.execute(
            f"""
            SELECT COUNT(*) FROM recipe_prepared_nutrient_values
            WHERE recipe_version_id IN ({version_placeholders})
            """,
            version_ids,
        ).fetchone()[0]
    return {
        "recipes": len(recipe_ids),
        "authorities": authorities,
        "values": values,
    }


def meal_plan_service(engine) -> MealPlanService:
    return MealPlanService(
        write_scope_factory=lambda: SqlAlchemyMealPlanUnitOfWork(engine),
        read_scope_factory=lambda: SqlAlchemyMealPlanReadScope(engine),
        household_read_scope_factory=lambda: SqlAlchemyHouseholdReadScope(engine),
        pattern_read_scope_factory=lambda: SqlAlchemyMealPatternCatalogueReadScope(
            engine
        ),
    )


def production_planner(engine):
    meal_plans = meal_plan_service(engine)
    households = create_household_service(engine)
    catalogue = create_food_recipe_catalogue_service(engine)
    nutrition = create_nutrition_service(engine)
    pantry = create_pantry_service(engine)
    recipe_nutrition = create_recipe_nutrition_v2_service(engine)
    planner = PlannerService(
        meal_plans,
        households,
        catalogue,
        nutrition,
        pantry,
        PlannerConfig(version="planner-v0.4", max_recipe_repetitions=3),
        recipe_nutrition=recipe_nutrition,
    )
    return planner, meal_plans, households, catalogue


def create_role_household(households, meal_plans, role: MealRole, share: str):
    household = households.create_household(
        name=f"R3-D {role.value} exclusion proof",
        timezone_name="Europe/Moscow",
        city="Санкт-Петербург",
    )
    member = households.add_household_member(
        household.id,
        name="Анна",
        activity_level="active",
        goal="maintain",
        birth_date=date(1990, 5, 20),
        sex="female",
        height_cm=Decimal(168),
        weight_kg=Decimal(62),
    )
    selection = meal_plans.accept_member_pattern(
        household_id=household.id,
        member_id=member.id,
        source_kind=MemberMealPatternSourceKind.CUSTOM,
        schedule={weekday: (role,) for weekday in range(1, 8)},
        energy_shares={weekday: (Decimal(share),) for weekday in range(1, 8)},
    )
    return household, member, selection


def test_r3d_existing_mappings_resolve_before_new_identities(database):
    frozen, _, _ = _load_contract()
    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        frozen_codes = {
            ingredient["food_code"]
            for row in frozen["selected"]
            for ingredient in row["ingredients"]
        }
        assert set(IDENTITY_ONLY_FOOD_CODES) <= frozen_codes
        for code in sorted(frozen_codes - set(IDENTITY_ONLY_FOOD_CODES)):
            assert food.get_by_code(code).canonical_code == code
        for code in IDENTITY_ONLY_FOOD_CODES:
            with pytest.raises(FoodIngredientNotFoundError):
                food.get_by_code(code)
    finally:
        engine.dispose()


def test_r3d_fresh_publication_activation_and_authority(database):
    frozen, _, _ = _load_contract()
    expected_by_code = {row["canonical_code"]: row for row in frozen["selected"]}

    result = seed_r3d_final_dc3_batch(database)

    assert result.publication.identity_food_inserted == 10
    assert result.publication.identity_food_existing == 0
    assert result.activation_changed is True
    assert result.active_recipe_codes == RECIPE_CODES
    assert (
        tuple(code for code, _ in result.publication.recipe_version_ids) == RECIPE_CODES
    )
    assert all(
        disposition == "FRESH"
        for _code, disposition in result.publication.authority_dispositions
    )

    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        catalogue = create_food_recipe_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)

        for code, version_id in result.publication.recipe_version_ids:
            expected = expected_by_code[code]
            recipe = catalogue.get_by_code(code)
            assert recipe.is_active is True
            detail = catalogue.get_current_verified(recipe.id)
            assert detail.version.id == version_id
            assert detail.version.meal_type_code.value == "main"
            assert detail.version.source_name == "RU_MR_2_4_0162_19"
            assert (
                detail.version.source_recipe_id
                == f"APPENDIX_5_CARD_{expected['source_card_code']}"
            )
            assert detail.version.source_url == expected["source_page_url"]
            assert detail.version.source_document_sha256 == (
                "973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e"
            )
            assert f"card_sha256={expected['source_card_raw_sha256']}" in (
                detail.version.change_note
            )
            assert f"source_partition_sha256={_review_commitment(expected)}" in (
                detail.version.change_note
            )
            assert "household=REVIEWED_PASS" in detail.version.change_note
            assert "medical=false" in detail.version.change_note
            assert detail.version.source_output_g == Decimal(
                expected["source_output_g"]
            )
            assert tuple(step.instruction for step in detail.steps) == tuple(
                expected["consumer_steps_ru"]
            )
            assert tuple(
                food.get(ingredient.food_ingredient_id).canonical_code
                for ingredient in detail.ingredients
            ) == tuple(
                ingredient["food_code"] for ingredient in expected["ingredients"]
            )
            assert tuple(
                ingredient.quantity for ingredient in detail.ingredients
            ) == tuple(
                Decimal(ingredient["quantity_g"])
                for ingredient in expected["ingredients"]
            )
            assert tuple(
                ingredient.source_amount_text for ingredient in detail.ingredients
            ) == tuple(
                f"{ingredient['source_label']}: {ingredient['quantity_g']} г "
                "(12 лет и старше)"
                for ingredient in expected["ingredients"]
            )

            projection = nutrition.neutral_consumption_projection(version_id)
            assert projection.exact_energy_ready is True
            assert projection.per_base_serving.kcal == Decimal(expected["energy_kcal"])
            canonical = nutrition.prepared_canonical_nutrition(version_id)
            assert len(canonical.required_total) == len(NUTRIENT_CODES) == 54
            assert canonical.total_amount("ENERGY_KCAL") == Decimal(
                expected["energy_kcal"]
            )
            unknown = tuple(
                row for row in canonical.required_total if row.code != "ENERGY_KCAL"
            )
            assert len(unknown) == 53
            assert all(row.amount is None for row in unknown)

        for code in IDENTITY_ONLY_FOOD_CODES:
            assert food.get_by_code(code).is_active is True
    finally:
        engine.dispose()

    placeholders = ",".join("?" for _ in IDENTITY_ONLY_FOOD_CODES)
    with sqlite3.connect(database.path) as db:
        rows = db.execute(
            f"""
            SELECT i.canonical_code,
                   (SELECT COUNT(*) FROM food_nutrition_profiles p
                    WHERE p.food_ingredient_id = i.id),
                   (SELECT COUNT(*) FROM food_composition_versions c
                    WHERE c.food_ingredient_id = i.id),
                   (
                     SELECT COUNT(*)
                     FROM nutrition_vector_seals s
                     JOIN food_nutrition_profiles p2 ON p2.id = s.profile_id
                     WHERE p2.food_ingredient_id = i.id
                   )
            FROM food_ingredients i
            WHERE i.canonical_code IN ({placeholders})
            ORDER BY i.canonical_code
            """,
            IDENTITY_ONLY_FOOD_CODES,
        ).fetchall()
    assert len(rows) == 10
    assert all(row[1:] == (0, 0, 0) for row in rows)

    assert (
        migrations.expected_migration_ids()[-1]
        == "0042_recipe_prepared_output_nutrition"
    )


def test_r3d_source_partition_evidence_is_not_promoted(database):
    frozen, _, _ = _load_contract()
    publish_r3d_final_dc3_batch(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        for expected in frozen["selected"]:
            detail = catalogue.get_latest_verified(
                catalogue.get_by_code(expected["canonical_code"]).id
            )
            assert len(detail.ingredients) == len(expected["ingredients"])
            source_texts = tuple(row.source_amount_text for row in detail.ingredients)
            for intermediate in expected.get("source_intermediates", []):
                assert all(
                    intermediate["source_label"] not in text for text in source_texts
                )
            for alternative in expected.get("source_alternative_rows", []):
                assert all(
                    alternative["source_label"] not in text for text in source_texts
                )

        ragout = next(
            row
            for row in frozen["selected"]
            if row["canonical_code"] == "MR2019_2_11_BEEF_VEGETABLE_RAGOUT"
        )
        assert ragout["source_intermediates"][0] == {
            "source_label": "варка крупным куском",
            "quantity_g": "50",
            "semantic_role": "COOKED_MEAT_INTERMEDIATE",
            "interpretation_note": (
                "Semantic role records the reviewed meaning; source_label remains "
                "exact retained source text."
            ),
        }
        assert ragout["source_alternative_rows"][0]["source_label"] == (
            "или мясо бескостное"
        )
        assert ragout["source_alternative_rows"][0]["quantity_g"] == "81"
    finally:
        engine.dispose()


def test_r3d_publication_phase_keeps_all_recipes_inactive(database):
    result = publish_r3d_final_dc3_batch(database)

    assert tuple(code for code, _ in result.recipe_version_ids) == RECIPE_CODES
    assert r3d_recipe_states(database) == {code: 0 for code in sorted(RECIPE_CODES)}

    changed = activate_r3d_final_dc3_batch(database)
    assert changed is True
    assert r3d_recipe_states(database) == {code: 1 for code in sorted(RECIPE_CODES)}


def test_r3d_exact_full_replay_is_zero_write(database):
    seed_r3d_final_dc3_batch(database)
    before = db_dump(database)

    replay = seed_r3d_final_dc3_batch(database)

    assert replay.publication.identity_food_inserted == 0
    assert replay.publication.identity_food_existing == 10
    assert replay.activation_changed is False
    assert all(
        disposition == "EXACT_REPLAY"
        for _code, disposition in replay.publication.authority_dispositions
    )
    assert db_dump(database) == before


def test_r3d_preserves_deliberate_deactivation_in_prior_r3c_batch(database):
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        prior = catalogue.get_by_code(R3C_RECIPE_CODES[0])
        catalogue.deactivate(prior.id)
        assert catalogue.get_by_code(R3C_RECIPE_CODES[0]).is_active is False
    finally:
        engine.dispose()

    result = seed_r3d_final_dc3_batch(database)

    assert result.active_recipe_codes == RECIPE_CODES
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        assert catalogue.get_by_code(R3C_RECIPE_CODES[0]).is_active is False
    finally:
        engine.dispose()


def test_r3d_mixed_activation_state_fails_closed(database):
    seed_r3d_final_dc3_batch(database)
    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        recipe = catalogue.get_by_code(RECIPE_CODES[0])
        catalogue.deactivate(recipe.id)
    finally:
        engine.dispose()
    before = db_dump(database)

    with pytest.raises(PreparedRecipeActivationError, match="mixed active/inactive"):
        seed_r3d_final_dc3_batch(database)

    assert db_dump(database) == before
    states = r3d_recipe_states(database)
    assert states[RECIPE_CODES[0]] == 0
    assert sum(states.values()) == len(RECIPE_CODES) - 1


def test_r3d_partial_publication_failure_resumes_missing_recipes(database, monkeypatch):
    original = SqlAlchemyPreparedRecipeNutritionRepository.add_authority
    calls = 0

    def fail_fourth(self, authority):
        nonlocal calls
        calls += 1
        if calls == 4:
            raise RuntimeError("injected fourth publication failure")
        return original(self, authority)

    with monkeypatch.context() as scoped:
        scoped.setattr(
            SqlAlchemyPreparedRecipeNutritionRepository,
            "add_authority",
            fail_fourth,
        )
        with pytest.raises(RuntimeError, match="fourth publication"):
            publish_r3d_final_dc3_batch(database)

    assert r3d_counts(database) == {"recipes": 3, "authorities": 3, "values": 3}
    assert set(r3d_recipe_states(database).values()) == {0}

    resumed = seed_r3d_final_dc3_batch(database)
    dispositions = dict(resumed.publication.authority_dispositions)
    assert tuple(dispositions[code] for code in RECIPE_CODES[:3]) == (
        "EXACT_REPLAY",
        "EXACT_REPLAY",
        "EXACT_REPLAY",
    )
    assert all(dispositions[code] == "FRESH" for code in RECIPE_CODES[3:])
    assert resumed.active_recipe_codes == RECIPE_CODES


@pytest.mark.parametrize("failure_point", ("version", "values", "authority"))
def test_r3d_first_recipe_publication_failure_rolls_back_atomically(
    database,
    monkeypatch,
    failure_point,
):
    def fail(*args, **kwargs):
        del args, kwargs
        raise RuntimeError(f"injected {failure_point} failure")

    with monkeypatch.context() as scoped:
        if failure_point == "version":
            scoped.setattr(SqlAlchemyRecipeVersionRepository, "add_detail", fail)
        elif failure_point == "values":
            scoped.setattr(
                SqlAlchemyPreparedRecipeNutritionRepository,
                "add_values",
                fail,
            )
        else:
            scoped.setattr(
                SqlAlchemyPreparedRecipeNutritionRepository,
                "add_authority",
                fail,
            )
        with pytest.raises(RuntimeError, match=f"injected {failure_point}"):
            publish_r3d_final_dc3_batch(database)

    assert r3d_counts(database) == {"recipes": 0, "authorities": 0, "values": 0}
    placeholders = ",".join("?" for _ in IDENTITY_ONLY_FOOD_CODES)
    with sqlite3.connect(database.path) as db:
        count = db.execute(
            f"""
            SELECT COUNT(*) FROM food_ingredients
            WHERE canonical_code IN ({placeholders})
            """,
            IDENTITY_ONLY_FOOD_CODES,
        ).fetchone()[0]
    assert count == 10


def test_r3d_batch_activation_failure_rolls_back_every_staged_write(
    database,
    monkeypatch,
):
    publish_r3d_final_dc3_batch(database)
    original = SqlAlchemyRecipeRepository.set_active
    calls = 0

    def fail_fourth(self, recipe_id, *, active, updated_at):
        nonlocal calls
        calls += 1
        if calls == 4:
            raise RuntimeError("injected fourth activation failure")
        return original(self, recipe_id, active=active, updated_at=updated_at)

    monkeypatch.setattr(SqlAlchemyRecipeRepository, "set_active", fail_fourth)

    with pytest.raises(RuntimeError, match="fourth activation"):
        activate_r3d_final_dc3_batch(database)

    assert r3d_recipe_states(database) == {code: 0 for code in sorted(RECIPE_CODES)}


def test_r3d_partial_prepared_state_fails_closed(database):
    publish_r3d_final_dc3_batch(database)
    with sqlite3.connect(database.path) as db:
        raw_version_id = db.execute(
            """
            SELECT v.id
            FROM food_recipe_versions v
            JOIN food_recipes r ON r.id = v.recipe_id
            WHERE r.canonical_code = ?
            """,
            (RECIPE_CODES[0],),
        ).fetchone()[0]
        db.execute("DROP TRIGGER recipe_prepared_nutrition_authorities_no_delete")
        deleted = db.execute(
            """
            DELETE FROM recipe_prepared_nutrition_authorities
            WHERE recipe_version_id = ?
            """,
            (raw_version_id,),
        ).rowcount
        db.commit()
        assert deleted == 1
    before = db_dump(database)

    with pytest.raises(RecipeNutritionV2ConflictError, match="Partial persisted R3-D"):
        publish_r3d_final_dc3_batch(database)

    assert db_dump(database) == before


def test_r3d_identity_conflict_fails_closed(database):
    frozen, _, _ = _load_contract()
    identity = frozen["new_identity_only_foods"][0]
    engine = create_sqlite_engine(database)
    try:
        food = create_food_catalogue_service(engine)
        food.reconcile_identity_seed(
            (
                TrustedFoodIngredientIdentitySeed(
                    canonical_code=identity["canonical_code"],
                    canonical_name="Конфликтующее растительное масло",
                    category_code=identity["category_code"],
                    default_unit=identity["default_unit"],
                ),
            )
        )
    finally:
        engine.dispose()

    before = db_dump(database)
    with pytest.raises(FoodCatalogueConflictError):
        publish_r3d_final_dc3_batch(database)
    assert db_dump(database) == before


def test_r3d_wrong_prepared_energy_conflicts_with_exact_authority(database):
    publish_r3d_final_dc3_batch(database)
    frozen, _, bundle = _load_contract()
    _, specs = _recipe_seeds_and_specs(frozen, bundle)
    bad = replace(
        specs[0],
        expected_available_amounts=(("ENERGY_KCAL", Decimal(113)),),
    )

    engine = create_sqlite_engine(database)
    try:
        nutrition = create_recipe_nutrition_v2_service(engine)
        with pytest.raises(RecipeNutritionV2ConflictError):
            nutrition.publish_prepared(bad)
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    ("artifact_name", "old", "new"),
    (
        (
            FROZEN_BATCH_PATH.name,
            '"energy_kcal": "112"',
            '"energy_kcal": "113"',
        ),
        (
            FROZEN_BATCH_PATH.name,
            '"VEGETABLE_OIL_REFINED_UNSPECIFIED"',
            '"VEGETABLE_OIL_REFINED_FAKE"',
        ),
        (
            SUMMARY_PATH.name,
            '"active_exact_energy_count": 51',
            '"active_exact_energy_count": 52',
        ),
    ),
)
def test_r3d_hash_pinned_gate_rejects_tampered_artifact(
    tmp_path,
    artifact_name,
    old,
    new,
):
    package = tmp_path / "package"
    shutil.copytree(PACKAGE, package)
    artifact = package / artifact_name
    text = artifact.read_text()
    assert old in text
    artifact.write_text(text.replace(old, new, 1))

    with pytest.raises(ValueError, match="R3-D"):
        _load_contract(package)


def test_r3d_hash_pinned_mr_bundle_rejects_tamper(tmp_path):
    bundle = tmp_path / MR_BUNDLE_PATH.name
    shutil.copyfile(MR_BUNDLE_PATH, bundle)
    text = bundle.read_text()
    assert '"source_card_code": "1.2а"' in text
    bundle.write_text(
        text.replace('"source_card_code": "1.2а"', '"source_card_code": "1.2б"', 1)
    )

    with pytest.raises(ValueError, match="R3-D MR bundle changed"):
        _load_contract(bundle_path=bundle)


def test_r3d_russian_steps_household_and_branch_commitments(database):
    frozen, _, _ = _load_contract()
    publish_r3d_final_dc3_batch(database)
    expected_by_code = {row["canonical_code"]: row for row in frozen["selected"]}

    engine = create_sqlite_engine(database)
    try:
        catalogue = create_food_recipe_catalogue_service(engine)
        for code in RECIPE_CODES:
            expected = expected_by_code[code]
            detail = catalogue.get_latest_verified(catalogue.get_by_code(code).id)
            assert tuple(step.instruction for step in detail.steps) == tuple(
                expected["consumer_steps_ru"]
            )
            assert all(
                not re.search(r"[A-Za-z]{2,}", step.instruction)
                for step in detail.steps
            )
            assert expected["household_applicability"] == "REVIEWED_PASS"
            assert expected["specialized_medical_scope"] is False
            assert expected["household_rationale"]
            assert expected["quarantined_source_context"]
            assert "household=REVIEWED_PASS" in detail.version.change_note
            assert f"source_partition_sha256={_review_commitment(expected)}" in (
                detail.version.change_note
            )

        for code in (
            "MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP",
            "MR2019_1_3_LENINGRAD_RASSOLNIK_SOUR_CREAM",
            "MR2019_1_4_OAT_VEGETABLE_SOUP_SOUR_CREAM",
            "MR2019_1_16_POTATO_SPLIT_PEA_SOUP",
        ):
            assert (
                "LOW_ENERGY_SERVING_FEASIBILITY_REQUIRES_DC4"
                in (expected_by_code[code]["quarantined_source_context"])
            )
        for code in (
            "MR2019_2_15_STEAMED_CHICKEN_SOUFFLE",
            "MR2019_2_9_STEAMED_BEEF_ROLL_OMELET",
        ):
            assert (
                "DIETETIC_SOURCE_COLLECTION_PROVENANCE_ONLY_NO_THERAPEUTIC_CLAIM"
                in expected_by_code[code]["quarantined_source_context"]
            )
    finally:
        engine.dispose()


def test_r3d_planner_admission_reaches_51_exact_energy_and_33_main(database):
    seed_r3d_final_dc3_batch(database)
    engine = create_sqlite_engine(database)
    try:
        planner, _, _, catalogue = production_planner(engine)
        eligible = tuple(
            row for row in planner.compose_candidate_admission() if row.eligible
        )
        assert len(eligible) == 51
        assert Counter(row.meal_type_code for row in eligible) == Counter(
            {"breakfast": 17, "main": 33, "sandwich": 1}
        )
        selected = {
            row.canonical_code: row
            for row in eligible
            if row.canonical_code in RECIPE_CODES
        }
        assert tuple(code for code in RECIPE_CODES if code in selected) == RECIPE_CODES
        assert all(row.exact_energy_ready for row in selected.values())
        assert all(row.meal_type_code == "main" for row in selected.values())

        food = create_food_catalogue_service(engine)
        beef_id = food.get_by_code(BEEF_FOOD_CODE).id
        fish_ids = {
            food.get_by_code(code).id
            for code in FISH_FOOD_CODES
            if any(
                ingredient.food_ingredient_id == food.get_by_code(code).id
                for admission in eligible
                if admission.meal_type_code == "main"
                for ingredient in catalogue.get_current_verified(
                    admission.recipe_id
                ).ingredients
            )
        }
        chicken_ids = {
            food.get_by_code(code).id
            for code in CHICKEN_FOOD_CODES
            if any(
                ingredient.food_ingredient_id == food.get_by_code(code).id
                for admission in eligible
                if admission.meal_type_code == "main"
                for ingredient in catalogue.get_current_verified(
                    admission.recipe_id
                ).ingredients
            )
        }

        family_counts = Counter()
        for admission in eligible:
            if admission.meal_type_code != "main":
                continue
            detail = catalogue.get_current_verified(admission.recipe_id)
            ingredient_ids = {row.food_ingredient_id for row in detail.ingredients}
            if beef_id in ingredient_ids:
                family_counts["beef"] += 1
            elif ingredient_ids & fish_ids:
                family_counts["fish"] += 1
            elif ingredient_ids & chicken_ids:
                family_counts["chicken"] += 1
            else:
                family_counts["meat_free"] += 1

        assert family_counts == Counter(
            {"beef": 14, "fish": 9, "chicken": 4, "meat_free": 6}
        )
    finally:
        engine.dispose()


def test_r3d_current_planner_contract_supports_main():
    compatible = set().union(*ROLE_COMPATIBILITY_V1.values())
    assert MealTypeCode.MAIN in compatible
    assert MealTypeCode.MAIN in ROLE_COMPATIBILITY_V1[MealRole.DINNER]
    assert PlannerConfig().max_recipe_repetitions == 3


def test_r3d_hard_beef_exclusion_has_19_unaffected_main_and_persists_week(database):
    seed_r3d_final_dc3_batch(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, _ = create_role_household(
            households,
            meal_plans,
            MealRole.DINNER,
            "0.25",
        )
        beef_id = food.get_by_code(BEEF_FOOD_CODE).id

        main_admissions = tuple(
            row
            for row in planner.compose_candidate_admission()
            if row.eligible and row.meal_type_code == "main"
        )
        beef_dependent = []
        beef_unaffected = []
        for admission in main_admissions:
            detail = catalogue.get_current_verified(admission.recipe_id)
            ingredient_ids = {row.food_ingredient_id for row in detail.ingredients}
            target = beef_dependent if beef_id in ingredient_ids else beef_unaffected
            target.append(admission.canonical_code)

        assert len(main_admissions) == 33
        assert len(beef_dependent) == 14
        assert len(beef_unaffected) == 19
        assert len(beef_unaffected) * PlannerConfig().max_recipe_repetitions == 57

        request = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=frozenset({beef_id}),
                ),
            ),
        )
        result, detail = planner.generate_authoritative(request)
        assert isinstance(result, PlannerSuccess)
        assert detail is not None
        assert len(result.events) == 7

        versions = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in RECIPE_CODES
        }
        for code in (
            "MR2019_2_11_BEEF_VEGETABLE_RAGOUT",
            "MR2019_2_9_STEAMED_BEEF_ROLL_OMELET",
        ):
            traces = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert traces
            assert any(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
                for row in traces
            )

        persisted = meal_plans.get_current_plan(household.id, WEEK_START)
        assert len(persisted.events) == 7
        assert len(persisted.servings) == 7
    finally:
        engine.dispose()


def test_r3d_preserves_hard_milk_breakfast_capacity_nine(database):
    seed_r3d_final_dc3_batch(database)
    engine = create_sqlite_engine(database)
    try:
        planner, meal_plans, households, catalogue = production_planner(engine)
        food = create_food_catalogue_service(engine)
        household, member, _ = create_role_household(
            households,
            meal_plans,
            MealRole.BREAKFAST,
            "0.30",
        )
        milk_id = food.get_by_code(MILK_FOOD_CODE).id
        request = AuthoritativeGenerationRequest(
            household.id,
            WEEK_START,
            (
                GenerationMemberConstraints(
                    member.id,
                    excluded_food_ingredient_ids=frozenset({milk_id}),
                ),
            ),
        )

        result, detail = planner.generate_authoritative(request)
        assert isinstance(result, PlannerSuccess)
        assert detail is not None

        relevant_codes = set(R3B_RECIPE_CODES) | set(MILK_UNAFFECTED_BREAKFAST_CODES)
        admissions = {
            row.recipe_version_id: row
            for row in planner.compose_candidate_admission()
            if row.canonical_code in relevant_codes
        }
        selected = Counter(
            admissions[event.recipe_version_id].canonical_code
            for event in result.events
        )
        assert set(selected) == set(MILK_UNAFFECTED_BREAKFAST_CODES)
        assert sum(selected.values()) == 7
        assert max(selected.values()) <= 3

        versions = {
            code: catalogue.get_current_verified(
                catalogue.get_by_code(code).id
            ).version.id
            for code in relevant_codes
        }
        for code in R3B_RECIPE_CODES:
            traces = [
                row
                for row in result.trace.candidates
                if row.recipe_version_id == versions[code]
            ]
            assert traces
            assert any(
                PlannerRejectionCode.MEMBER_EXCLUDED_INGREDIENT in row.rejection_codes
                for row in traces
            )
    finally:
        engine.dispose()
