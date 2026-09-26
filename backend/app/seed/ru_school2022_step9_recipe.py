"""Hash-pinned Step 9 publication of one School2022 RecipeVersion."""

from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_composition import CompositionKind, CompositionStatus, MassState
from app.domain.nutrient_method_adapters import REGISTRY_V2
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_composition_scope import (
    SqlAlchemyCompositionReadScope,
)
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.services.food_composition import ApplicabilityAwareCompositionCalculator
from app.services.food_ingredients import FoodIngredientNotFoundError
from app.services.food_recipes import (
    RecipeSeedSummary,
    TrustedRecipeIngredientSeed,
    TrustedRecipeSeed,
    TrustedRecipeSeedDisposition,
    TrustedRecipeVersionSeed,
)

PACKAGE = REPOSITORY_ROOT / "data/curation/ru-school2022-step9-recipe-runtime"
PUBLICATION_SHA256 = "241bbd0dd2910317be0b65f46586b8e1f40cb06e3fbac1122b4ea1056c26e28f"

ARCHIVE_SHA256 = "c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea"
ARCHIVE_SIZE_BYTES = 206692075
SOURCE_JSON_SHA256 = "7de777b9ea0104e00bbb2e8cc98f2868bc6e5eead8a15b139d83706db765409b"
SCHOOL_PDF_SHA256 = "c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d"
SOURCE_URL = (
    "https://www.niig.su/images/documents/science/"
    "Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf"
)
RECIPE_CODE = "SCHOOL2022_53_19Z_BUTTER_PORTION"
FOOD_CODE = "BUTTER_PEASANT_72_5_UNSALTED"
SOURCE_RECIPE_ID = "ru-school2022:recipe:53-19з"
PROCESS_EVIDENCE_ID = "ru-school2022:recipe:53-19з:process-evidence:40"

LINEAGE = (
    (
        "normalized_card",
        SOURCE_RECIPE_ID,
        "9090bb6d28ad83808acdaef124ae79208fd280316452409f12249bad83c73f9c",
        "corpus-work/packages/school2022/normalized/recipes.jsonl",
    ),
    (
        "source_variant",
        "ru-school2022:recipe:53-19з:source-variant:1",
        "9a7e02487b9bd3d2b7fdac68c90f717701708ed68d0e7c421ad1631cbcae8f42",
        "corpus-work/packages/recipe-resolution/normalized/source-variants.jsonl",
    ),
    (
        "ingredient_demand",
        "ru-school2022:recipe:53-19з:row:1:demand:1",
        "f27dd3a8e156eb7c07cac9dd5460a29f0eda2b4a2efecc8b1c900ecacc71e164",
        "corpus-work/packages/recipe-resolution/normalized/ingredient-demands.jsonl",
    ),
    (
        "source_process",
        "ru-school2022:recipe:53-19з:source-process",
        "b9f4975ed8ed330464ed03fa8fffc713109dc5f10f6112695ee5e9cbc31c4f4e",
        "corpus-work/packages/recipe-closure/normalized/process-instructions.jsonl",
    ),
    (
        "process_evidence",
        PROCESS_EVIDENCE_ID,
        "5428e818127eceea1c69617e435666c6ce817666ba88bf7486b8c6ce4b60a6e4",
        "corpus-work/packages/school2022/normalized/process_evidence.jsonl",
    ),
    (
        "selection",
        "ru-school2022:recipe:53-19з:source-variant:1:selection:86446b0c327de7f405fe",
        "f0a235291eba3b04e370b39bb758b9f8e34d60dc9870c90e4b6798e47829bdbc",
        "corpus-work/packages/recipe-resolution/normalized/executable-selections.jsonl",
    ),
    (
        "resolved_route",
        (
            "ru-school2022:recipe:53-19з:source-variant:1:"
            "selection:86446b0c327de7f405fe:closure:route:"
            "4f53cda18c2baa0c0354bb5f"
        ),
        "a92d315561553a44b7f5ec6dd57d621aff73a8c471873eac5b1d7dbb89723a46",
        "corpus-work/packages/recipe-closure/normalized/resolved-executions.jsonl",
    ),
)

RIGHTS_BASIS = (
    "Нормативная рецептурная карта публикуется как фактические рецептурные данные "
    "по пользовательскому решению, зафиксированному в "
    "docs/family-food/ru-normative-recipe-corpus.md; сохраняются источник, версия, "
    "URL и SHA-256; фотографии, издательская вёрстка, логотипы и сторонние "
    "авторские комментарии не публикуются."
)

MATERIAL_STEPS = (
    "Термическая обработка не требуется.",
    "Нарезать сливочное масло на порционные кусочки.",
)

EXPECTED_RECIPE_AMOUNTS = {
    "ENERGY_KCAL": Decimal("66.09"),
    "PROTEIN": Decimal("0.08"),
    "FAT_TOTAL": Decimal("7.25"),
    "FATTY_ACIDS_SATURATED_TOTAL": Decimal("4.71"),
    "STARCH": Decimal("0.00"),
    "SUGARS_TOTAL": Decimal("0.13"),
    "FIBER_TOTAL_DIETARY": Decimal("0.00"),
    "VITAMIN_A_RE": Decimal("45.00"),
    "THIAMIN": Decimal("0.001"),
    "RIBOFLAVIN": Decimal("0.012"),
    "VITAMIN_C": Decimal("0.00"),
    "SODIUM": Decimal("1.50"),
    "POTASSIUM": Decimal("3.00"),
    "CALCIUM": Decimal("2.40"),
    "PHOSPHORUS": Decimal("3.00"),
    "IRON": Decimal("0.02"),
    "MAGNESIUM": Decimal("0.05"),
}


def _checked_json(path: Path, digest: str) -> Any:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Изменён проверенный файл данных: {path.name}.")
    return json.loads(raw)


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str) or not value or value.startswith("-"):
        raise ValueError(f"Поле {field} должно быть исходной Decimal-строкой.")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Поле {field} не является Decimal.") from exc
    if not result.is_finite() or result < 0 or format(result, "f") != value:
        raise ValueError(f"Поле {field} не является канонической Decimal-строкой.")
    return result


def _expected_lineage() -> list[dict[str, str]]:
    return [
        {
            "kind": kind,
            "id": record_id,
            "canonical_json_sha256": digest,
            "corpus_path": path,
        }
        for kind, record_id, digest, path in LINEAGE
    ]


def load_ru_school2022_step9_recipe_seed(
    package: Path = PACKAGE,
) -> tuple[TrustedRecipeSeed, dict[str, Any]]:
    publication = _checked_json(package / "publication.json", PUBLICATION_SHA256)
    if not isinstance(publication, dict) or publication.get("schema_version") != 1:
        raise ValueError("Неизвестный Step 9 publication payload.")

    source = publication.get("source")
    if source != {
        "archive_filename": "FamilyFoodOS-corpus-0.3.0-2026-09-20.zip",
        "archive_size_bytes": ARCHIVE_SIZE_BYTES,
        "archive_sha256": ARCHIVE_SHA256,
        "captured_date": "2026-09-20",
        "durable_private_locator": (
            "private-library:/FamilyFoodOS/source-artifacts/"
            "FamilyFoodOS-corpus-0.3.0-2026-09-20.zip"
        ),
        "latest_independent_verification_date": "2026-09-26",
        "official_url": SOURCE_URL,
        "pdf_sha256": SCHOOL_PDF_SHA256,
        "publisher": "Федеральный центр гигиены и эпидемиологии Роспотребнадзора",
        "source_id": "ru-school2022",
        "source_json_sha256": SOURCE_JSON_SHA256,
        "source_title": (
            "Сборник рецептур блюд и типовых меню для организации питания "
            "обучающихся 1—4-х классов в общеобразовательных организациях: Пособие"
        ),
        "year": 2022,
    }:
        raise ValueError("Step 9 source identity расходится с merged contract.")

    if publication.get("lineage") != _expected_lineage():
        raise ValueError("Step 9 source lineage изменён.")

    context = publication.get("institutional_context")
    if context != {
        "applicability": "institutional_school_catering_only",
        "consumer_recipe_step_promotion": False,
        "domestic_applicability": "unestablished",
        "home_storage_status": "not_granted",
        "not_executable_rule": True,
        "process_evidence_id": PROCESS_EVIDENCE_ID,
        "process_evidence_sha256": (
            "5428e818127eceea1c69617e435666c6ce817666ba88bf7486b8c6ce4b60a6e4"
        ),
        "refrigerated_holding_fact": (
            "Перед раздачей порционированное масло хранят в холодильнике."
        ),
        "serving_temperature_c": "14",
    }:
        raise ValueError("Step 9 institutional applicability context изменён.")

    nutrition = publication.get("nutrition_validation")
    if not isinstance(nutrition, dict):
        raise ValueError("Step 9 nutrition validation отсутствует.")
    if nutrition.get("food_ingredient_code") != FOOD_CODE:
        raise ValueError("Step 9 FoodIngredient dependency изменена.")
    if nutrition.get("composition_version") != 1:
        raise ValueError("Step 9 требует exact ATOMIC composition v1.")
    if nutrition.get("composition_input_state") != "INPUT":
        raise ValueError("Step 9 требует INPUT composition.")
    if nutrition.get("registry_version") != REGISTRY_V2:
        raise ValueError("Step 9 registry version изменена.")
    if nutrition.get("recipe_input_mass_g") != "10":
        raise ValueError("Step 9 recipe input должен быть exact 10 g.")
    if nutrition.get("composition_basis_g") != "100":
        raise ValueError("Step 9 composition basis должен быть exact 100 g.")
    if nutrition.get("scale_factor") != "0.1":
        raise ValueError("Step 9 scale factor должен быть exact 0.1.")
    if nutrition.get("water_state") != "unknown":
        raise ValueError("Step 9 WATER должен оставаться unknown.")
    if nutrition.get("canonical_total_carbohydrate_state") != "unknown":
        raise ValueError("Step 9 carbohydrate должен оставаться unknown.")
    if nutrition.get("source_declared_recipe_nutrition_authority") != "reference_only":
        raise ValueError("School2022 nutrition не является production authority.")
    amounts = nutrition.get("expected_recipe_amounts")
    if not isinstance(amounts, dict) or set(amounts) != set(EXPECTED_RECIPE_AMOUNTS):
        raise ValueError("Step 9 expected V2 nutrient set изменён.")
    parsed_amounts = {
        code: _decimal(value, field=code) for code, value in amounts.items()
    }
    if parsed_amounts != EXPECTED_RECIPE_AMOUNTS:
        raise ValueError("Step 9 expected V2 amounts изменены.")

    recipe = publication.get("recipe")
    if not isinstance(recipe, dict):
        raise ValueError("Step 9 Recipe payload отсутствует.")
    if recipe.get("canonical_code") != RECIPE_CODE:
        raise ValueError("Step 9 Recipe canonical code изменён.")
    if recipe.get("canonical_name") != "Масло сливочное (порциями)":
        raise ValueError("Step 9 Recipe canonical name изменён.")
    if recipe.get("initial_is_active") is not False:
        raise ValueError("Step 9 Recipe должен создаваться inactive.")

    version = recipe.get("version")
    if not isinstance(version, dict):
        raise ValueError("Step 9 RecipeVersion payload отсутствует.")
    if version.get("version_number") != 1:
        raise ValueError("Step 9 fresh RecipeVersion должен быть v1.")
    if version.get("steps") != list(MATERIAL_STEPS):
        raise ValueError("Step 9 material RecipeSteps изменены.")
    if version.get("equipment_codes") != []:
        raise ValueError("Step 9 не публикует equipment.")
    ingredient_rows = version.get("ingredients")
    if ingredient_rows != [
        {
            "food_ingredient_code": FOOD_CODE,
            "normalization_note": (
                "Recipe input uses source net 10 g; gross = net = 10 g; "
                "exact 72.5% unsalted form resolved by Step 8."
            ),
            "optional": False,
            "prep_note": None,
            "quantity": "10",
            "source_amount_text": "масло сливочное: брутто 10 г; нетто 10 г",
            "unit": "g",
        }
    ]:
        raise ValueError("Step 9 RecipeIngredient изменён.")

    expected_version = {
        "base_servings": "1",
        "batch_friendly": None,
        "change_note": (
            "Step 9 reviewed publication of School2022 53-19з; material "
            "preparation only; institutional holding/serving facts retained as "
            "source context."
        ),
        "cook_time_minutes": None,
        "difficulty_code": None,
        "equipment_codes": [],
        "freezable": None,
        "ingredients": ingredient_rows,
        "meal_type_code": "other",
        "prep_time_minutes": None,
        "rights_basis": RIGHTS_BASIS,
        "rights_review_status": "REVIEWED",
        "source_document_sha256": SCHOOL_PDF_SHA256,
        "source_name": "ru-school2022",
        "source_original_servings": "1",
        "source_recipe_id": SOURCE_RECIPE_ID,
        "source_retrieved_at": None,
        "source_url": SOURCE_URL,
        "source_version": f"sha256:{SCHOOL_PDF_SHA256}",
        "steps": list(MATERIAL_STEPS),
        "storage_days_freezer": None,
        "storage_days_fridge": None,
        "total_time_minutes": None,
        "verification_status": "SOURCE_VERIFIED",
        "verified_at": "2026-09-26T00:00:00Z",
        "version_number": 1,
    }
    if version != expected_version:
        raise ValueError("Step 9 RecipeVersion facts изменены.")

    seed = TrustedRecipeSeed(
        canonical_code=RECIPE_CODE,
        canonical_name="Масло сливочное (порциями)",
        version=TrustedRecipeVersionSeed(
            base_servings=Decimal("1"),
            meal_type_code="other",
            prep_time_minutes=None,
            cook_time_minutes=None,
            total_time_minutes=None,
            difficulty_code=None,
            batch_friendly=None,
            freezable=None,
            storage_days_fridge=None,
            storage_days_freezer=None,
            verification_status="SOURCE_VERIFIED",
            verified_at=datetime.fromisoformat("2026-09-26T00:00:00+00:00"),
            source_name="ru-school2022",
            source_recipe_id=SOURCE_RECIPE_ID,
            source_url=SOURCE_URL,
            source_version=f"sha256:{SCHOOL_PDF_SHA256}",
            source_retrieved_at=None,
            source_document_sha256=SCHOOL_PDF_SHA256,
            source_original_servings=Decimal("1"),
            rights_review_status="REVIEWED",
            rights_basis=RIGHTS_BASIS,
            change_note=expected_version["change_note"],
            ingredients=(
                TrustedRecipeIngredientSeed(
                    food_ingredient_code=FOOD_CODE,
                    quantity=Decimal("10"),
                    unit="g",
                    source_amount_text="масло сливочное: брутто 10 г; нетто 10 г",
                    normalization_note=ingredient_rows[0]["normalization_note"],
                    prep_note=None,
                    optional=False,
                ),
            ),
            steps=MATERIAL_STEPS,
            equipment_codes=(),
        ),
        initial_is_active=False,
    )
    return seed, publication


def _validate_step8_dependency(engine, publication: dict[str, Any]) -> None:
    try:
        food = create_food_catalogue_service(engine).get_by_code(FOOD_CODE)
    except FoodIngredientNotFoundError as exc:
        raise ValueError("Step 9 exact Step 8 FoodIngredient отсутствует.") from exc
    if not food.is_active:
        raise ValueError("Step 9 exact Step 8 FoodIngredient должен быть active.")

    nutrition = publication["nutrition_validation"]
    expected = {
        code: _decimal(value, field=code)
        for code, value in nutrition["expected_recipe_amounts"].items()
    }

    with SqlAlchemyCompositionReadScope(engine) as scope:
        composition = scope.compositions.find_version(food.id, 1)
        if composition is None:
            raise ValueError("Step 9 exact Step 8 ATOMIC composition v1 отсутствует.")
        if (
            composition.food_ingredient_id != food.id
            or composition.version != 1
            or composition.kind is not CompositionKind.ATOMIC
            or composition.input_state is not MassState.INPUT
        ):
            raise ValueError("Step 9 composition identity/state изменены.")
        result = ApplicabilityAwareCompositionCalculator(
            scope.compositions,
            scope.nutrient_vectors,
            scope.nutrient_registry,
        ).calculate(
            composition.id,
            registry_version=REGISTRY_V2,
            nutrient_codes=tuple(sorted(expected)),
        )

    if (
        result.status is not CompositionStatus.COMPLETE
        or result.input_mass_g != Decimal("100")
        or result.output_mass_g != Decimal("100")
        or result.output_mass_state is not MassState.INPUT
        or result.issues
    ):
        raise ValueError("Step 9 V2 composition calculation incomplete.")

    actual = {}
    for nutrient in result.nutrients:
        if nutrient.amount is None:
            raise ValueError("Step 9 V2 nutrient unexpectedly unknown.")
        actual[nutrient.definition.code] = nutrient.amount * Decimal("0.1")
    if actual != expected:
        raise ValueError("Step 9 deterministic 10 g V2 nutrition изменена.")


def seed_ru_school2022_step9_recipe(
    config: DatabaseConfig | None = None,
    *,
    package: Path = PACKAGE,
) -> RecipeSeedSummary:
    seed, publication = load_ru_school2022_step9_recipe_seed(package)
    engine = create_sqlite_engine(config)
    try:
        _validate_step8_dependency(engine, publication)
        service = create_food_recipe_catalogue_service(engine)
        disposition = service.preflight_trusted_seed(seed)
        result = service.reconcile_seed((seed,))
        if disposition is TrustedRecipeSeedDisposition.FRESH:
            if (
                result.recipes_inserted,
                result.versions_inserted,
                result.ingredients_inserted,
                result.steps_inserted,
                result.equipment_inserted,
            ) != (1, 1, 1, 2, 0):
                raise RuntimeError("Step 9 fresh publication result изменён.")
        else:
            if (
                result.recipes_inserted,
                result.versions_inserted,
                result.ingredients_inserted,
                result.steps_inserted,
                result.equipment_inserted,
            ) != (0, 0, 0, 0, 0):
                raise RuntimeError("Step 9 exact replay выполнил запись.")
        return result
    finally:
        engine.dispose()


if __name__ == "__main__":
    result = seed_ru_school2022_step9_recipe()
    print(
        json.dumps(
            {
                "equipment_inserted": result.equipment_inserted,
                "ingredients_inserted": result.ingredients_inserted,
                "recipes_inserted": result.recipes_inserted,
                "steps_inserted": result.steps_inserted,
                "versions_inserted": result.versions_inserted,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
