"""Explicit offline upgrade of a populated 0029 catalogue in one project UoW.

Historical seed loaders remain historical. This command is the bounded data
upgrade, also run once after the accepted seed chain on fresh installations.
"""

from dataclasses import asdict, replace
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.b2b2_vector_import import prepare_reviewed_source
from app.domain.food_composition import (
    CompositionKind,
    CompositionProvenance,
    FoodCompositionVersion,
    MassState,
)
from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.nutrition_evidence import MeasureMassEvidence
from app.domain.units import UnitCode
from app.domain.nutrient_vector_backfill_v1 import canonical_json, value_set_digest
from app.persistence.sqlalchemy_core.b2b2 import B2B2UnitOfWork
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.services.food_composition import CompositionCalculator

PACKAGE = REPOSITORY_ROOT / "data/curation/pr6-data-b2-b2-redesigned"
OPERATION = "PR6-DATA-B2-B2-REDESIGNED"
REVIEWED_AT = datetime.fromisoformat("2026-09-12T06:42:55+00:00")
MANIFEST_SHA256 = "d3c8c77af07479b589b2e72e6105558df35eeffaf43f5b473fa26cbef39a3ec6"
PROMOTED = {"MAYONNAISE_LOW_FAT": "173594", "OATS_ROLLED": "173904", "TOMATO": "170457"}
REMAPS = {
    "SNAP2_SIMPLE_GREEN_SMOOTHIE": "STRAWBERRY_FROZEN_UNSWEETENED",
    "WIC2_SPINACH_CAULIFLOWER_SMOOTHIE": "CAULIFLOWER_FROZEN",
}


def require(condition: Any, message: str) -> None:
    if not condition:
        raise ValueError(message)


def plain(value: Any) -> Any:
    return json.loads(
        json.dumps(
            value,
            default=lambda v: v.isoformat() if isinstance(v, datetime) else str(v),
        )
    )


def facts(value: Any, *excluded: str) -> dict[str, Any]:
    return plain({k: v for k, v in asdict(value).items() if k not in excluded})


def profile_facts(profile: FoodNutritionProfile) -> dict[str, Any]:
    return facts(profile, "id", "food_ingredient_id", "created_at", "is_current")


def assessment_facts(assessment: Any, evidence: Any) -> dict[str, Any]:
    return facts(
        assessment,
        "id",
        "recipe_ingredient_id",
        "nutrition_profile_id",
        "measure_evidence_id",
        "is_current",
    ) | {
        "evidence_key": None if evidence is None else evidence.evidence_key,
    }


def row_facts(uow: Any, detail: Any, row: Any) -> dict[str, Any]:
    food = uow.ingredients.get(row.food_ingredient_id)
    profile = uow.nutrition_profiles.get_current(food.id)
    assessment = uow.evidence.get_current_assessment(row.id)
    require(
        profile is not None and assessment is not None,
        "Нет проверенного профиля или оценки строки.",
    )
    require(
        assessment.nutrition_profile_id == profile.id,
        "Оценка строки ссылается на устаревший профиль.",
    )
    evidence = (
        None
        if assessment.measure_evidence_id is None
        else uow.evidence.get_evidence(assessment.measure_evidence_id)
    )
    return {
        "identity": f"{detail.recipe.canonical_code}:v{detail.version.version_number}:{row.position}",
        "row": facts(
            row, "id", "recipe_version_id", "food_ingredient_id", "created_at"
        ),
        "food": facts(food, "id", "created_at", "updated_at"),
        "profile": profile_facts(profile),
        "assessment": assessment_facts(assessment, evidence),
        "source": {
            k: v for k, v in facts(detail.version).items() if k.startswith("source_")
        },
    }


def detail_facts(uow: Any, detail: Any) -> dict[str, Any]:
    return {
        "recipe": facts(detail.recipe, "id", "created_at", "updated_at"),
        "version": facts(
            detail.version, "id", "recipe_id", "created_at", "created_from_version_id"
        ),
        "ingredients": [
            facts(r, "id", "recipe_version_id", "food_ingredient_id", "created_at")
            | {"food_code": uow.ingredients.get(r.food_ingredient_id).canonical_code}
            for r in detail.ingredients
        ],
        "steps": [
            facts(r, "id", "recipe_version_id", "created_at") for r in detail.steps
        ],
        "equipment": [facts(r, "recipe_version_id") for r in detail.equipment],
    }


def load_package(package: Path = PACKAGE) -> dict[str, Any]:
    raw = (package / "manifest.json").read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == MANIFEST_SHA256,
        "Изменён манифест проверенной операции.",
    )
    manifest = json.loads(raw)
    for name, digest in manifest["protected_inputs"].items():
        require(
            hashlib.sha256((REPOSITORY_ROOT / name).read_bytes()).hexdigest() == digest,
            "Изменён исходный проверенный пакет.",
        )
    docs = {}
    for name, digest in manifest["payload_sha256"].items():
        raw = (package / name).read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == digest,
            "Изменены проверенные решения операции.",
        )
        docs[name] = json.loads(raw)
    require(
        {
            r["food_code"]: r["source_id"]
            for r in docs["profile-decisions.json"]["decisions"]
            if r["decision"] == "PROMOTE"
        }
        == PROMOTED,
        "Изменён набор разрешённых профилей.",
    )
    mappings = json.loads(
        (
            REPOSITORY_ROOT / "data/curation/pr6-nutrient-vector-a/source-mappings.json"
        ).read_text()
    )["mappings"]
    prepared = {}
    for code, sid in PROMOTED.items():
        source = docs["source-manifest.json"]["profiles"][sid]
        legacy, values, observations = prepare_reviewed_source(source, mappings)
        profile = dict(
            legacy,
            basis_grams=Decimal("100"),
            source_name="USDA_FDC",
            source_id=sid,
            source_version="2018-04",
            source_data_type="SR Legacy",
            verified_at=REVIEWED_AT,
            estimated=None,
        )
        prepared[code] = (profile, values, observations)
    docs["prepared"] = prepared
    docs["frozen_authorities"] = [
        row
        for row in json.loads(
            (
                REPOSITORY_ROOT / "data/curation/pr6-ru-food-data/food-readiness.json"
            ).read_text()
        )["rows"]
        if row["food_code"] in REMAPS.values()
    ]
    return docs


def _revision(uow: Any, parent: Any, food_code: str) -> Any:
    key = uuid4()
    food = uow.ingredients.get_by_code(food_code)
    require(food is not None, "Утверждённая замороженная форма отсутствует.")
    return replace(
        parent,
        version=replace(
            parent.version,
            id=key,
            version_number=2,
            created_from_version_id=parent.version.id,
            created_at=REVIEWED_AT,
            change_note="Проверенное исправление формы ингредиента 6; исходный документ и количества сохранены.",
        ),
        ingredients=tuple(
            replace(
                r,
                id=uuid4(),
                recipe_version_id=key,
                created_at=REVIEWED_AT,
                food_ingredient_id=food.id if r.position == 6 else r.food_ingredient_id,
            )
            for r in parent.ingredients
        ),
        steps=tuple(
            replace(r, id=uuid4(), recipe_version_id=key, created_at=REVIEWED_AT)
            for r in parent.steps
        ),
        equipment=tuple(replace(r, recipe_version_id=key) for r in parent.equipment),
    )


def _evidence(
    source: dict[str, Any], portion: dict[str, str], normalized: str
) -> MeasureMassEvidence:
    return MeasureMassEvidence(
        id=uuid4(),
        evidence_key=f"B2B2:FDC-{source['source_id']}:PORTION-{portion['id']}:exact",
        source_name="USDA FoodData Central",
        source_type="FOOD_PORTION",
        source_id=source["source_id"],
        source_version=source["source_version"],
        source_url=f"https://fdc.nal.usda.gov/food-details/{source['source_id']}/nutrients",
        food_description=source["food"]["description"],
        form_modifier=portion["modifier"],
        edible_basis="Edible input; exact reviewed source food and household measure; excludes refuse.",
        source_measure_amount=Decimal(portion["amount"]),
        source_measure_text=portion["modifier"],
        normalized_input_quantity=Decimal(normalized),
        normalized_input_unit=UnitCode.MILLILITER,
        gram_weight=Decimal(portion["gram_weight"]),
        evidence_quality="OFFICIAL_EXACT_SAME_FOOD_FORM_PORTION",
        estimated=False,
        retrieved_at=None,
        created_at=REVIEWED_AT,
    )


def reconcile(uow: Any, docs: dict[str, Any]) -> dict[str, int]:
    plan = docs["plan.json"]
    # Validate the exact PR28 prerequisites, including the sealed authority path.
    # A partially provisioned catalogue cannot publish a recipe-only correction.
    for authority in docs["frozen_authorities"]:
        food = uow.ingredients.get_by_code(authority["food_code"])
        require(food is not None, "Отсутствует утверждённая замороженная форма.")
        source = authority["nutrition_profile_source"]
        profile = uow.nutrition_profiles.get_by_provenance(
            food.id,
            source["source_name"],
            source["source_id"],
            source["source_version"],
        )
        require(
            profile is not None and profile.is_current,
            "Нет текущего утверждённого профиля замороженной формы.",
        )
        vector = uow.nutrient_vectors.get(profile.id)
        actual_values = [
            {
                "nutrient_code": v.definition.code,
                "amount": v.amount,
                "provenance_json": v.provenance.evidence_json,
            }
            for v in vector.values
        ]
        require(
            authority["vector_reference"]
            == {
                "value_count": len(actual_values),
                "value_sha256": value_set_digest(actual_values),
            },
            "Вектор замороженной формы отличается от утверждённого.",
        )
        composition = uow.compositions.find_version(food.id, 1)
        require(
            composition is not None
            and composition.kind == CompositionKind.ATOMIC
            and composition.profile_id == profile.id
            and composition.input_state == authority["mass_state"],
            "Нет утверждённого состава замороженной формы.",
        )
    counts = dict(
        recipe_versions=0,
        profiles=0,
        nutrient_values=0,
        vector_seals=0,
        compositions=0,
        evidence=0,
        assessments=0,
    )
    details = uow.current_details()
    by_code = {d.recipe.canonical_code: d for d in details}
    # Full all-use coverage, including non-target uses; fail closed on additional uses.
    actual = sorted(
        [
            row_facts(uow, d, r)
            for d in details
            for r in d.ingredients
            if uow.ingredients.get(r.food_ingredient_id).canonical_code
            in plan["impact_food_codes"]
        ],
        key=lambda r: r["identity"],
    )
    already = actual == plan["after"]
    require(
        already or actual == plan["before"],
        "Текущий набор использований или его авторитетные данные изменились; требуется повторное ревью.",
    )
    for code in REMAPS:
        history = uow.versions.list_for_recipe(by_code[code].recipe.id)
        parent = uow.versions.get_detail(history[0].id)
        require(
            parent.version.created_from_version_id is None
            and detail_facts(uow, parent) == plan["recipe_parents"][code],
            "Исходная версия рецепта изменена.",
        )
        if already:
            require(
                len(history) == 2
                and by_code[code].version.created_from_version_id == parent.version.id
                and detail_facts(uow, by_code[code]) == plan["recipe_revisions"][code],
                "Исправленная версия рецепта не соответствует проверенной.",
            )
        else:
            require(len(history) == 1, "Обнаружена непроверенная версия рецепта.")

    # Every required current use and its final assessment was checked before writes.
    for code, (profile_data, values, observations) in docs["prepared"].items():
        food = uow.ingredients.get_by_code(code)
        expected = FoodNutritionProfile(
            id=uuid4(),
            food_ingredient_id=food.id,
            is_current=True,
            created_at=REVIEWED_AT,
            **profile_data,
        )
        profile = uow.nutrition_profiles.get_by_provenance(
            food.id, expected.source_name, expected.source_id, expected.source_version
        )
        if not already:
            require(
                profile is None,
                "Замещающий профиль уже существует вне проверенной операции.",
            )
            uow.nutrition_profiles.clear_current(food.id)
            profile = expected
            uow.nutrition_profiles.add(profile)
            uow.publish_vector(profile, values, observations)
            counts["profiles"] += 1
            counts["nutrient_values"] += len(values)
            counts["vector_seals"] += 1
        require(
            profile is not None
            and profile.is_current
            and profile_facts(profile) == profile_facts(expected),
            "Текущий профиль не соответствует проверенному.",
        )
        vector = uow.nutrient_vectors.get(profile.id)
        require(
            vector.observations_json == observations
            and value_set_digest(
                [
                    {
                        "nutrient_code": v.definition.code,
                        "amount": v.amount,
                        "provenance_json": v.provenance.evidence_json,
                    }
                    for v in vector.values
                ]
            )
            == value_set_digest(values),
            "Запечатанный вектор не соответствует источнику.",
        )
        expected_composition = FoodCompositionVersion(
            id=uuid4(),
            food_ingredient_id=food.id,
            version=plan["composition_versions"][code],
            kind=CompositionKind.ATOMIC,
            input_state=MassState.INPUT,
            profile_id=profile.id,
            provenance=CompositionProvenance(
                OPERATION,
                "1",
                f"data/curation/pr6-data-b2-b2-redesigned/profile-decisions.json#{code}",
                f"{OPERATION}:{code}",
            ),
        )
        composition = uow.compositions.find_version(
            food.id, expected_composition.version
        )
        if not already:
            require(
                composition is None,
                "Версия состава уже существует вне проверенной операции.",
            )
            uow.compositions.add_versions((expected_composition,))
            composition = expected_composition
            counts["compositions"] += 1
        require(
            composition is not None
            and composition == replace(expected_composition, id=composition.id),
            "Состав не закрепляет проверенный профиль.",
        )
        CompositionCalculator(uow.compositions, uow.nutrient_vectors).calculate(
            composition.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN", "CALCIUM")
        )

    if already:
        _verify_mass_evidence(uow, docs)
        _verify_publications(uow, by_code, plan)
        return counts
    for code, food_code in REMAPS.items():
        revised = _revision(uow, by_code[code], food_code)
        require(
            detail_facts(uow, revised) == plan["recipe_revisions"][code],
            "Ревизия изменяет непроверенные поля.",
        )
        uow.versions.add_detail(revised)
        by_code[code] = revised
        counts["recipe_versions"] += 1
    exact = {}
    for entry in plan["mass_evidence"]:
        source = docs["source-manifest.json"]["profiles"][entry["source_id"]]
        portion = next(p for p in source["portions"] if p["id"] == entry["portion_id"])
        value = _evidence(source, portion, entry["normalized_input_quantity"])
        require(
            uow.evidence.get_by_key(value.evidence_key) is None,
            "Новое доказательство уже существует вне проверенной операции.",
        )
        uow.evidence.add_evidence(value)
        exact[value.evidence_key] = value
        counts["evidence"] += 1
    for entry in plan["assessment_publications"]:
        code, position = entry["recipe_code"], entry["position"]
        detail = by_code[code]
        row = detail.ingredients[position - 1]
        parent_detail = next(d for d in details if d.recipe.canonical_code == code)
        parent_row = parent_detail.ingredients[position - 1]
        old = uow.evidence.get_current_assessment(parent_row.id)
        food = uow.ingredients.get(row.food_ingredient_id)
        profile = uow.nutrition_profiles.get_current(food.id)
        expected = entry["assessment"]
        key = expected["evidence_key"]
        evidence = (
            None if key is None else exact.get(key) or uow.evidence.get_by_key(key)
        )
        require(
            key is None or evidence is not None,
            "Отсутствует закреплённое доказательство массы.",
        )
        assessment = replace(
            old,
            id=uuid4(),
            recipe_ingredient_id=row.id,
            nutrition_profile_id=profile.id,
            measure_evidence_id=None if evidence is None else evidence.id,
            **{
                k: tuple(v)
                if k == "issues"
                else datetime.fromisoformat(v)
                if k in ("reviewed_at", "created_at")
                else v
                for k, v in expected.items()
                if k != "evidence_key"
            },
        )
        uow.evidence.add_assessment(assessment)
        counts["assessments"] += 1
    after = sorted(
        [
            row_facts(uow, d, r)
            for d in uow.current_details()
            for r in d.ingredients
            if uow.ingredients.get(r.food_ingredient_id).canonical_code
            in plan["impact_food_codes"]
        ],
        key=lambda r: r["identity"],
    )
    require(after == plan["after"], "Итог операции расходится с проверенным планом.")
    _verify_mass_evidence(uow, docs)
    _verify_publications(uow, by_code, plan)
    return counts


def _verify_mass_evidence(uow: Any, docs: dict[str, Any]) -> None:
    for entry in docs["plan.json"]["mass_evidence"]:
        source = docs["source-manifest.json"]["profiles"][entry["source_id"]]
        portion = next(p for p in source["portions"] if p["id"] == entry["portion_id"])
        expected = _evidence(source, portion, entry["normalized_input_quantity"])
        actual = uow.evidence.get_by_key(expected.evidence_key)
        require(
            actual is not None and actual == replace(expected, id=actual.id),
            "Доказательство массы отличается от проверенного источника.",
        )


def _verify_publications(
    uow: Any, details: dict[str, Any], plan: dict[str, Any]
) -> None:
    """Also verify carried-forward rows outside the 46-use food universe."""
    for entry in plan["assessment_publications"]:
        detail = details[entry["recipe_code"]]
        row = detail.ingredients[entry["position"] - 1]
        actual = row_facts(uow, detail, row)
        require(
            actual["assessment"] == entry["assessment"],
            "Опубликованная оценка строки отличается от проверенной.",
        )


def upgrade_b2b2(
    config: DatabaseConfig | None = None, *, package: Path = PACKAGE
) -> dict[str, int]:
    docs = load_package(package)
    engine = create_sqlite_engine(config)
    try:
        with B2B2UnitOfWork(engine) as uow:
            counts = reconcile(uow, docs)
            uow.commit()
        return counts
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(canonical_json(upgrade_b2b2()))
