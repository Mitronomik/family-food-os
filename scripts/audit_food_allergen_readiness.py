"""Whole-catalogue, source-safe allergen readiness and review-package preflight.

This developer tool NEVER publishes or changes FoodIngredient, RecipeVersion,
MealPlan, nutrition or customer data. It audits ALL canonical FoodIngredients
(not the first page of list_active) and exact current active recipe dependencies.

Persisted 'allergens_reviewed' is an observation, NOT proof that this database
stores review references. A separate immutable attestation contract is required
before source-backed bulk publication or revocation can be implemented.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
    SqlAlchemyFoodIngredientRepository,
)
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_ingredients_table,
)
from app.persistence.sqlalchemy_core.food_recipe_repositories import (
    SqlAlchemyRecipeRepository,
    SqlAlchemyRecipeVersionRepository,
)
from app.persistence.sqlalchemy_core.uow import SqlAlchemyReadOnlyScope
from app.seed.dc4_a3_russian_step_corrections import (
    seed_dc4_a3_russian_step_corrections,
)
from sqlalchemy import create_engine, select

SCHEMA = "FOOD_ALLERGEN_CATALOGUE_READINESS_V1"
PACKAGE_SCHEMA = "FOOD_ALLERGEN_REVIEW_PROPOSAL_V1"
CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class AllergenReadinessBlocked(ValueError):
    """Invalid source identity, incomplete review proposal or unsafe input."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise AllergenReadinessBlocked(reason)


def _digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def inventory_from_engine(engine) -> dict:
    """Read the full catalogue without pagination cutoff, N+1 authority writes or AI."""
    with SqlAlchemyReadOnlyScope(engine) as readonly:
        db = readonly.adapter_connection
        food_repo = SqlAlchemyFoodIngredientRepository(db)
        recipes = SqlAlchemyRecipeRepository(db)
        versions = SqlAlchemyRecipeVersionRepository(db)
        rows = (
            db.execute(
                select(food_ingredients_table.c.id).order_by(
                    food_ingredients_table.c.canonical_code
                )
            )
            .scalars()
            .all()
        )
        foods = [food_repo.get(food_id) for food_id in rows]
        _require(
            all(food is not None for food in foods),
            "Каталог содержит потерянный FoodIngredient.",
        )
        _require(
            len({food.canonical_code for food in foods}) == len(foods),
            "Canonical FoodIngredient identity конфликтует.",
        )
        by_id = {food.id: food for food in foods}
        used_by_active = defaultdict(set)
        used_by_any_version = defaultdict(set)
        historical_version_refs = defaultdict(list)
        recipe_rows = []
        for recipe in sorted(recipes.list_all(), key=lambda x: x.canonical_code):
            historical = versions.list_for_recipe(recipe.id)
            for version in historical:
                detail = versions.get_detail(version.id)
                _require(detail is not None, "Историческая RecipeVersion не читается.")
                for ingredient in detail.ingredients:
                    _require(
                        ingredient.food_ingredient_id in by_id,
                        "RecipeIngredient ссылается на отсутствующий FoodIngredient.",
                    )
                    used_by_any_version[ingredient.food_ingredient_id].add(
                        recipe.canonical_code
                    )
                    historical_version_refs[ingredient.food_ingredient_id].append(
                        (recipe.canonical_code, version.version_number, str(version.id))
                    )
            if not recipe.is_active:
                continue
            current = versions.get_current_verified(recipe.id)
            if current is None:
                recipe_rows.append(
                    {
                        "recipe_code": recipe.canonical_code,
                        "source_status": "NO_VERIFIED_RECIPE_VERSION",
                        "allergen_readiness": "BLOCKED",
                        "missing_food_codes": [],
                    }
                )
                continue
            ids = {row.food_ingredient_id for row in current.ingredients}
            for identity in ids:
                used_by_active[identity].add(recipe.canonical_code)
            blockers = sorted(
                by_id[identity].canonical_code
                for identity in ids
                if not by_id[identity].is_active
                or not by_id[identity].allergens_reviewed
            )
            recipe_rows.append(
                {
                    "recipe_code": recipe.canonical_code,
                    "source_status": "CURRENT_SOURCE_VERIFIED",
                    "allergen_readiness": "BLOCKED"
                    if blockers
                    else "RECORDED_REVIEW_COMPLETE",
                    "missing_food_codes": blockers,
                }
            )
        items = []
        for food in foods:
            status = (
                "UNKNOWN"
                if not food.allergens_reviewed
                else "RECORDED_REVIEWED_WITH_CODES"
                if food.allergen_codes
                else "RECORDED_REVIEWED_EMPTY_SET"
            )
            items.append(
                {
                    "canonical_code": food.canonical_code,
                    "canonical_name_ru": food.canonical_name,
                    "category_code": food.category_code,
                    "default_unit": food.default_unit.value,
                    "is_active": food.is_active,
                    "status": status,
                    "recorded_allergen_codes": list(food.allergen_codes),
                    "review_provenance_in_db": "NOT_STORED",
                    "active_recipe_codes": sorted(used_by_active[food.id]),
                    "historical_recipe_codes": sorted(used_by_any_version[food.id]),
                    "historical_recipe_versions": [
                        {"recipe_code": code, "version_number": number, "version_id": version_id}
                        for code, number, version_id in sorted(set(historical_version_refs[food.id]))
                    ],
                }
            )
    unknown = [row for row in items if row["status"] == "UNKNOWN"]
    active_unknown = [row for row in unknown if row["is_active"]]
    blocked = [r for r in recipe_rows if r["allergen_readiness"] == "BLOCKED"]
    evidence = {
        "schema": SCHEMA,
        "scope": "ALL_CANONICAL_FOOD_INGREDIENTS_AND_ALL_RECIPE_VERSIONS",
        "source": "PERSISTED_CATALOGUE_OBSERVATIONS_ONLY",
        "authority": "REVIEW_PROVENANCE_NOT_STORED_IN_CURRENT_SCHEMA",
        "summary": {
            "food_ingredients_total": len(items),
            "food_ingredients_active": sum(row["is_active"] for row in items),
            "food_ingredients_unknown": len(unknown),
            "active_food_ingredients_unknown": len(active_unknown),
            "unresolved_food_ingredients_total": len(unknown),
            "food_ingredients_with_recorded_review": len(items) - len(unknown),
            "recipes_active_total": len(recipe_rows),
            "active_recipes_blocked_for_composition": len(blocked),
            "active_recipes_with_recorded_allergen_coverage": len(recipe_rows)
            - len(blocked),
            "historical_food_dependencies_included": True,
        },
        "foods": items,
        "active_recipes": recipe_rows,
        "unresolved_queue": [
            {
                "canonical_code": row["canonical_code"],
                "canonical_name_ru": row["canonical_name_ru"],
                "active_recipe_codes": row["active_recipe_codes"],
                "reason": "ALLERGEN_REVIEW_NOT_RECORDED",
            }
            for row in unknown
        ],
        "active_unresolved_queue": [
            {"canonical_code": row["canonical_code"], "canonical_name_ru": row["canonical_name_ru"],
             "active_recipe_codes": row["active_recipe_codes"], "reason": "ALLERGEN_REVIEW_NOT_RECORDED"}
            for row in active_unknown
        ],
        "limitations": {
            "reviewed_empty_codes_means_no_allergies_of_any_kind": False,
            "review_source_provenance_verified": False,
            "ready_for_bulk_publication": False,
            "family_admission_granted": False,
            "new_identity_automatically_approved": False,
            "historical_versions_rewritten": False,
        },
    }
    return {**evidence, "semantic_sha256": _digest(evidence)}


def validate_review_proposals(report: dict, payload: dict) -> dict:
    """Preview a proposed review batch; NEVER authorize or publish its entries.

    Names/forms/units and source evidence are all required for any purported
    completed review. No generic food-name inference, empty-code assumption or
    source URL hash masquerading as source bytes is accepted.
    """
    _require(payload.get("schema") == PACKAGE_SCHEMA, "Неверная версия review-package.")
    entries = payload.get("entries")
    _require(isinstance(entries, list), "Entries должны быть массивом.")
    existing = {food["canonical_code"]: food for food in report["foods"]}
    seen = set()
    decisions = []
    for entry in entries:
        _require(isinstance(entry, dict), "Review entry должен быть объектом.")
        code = entry.get("canonical_code")
        _require(
            isinstance(code, str) and CODE_RE.fullmatch(code) is not None,
            "Недопустимый canonical_code.",
        )
        _require(code not in seen, "Повторяющийся canonical_code в review package.")
        seen.add(code)
        food = existing.get(code)
        _require(
            food is not None,
            "Неизвестный FoodIngredient: сначала проверенная публикация identity.",
        )
        _require(
            food["canonical_name_ru"] == entry.get("canonical_name_ru")
            and food["category_code"] == entry.get("category_code")
            and food["default_unit"] == entry.get("default_unit"),
            "FoodIngredient identity/form/unit изменена относительно каталога.",
        )
        state = entry.get("review_state")
        _require(
            state in ("UNKNOWN", "REVIEWED_WITH_CODES", "REVIEWED_EMPTY_SET"),
            "Неверный review_state.",
        )
        codes = entry.get("allergen_codes")
        _require(
            isinstance(codes, list)
            and all(isinstance(c, str) and CODE_RE.fullmatch(c) for c in codes)
            and len(set(codes)) == len(codes),
            "Аллергенные коды не являются точным нормализованным набором.",
        )
        _require(
            (state == "REVIEWED_WITH_CODES" and bool(codes))
            or (state in ("UNKNOWN", "REVIEWED_EMPTY_SET") and not codes),
            "Недопустимое сочетание review_state и аллергенов.",
        )
        if state != "UNKNOWN":
            proof = entry.get("evidence")
            _require(isinstance(proof, dict), "Проверенный статус требует evidence.")
            try:
                reviewed_at = datetime.fromisoformat(proof.get("reviewed_at", ""))
            except (TypeError, ValueError) as exc:
                raise AllergenReadinessBlocked(
                    "Не хватает действительной даты решения reviewer."
                ) from exc
            _require(
                reviewed_at.tzinfo is not None and reviewed_at.utcoffset() is not None,
                "Решение reviewer должно содержать часовой пояс.",
            )
            _require(
                isinstance(proof.get("source_name"), str)
                and bool(proof["source_name"].strip())
                and isinstance(proof.get("source_locator"), str)
                and proof["source_locator"].startswith(
                    ("https://", "http://", "private-library:")
                )
                and isinstance(proof.get("taxonomy_code"), str)
                and bool(proof["taxonomy_code"].strip())
                and isinstance(proof.get("taxonomy_version"), str)
                and bool(proof["taxonomy_version"].strip())
                and isinstance(proof.get("source_version"), str)
                and bool(proof["source_version"].strip())
                and isinstance(proof.get("source_sha256"), str)
                and SHA_RE.fullmatch(proof["source_sha256"]) is not None
                and isinstance(proof.get("review_reference"), str)
                and bool(proof["review_reference"].strip())
                and isinstance(proof.get("applicability"), str)
                and bool(proof["applicability"].strip()),
                "Не хватает версии/байтового SHA/применимости и review provenance.",
            )
        decisions.append(
            {
                "canonical_code": code,
                "proposal": state,
                "current_status": food["status"],
                "publication": "NOT_AUTHORIZED_REVIEW_ONLY",
            }
        )
    _require(
        report["limitations"]["ready_for_bulk_publication"] is False,
        "Read-only audit нельзя считать bulk publisher.",
    )
    return {
        "schema": PACKAGE_SCHEMA,
        "status": "STRUCTURALLY_CHECKED_NOT_APPROVED",
        "entries": sorted(decisions, key=lambda row: row["canonical_code"]),
        "publication_performed": False,
        "mutation_performed": False,
    }


def audit_catalogue(*, sqlite_path: Path | None = None) -> dict:
    """Default is a reproducible real-seed DB; supplied existing DB stays read-only."""
    if sqlite_path is None:
        with tempfile.TemporaryDirectory(prefix="familyfood-allergen-audit-") as temp:
            config = DatabaseConfig(path=Path(temp) / "seed.sqlite")
            seed_dc4_a3_russian_step_corrections(config)
            engine = create_sqlite_engine(config)
            try:
                return inventory_from_engine(engine)
            finally:
                engine.dispose()
    path = Path(sqlite_path)
    _require(path.is_file(), "Указанная SQLite-база должна уже существовать.")
    # Enforce read-only in the SQLite driver, not merely by avoiding explicit writes.
    # The normal project engine creates directories and opens a writable connection.
    uri = path.resolve().as_uri() + "?mode=ro"
    engine = create_engine(
        "sqlite+pysqlite://",
        creator=lambda: sqlite3.connect(uri, uri=True, autocommit=False),
    )
    try:
        return inventory_from_engine(engine)
    finally:
        engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only full-catalogue allergen readiness and source review backlog"
    )
    parser.add_argument("--sqlite", type=Path)
    parser.add_argument("--review-proposal", type=Path)
    args = parser.parse_args()
    report = audit_catalogue(sqlite_path=args.sqlite)
    if args.review_proposal:
        proposal = json.loads(args.review_proposal.read_text(encoding="utf-8"))
        report["review_proposal_preview"] = validate_review_proposals(report, proposal)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
