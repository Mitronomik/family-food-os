"""Trusted offline loader for the reviewed Meal Pattern Catalogue seed."""

import json
from datetime import date, datetime
from pathlib import Path

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_pattern_composition import (
    create_meal_pattern_catalogue_service,
)
from app.services.meal_patterns import (
    MealPatternSeedSummary,
    TrustedMealPatternEvidenceSeed,
    TrustedMealPatternSeed,
    TrustedMealPatternVersionSeed,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SEED_PATH = PROJECT_ROOT / "data" / "seed" / "meal_patterns" / "programs.json"
DEFAULT_EVIDENCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "curation"
    / "pr7-support-meal-pattern-catalogue"
    / "evidence.json"
)
EXPECTED_PROGRAM_CODES = {
    "ADULT_REGULAR_3",
    "ADULT_REGULAR_3_PLUS_SNACK",
}


class MealPatternSeedError(ValueError):
    pass


def load_seed_entries(
    seed_path: Path = DEFAULT_SEED_PATH,
    evidence_path: Path = DEFAULT_EVIDENCE_PATH,
) -> tuple[TrustedMealPatternSeed, ...]:
    seed_payload = _json(seed_path)
    evidence_payload = _json(evidence_path)
    if seed_payload.get("schema_version") != 1:
        raise MealPatternSeedError("Unsupported Meal Pattern seed schema.")
    program_rows = seed_payload.get("programs")
    source_rows = evidence_payload.get("sources")
    if not isinstance(program_rows, list) or not isinstance(source_rows, list):
        raise MealPatternSeedError("Meal Pattern seed/evidence must contain lists.")
    evidence_by_code: dict[str, dict[str, object]] = {}
    for row in source_rows:
        if not isinstance(row, dict):
            raise MealPatternSeedError("Evidence row must be an object.")
        code = _required(row, "code")
        if code in evidence_by_code:
            raise MealPatternSeedError("Evidence codes must be unique.")
        evidence_by_code[code] = row

    entries: list[TrustedMealPatternSeed] = []
    seen_codes: set[str] = set()
    for row in program_rows:
        if not isinstance(row, dict) or not isinstance(row.get("version"), dict):
            raise MealPatternSeedError("Program row is invalid.")
        code = _required(row, "code")
        if code in seen_codes:
            raise MealPatternSeedError("Program codes must be unique.")
        seen_codes.add(code)
        version = row["version"]
        evidence_codes = version.get("evidence_codes")
        opportunity_roles = version.get("opportunity_roles")
        tags = version.get("tags")
        if not isinstance(evidence_codes, list) or not evidence_codes:
            raise MealPatternSeedError("Published seed programs require evidence.")
        if not isinstance(opportunity_roles, list) or not opportunity_roles:
            raise MealPatternSeedError("Seed programs require opportunities.")
        if not isinstance(tags, list):
            raise MealPatternSeedError("Seed program tags must be a list.")

        evidence = tuple(
            _evidence(evidence_by_code, source_code) for source_code in evidence_codes
        )
        parsed_tags: list[tuple[str, str]] = []
        for tag in tags:
            if (
                not isinstance(tag, list)
                or len(tag) != 2
                or not all(isinstance(value, str) and value.strip() for value in tag)
            ):
                raise MealPatternSeedError("Seed tag must be [kind, code].")
            parsed_tags.append((tag[0], tag[1]))

        entries.append(
            TrustedMealPatternSeed(
                code=code,
                version=TrustedMealPatternVersionSeed(
                    lifecycle=_required(version, "lifecycle"),
                    scope=_required(version, "scope"),
                    display_name_ru=_required(version, "display_name_ru"),
                    explanation_ru=_required(version, "explanation_ru"),
                    min_age_years=_nonnegative_int(version, "min_age_years"),
                    max_age_years=_optional_nonnegative_int(
                        version, "max_age_years"
                    ),
                    review_status=_required(version, "review_status"),
                    reviewed_at=_instant(version.get("reviewed_at")),
                    published_at=_instant(version.get("published_at")),
                    change_note=_required(version, "change_note"),
                    opportunity_roles=tuple(str(value) for value in opportunity_roles),
                    tags=tuple(parsed_tags),
                    evidence=evidence,
                ),
            )
        )
    if seen_codes != EXPECTED_PROGRAM_CODES:
        raise MealPatternSeedError(
            "Initial Meal Pattern seed must contain only the reviewed bounded corpus."
        )
    return tuple(entries)


def seed_meal_patterns(
    config: DatabaseConfig | None = None,
    *,
    seed_path: Path = DEFAULT_SEED_PATH,
    evidence_path: Path = DEFAULT_EVIDENCE_PATH,
) -> MealPatternSeedSummary:
    entries = load_seed_entries(seed_path, evidence_path)
    apply_migrations(config)
    engine = create_sqlite_engine(config)
    try:
        return create_meal_pattern_catalogue_service(engine).reconcile_seed(entries)
    finally:
        engine.dispose()


def _json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MealPatternSeedError(f"Could not read {path}.") from exc
    if not isinstance(payload, dict):
        raise MealPatternSeedError(f"{path} must contain an object.")
    return payload


def _required(row: dict[str, object], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise MealPatternSeedError(f"{field} is required.")
    return value.strip()


def _nonnegative_int(row: dict[str, object], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MealPatternSeedError(f"{field} must be a non-negative integer.")
    return value


def _optional_nonnegative_int(
    row: dict[str, object], field: str
) -> int | None:
    value = row.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MealPatternSeedError(f"{field} must be null or a non-negative integer.")
    return value


def _instant(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise MealPatternSeedError("Timestamp must be ISO-8601 text.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise MealPatternSeedError("Timestamp must be valid ISO-8601.") from exc
    if parsed.tzinfo is None:
        raise MealPatternSeedError("Timestamp must include an offset.")
    return parsed


def _evidence(
    evidence_by_code: dict[str, dict[str, object]], source_code: object
) -> TrustedMealPatternEvidenceSeed:
    if not isinstance(source_code, str) or source_code not in evidence_by_code:
        raise MealPatternSeedError("Program references unknown evidence.")
    row = evidence_by_code[source_code]
    retrieved = row.get("retrieved_on")
    if not isinstance(retrieved, str):
        raise MealPatternSeedError("Evidence retrieved_on is required.")
    try:
        retrieved_on = date.fromisoformat(retrieved)
    except ValueError as exc:
        raise MealPatternSeedError("Evidence retrieved_on must be ISO date.") from exc
    return TrustedMealPatternEvidenceSeed(
        source_name=_required(row, "source_name"),
        source_title=_required(row, "source_title"),
        source_url=_required(row, "source_url"),
        source_version=_required(row, "source_version"),
        retrieved_on=retrieved_on,
        evidence_scope=_required(row, "evidence_scope"),
        review_note_ru=_required(row, "review_note_ru"),
    )
