"""Explicit, offline, hash-pinned RU food seed; never called by historical loaders."""

import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig, REPOSITORY_ROOT
from app.domain.food_ingredients import normalize_unicode_search_key
from app.domain.nutrient_vector_backfill_v1 import prepare_profile, value_set_digest
from app.domain.ru_food_data import BASELINE_CHAINS, derive_readiness
from app.domain.ru_food_vector_import import prepare_reviewed_source
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.ru_food_data import SqlAlchemyRuFoodUnitOfWork
from app.services.ru_food_data import reconcile_ru_food_data

PACKAGE = REPOSITORY_ROOT / "data/curation/pr6-ru-food-data"
PACKAGE_SHA256: dict[str, str] = {
    "source-manifest.json": "a1f7238a161cca8b3752e2579032293462320686bb68aeaf6304002a906bc307",
    "market-evidence.json": "f6a43afba648f71652451f12e5e8b711afd83d19bd1d095144e51492b951661b",
    "food-readiness.json": "215aa5128ac406a69cb598a26c400987df0bb61d21c711885c99b657665be200",
    "research-log.json": "06d314500299071906632eb2944199e7de3e12082c61deca06e02c75fe222dc6",
}
PROMOTED = {"CAULIFLOWER_FROZEN": "170398", "STRAWBERRY_FROZEN_UNSWEETENED": "168173"}
CANDIDATES = {
    "APPLE_PEELED",
    "CAULIFLOWER_FROZEN",
    "LEMON_JUICE",
    "ORANGE_JUICE",
    "PASTA_COOKED",
    "SPINACH_BABY",
    "STRAWBERRY_FROZEN_UNSWEETENED",
}


def checked_json(path: Path, expected: str) -> dict[str, Any]:
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"Изменён проверенный файл данных: {path.name}.")
    return json.loads(payload)


def load_ru_food_entries(package: Path = PACKAGE) -> tuple[dict[str, Any], ...]:
    docs = {
        name: checked_json(package / name, digest)
        for name, digest in PACKAGE_SHA256.items()
    }
    manifest = docs["source-manifest.json"]
    for path, digest in manifest["protected_inputs"].items():
        if hashlib.sha256((REPOSITORY_ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError("Изменён исходный проверенный пакет данных.")
    bundle = {
        name: json.loads(
            (REPOSITORY_ROOT / "data/curation/pr6-nutrient-vector-a" / name).read_text()
        )
        for name in (
            "nutrient-registry.json",
            "source-mappings.json",
            "legacy-v1-crosswalk.json",
        )
    }
    market = docs["market-evidence.json"]
    if tuple(market["baseline_chains"]) != BASELINE_CHAINS:
        raise ValueError("Изменена базовая панель сетей.")
    evidence = {r["id"]: r for r in market["observations"]}
    if len(evidence) != len(market["observations"]):
        raise ValueError("Повторная запись рыночного доказательства.")
    rows = docs["food-readiness.json"]["rows"]
    codes = {r["food_code"] for r in rows}
    names = {normalize_unicode_search_key(r["canonical_name_ru"]) for r in rows}
    if len(codes) != len(rows) or len(names) != len(rows):
        raise ValueError("Повторный код или русское название продукта.")
    if {
        r["food_code"] for r in rows if r["population"] == "RESEARCH_CANDIDATE"
    } != CANDIDATES:
        raise ValueError("Изменён набор исследуемых форм.")
    if {r["food_code"] for r in rows if r["decision"] == "PROMOTE"} != set(PROMOTED):
        raise ValueError("Изменён набор утверждённых добавлений.")
    with (
        REPOSITORY_ROOT / "data/seed/food_ingredients/ingredients.csv"
    ).open() as stream:
        catalogue = {r["canonical_code"]: r for r in csv.DictReader(stream)}
    with (REPOSITORY_ROOT / "data/seed/food_ingredients/aliases.csv").open() as stream:
        alias_keys = {
            normalize_unicode_search_key(r["alias"]) for r in csv.DictReader(stream)
        }
    existing_names = {
        normalize_unicode_search_key(r["canonical_name"]) for r in catalogue.values()
    }
    entries = []
    for row in rows:
        linked = [evidence[key] for key in row["market_evidence_refs"]]
        if any(
            row.get(k) != value for k, value in derive_readiness(row, linked).items()
        ):
            raise ValueError(
                "Готовность или классификация противоречат доказательствам."
            )
        if row["decision"] == "PROMOTE":
            code = row["food_code"]
            key = normalize_unicode_search_key(row["canonical_name_ru"])
            if (
                code in catalogue
                or key in existing_names
                or key in alias_keys
                or code == row["parent_food_code"]
            ):
                raise ValueError("Новая форма конфликтует с исходным каталогом.")
        if row["final_readiness"] != "RU_READY":
            continue
        profile = {
            k: v
            for k, v in row["nutrition_profile_source"].items()
            if k not in {"source_description", "energy_nutrient_id"}
        }
        if row["decision"] == "PROMOTE":
            source = manifest["profiles"][PROMOTED[row["food_code"]]]
            legacy, values, observations = prepare_reviewed_source(
                source, bundle["source-mappings.json"]["mappings"]
            )
            if any(
                profile[k] != source[k]
                for k in (
                    "source_name",
                    "source_id",
                    "source_version",
                    "source_data_type",
                    "basis_grams",
                )
            ):
                raise ValueError("Профиль подменяет исходную пищевую идентичность.")
            if any(
                (None if profile[k] is None else Decimal(profile[k])) != v
                for k, v in legacy.items()
            ):
                raise ValueError("Поля Nutrition v1 не являются проекцией источника.")
        else:
            if (
                row["canonical_name_ru"]
                != catalogue[row["food_code"]]["canonical_name"]
            ):
                raise ValueError("Изменено существующее русское имя.")
            prepared = prepare_profile(profile, row["food_code"], bundle)
            if prepared is None:
                raise ValueError("Исходный профиль отсутствует в историческом аудите.")
            values, observations = prepared
        if row["vector_reference"] != {
            "value_count": len(values),
            "value_sha256": value_set_digest(values),
        }:
            raise ValueError("Ссылка на вектор не совпадает с источником.")
        for key in (
            "basis_grams",
            "kcal",
            "protein_g",
            "fat_g",
            "carbohydrates_g",
            "fiber_g",
        ):
            profile[key] = None if profile[key] is None else Decimal(profile[key])
        profile["verified_at"] = datetime.fromisoformat(profile["verified_at"])
        entries.append(
            {
                "row": row,
                "profile": profile,
                "values": values,
                "observations": observations,
                "category_code": catalogue[
                    row.get("parent_food_code", row["food_code"])
                ]["category_code"],
            }
        )
    return tuple(entries)


def seed_ru_food_data(
    config: DatabaseConfig | None = None, *, package: Path = PACKAGE
) -> dict[str, int]:
    entries = load_ru_food_entries(package)
    # The caller must have run migrations + accepted catalogue first. No migration,
    # historical seed or recipe action is hidden in this bounded operation.
    engine = create_sqlite_engine(config)
    try:
        return reconcile_ru_food_data(
            lambda: SqlAlchemyRuFoodUnitOfWork(engine), entries
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(json.dumps(seed_ru_food_data(), ensure_ascii=False, sort_keys=True))
