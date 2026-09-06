"""Bounded production B1 promotion loader; run after food and recipe seeds.

Research files are hash-verified at import time only. Calculation uses persisted
facts, never research JSON. No prerequisite catalogue data is silently remapped.
"""

from collections import Counter
from dataclasses import fields, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from app.db.config import DatabaseConfig
from app.domain.nutrition_evidence import (
    MeasureMassEvidence,
    RecipeIngredientNutritionAssessment,
)
from app.domain.units import UnitCode
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.nutrition_evidence_uow import (
    SqlAlchemyNutritionEvidenceUnitOfWork,
)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SEED_DIRECTORY = ROOT / "data/seed/nutrition_measure_evidence"
SOURCE_MAIN = "60908eb8270ef356eff8552855b4cc5d2aa9ee44"
SOURCE_PATHS = {
    f"data/curation/pr6-data-a/{name}.json"
    for name in ("conversion-gap-audit", "source-manifest", "summary")
}
INPUT_PATHS = {
    "data/seed/recipes/recipes.json",
    "data/seed/food_ingredients/nutrition.csv",
}
PROFILE_FIELDS = {
    "basis_grams",
    "kcal",
    "protein_g",
    "fat_g",
    "carbohydrates_g",
    "fiber_g",
    "source_name",
    "source_id",
    "source_version",
    "source_data_type",
    "verified_at",
    "estimated",
}
IDENTITY_FIELDS = {
    "recipe_canonical_code",
    "recipe_source_name",
    "recipe_source_id",
    "recipe_source_version",
    "ingredient_position",
    "food_ingredient_code",
    "recipe_quantity",
    "recipe_unit",
    "optional",
    "source_amount_text",
    "normalization_note",
    "prep_note",
    "profile",
    "evidence_key",
}
ASSESSMENT_FIELDS = {f.name for f in fields(RecipeIngredientNutritionAssessment)} - {
    "id",
    "recipe_ingredient_id",
    "nutrition_profile_id",
    "measure_evidence_id",
    "is_current",
}


class NutritionEvidenceSeedError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise NutritionEvidenceSeedError(message)


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _instant(value):
    _require(isinstance(value, str), "Timestamp must be text.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    _require(parsed.utcoffset() is not None, "Timestamp requires timezone.")
    return parsed


def _prototype(row):
    values = {k: row[k] for k in ASSESSMENT_FIELDS}
    values["issues"] = tuple(values["issues"])
    for name in ("reviewed_at", "created_at"):
        values[name] = _instant(values[name])
    return RecipeIngredientNutritionAssessment(
        id=uuid4(),
        recipe_ingredient_id=uuid4(),
        nutrition_profile_id=uuid4(),
        measure_evidence_id=uuid4() if row["evidence_key"] else None,
        is_current=True,
        **values,
    )


def load_seed_entries(seed_directory=DEFAULT_SEED_DIRECTORY, *, root=ROOT):
    """Validate the complete immutable promotion before opening a write scope."""
    try:
        manifest = _json(seed_directory / "manifest.json")
        _require(
            set(manifest)
            == {
                "schema_version",
                "source_operation",
                "source_merged_main",
                "source_sha256",
                "production_input_sha256",
                "payload_sha256",
                "evidence_count",
                "assessment_count",
                "issue_count",
                "status_counts",
                "issue_counts",
            },
            "Invalid manifest schema.",
        )
        _require(
            manifest["schema_version"] == 1
            and manifest["source_operation"] == "PR6-DATA-A"
            and manifest["source_merged_main"] == SOURCE_MAIN,
            "Promotion authority mismatch.",
        )
        for field, paths, base in (
            ("source_sha256", SOURCE_PATHS, root),
            ("production_input_sha256", INPUT_PATHS, root),
            ("payload_sha256", {"evidence.json", "assessments.json"}, seed_directory),
        ):
            _require(set(manifest[field]) == paths, "Invalid manifest hash inventory.")
            for name, digest in manifest[field].items():
                _require(
                    hashlib.sha256((base / name).read_bytes()).hexdigest() == digest,
                    "Promotion hash mismatch: " + name,
                )
        evidence_data, assessment_data = (
            _json(seed_directory / name)
            for name in ("evidence.json", "assessments.json")
        )
        _require(
            set(evidence_data) == {"schema_version", "evidence"}
            and evidence_data["schema_version"] == 1,
            "Invalid evidence schema.",
        )
        _require(
            set(assessment_data) == {"schema_version", "assessments"}
            and assessment_data["schema_version"] == 1,
            "Invalid assessment schema.",
        )
        evidence = []
        for row in evidence_data["evidence"]:
            _require(
                set(row) == {f.name for f in fields(MeasureMassEvidence)} - {"id"},
                "Invalid evidence fields.",
            )
            values = dict(row)
            for name in (
                "source_measure_amount",
                "normalized_input_quantity",
                "gram_weight",
            ):
                if values[name] is not None:
                    _require(
                        isinstance(values[name], str), "Source decimal must be text."
                    )
                    values[name] = Decimal(values[name])
            for name in ("created_at", "retrieved_at"):
                if values[name] is not None:
                    values[name] = _instant(values[name])
            evidence.append(MeasureMassEvidence(id=uuid4(), **values))
        evidence_map = {r.evidence_key: r for r in evidence}
        _require(
            len(evidence_map) == len(evidence) == manifest["evidence_count"],
            "Duplicate evidence key or count mismatch.",
        )
        rows = assessment_data["assessments"]
        identities = set()
        for row in rows:
            _require(
                set(row) == IDENTITY_FIELDS | ASSESSMENT_FIELDS,
                "Invalid assessment fields.",
            )
            prototype = _prototype(row)
            _require(
                row["assessment_version"] == 1
                and row["source_audit_operation"] == "PR6-DATA-A",
                "B1 promotion must retain DATA-A first review.",
            )
            _require(
                type(row["ingredient_position"]) is int
                and row["ingredient_position"] > 0
                and type(row["optional"]) is bool,
                "Invalid row position/optionality.",
            )
            _require(
                isinstance(row["recipe_quantity"], str)
                and Decimal(row["recipe_quantity"]).is_finite()
                and Decimal(row["recipe_quantity"]) > 0,
                "Invalid row quantity.",
            )
            UnitCode(row["recipe_unit"])
            for field in (
                "recipe_canonical_code",
                "recipe_source_name",
                "recipe_source_id",
                "recipe_source_version",
                "food_ingredient_code",
                "source_amount_text",
            ):
                _require(
                    isinstance(row[field], str) and row[field].strip(),
                    "Invalid stable row text: " + field,
                )
            for field in ("normalization_note", "prep_note"):
                _require(
                    row[field] is None or isinstance(row[field], str),
                    "Invalid row note.",
                )
            _require(
                set(row["profile"]) == PROFILE_FIELDS, "Invalid pinned profile schema."
            )
            _require(
                row["profile"]["estimated"] is None
                or type(row["profile"]["estimated"]) is bool,
                "Invalid profile estimation flag.",
            )
            for field, value in row["profile"].items():
                if field in (
                    "basis_grams",
                    "kcal",
                    "protein_g",
                    "fat_g",
                    "carbohydrates_g",
                    "fiber_g",
                ):
                    if field == "fiber_g" and value is None:
                        continue
                    _require(
                        isinstance(value, str), "Pinned profile decimal must be text."
                    )
                    parsed = Decimal(value)
                    _require(
                        parsed.is_finite() and parsed >= 0,
                        "Invalid pinned profile decimal.",
                    )
                elif field == "verified_at":
                    if value is not None:
                        _instant(value)
                elif field != "estimated":
                    _require(
                        isinstance(value, str) and value.strip(),
                        "Invalid profile provenance text.",
                    )
            stable_key = f"{row['recipe_canonical_code']}:{row['recipe_source_id']}:{row['recipe_source_version']}:{row['ingredient_position']}:{row['food_ingredient_code']}"
            _require(
                row["source_audit_key"] == stable_key and stable_key not in identities,
                "Duplicate/mismatched stable row identity.",
            )
            identities.add(stable_key)
            measure = evidence_map.get(row["evidence_key"])
            _require(
                row["evidence_key"] is None or measure is not None,
                "Unresolved seed evidence.",
            )
            if prototype.status_code == "APPROVED_EXACT":
                _require(
                    measure is not None
                    and not measure.estimated
                    and measure.normalized_input_unit == row["recipe_unit"],
                    "Invalid exact binding.",
                )
            if prototype.status_code == "APPROVED_NO_CONVERSION":
                _require(
                    row["recipe_unit"] == "g", "Non-gram approval without conversion."
                )
        _require(
            len(rows) == manifest["assessment_count"] == 189,
            "B1 requires 189 assessments.",
        )
        _require(
            Counter(r["status_code"] for r in rows) == manifest["status_counts"]
            and manifest["status_counts"].get("APPROVED_EXACT") == 66,
            "Assessment status count mismatch.",
        )
        issue_counts = Counter(i for r in rows for i in r["issues"])
        _require(
            issue_counts == manifest["issue_counts"]
            and sum(issue_counts.values()) == manifest["issue_count"],
            "Issue count mismatch.",
        )
        _require(
            {r["evidence_key"] for r in rows if r["evidence_key"]} == set(evidence_map),
            "Unselected evidence in promotion.",
        )
        return manifest, tuple(evidence), tuple(rows)
    except (OSError, KeyError, TypeError, ValueError, InvalidOperation) as exc:
        if isinstance(exc, NutritionEvidenceSeedError):
            raise
        raise NutritionEvidenceSeedError(
            "Invalid B1 production seed: " + str(exc)
        ) from exc


def _resolve(uow, descriptor, evidence):
    recipe = uow.recipes.get_by_code(descriptor["recipe_canonical_code"])
    _require(recipe is not None, "Unresolved recipe code.")
    detail = uow.versions.get_by_provenance(
        recipe.id,
        descriptor["recipe_source_name"],
        descriptor["recipe_source_id"],
        descriptor["recipe_source_version"],
    )
    current = uow.versions.get_current_verified(recipe.id)
    _require(
        detail is not None
        and current is not None
        and current.version.id == detail.version.id,
        "Pinned RecipeVersion is absent or no longer current.",
    )
    row = next(
        (
            r
            for r in detail.ingredients
            if r.position == descriptor["ingredient_position"]
        ),
        None,
    )
    food = uow.ingredients.get_by_code(descriptor["food_ingredient_code"])
    _require(
        row is not None and food is not None and row.food_ingredient_id == food.id,
        "Unresolved/mismatched ingredient row.",
    )
    for field, expected in (
        ("quantity", Decimal(descriptor["recipe_quantity"])),
        ("unit", descriptor["recipe_unit"]),
        ("optional", descriptor["optional"]),
        ("source_amount_text", descriptor["source_amount_text"]),
        ("normalization_note", descriptor["normalization_note"]),
        ("prep_note", descriptor["prep_note"]),
    ):
        _require(
            getattr(row, field) == expected, "Pinned RecipeIngredient differs: " + field
        )
    pinned = descriptor["profile"]
    profile = uow.nutrition_profiles.get_by_provenance(
        food.id, pinned["source_name"], pinned["source_id"], pinned["source_version"]
    )
    _require(
        profile is not None and profile.is_current,
        "Pinned FoodNutritionProfile is absent/stale.",
    )
    for field, value in pinned.items():
        if value is not None and field in (
            "basis_grams",
            "kcal",
            "protein_g",
            "fat_g",
            "carbohydrates_g",
            "fiber_g",
        ):
            value = Decimal(value)
        if value is not None and field == "verified_at":
            value = _instant(value)
        _require(
            getattr(profile, field) == value,
            "Pinned FoodNutritionProfile differs: " + field,
        )
    return replace(
        _prototype(descriptor),
        recipe_ingredient_id=row.id,
        nutrition_profile_id=profile.id,
        measure_evidence_id=None
        if descriptor["evidence_key"] is None
        else evidence[descriptor["evidence_key"]].id,
    )


def seed_nutrition_measure_evidence(
    config: DatabaseConfig | None = None,
    *,
    seed_directory: Path = DEFAULT_SEED_DIRECTORY,
):
    manifest, evidence, descriptors = load_seed_entries(seed_directory)
    engine = create_sqlite_engine(config)
    inserted_evidence = inserted_assessments = 0
    try:
        with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as uow:
            resolved_evidence = {}
            for item in evidence:
                existing = uow.evidence.get_by_key(item.evidence_key)
                if existing is None:
                    uow.evidence.add_evidence(item)
                    inserted_evidence += 1
                else:
                    _require(
                        replace(item, id=existing.id) == existing,
                        "Immutable evidence differs: " + item.evidence_key,
                    )
                    item = existing
                resolved_evidence[item.evidence_key] = item
            row_ids = set()
            for descriptor in descriptors:
                assessment = _resolve(uow, descriptor, resolved_evidence)
                _require(
                    assessment.recipe_ingredient_id not in row_ids,
                    "Stable descriptors resolve to duplicate local row.",
                )
                row_ids.add(assessment.recipe_ingredient_id)
                existing = uow.evidence.get_current_assessment(
                    assessment.recipe_ingredient_id
                )
                if existing is None:
                    uow.evidence.add_assessment(assessment)
                    inserted_assessments += 1
                else:
                    _require(
                        replace(assessment, id=existing.id) == existing,
                        "Existing review differs; B1 must not overwrite/rebind it.",
                    )
            uow.commit()
        return {
            k: manifest[k]
            for k in (
                "evidence_count",
                "assessment_count",
                "issue_count",
                "status_counts",
                "issue_counts",
            )
        } | {
            "inserted_evidence": inserted_evidence,
            "inserted_assessments": inserted_assessments,
            "resolved_current_rows": len(row_ids),
        }
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(json.dumps(seed_nutrition_measure_evidence(), sort_keys=True))
