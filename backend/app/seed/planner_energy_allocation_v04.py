"""Reviewed allocation-ready Meal Pattern publication for Planner v0.4."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.db.config import DatabaseConfig
from app.db.migrations import apply_migrations
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.meal_pattern_composition import (
    create_meal_pattern_catalogue_service,
)
from app.seed.meal_patterns import seed_meal_patterns
from app.services.meal_patterns import (
    MealPatternSeedSummary,
    TrustedMealPatternEvidenceSeed,
    TrustedMealPatternTargetVersionSeed,
    TrustedMealPatternVersionSeed,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PACKAGE = (
    PROJECT_ROOT / "data" / "curation" / "planner-energy-allocation-v04" / "programs.json"
)
EXPECTED_CODES = ("ADULT_REGULAR_3", "ADULT_REGULAR_3_PLUS_SNACK")


class PlannerEnergyAllocationSeedError(ValueError):
    pass


def _decimal(value: object, *, field: str) -> Decimal:
    if not isinstance(value, str):
        raise PlannerEnergyAllocationSeedError(f"{field} must be decimal text.")
    parsed = Decimal(value)
    if not parsed.is_finite():
        raise PlannerEnergyAllocationSeedError(f"{field} must be finite.")
    return parsed


def load_planner_energy_allocation_seeds(
    path: Path = DEFAULT_PACKAGE,
) -> tuple[TrustedMealPatternTargetVersionSeed, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if (
        payload.get("schema_version") != 1
        or payload.get("operation") != "PLANNER_ENERGY_ALLOCATION_V04_PROGRAMS"
        or payload.get("accepted_base")
        != "690a17a8c220e7e8f8e93bd63ba46356c73f0503"
    ):
        raise PlannerEnergyAllocationSeedError("Unknown allocation publication package.")
    sources = payload.get("sources")
    programs = payload.get("programs")
    if not isinstance(sources, list) or not isinstance(programs, list):
        raise PlannerEnergyAllocationSeedError("Allocation package lists are required.")
    evidence_by_code = {
        row["code"]: row for row in sources if isinstance(row, dict) and "code" in row
    }
    if len(evidence_by_code) != len(sources):
        raise PlannerEnergyAllocationSeedError("Allocation evidence codes must be unique.")

    seeds = []
    seen = []
    for row in programs:
        if not isinstance(row, dict):
            raise PlannerEnergyAllocationSeedError("Program rows must be objects.")
        code = row["code"]
        seen.append(code)
        shares = tuple(
            _decimal(value, field=f"{code}.shares") for value in row["shares"]
        )
        total = sum(shares, Decimal(0))
        residual = _decimal(row["residual_share"], field=f"{code}.residual_share")
        if total + residual != Decimal(1):
            raise PlannerEnergyAllocationSeedError(
                f"{code} shares and residual must equal one."
            )
        rationale = row.get("residual_rationale_ru")
        if not isinstance(rationale, str) or not rationale.strip():
            raise PlannerEnergyAllocationSeedError(
                f"{code} residual rationale is required."
            )
        share_rationale = row.get("share_rationale_ru")
        if not isinstance(share_rationale, str) or not share_rationale.strip():
            raise PlannerEnergyAllocationSeedError(
                f"{code} exact-share review rationale is required."
            )
        evidence = []
        for evidence_code in row["evidence_codes"]:
            source = evidence_by_code.get(evidence_code)
            if source is None:
                raise PlannerEnergyAllocationSeedError(
                    f"Unknown evidence code: {evidence_code}."
                )
            evidence.append(
                TrustedMealPatternEvidenceSeed(
                    source_name=source["source_name"],
                    source_title=source["source_title"],
                    source_url=source["source_url"],
                    source_version=source["source_version"],
                    retrieved_on=date.fromisoformat(source["retrieved_on"]),
                    evidence_scope=source["evidence_scope"],
                    review_note_ru=source["review_note_ru"],
                )
            )
        if code not in EXPECTED_CODES:
            raise PlannerEnergyAllocationSeedError(f"Unexpected program code: {code}.")
        roles_raw = row.get("roles")
        tags_raw = row.get("tags")
        if not isinstance(roles_raw, list) or not isinstance(tags_raw, list):
            raise PlannerEnergyAllocationSeedError(
                f"{code} must pin roles and tags."
            )
        roles = tuple(str(value) for value in roles_raw)
        tags = tuple(
            (str(value[0]), str(value[1]))
            for value in tags_raw
            if isinstance(value, list) and len(value) == 2
        )
        if len(tags) != len(tags_raw):
            raise PlannerEnergyAllocationSeedError(f"{code} tags are invalid.")
        if len(shares) != len(roles):
            raise PlannerEnergyAllocationSeedError(
                f"{code} must have one share per opportunity."
            )
        seeds.append(
            TrustedMealPatternTargetVersionSeed(
                code=code,
                target_version_number=int(row["target_version_number"]),
                expected_previous_version_number=int(
                    row["expected_previous_version_number"]
                ),
                version=TrustedMealPatternVersionSeed(
                    lifecycle=row["lifecycle"],
                    scope=row["scope"],
                    display_name_ru=row["display_name_ru"],
                    explanation_ru=row["explanation_ru"],
                    min_age_years=int(row["min_age_years"]),
                    max_age_years=row["max_age_years"],
                    review_status=row["review_status"],
                    reviewed_at=datetime.fromisoformat(row["reviewed_at"]),
                    published_at=datetime.fromisoformat(row["published_at"]),
                    change_note=(
                        f"{row['change_note']} "
                        f"Exact-share rationale: {share_rationale.strip()} "
                        f"Residual allocation: {row['residual_share']}; "
                        f"residual rationale: {rationale.strip()}"
                    ),
                    opportunity_roles=roles,
                    tags=tags,
                    evidence=tuple(evidence),
                    opportunity_energy_shares=shares,
                ),
            )
        )
    if tuple(seen) != EXPECTED_CODES:
        raise PlannerEnergyAllocationSeedError(
            "Allocation package must contain exactly the reviewed bounded programs."
        )
    return tuple(seeds)


def seed_planner_energy_allocation_v04(
    config: DatabaseConfig | None = None,
    *,
    path: Path = DEFAULT_PACKAGE,
) -> MealPatternSeedSummary:
    apply_migrations(config)
    seed_meal_patterns(config)
    engine = create_sqlite_engine(config)
    try:
        return create_meal_pattern_catalogue_service(engine).reconcile_target_versions(
            load_planner_energy_allocation_seeds(path)
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(seed_planner_energy_allocation_v04())
