"""Read the exact Candidate A predecessor and its authority without publishing it."""

import argparse
import json
import re
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, DecimalException
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from app.db.migration_lineage import (
    has_family_food_workspace_identity,
    inspect_migration_lineage,
    missing_required_tables,
)
from app.domain.food_recipes import RecipeVersion, RecipeVersionDetail
from app.domain.nutrient_vector_backfill_v1 import canonical_json
from app.persistence.sqlalchemy_core.food_recipe_tables import (
    food_recipe_equipment_table,
    food_recipe_ingredients_table,
    food_recipe_steps_table,
    food_recipe_versions_table,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    SqlAlchemyRecipeNutritionV2ReadScope,
    create_recipe_nutrition_v2_service,
)
from app.seed.r2c_breakfast_grain_diversity import (
    BUCKWHEAT_RECIPE_CODE,
    PUBLICATION_SPECS_GIT_BLOB_SHA,
    _load_contract,
    _prepared_spec,
    _recipe_seed,
)
from app.services.food_recipes import trusted_recipe_seed_matches
from app.services.pr10_ff_manifest_loader import process_steps_sha256
from app.services.recipe_nutrition_v2 import (
    RecipeNutritionV2UnavailableError,
    ReviewedPreparedRecipeNutritionSpec,
)
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

SCHEMA = "PR10_CANDIDATE_A_PREDECESSOR_READBACK_V1"
PROCESS_SHA256 = "d6340081a54597250753ef81de33af980212098c7e3a6ba292ac4710fe8af20b"
STEP4_SHA256 = "b800669831dec3f3bed61959c1c4fa300e14b163e308f389c8d53e93c10f135d"
CONTEXTS = ("target-snapshot", "disposable-test")


class ReadbackBlocked(Exception):
    """An observation cannot establish the expected predecessor."""


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ReadbackBlocked(reason)


def _version_ref(version: RecipeVersion) -> dict:
    return {
        "id": str(version.id),
        "version_number": version.version_number,
        "created_from_version_id": (
            str(version.created_from_version_id)
            if version.created_from_version_id
            else None
        ),
        "verification_status": version.verification_status.value,
    }


def _prepared_readback(
    engine: Engine,
    scope: SqlAlchemyRecipeNutritionV2ReadScope,
    detail: RecipeVersionDetail,
    spec: ReviewedPreparedRecipeNutritionSpec,
) -> dict:
    version_id = detail.version.id
    authority = scope.prepared.get_authority(version_id)
    _require(authority is not None, "PREPARED_AUTHORITY_MISSING")
    assert authority is not None
    fields = {
        "output_mass_g": spec.output_mass_g,
        "source_name": spec.source_name,
        "source_id": spec.source_recipe_id,
        "source_version": spec.source_version,
        "source_locator": spec.source_locator,
        "source_document_sha256": spec.source_document_sha256,
        "source_data_type": spec.source_data_type,
        "rights_review_status": spec.rights_review_status,
        "rights_basis": spec.rights_basis,
        "review_reference": spec.review_reference,
    }
    _require(
        all(getattr(authority, field) == value for field, value in fields.items()),
        "PREPARED_AUTHORITY_SOURCE_MISMATCH",
    )
    nutrition = create_recipe_nutrition_v2_service(engine)
    try:
        canonical = nutrition.prepared_canonical_nutrition_in_scope(scope, version_id)
    except (DecimalException, RecipeNutritionV2UnavailableError) as exc:
        raise ReadbackBlocked("PREPARED_AUTHORITY_INVALID") from exc
    values = scope.prepared.list_values(version_id)
    # The publisher seals canonical JSON. Compare the stored text so duplicate
    # keys cannot disappear during parsing and the reported seal stays verifiable.
    value_provenance = canonical_json(
        {
            "schema_version": "R1F_PREPARED_OUTPUT_VALUE_V1",
            "recipe_code": spec.recipe_code,
            "source_name": spec.source_name,
            "source_id": spec.source_recipe_id,
            "source_version": spec.source_version,
            "source_locator": spec.source_locator,
            "source_document_sha256": spec.source_document_sha256,
            "review_reference": spec.review_reference,
        }
    )
    _require(
        all(value.provenance_json == value_provenance for value in values),
        "PREPARED_NUTRIENT_PROVENANCE_MISMATCH",
    )
    available = {
        item.code: item.amount
        for item in canonical.required_total
        if item.amount is not None
    }
    unknown = sorted(
        item.code for item in canonical.required_total if item.amount is None
    )
    _require(
        available == dict(spec.expected_available_amounts)
        and unknown == sorted(spec.expected_unknown_codes),
        "PREPARED_NUTRIENT_PARTITION_MISMATCH",
    )
    return {
        "authority": asdict(authority),
        "values": [asdict(value) for value in values],
        "available": available,
        "unknown": unknown,
    }


def _verify_persisted_text(conn: Connection, detail: RecipeVersionDetail) -> None:
    # The domain adapters normalize text. The evidence must match the stored text.
    for table, selector, fields, expected in (
        (
            food_recipe_versions_table,
            "id",
            (
                "difficulty_code",
                "source_name",
                "source_recipe_id",
                "source_url",
                "source_version",
                "source_document_sha256",
                "rights_basis",
                "change_note",
                "source_output_text",
            ),
            (detail.version,),
        ),
        (
            food_recipe_ingredients_table,
            "recipe_version_id",
            ("source_amount_text", "normalization_note", "prep_note"),
            detail.ingredients,
        ),
        (
            food_recipe_steps_table,
            "recipe_version_id",
            ("instruction", "stage_code"),
            detail.steps,
        ),
        (
            food_recipe_equipment_table,
            "recipe_version_id",
            ("equipment_code",),
            detail.equipment,
        ),
    ):
        query = select(*(table.c[field] for field in fields)).where(
            table.c[selector] == detail.version.id
        )
        if "position" in table.c:
            query = query.order_by(table.c.position)
        rows = conn.execute(query).all()
        _require(
            [tuple(row) for row in rows]
            == [tuple(getattr(item, field) for field in fields) for item in expected],
            "PERSISTED_TEXT_MISMATCH",
        )


def _read_snapshot(engine: Engine, report: dict) -> None:
    _, _, specs = _load_contract()
    pinned = specs["recipes"][BUCKWHEAT_RECIPE_CODE]
    seed = _recipe_seed(pinned)
    prepared_spec = _prepared_spec(pinned, seed)
    with SqlAlchemyRecipeNutritionV2ReadScope(engine) as scope:
        conn = scope.adapter_connection.connection.driver_connection
        lineage = inspect_migration_lineage(conn)
        target = report["target"]
        target["schema_lineage"] = lineage.status
        if lineage.rejection:
            target["schema_rejection"] = lineage.rejection
        if lineage.applied_ids:
            target["recorded_schema_revision"] = lineage.applied_ids[-1]
        _require(lineage.is_current_head, "SCHEMA_NOT_AT_ACCEPTED_REVISION")
        missing = missing_required_tables(conn, lineage.applied_ids)
        if missing:
            target["missing_required_tables"] = sorted(missing)
            raise ReadbackBlocked("REQUIRED_SCHEMA_TABLES_MISSING")
        _require(
            has_family_food_workspace_identity(conn, lineage.applied_ids),
            "WORKSPACE_IDENTITY_MISMATCH",
        )
        target["schema_revision"] = lineage.applied_ids[-1]

        recipe = scope.recipes.get_by_code(BUCKWHEAT_RECIPE_CODE)
        _require(recipe is not None, "RECIPE_MISSING")
        assert recipe is not None
        versions = scope.versions.list_for_recipe(recipe.id)
        current = scope.versions.get_current_verified(recipe.id)
        report["recipe"] = {
            "id": str(recipe.id),
            "is_active": recipe.is_active,
            "versions": [_version_ref(version) for version in versions],
            "current_verified_version_id": str(current.version.id) if current else None,
        }
        predecessors = [version for version in versions if version.version_number == 1]
        _require(len(predecessors) == 1, "PREDECESSOR_NOT_UNIQUE")
        predecessor = predecessors[0]
        _require(
            predecessor.created_from_version_id is None, "PREDECESSOR_PARENT_UNEXPECTED"
        )
        _require(len(versions) == 1, "LATER_VERSION_PRESENT")
        _require(
            current is not None and current.version.id == predecessor.id,
            "PREDECESSOR_NOT_CURRENT",
        )
        _require(recipe.is_active, "RECIPE_INACTIVE")
        assert current is not None
        _require(
            trusted_recipe_seed_matches(scope, current, seed)
            and all(step.stage_code is None for step in current.steps),
            "PINNED_R2C_CONTENT_MISMATCH",
        )
        _verify_persisted_text(scope.adapter_connection, current)

        for rows in (current.ingredients, current.steps, current.equipment):
            _require(
                [row.position for row in rows] == list(range(1, len(rows) + 1)),
                "PERSISTED_POSITIONS_MISMATCH",
            )
        steps = [step.instruction for step in current.steps]
        process_sha = process_steps_sha256(steps)
        step_hashes = [sha256(step.encode("utf-8")).hexdigest() for step in steps]
        _require(
            len(steps) == 4
            and process_sha == PROCESS_SHA256
            and step_hashes[3] == STEP4_SHA256,
            "PINNED_RECIPE_PROCESS_MISMATCH",
        )
        report["predecessor"] = {
            "version": asdict(current.version),
            "ingredients": [asdict(row) for row in current.ingredients],
            "steps": [
                {**asdict(step), "sha256": step_hash}
                for step, step_hash in zip(current.steps, step_hashes, strict=True)
            ],
            "equipment": [asdict(item) for item in current.equipment],
            "process_sha256": process_sha,
            "source_card": {
                "evidence": "R2C_PUBLICATION_MANIFEST",
                "exact_source_card_sha256": pinned["source_receipt"][
                    "exact_source_card_sha256"
                ],
            },
        }
        report["prepared"] = _prepared_readback(engine, scope, current, prepared_spec)


def _snapshot_identity(path: Path) -> tuple[int, ...]:
    _require(
        not any(
            Path(f"{path}{suffix}").exists() for suffix in ("-wal", "-shm", "-journal")
        ),
        "SQLITE_SNAPSHOT_HAS_SIDECARS",
    )
    info = path.stat()
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def readback(*, sqlite_path: Path, target_id: str, context: str) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", target_id) or context not in CONTEXTS:
        raise ValueError(
            "Укажите нечувствительную метку без пути и допустимый контекст."
        )
    report = {
        "schema": SCHEMA,
        "status": "BLOCKED",
        "target": {
            "id": target_id,
            "operator_declared_context": context,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        },
        "recipe_code": BUCKWHEAT_RECIPE_CODE,
        "publication_spec_git_blob": PUBLICATION_SPECS_GIT_BLOB_SHA,
        "publication_gate": "NO_GO_TO_CORRECTION_PUBLICATION",
    }
    try:
        if not sqlite_path.is_file():
            return {**report, "reason": "SQLITE_FILE_MISSING"}
        path = sqlite_path.resolve(strict=True)
        initial = _snapshot_identity(path)
    except ReadbackBlocked as exc:
        return {**report, "reason": str(exc)}
    except OSError:
        return {**report, "reason": "READBACK_INVALID_OR_UNAVAILABLE"}

    # Only open an offline, standalone snapshot. Plain mode=ro may create WAL sidecars.
    uri = path.as_uri() + "?mode=ro&immutable=1"
    engine = create_engine(
        "sqlite+pysqlite://",
        creator=lambda: sqlite3.connect(uri, uri=True, autocommit=False),
    )
    observed = {**report, "target": dict(report["target"])}
    try:
        _read_snapshot(engine, observed)
    except ReadbackBlocked as exc:
        observed["reason"] = str(exc)
    except (
        SQLAlchemyError,
        sqlite3.Error,
        DecimalException,
        OSError,
        TypeError,
        ValueError,
    ):
        # Driver errors can contain local paths or raw SQLite records.
        observed["reason"] = "READBACK_INVALID_OR_UNAVAILABLE"
    else:
        observed["status"] = "PREDECESSOR_MATCH"
    finally:
        engine.dispose()
    try:
        if _snapshot_identity(path) == initial:
            return observed
    except (ReadbackBlocked, OSError):
        pass
    return {**report, "reason": "SQLITE_SNAPSHOT_CHANGED"}


def _json_value(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"Unsupported receipt value type: {type(value).__name__}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite",
        type=Path,
        required=True,
        help="Закрытый самостоятельный снимок SQLite.",
    )
    parser.add_argument(
        "--target-id", required=True, help="Нечувствительная метка снимка без пути."
    )
    parser.add_argument("--context", choices=CONTEXTS, required=True)
    args = parser.parse_args()
    try:
        report = readback(
            sqlite_path=args.sqlite, target_id=args.target_id, context=args.context
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            report, ensure_ascii=False, sort_keys=True, indent=2, default=_json_value
        )
    )
    if report["status"] == "BLOCKED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
