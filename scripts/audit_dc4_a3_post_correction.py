"""Focused post-A3 DC4 Layer-A / Russian-readiness evidence."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.db.config import DatabaseConfig
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_ingredient_composition import (
    create_food_catalogue_service,
)
from app.persistence.sqlalchemy_core.food_recipe_composition import (
    create_food_recipe_catalogue_service,
)
from app.persistence.sqlalchemy_core.recipe_nutrition_v2 import (
    create_recipe_nutrition_v2_service,
)
from app.seed.dc4_a3_russian_step_corrections import (
    CORRECTION_CODES,
    _load_corrections,
    seed_dc4_a3_russian_step_corrections,
)

from scripts.audit_dc4_corpus_readiness import _audit_active_catalogue

SCHEMA_VERSION = "DC4_A3_POST_CORRECTION_EVIDENCE_V1"


def focused_audit(
    config: DatabaseConfig,
    *,
    source_sha: str | None = None,
) -> dict[str, Any]:
    publication = seed_dc4_a3_russian_step_corrections(config)
    correction_artifact = _load_corrections()
    correction_by_code = {
        row["canonical_code"]: row for row in correction_artifact["recipes"]
    }

    engine = create_sqlite_engine(config)
    try:
        recipes = create_food_recipe_catalogue_service(engine)
        food = create_food_catalogue_service(engine)
        nutrition = create_recipe_nutrition_v2_service(engine)
        catalogue = _audit_active_catalogue(recipes, food, nutrition)
    finally:
        engine.dispose()

    by_code = {row["canonical_code"]: row for row in catalogue["recipes"]}
    corrected = [by_code[code] for code in CORRECTION_CODES]
    publication_by_code = {
        row.canonical_code: row for row in publication.recipes
    }

    runtime_ids = []
    for code in CORRECTION_CODES:
        published = publication_by_code[code]
        audited = by_code[code]
        correction = correction_by_code[code]
        runtime_ids.append(
            {
                "canonical_code": code,
                "predecessor_version_id": str(published.predecessor_version_id),
                "successor_version_id": str(published.successor_version_id),
                "current_audited_recipe_version_id": audited["recipe_version_id"],
                "publication_disposition": published.disposition,
                "source_name": correction_artifact["source_name"],
                "source_recipe_id": correction["source_recipe_id"],
                "source_version": correction_artifact["source_version"],
                "source_document_sha256": correction_artifact[
                    "source_document_sha256"
                ],
                "rights_basis": correction_artifact["rights_basis"],
                "output_mass_g": correction["output_mass_g"],
                "expected_energy_kcal": correction["energy_kcal"],
                "old_steps": correction["old_steps"],
                "new_steps": correction["new_steps"],
            }
        )

    russian_blocked = [
        row["canonical_code"]
        for row in catalogue["recipes"]
        if "RUSSIAN_STEPS_NOT_READY" in row["issues"]
    ]
    corrected_issues = {
        row["canonical_code"]: row["issues"] for row in corrected
    }
    corrected_pass = all(
        row["disposition"] == "PASS"
        and "RUSSIAN_STEPS_NOT_READY" not in row["issues"]
        for row in corrected
    )
    runtime_id_match = all(
        row["successor_version_id"] == row["current_audited_recipe_version_id"]
        for row in runtime_ids
    )

    pass_status = (
        catalogue["active_count"] == 51
        and catalogue["blocked_count"] == 0
        and not russian_blocked
        and corrected_pass
        and runtime_id_match
        and publication.active_recipe_count == 51
        and publication.eligible_count == 51
        and dict(publication.meal_type_counts)
        == {"breakfast": 17, "main": 33, "sandwich": 1}
        and publication.planner_version == "planner-v0.5"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_scope": "POST_A3_FOCUSED_LAYER_A_RUSSIAN_READINESS",
        "source_sha": source_sha,
        "full_dc4_rerun": False,
        "status": "PASS" if pass_status else "BLOCKED",
        "prior_russian_blocker_codes": list(CORRECTION_CODES),
        "prior_russian_blocker_count": 7,
        "current_russian_steps_not_ready_codes": sorted(russian_blocked),
        "current_russian_steps_not_ready_count": len(russian_blocked),
        "prior_russian_blockers_cleared": corrected_pass and not russian_blocked,
        "runtime_identity_matches_current_catalogue": runtime_id_match,
        "runtime_version_receipts": runtime_ids,
        "correction_change_note": correction_artifact["change_note"],
        "correction_contract_path": (
            "data/curation/dc4-a3-russian-step-corrections/corrections.json"
        ),
        "corrected_recipe_issues": corrected_issues,
        "layer_a": {
            "active_count": catalogue["active_count"],
            "blocked_count": catalogue["blocked_count"],
            "blocked_recipe_codes": catalogue["blocked_recipe_codes"],
        },
        "planner_supply": {
            "eligible_count": publication.eligible_count,
            "meal_type_counts": dict(publication.meal_type_counts),
            "planner_version": publication.planner_version,
        },
        "explicitly_not_run": [
            "DC4_GATE1_FIXTURES",
            "DC4_BOUNDED_INFEASIBILITY",
            "FULL_DC4_OVERALL_STATUS_RECOMPUTE",
            "GATE1_CLOSE",
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    receipts = "\n".join(
        "| {canonical_code} | `{predecessor_version_id}` | "
        "`{successor_version_id}` | `{current_audited_recipe_version_id}` |".format(
            **row
        )
        for row in result["runtime_version_receipts"]
    )
    if not receipts:
        receipts = "| — | — | — | — |"

    return f"""# DC4-A3 post-correction focused evidence

**Status:** {result["status"]}
**Scope:** focused Layer-A / Russian-readiness verification only
**Full DC4 rerun:** NO
**Evidence source SHA:** `{result.get("source_sha") or "UNSPECIFIED"}`

## Result

- active production catalogue: **{result["layer_a"]["active_count"]}**;
- Layer-A blocked rows: **{result["layer_a"]["blocked_count"]}**;
- current `RUSSIAN_STEPS_NOT_READY`: **{result["current_russian_steps_not_ready_count"]}**;
- prior seven Russian-step blockers cleared: **{result["prior_russian_blockers_cleared"]}**;
- Planner exact-energy supply: **{result["planner_supply"]["eligible_count"]}**;
- split: **{result["planner_supply"]["meal_type_counts"]}**;
- Planner version: **{result["planner_supply"]["planner_version"]}**.

## Exact-run RecipeVersion identity receipt

These UUIDs identify this exact evidence database/run. They are intentionally
runtime-instance-specific and are not a cross-database identity contract.

| Recipe | predecessor RecipeVersion | successor RecipeVersion | audited current RecipeVersion |
| --- | --- | --- | --- |
{receipts}

The machine-readable receipt also contains full old/new RecipeStep arrays,
source provenance/rights/output commitments and expected prepared energy for
each row.

## Boundary

This receipt does **not** run the three Gate1 fixtures, bounded infeasibility,
full DC4 blocker recomputation or Gate1-CLOSE. Those remain reserved for the
separate DC4 rerun after A3 is accepted.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db")
    parser.add_argument("--output", required=True)
    parser.add_argument("--markdown-output")
    parser.add_argument("--source-sha")
    args = parser.parse_args()

    if args.db:
        config = DatabaseConfig(path=Path(args.db))
        result = focused_audit(config, source_sha=args.source_sha)
    else:
        with tempfile.TemporaryDirectory(prefix="dc4-a3-focused-") as tmp:
            config = DatabaseConfig(path=Path(tmp) / "evidence.sqlite")
            result = focused_audit(config, source_sha=args.source_sha)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.markdown_output:
        markdown = Path(args.markdown_output)
        markdown.parent.mkdir(parents=True, exist_ok=True)
        markdown.write_text(render_markdown(result), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
