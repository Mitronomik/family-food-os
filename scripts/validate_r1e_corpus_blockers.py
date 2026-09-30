"""Validate the committed R1-E blocker map against deterministic rebuild."""

from __future__ import annotations

import json

from build_r1e_corpus_blockers import OUT, build


def main() -> None:
    expected_rows, expected_summary, expected_batch = build()
    actual_rows = [
        json.loads(line)
        for line in (OUT / "blocker-map.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    actual_summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    actual_batch = json.loads((OUT / "selected-batch.json").read_text(encoding="utf-8"))

    if actual_rows != expected_rows:
        raise SystemExit("R1-E blocker map differs from deterministic rebuild.")
    if actual_summary != expected_summary:
        raise SystemExit("R1-E summary differs from deterministic rebuild.")
    if actual_batch != expected_batch:
        raise SystemExit("R1-E selected batch differs from deterministic rebuild.")

    if len(actual_rows) != 547:
        raise SystemExit("R1-E must retain exactly 547 recipe identities.")
    if any(not row["next_blocker"] for row in actual_rows):
        raise SystemExit("Every R1-E row must have one deterministic next blocker.")

    school_unpublished = [
        row
        for row in actual_rows
        if row["source_family"] == "ru-school2022"
        and row["production_catalogue_state"]
        == "NOT_PUBLISHED_IN_CURRENT_RUSSIAN_R1_PATH"
    ]
    if any(
        "CONSUMED_NUTRITION_AUTHORITY" in row["known_blockers"]
        for row in school_unpublished
    ):
        raise SystemExit(
            "School2022 aggregate Nutrition evidence must not become per-recipe truth."
        )
    if any(
        row["next_blocker"] != "HOUSEHOLD_APPLICABILITY" for row in school_unpublished
    ):
        raise SystemExit(
            "Unpublished School2022 rows must stop first at household applicability."
        )

    if actual_batch["selection"] != "FIRST_MIXED_COOKED_AUTHORITY_PILOT":
        raise SystemExit("R1-E must select the reviewed mixed authority pilot.")
    if actual_batch["recipe_ids"] != ["USSR82-453", "USSR82-697"]:
        raise SystemExit("R1-E mixed pilot identities drifted.")
    if actual_batch["role_coverage"] != {"breakfast": 1, "main": 1}:
        raise SystemExit("R1-E mixed pilot must cover breakfast and main.")
    if "ACTIVATION_REQUIRED" in actual_batch["mode_independent_local_blockers"].get(
        "USSR82-697", ()
    ):
        raise SystemExit("Activation is downstream, not a pre-authority local blocker.")

    cooked_r1 = {
        "USSR82-453": "COMPOSITION_AUTHORITY",
        "USSR82-467": "REQUIRED_QUANTITY_UNRESOLVED",
        "USSR82-492": "REQUIRED_QUANTITY_UNRESOLVED",
        "USSR82-1081": "COMPOSITION_AUTHORITY",
        "USSR82-697": "FOOD_IDENTITY_OR_FORM",
    }
    by_source = {row["source_recipe_id"]: row for row in actual_rows}
    for source_id, expected_next in cooked_r1.items():
        row = by_source[source_id]
        if "CONSUMED_NUTRITION_AUTHORITY" not in row["known_blockers"]:
            raise SystemExit(
                f"{source_id} must retain the accepted cooked Nutrition blocker."
            )
        if "CONSUMED_NUTRITION_AUTHORITY" not in row["mode_dependent_blockers"]:
            raise SystemExit(
                f"{source_id} must classify cooked Nutrition as mode-dependent."
            )
        if row["next_blocker"] != expected_next:
            raise SystemExit(
                f"{source_id} local next blocker drifted: {row['next_blocker']!r}"
            )

    if actual_summary["known_blocker_counts"].get("CONSUMED_NUTRITION_AUTHORITY") != 5:
        raise SystemExit(
            "Exactly five selected cooked USSR82 rows must carry the known gap."
        )
    if (
        actual_summary["unproven_later_gate_counts"].get("CONSUMED_NUTRITION_AUTHORITY")
        != 264
    ):
        raise SystemExit(
            "Only the 264 unpublished School2022 rows should retain the unproven gate."
        )

    options = {row["option"] for row in actual_batch["comparison"]}
    required_options = {
        "BREAKFAST_CLUSTER_4",
        "MIXED_AUTHORITY_PILOT",
        "HISTORICAL_MAIN_BLOCKERS",
        "SCHOOL2022_PILOT_PATH",
    }
    if options != required_options:
        raise SystemExit(f"R1-E comparison options drifted: {options!r}")

    print("R1-E corpus blocker map: OK")


if __name__ == "__main__":
    main()
