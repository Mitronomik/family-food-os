"""Verify retained Assembly A preflight evidence, never publish culinary truth.

Exit 0 means the BLOCKED research package is internally consistent. It does not
mean the three-template production acceptance gate passed. Optional --database
reproduces accepted PR6 evidence using existing loaders in a temporary DB only.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/recipe-assembly-a"


def read(path: Path):
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_database() -> None:
    sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]
    from app.db.config import DatabaseConfig
    from audit_pr6_close import encode, measure

    with TemporaryDirectory() as directory:
        reports = measure(DatabaseConfig(path=Path(directory) / "preflight.sqlite"))
    for name in ("recipe-readiness.json", "food-readiness.json"):
        require(
            encode(reports[name])
            == (ROOT / "data/curation/pr6-close" / name).read_text(),
            f"Базовый отчёт не воспроизводится: {name}",
        )
    summary = reports["closure-evidence.json"]
    print(
        json.dumps(
            dict(
                accepted_baseline_database="PASS",
                migration_head=summary["migration_head"],
                reports_byte_identical=True,
                non_executable_estimates=len(summary["estimate_usages_non_executable"]),
                historical_replay=summary["historical_replay"],
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    args = parser.parse_args()
    manifest = read(PACKAGE / "source-manifest.json")
    for item in manifest["input_files"]:
        require(
            hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
            == item["sha256"],
            f"Исходные доказательства изменились: {item['path']}",
        )
    for name, digest in read(PACKAGE / "checksums.json")["files"].items():
        require(
            hashlib.sha256((PACKAGE / name).read_bytes()).hexdigest() == digest,
            f"Пакет доказательств изменился: {name}",
        )
    recipes = read(ROOT / "data/curation/pr6-close/recipe-readiness.json")["recipes"]
    foods = {
        item["food_code"]: item
        for item in read(ROOT / "data/curation/pr6-close/food-readiness.json")["foods"]
    }
    review = read(PACKAGE / "candidate-review.json")
    expected = []
    for recipe in recipes:
        rows = [row for row in recipe["rows"] if not row["optional"]]
        missing_mass = [row["identity"] for row in rows if row["mass_g"] is None]
        missing_composition = sorted(
            {
                row["food_code"]
                for row in rows
                if foods[row["food_code"]]["composition_version"] is None
            }
        )
        expected.append(
            dict(
                recipe_code=recipe["recipe_code"],
                current_version=recipe["current_version"],
                source_provenance=recipe["source_provenance"],
                required_row_count=len(rows),
                missing_required_mass_rows=missing_mass,
                required_foods_without_composition=missing_composition,
                required_foods_not_ru_mass_market=sorted(
                    {
                        row["food_code"]
                        for row in rows
                        if foods[row["food_code"]]["ru_classification"]
                        != "RU_MASS_MARKET"
                    }
                ),
                carry_forward_ready=not (missing_mass or missing_composition),
            )
        )
    require(review["screening"] == expected, "Скрининг не совпадает с PR6-CLOSE.")
    require(len(expected) == 30, "Изменился принятый корпус из 30 рецептов.")
    require(
        not any(item["carry_forward_ready"] for item in expected),
        "Основание блокировки изменилось; требуется новая проверка.",
    )
    by_code = {recipe["recipe_code"]: recipe for recipe in recipes}
    candidates = review["candidates"]
    codes = {candidate["recipe_code"] for candidate in candidates}
    require(len(candidates) == len(codes) == 3, "Нужны три различных кандидата.")
    for candidate in candidates:
        source = by_code[candidate["recipe_code"]]
        expected_rows = [
            {key: row[key] for key in candidate["evidence_rows"][0]}
            for row in source["rows"]
        ]
        require(
            candidate["evidence_rows"] == expected_rows, "Строки источника изменены."
        )
        require(candidate["disposition"] == "DEFERRED", "Публикация не разрешена.")
        require(candidate["rule_snapshot"] is None, "Правила не подтверждены.")
    decision = read(PACKAGE / "template-decisions.json")
    require(decision["status"] == review["status"] == "BLOCKED", "Неверный статус.")
    require(decision["production_family_target"] == 3, "Цель нельзя уменьшать.")
    require(
        decision["production_families_published"] == 0, "Публикации быть не должно."
    )
    for name, count_field in (
        ("kitchen-verification.json", "production_verified_count"),
        ("ru-familiarity.json", "ru_recipe_familiar_count"),
    ):
        report = read(PACKAGE / name)
        require(report[count_field] == 0, "Неподтверждённый положительный статус.")
        require(
            {item["recipe_code"] for item in report["candidates"]} == codes,
            "Наборы кандидатов не совпадают.",
        )
    market = read(PACKAGE / "market-evidence.json")
    for candidate in market["candidates"]:
        source = by_code[candidate["recipe_code"]]
        require(
            {item["food_code"] for item in candidate["terminal_inputs"]}
            == {row["food_code"] for row in source["rows"] if not row["optional"]},
            "Список обязательных покупаемых продуктов не совпадает.",
        )
        require(candidate["gate"] == "NOT_PASSED", "Доступность не подтверждена.")
    if args.database:
        verify_database()
    print(
        json.dumps(
            dict(
                evidence_consistency="PASS",
                operation_status="BLOCKED",
                screened_current_recipes=len(expected),
                carry_forward_ready=0,
                shortlisted_deferred=len(candidates),
                production_templates_published=0,
                production_readiness=False,
            ),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
