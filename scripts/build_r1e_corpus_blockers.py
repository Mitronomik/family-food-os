"""Build the R1-E evidence-backed blocker map for all retained recipes."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R1D = ROOT / "data/curation/r1d-planner-admission/source-inventory.jsonl"
DC1 = ROOT / "data/curation/data-corpus-v1-dc1/candidate-recipes.csv"
R1A = ROOT / "data/curation/r1a-planner-capacity-dependencies/dependency-manifest.json"
R1B = ROOT / "data/curation/r1b-reviewed-recipes/publication.json"
OUT = ROOT / "data/curation/r1e-corpus-blockers"

BLOCKER_ORDER = (
    "HOUSEHOLD_APPLICABILITY",
    "SOURCE_STRUCTURE_OR_VARIANT",
    "REQUIRED_QUANTITY_UNRESOLVED",
    "FOOD_IDENTITY_OR_FORM",
    "COMPOSITION_AUTHORITY",
    "CONSUMED_NUTRITION_AUTHORITY",
    "ROLE_OR_MEAL_COMPOSITION",
    "RECIPE_PUBLICATION_REQUIRED",
    "ACTIVATION_REQUIRED",
)

R1B_LOCAL = {
    "USSR82-453": ("COMPOSITION_AUTHORITY",),
    "USSR82-467": ("REQUIRED_QUANTITY_UNRESOLVED",),
    "USSR82-492": ("REQUIRED_QUANTITY_UNRESOLVED",),
    "USSR82-1081": ("COMPOSITION_AUTHORITY",),
    "USSR82-697": (
        "FOOD_IDENTITY_OR_FORM",
        "CONSUMED_NUTRITION_AUTHORITY",
        "ACTIVATION_REQUIRED",
    ),
}

EVIDENCE = {
    "cross_corpus_review": "docs/family-food/r1-cross-corpus-consumed-nutrition-review.md",
    "candidate_universe": "docs/family-food/r1-cross-corpus-candidate-universe-decision.md",
    "dc1": "data/curation/data-corpus-v1-dc1/candidate-recipes.csv",
    "r1a": "data/curation/r1a-planner-capacity-dependencies/dependency-manifest.json",
    "r1b": "data/curation/r1b-reviewed-recipes/publication.json",
    "r1d": "data/curation/r1d-planner-admission/source-inventory.jsonl",
}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _dc1() -> dict[str, dict[str, str]]:
    with DC1.open(encoding="utf-8", newline="") as handle:
        return {row["source_recipe_id"]: row for row in csv.DictReader(handle)}


def _r1_roles() -> dict[str, str]:
    manifest = _json(R1A)
    return {
        row["source_recipe_id"]: row["target_role_family"]
        for row in manifest["recipes"]
    }


def _split_ids(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split("|") if item.strip())


def _ordered(blockers: set[str]) -> tuple[str, ...]:
    return tuple(code for code in BLOCKER_ORDER if code in blockers)


def build() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    inventory = _jsonl(R1D)
    dc1 = _dc1()
    r1_roles = _r1_roles()

    rows: list[dict[str, Any]] = []
    for item in inventory:
        source_id = item["source_recipe_id"]
        family = item["source_family"]
        blockers: set[str] = set()
        refs = {EVIDENCE["r1d"], EVIDENCE["candidate_universe"]}
        role = r1_roles.get(source_id)
        classification_basis = "FAMILY_LEVEL_RETAINED_EVIDENCE"

        if item["production_catalogue_state"].startswith("PUBLISHED"):
            blockers.update(
                code
                for code in R1B_LOCAL.get(source_id, ())
                if code != "RECIPE_PUBLICATION_REQUIRED"
            )
            if source_id == "ru-school2022:recipe:53-19з":
                blockers.update({"ROLE_OR_MEAL_COMPOSITION", "ACTIVATION_REQUIRED"})
                refs.add(EVIDENCE["cross_corpus_review"])
                classification_basis = "ACCEPTED_PUBLICATION_AND_REVIEW"
            elif source_id == "USSR82-697":
                refs.add(EVIDENCE["r1b"])
                refs.add(EVIDENCE["cross_corpus_review"])
                classification_basis = "ACCEPTED_R1_REVIEW"
            elif not item.get("production_catalogue_state", "").endswith("ACTIVE"):
                blockers.add("ACTIVATION_REQUIRED")
        else:
            blockers.add("RECIPE_PUBLICATION_REQUIRED")

            if family == "USSR82":
                source = dc1[source_id]
                refs.add(EVIDENCE["dc1"])
                classification_basis = "DC1_RECIPE_LEVEL_EVIDENCE"

                if source_id in R1B_LOCAL:
                    blockers.update(R1B_LOCAL[source_id])
                    refs.add(EVIDENCE["r1b"])
                    refs.add(EVIDENCE["cross_corpus_review"])
                    classification_basis = "ACCEPTED_R1_REVIEW"
                else:
                    if (
                        source["source_structure_status"]
                        != "SINGLE_VARIANT_NO_EXPLICIT_ALTERNATIVE"
                        or source["variant_selection_status"]
                        not in {
                            "SIMPLE_SOURCE_BRANCH_CANDIDATE",
                            "REVIEWED_SOURCE_BRANCH",
                        }
                    ):
                        blockers.add("SOURCE_STRUCTURE_OR_VARIANT")
                    if (
                        _split_ids(source.get("dc2_required_ids"))
                        or _split_ids(source.get("semantic_label_review_ids"))
                    ):
                        blockers.add("FOOD_IDENTITY_OR_FORM")

            elif family == "ru-school2022":
                # Retained review proves strong material readiness in aggregate but
                # does not support per-card household applicability or Nutrition
                # readiness. Preserve that uncertainty instead of inventing it.
                blockers.update(
                    {
                        "HOUSEHOLD_APPLICABILITY",
                        "CONSUMED_NUTRITION_AUTHORITY",
                    }
                )
                refs.add(EVIDENCE["cross_corpus_review"])

            elif family == "RU-MR-2019":
                # Current retained interpretation did not establish the ordinary
                # household path. Applicability review therefore owns the next step.
                blockers.add("HOUSEHOLD_APPLICABILITY")
                refs.add(EVIDENCE["cross_corpus_review"])
            else:
                blockers.add("HOUSEHOLD_APPLICABILITY")

        ordered = _ordered(blockers)
        next_blocker = ordered[0] if ordered else "PLANNER_READY"

        rows.append(
            {
                "source_family": family,
                "source_recipe_id": source_id,
                "source_name": item.get("source_name"),
                "planner_capacity_role": role,
                "production_catalogue_state": item["production_catalogue_state"],
                "blockers": list(ordered),
                "next_blocker": next_blocker,
                "classification_basis": classification_basis,
                "evidence_refs": sorted(refs),
            }
        )

    rows.sort(key=lambda row: (row["source_family"], row["source_recipe_id"]))

    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    overall = Counter()
    next_counts = Counter()
    for row in rows:
        for blocker in row["blockers"]:
            overall[blocker] += 1
            by_family[row["source_family"]][blocker] += 1
        next_counts[row["next_blocker"]] += 1

    summary = {
        "schema_version": 1,
        "accepted_base": "48707e1e84eff260726609c4508f05407e9f9448",
        "total_retained_recipes": len(rows),
        "source_family_counts": dict(
            sorted(Counter(row["source_family"] for row in rows).items())
        ),
        "blocker_counts": dict(sorted(overall.items())),
        "next_blocker_counts": dict(sorted(next_counts.items())),
        "blocker_counts_by_family": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(by_family.items())
        },
        "planner_capacity_roles": dict(
            sorted(
                Counter(
                    row["planner_capacity_role"]
                    for row in rows
                    if row["planner_capacity_role"] is not None
                ).items()
            )
        ),
    }

    batch_ids = ("USSR82-453", "USSR82-467", "USSR82-492", "USSR82-1081")
    selected = [row for row in rows if row["source_recipe_id"] in batch_ids]
    batch = {
        "schema_version": 1,
        "accepted_base": "48707e1e84eff260726609c4508f05407e9f9448",
        "selection": "FIRST_BREAKFAST_CAPACITY_CLOSURE_BATCH",
        "recipe_ids": list(batch_ids),
        "role": "breakfast",
        "candidate_count": len(selected),
        "local_blockers": {
            row["source_recipe_id"]: row["blockers"] for row in selected
        },
        "shared_post_local_seam": "CONSUMED_NUTRITION_AUTHORITY",
        "decision": (
            "Close the four accepted breakfast candidates as one Planner-capacity "
            "program: first resolve their exact local Composition/quantity blockers, "
            "then review one reusable consumed-Nutrition authority seam for cooked "
            "recipes. No current evidence supports treating them as V1 no-thermal "
            "recipes."
        ),
        "why_not_no_thermal_controls": (
            "School2022 no-thermal controls prove the existing V1 calculation path "
            "but do not provide material BREAKFAST/MAIN Planner capacity."
        ),
        "why_not_usrr82_697_first": (
            "USSR82-697 remains a useful MAIN candidate but has an additional exact "
            "source identity conflict before the shared consumed-Nutrition blocker."
        ),
        "evidence_refs": sorted(
            {
                EVIDENCE["r1a"],
                EVIDENCE["r1b"],
                EVIDENCE["cross_corpus_review"],
                EVIDENCE["candidate_universe"],
            }
        ),
    }
    return rows, summary, batch


def main() -> None:
    rows, summary, batch = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "blocker-map.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT / "selected-batch.json").write_text(
        json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
