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

R1B_REASON_TO_BLOCKER = {
    "V2_COMPOSITION_AUTHORITY_MISSING_EGG": "COMPOSITION_AUTHORITY",
    "V2_COMPOSITION_AUTHORITY_MISSING_BUTTER": "COMPOSITION_AUTHORITY",
    "UNQUANTIFIED_PROCESS_INGREDIENT_SALT": "REQUIRED_QUANTITY_UNRESOLVED",
}

EVIDENCE = {
    "cross_corpus_review": "docs/family-food/r1-cross-corpus-consumed-nutrition-review.md",
    "candidate_universe": "docs/family-food/r1-cross-corpus-candidate-universe-decision.md",
    "dc1": "data/curation/data-corpus-v1-dc1/candidate-recipes.csv",
    "r1a": "data/curation/r1a-planner-capacity-dependencies/dependency-manifest.json",
    "r1b": "data/curation/r1b-reviewed-recipes/publication.json",
    "r1d": "data/curation/r1d-planner-admission/source-inventory.jsonl",
}

R1_MODE_INDEPENDENT = {
    "USSR82-453": ("RECIPE_PUBLICATION_REQUIRED",),
    "USSR82-467": ("REQUIRED_QUANTITY_UNRESOLVED", "RECIPE_PUBLICATION_REQUIRED"),
    "USSR82-492": ("REQUIRED_QUANTITY_UNRESOLVED", "RECIPE_PUBLICATION_REQUIRED"),
    "USSR82-1081": ("RECIPE_PUBLICATION_REQUIRED",),
    "USSR82-697": ("FOOD_IDENTITY_OR_FORM",),
}

R1_MODE_DEPENDENT = {
    "USSR82-453": ("COMPOSITION_AUTHORITY", "CONSUMED_NUTRITION_AUTHORITY"),
    "USSR82-467": ("CONSUMED_NUTRITION_AUTHORITY",),
    "USSR82-492": ("CONSUMED_NUTRITION_AUTHORITY",),
    "USSR82-1081": ("COMPOSITION_AUTHORITY", "CONSUMED_NUTRITION_AUTHORITY"),
    "USSR82-697": ("CONSUMED_NUTRITION_AUTHORITY",),
}

SELECTED_COOKED_R1 = frozenset(R1_MODE_DEPENDENT)


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


def _r1_manifest() -> dict[str, dict[str, Any]]:
    manifest = _json(R1A)
    return {row["source_recipe_id"]: row for row in manifest["recipes"]}


def _r1b_blockers() -> dict[str, tuple[str, ...]]:
    publication = _json(R1B)
    result: dict[str, tuple[str, ...]] = {}
    seen_expected = set()
    for row in publication["candidates"]:
        source_id = row["source_recipe_id"]
        if row["disposition"] == "BLOCKED":
            reason = row["reason"]
            if reason not in R1B_REASON_TO_BLOCKER:
                raise ValueError(f"Unmapped accepted R1-B blocker reason: {reason}")
            result[source_id] = (R1B_REASON_TO_BLOCKER[reason],)
            seen_expected.add(source_id)
        elif source_id == "USSR82-697":
            if row.get("activation") != "INACTIVE_PENDING_TRANSFORMATION_AUTHORITY":
                raise ValueError("USSR82-697 activation disposition drifted.")
            result[source_id] = ("ACTIVATION_REQUIRED",)
            seen_expected.add(source_id)

    expected = {
        "USSR82-453",
        "USSR82-467",
        "USSR82-492",
        "USSR82-697",
        "USSR82-1081",
    }
    if seen_expected != expected:
        raise ValueError(f"Accepted R1-B candidate set drifted: {seen_expected!r}")
    return result


def _split_ids(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split("|") if item.strip())


def _ordered(blockers: set[str]) -> tuple[str, ...]:
    return tuple(code for code in BLOCKER_ORDER if code in blockers)


def _batch_comparison(r1_manifest: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "option": "BREAKFAST_CLUSTER_4",
            "recipe_ids": ["USSR82-453", "USSR82-467", "USSR82-492", "USSR82-1081"],
            "role_coverage": {"breakfast": 4, "main": 0},
            "mode_independent_local_closure": {
                "USSR82-467": ["REQUIRED_QUANTITY_UNRESOLVED"],
                "USSR82-492": ["REQUIRED_QUANTITY_UNRESOLVED"],
            },
            "mode_dependent_local_closure": {
                "USSR82-453": ["COMPOSITION_AUTHORITY", "CONSUMED_NUTRITION_AUTHORITY"],
                "USSR82-467": ["CONSUMED_NUTRITION_AUTHORITY"],
                "USSR82-492": ["CONSUMED_NUTRITION_AUTHORITY"],
                "USSR82-1081": [
                    "COMPOSITION_AUTHORITY",
                    "CONSUMED_NUTRITION_AUTHORITY",
                ],
            },
            "authority_value": "strong shared cooked-Nutrition learning across four breakfasts",
            "r1c_role_gap": "does not create MAIN capacity by itself",
        },
        {
            "option": "MIXED_AUTHORITY_PILOT",
            "recipe_ids": ["USSR82-453", "USSR82-697"],
            "role_coverage": {"breakfast": 1, "main": 1},
            "mode_independent_local_closure": {
                "USSR82-697": ["FOOD_IDENTITY_OR_FORM"],
            },
            "mode_dependent_local_closure": {
                "USSR82-453": ["COMPOSITION_AUTHORITY", "CONSUMED_NUTRITION_AUTHORITY"],
                "USSR82-697": ["CONSUMED_NUTRITION_AUTHORITY"],
            },
            "authority_value": (
                "tests one breakfast and one main against the same cooked-consumption "
                "authority decision framework while advancing the two Planner role "
                "families needed for a complete week"
            ),
            "r1c_role_gap": "still insufficient alone for a robust seven-day catalogue",
        },
        {
            "option": "HISTORICAL_MAIN_BLOCKERS",
            "recipe_ids": ["USSR82-364", "USSR82-208"],
            "role_coverage": {"breakfast": 0, "main": 2},
            "mode_independent_local_closure": {
                "USSR82-364": list(r1_manifest["USSR82-364"].get("blockers", ())),
                "USSR82-208": list(r1_manifest["USSR82-208"].get("blockers", ())),
            },
            "mode_dependent_local_closure": {},
            "authority_value": "adds MAIN diversity but first requires unresolved food identity/form work",
            "r1c_role_gap": "does not add breakfast capacity",
        },
        {
            "option": "SCHOOL2022_PILOT_PATH",
            "recipe_ids": [],
            "role_coverage": {},
            "mode_independent_local_closure": {
                "family": ["HOUSEHOLD_APPLICABILITY_REVIEW_REQUIRED"]
            },
            "mode_dependent_local_closure": {},
            "authority_value": (
                "large future corpus, but retained evidence does not yet support "
                "recipe-level household-role ranking for a production batch"
            ),
            "r1c_role_gap": "candidate identities must be selected only after applicability review",
        },
    ]


def build() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    inventory = _jsonl(R1D)
    dc1 = _dc1()
    r1_manifest = _r1_manifest()
    r1b = _r1b_blockers()

    rows: list[dict[str, Any]] = []
    for item in inventory:
        source_id = item["source_recipe_id"]
        family = item["source_family"]
        known: set[str] = set()
        later_gates: set[str] = set()
        refs = {EVIDENCE["r1d"], EVIDENCE["candidate_universe"]}
        role = r1_manifest.get(source_id, {}).get("target_role_family")
        classification_basis = "FAMILY_LEVEL_RETAINED_EVIDENCE"

        if item["production_catalogue_state"].startswith("PUBLISHED"):
            known.update(r1b.get(source_id, ()))
            if source_id == "ru-school2022:recipe:53-19з":
                known.update({"ROLE_OR_MEAL_COMPOSITION", "ACTIVATION_REQUIRED"})
                refs.add(EVIDENCE["cross_corpus_review"])
                classification_basis = "ACCEPTED_PUBLICATION_AND_REVIEW"
            elif source_id == "USSR82-697":
                known.add("FOOD_IDENTITY_OR_FORM")
                later_gates.add("CONSUMED_NUTRITION_AUTHORITY")
                refs.update({EVIDENCE["r1b"], EVIDENCE["cross_corpus_review"]})
                classification_basis = "ACCEPTED_R1_REVIEW"
            elif not item.get("production_catalogue_state", "").endswith("ACTIVE"):
                known.add("ACTIVATION_REQUIRED")
        else:
            known.add("RECIPE_PUBLICATION_REQUIRED")

            if family == "USSR82":
                source = dc1[source_id]
                refs.add(EVIDENCE["dc1"])
                classification_basis = "DC1_RECIPE_LEVEL_EVIDENCE"

                if source_id in r1b:
                    known.update(r1b[source_id])
                    refs.update({EVIDENCE["r1b"], EVIDENCE["cross_corpus_review"]})
                    classification_basis = "ACCEPTED_R1_REVIEW"
                else:
                    if source[
                        "source_structure_status"
                    ] != "SINGLE_VARIANT_NO_EXPLICIT_ALTERNATIVE" or source[
                        "variant_selection_status"
                    ] not in {
                        "SIMPLE_SOURCE_BRANCH_CANDIDATE",
                        "REVIEWED_SOURCE_BRANCH",
                    }:
                        known.add("SOURCE_STRUCTURE_OR_VARIANT")
                    if _split_ids(source.get("dc2_required_ids")) or _split_ids(
                        source.get("semantic_label_review_ids")
                    ):
                        known.add("FOOD_IDENTITY_OR_FORM")

            elif family == "ru-school2022":
                # Per-card household applicability is not established by the retained
                # aggregate closure. Do not turn aggregate zero-Nutrition-ready counts
                # into a per-recipe consumed-Nutrition fact.
                known.add("HOUSEHOLD_APPLICABILITY")
                later_gates.add("CONSUMED_NUTRITION_AUTHORITY")
                refs.add(EVIDENCE["cross_corpus_review"])

            elif family == "RU-MR-2019":
                known.add("HOUSEHOLD_APPLICABILITY")
                refs.add(EVIDENCE["cross_corpus_review"])
            else:
                known.add("HOUSEHOLD_APPLICABILITY")

        if source_id in SELECTED_COOKED_R1:
            known.add("CONSUMED_NUTRITION_AUTHORITY")
            later_gates.discard("CONSUMED_NUTRITION_AUTHORITY")
            refs.add(EVIDENCE["cross_corpus_review"])

        ordered_known = _ordered(known)
        next_blocker = ordered_known[0] if ordered_known else "PLANNER_READY"

        mode_independent = tuple(
            blocker
            for blocker in R1_MODE_INDEPENDENT.get(source_id, ())
            if blocker in known
        )
        mode_dependent = tuple(
            blocker
            for blocker in R1_MODE_DEPENDENT.get(source_id, ())
            if blocker in known or blocker in later_gates
        )

        rows.append(
            {
                "source_family": family,
                "source_recipe_id": source_id,
                "source_name": item.get("source_name"),
                "planner_capacity_role": role,
                "production_catalogue_state": item["production_catalogue_state"],
                "known_blockers": list(ordered_known),
                "unproven_later_gates": list(_ordered(later_gates)),
                "next_blocker": next_blocker,
                "mode_independent_blockers": list(mode_independent),
                "mode_dependent_blockers": list(mode_dependent),
                "classification_basis": classification_basis,
                "evidence_refs": sorted(refs),
            }
        )

    rows.sort(key=lambda row: (row["source_family"], row["source_recipe_id"]))

    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    known_counts = Counter()
    later_gate_counts = Counter()
    next_counts = Counter()
    for row in rows:
        for blocker in row["known_blockers"]:
            known_counts[blocker] += 1
            by_family[row["source_family"]][blocker] += 1
        for gate in row["unproven_later_gates"]:
            later_gate_counts[gate] += 1
        next_counts[row["next_blocker"]] += 1

    summary = {
        "schema_version": 2,
        "accepted_base": "48707e1e84eff260726609c4508f05407e9f9448",
        "total_retained_recipes": len(rows),
        "source_family_counts": dict(
            sorted(Counter(row["source_family"] for row in rows).items())
        ),
        "known_blocker_counts": dict(sorted(known_counts.items())),
        "unproven_later_gate_counts": dict(sorted(later_gate_counts.items())),
        "next_blocker_counts": dict(sorted(next_counts.items())),
        "known_blocker_counts_by_family": {
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

    comparison = _batch_comparison(r1_manifest)
    selected_ids = ("USSR82-453", "USSR82-697")
    selected = [row for row in rows if row["source_recipe_id"] in selected_ids]
    batch = {
        "schema_version": 2,
        "accepted_base": "48707e1e84eff260726609c4508f05407e9f9448",
        "selection": "FIRST_MIXED_COOKED_AUTHORITY_PILOT",
        "recipe_ids": list(selected_ids),
        "role_coverage": {"breakfast": 1, "main": 1},
        "candidate_count": len(selected),
        "mode_independent_local_blockers": {
            row["source_recipe_id"]: row["mode_independent_blockers"]
            for row in selected
        },
        "mode_dependent_local_blockers": {
            row["source_recipe_id"]: row["mode_dependent_blockers"] for row in selected
        },
        "decision": (
            "Use one breakfast and one main as the first cooked-Nutrition authority "
            "pilot. Close only mode-independent prerequisites unconditionally. "
            "Resolve the consumed-Nutrition authority mode before spending work on "
            "mode-dependent Composition closure; activation remains downstream of "
            "accepted Nutrition authority."
        ),
        "comparison": comparison,
        "expansion_batch_after_pilot": [
            "USSR82-467",
            "USSR82-492",
            "USSR82-1081",
        ],
        "why_selected": (
            "This pair covers both Planner role families required by the R1-C week "
            "while exercising the same cooked-consumption authority decision. "
            "The four-breakfast cluster remains the immediate expansion path after "
            "the authority mode is proven."
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
