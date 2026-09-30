"""Build the R1-D corpus-wide Planner source admission inventory deterministically."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = (
    ROOT
    / "data/curation/corpus-v03-reconciliation/generated/recipe-crosswalk.jsonl"
)
DC1 = ROOT / "data/curation/data-corpus-v1-dc1/candidate-recipes.csv"
OUT = ROOT / "data/curation/r1d-planner-admission"


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _dc1() -> dict[str, dict[str, str]]:
    with DC1.open(encoding="utf-8", newline="") as handle:
        return {row["source_recipe_id"]: row for row in csv.DictReader(handle)}


def _known_publications() -> dict[str, dict[str, str]]:
    # Import accepted repository-owned publication packages instead of duplicating
    # source identities/canonical codes here.
    from app.seed.r1b_reviewed_recipes import load_r1b_recipe_seeds
    from app.seed.ru_school2022_step9_recipe import (
        load_ru_school2022_step9_recipe_seed,
    )

    result: dict[str, dict[str, str]] = {}

    r1b_seeds, r1b_package = load_r1b_recipe_seeds()
    by_source = {
        row["source_recipe_id"]: row
        for row in r1b_package["candidates"]
        if row["disposition"] == "PUBLISH"
    }
    for seed in r1b_seeds:
        source_id = seed.version.source_recipe_id
        row = by_source[source_id]
        result[source_id] = {
            "catalogue_code": seed.canonical_code,
            "state": (
                "PUBLISHED_INACTIVE"
                if not seed.initial_is_active
                else "PUBLISHED_ACTIVE"
            ),
            "blocker": row.get("activation_reason") or "REVIEW_REQUIRED",
        }

    school_seed, _ = load_ru_school2022_step9_recipe_seed()
    result[school_seed.version.source_recipe_id] = {
        "catalogue_code": school_seed.canonical_code,
        "state": (
            "PUBLISHED_INACTIVE"
            if not school_seed.initial_is_active
            else "PUBLISHED_ACTIVE"
        ),
        "blocker": (
            "ROLE_UNSUPPORTED_OTHER"
            if str(school_seed.version.meal_type_code) == "other"
            else "REVIEW_REQUIRED"
        ),
    }
    return result


def build() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    crosswalk = _jsonl(CROSSWALK)
    dc1 = _dc1()
    known = _known_publications()

    inventory: list[dict[str, Any]] = []
    for row in crosswalk:
        source_id = row["source_record_id"]
        dc = dc1.get(source_id)
        publication = known.get(source_id)
        inventory.append(
            {
                "source_family": row["edition_namespace"],
                "source_recipe_id": source_id,
                "source_name": dc["recipe_name"] if dc else None,
                "retained_route_count": len(row.get("route_ids") or ()),
                "reconciliation_disposition": row["disposition"],
                "reconciliation_publication_ready": bool(
                    row.get("publication_ready")
                ),
                "dc1_production_ready": (
                    dc["production_ready"] == "YES" if dc else None
                ),
                "dc1_proposed_batch": (
                    dc["proposed_dc3_batch"] or None if dc else None
                ),
                "production_catalogue_state": (
                    publication["state"]
                    if publication
                    else "NOT_PUBLISHED_IN_CURRENT_RUSSIAN_R1_PATH"
                ),
                "production_catalogue_code": (
                    publication["catalogue_code"] if publication else None
                ),
                "current_closure_blocker": (
                    publication["blocker"]
                    if publication
                    else "PRODUCTION_RECONCILIATION_REQUIRED"
                ),
            }
        )

    inventory.sort(
        key=lambda item: (item["source_family"], item["source_recipe_id"])
    )

    counts: dict[str, dict[str, int]] = {}
    for item in inventory:
        family = item["source_family"]
        bucket = counts.setdefault(
            family,
            {"retained": 0, "published": 0, "unpublished": 0},
        )
        bucket["retained"] += 1
        if item["production_catalogue_state"].startswith("PUBLISHED"):
            bucket["published"] += 1
        else:
            bucket["unpublished"] += 1

    published = sum(
        item["production_catalogue_state"].startswith("PUBLISHED")
        for item in inventory
    )
    summary = {
        "schema_version": 1,
        "accepted_base": "e350e747a9c6e06e74b2cd450637c25a442c8749",
        "total_retained_recipes": len(inventory),
        "source_family_counts": counts,
        "known_current_russian_production_publications": published,
        "source_only_pending_production_reconciliation": len(inventory) - published,
        "purpose": (
            "Corpus-wide source → production catalogue → Planner admission closure "
            "queue; source presence is not production authority."
        ),
    }
    return inventory, summary


def main() -> None:
    inventory, summary = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "source-inventory.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in inventory
        ),
        encoding="utf-8",
    )
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
