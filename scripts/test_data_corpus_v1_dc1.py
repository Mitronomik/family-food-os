from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

import validate_data_corpus_v1_dc1 as validator

Mutation = Callable[[Path], None]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise AssertionError(f"missing header: {path}")
        return list(reader.fieldnames), [dict(row) for row in reader]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def expect_rejected(package: Path, name: str, mutate: Mutation) -> None:
    with tempfile.TemporaryDirectory(prefix="dc1-negative-") as td:
        target = Path(td) / "package"
        shutil.copytree(package, target)
        mutate(target)
        try:
            validator.validate(target, check_checksums=False)
        except SystemExit:
            print(f"PASS rejected: {name}")
            return
        raise AssertionError(f"validator accepted adversarial case: {name}")


def drop_candidate(pkg: Path) -> None:
    path = pkg / "candidate-recipes.csv"
    fields, rows = read_csv(path)
    write_csv(path, fields, rows[1:])


def drop_relationship(pkg: Path) -> None:
    path = pkg / "source-relationships-part1.csv"
    fields, rows = read_csv(path)
    write_csv(path, fields, rows[1:])


def unknown_relationship_identity(pkg: Path) -> None:
    path = pkg / "source-relationships-part1.csv"
    fields, rows = read_csv(path)
    rows[0]["resolved_ingredient_id"] = "ING-UNKNOWN-NEGATIVE"
    write_csv(path, fields, rows)


def duplicate_relationship(pkg: Path) -> None:
    path = pkg / "source-relationships-part1.csv"
    fields, rows = read_csv(path)
    rows[1] = dict(rows[0])
    write_csv(path, fields, rows)


def zero_relationship_amount(pkg: Path) -> None:
    path = pkg / "source-relationships-part1.csv"
    fields, rows = read_csv(path)
    rows[0]["amount_g"] = "0"
    write_csv(path, fields, rows)


def summary_drift(pkg: Path) -> None:
    path = pkg / "summary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidate_selection"]["recipe_family_count"] += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def batch_omission(pkg: Path) -> None:
    path = pkg / "batch-plan.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    group = next(iter(data["dc2"].values()))
    group["external_ingredient_ids"].pop()
    group["count"] = len(group["external_ingredient_ids"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def batch_overlap(pkg: Path) -> None:
    path = pkg / "batch-plan.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = list(data["dc2"].values())
    duplicate_id = groups[0]["external_ingredient_ids"][0]
    groups[1]["external_ingredient_ids"].append(duplicate_id)
    groups[1]["count"] = len(groups[1]["external_ingredient_ids"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def false_simple_status(pkg: Path) -> None:
    path = pkg / "candidate-recipes.csv"
    fields, rows = read_csv(path)
    row = next(r for r in rows if r["source_recipe_id"] == "USSR82-286")
    row["variant_selection_status"] = "SIMPLE_SOURCE_BRANCH_CANDIDATE"
    row["proposed_dc3_batch"] = "DC3-A_CLEAN_BRANCH_EXISTING_PROFILE_REVIEW"
    write_csv(path, fields, rows)


def premature_profile_reuse(pkg: Path) -> None:
    path = pkg / "food-demand.csv"
    fields, rows = read_csv(path)
    row = next(r for r in rows if r["map_state"] in {"EXACT_EXISTING", "ALIAS_EXISTING"})
    row["proposed_dc2_batch"] = "REUSE_NO_DC2_WRITE"
    write_csv(path, fields, rows)


def missing_authority_assignment(pkg: Path) -> None:
    path = pkg / "food-demand.csv"
    fields, rows = read_csv(path)
    rows[0]["authority_assignment_status"] = ""
    write_csv(path, fields, rows)


def incomplete_input_metadata(pkg: Path) -> None:
    path = pkg / "source-artifacts.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    loaded = data["repository"]["mapping_rows_loaded"]
    loaded["candidate_rows_total_from_full_pr39_package"] = 68
    loaded["ingredient_mapping_rows_total_from_full_pr39_package"] = 96
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    args = parser.parse_args()
    package = Path(args.package)

    validator.validate(package, check_checksums=True)
    print("PASS baseline package")

    cases: list[tuple[str, Mutation]] = [
        ("candidate loss", drop_candidate),
        ("relationship loss", drop_relationship),
        ("relationship identity mismatch", unknown_relationship_identity),
        ("duplicate relationship", duplicate_relationship),
        ("unknown-to-zero amount substitution", zero_relationship_amount),
        ("summary drift", summary_drift),
        ("batch omission", batch_omission),
        ("batch overlap", batch_overlap),
        ("false simple status", false_simple_status),
        ("premature profile reuse", premature_profile_reuse),
        ("missing authority assignment", missing_authority_assignment),
        ("incomplete full-input metadata", incomplete_input_metadata),
    ]
    for name, mutate in cases:
        expect_rejected(package, name, mutate)

    print(f"PASS adversarial suite: {len(cases)} rejected cases")


if __name__ == "__main__":
    main()
