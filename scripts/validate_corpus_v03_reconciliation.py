"""Validate the pinned DC1 metadata package without accessing external books."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def load_rows(root: Path, name: str) -> dict:
    rows = [json.loads(line) for line in (root / name).read_text().splitlines()]
    result = {row["id"]: row for row in rows}
    require(len(result) == len(rows), f"duplicate ids: {name}")
    require(
        all(r.get("publication_ready") is False for r in rows),
        f"publication promotion: {name}",
    )
    return result


def validate(root: Path) -> dict:
    expected_files = {
        "summary.json",
        "git-inputs.json",
        "review-batches.json",
        "recipe-crosswalk.jsonl",
        "food-demand.jsonl",
        "pr70-food-crosswalk.jsonl",
        "route-index.jsonl",
        "food-review-groups.jsonl",
        "book-reference-index.jsonl",
    }
    hashes = {}
    for line in (root / "checksums.sha256").read_text().splitlines():
        sha, name = line.split("  ")
        require(name not in hashes and name in expected_files, "invalid manifest entry")
        hashes[name] = sha
        require(
            hashlib.sha256((root / name).read_bytes()).hexdigest() == sha,
            f"hash mismatch: {name}",
        )
    require(set(hashes) == expected_files, "incomplete checksum inventory")
    require(
        {p.name for p in root.iterdir()} == expected_files | {"checksums.sha256"},
        "unexpected files",
    )
    recipes = load_rows(root, "recipe-crosswalk.jsonl")
    foods = load_rows(root, "food-demand.jsonl")
    old = load_rows(root, "pr70-food-crosswalk.jsonl")
    routes = load_rows(root, "route-index.jsonl")
    groups = load_rows(root, "food-review-groups.jsonl")
    books = load_rows(root, "book-reference-index.jsonl")
    summary = json.loads((root / "summary.json").read_text())
    expected = {
        "pr70_recipe_families": 68,
        "pr70_food_identities": 96,
        "v03_cards": 479,
        "v03_routes": 1473,
        "food_occurrences_not_canonical_foods": 2693,
        "source_book_records": 1113,
        "reference_unique_source_codes": 412,
        "nonclinical_material_routes": 377,
        "nonclinical_procurement_routes": 376,
        "publication_ready_foods": 0,
        "publication_ready_recipes": 0,
        "exact_cross_edition_joins": 0,
    }
    require(
        all(summary[k] == v for k, v in expected.items()),
        "pinned release summary changed",
    )
    require(
        not summary["production_changed"] and not summary["pr70_merged"],
        "scope/status promotion",
    )
    require(
        (len(recipes), len(foods), len(old), len(routes), len(books))
        == (547, 2693, 96, 1473, 1113),
        "incomplete release accounting",
    )
    for row in recipes.values():
        if row["id"].startswith("pr70:"):
            require(
                row["edition_namespace"] == "USSR82" and row["v03_card_id"] is None,
                "historical edition promoted",
            )
            require(
                all("pr70:" + i in old for i in row["ingredient_ids"]),
                "missing historical food",
            )
        else:
            require(row["pr70_recipe_id"] is None, "unproven cross-edition join")
            actual = sorted(
                r["id"]
                for r in routes.values()
                if r["card_id"] == row["source_record_id"]
            )
            require(
                row["route_ids"] == actual and bool(actual), "card routes not closed"
            )
    eligible = {
        r["id"]
        for r in routes.values()
        if r["material_ready"] and not r["clinical_scope"]
    }
    require(len(eligible) == 377, "clinical/material partition changed")
    require(
        sum(r["procurement_ready"] and not r["clinical_scope"] for r in routes.values())
        == 376,
        "procurement count changed",
    )
    for row in foods.values():
        require(row["canonical_food_id"] is None, "unreviewed canonical identity")
        require(row["review_group_id"] in groups, "dangling review group")
        require(
            row["id"] in groups[row["review_group_id"]]["occurrence_ids"],
            "wrong reverse group",
        )
        actual = sorted(
            r["id"] for r in routes.values() if row["id"] in r["food_occurrence_ids"]
        )
        require(actual == row["route_ids"], "occurrence reverse links changed")
    for row in routes.values():
        require(set(row["food_occurrence_ids"]) <= foods.keys(), "dangling route food")
    members = [i for g in groups.values() for i in g["occurrence_ids"]]
    require(
        len(members) == len(set(members)) == len(foods)
        and set(members) == foods.keys(),
        "review group partition",
    )
    require(
        all(g["is_semantic_equivalence"] is False for g in groups.values()),
        "lexical equivalence promoted",
    )
    require(
        all(r["exact_v03_mapping"] is None for r in old.values()),
        "unreviewed PR70 mapping promotion",
    )
    require(
        all(r["canonical_food_id"] is None for r in books.values()),
        "book identity promoted",
    )
    require(
        all(
            r["source_pdf_sha256"]
            == "e9c302fea52547222b778a3313d876135190131a4f2a04bf59f9b0751a4388d5"
            for r in books.values()
        ),
        "wrong book edition hash",
    )
    reviewed_codes = {
        (r["source_id"], r["source_code"]) for r in books.values() if r["review_layers"]
    }
    require(len(reviewed_codes) == 412, "reference layer accounting")
    batches = json.loads((root / "review-batches.json").read_text())
    batch_ids = [b["id"] for b in batches]
    require(len(batch_ids) == len(set(batch_ids)), "duplicate batches")
    require(
        all(b["publication_ready"] is False for b in batches),
        "batch prematurely publishable",
    )
    food_batches = [
        b for b in batches if b["kind"] == "food_review_queue_not_publication"
    ]
    recipe_batches = [
        b for b in batches if b["kind"] == "recipe_route_review_queue_not_publication"
    ]
    require(
        len(food_batches) + len(recipe_batches) == len(batches), "unknown batch kind"
    )
    food_members = [i for b in food_batches for i in b["food_occurrence_ids"]]
    require(
        len(food_members) == len(set(food_members)) == len(foods)
        and set(food_members) == foods.keys(),
        "food batch partition",
    )
    for b in food_batches:
        require(set(b["review_group_ids"]) <= groups.keys(), "unknown batch group")
        expected_members = sorted(
            i for gid in b["review_group_ids"] for i in groups[gid]["occurrence_ids"]
        )
        require(b["food_occurrence_ids"] == expected_members, "batch/group mismatch")
    membership = {i: b["id"] for b in food_batches for i in b["food_occurrence_ids"]}
    route_members = [i for b in recipe_batches for i in b["route_ids"]]
    require(
        len(route_members) == len(set(route_members))
        and set(route_members) == eligible,
        "route batch partition",
    )
    for b in recipe_batches:
        needed = sorted(
            {
                membership[i]
                for rid in b["route_ids"]
                for i in routes[rid]["food_occurrence_ids"]
            }
        )
        require(b["dependencies"] == needed, "lost recipe dependencies")
    return {
        "status": "PASS",
        "recipes_accounted": len(recipes),
        "food_occurrences_accounted": len(foods),
        "review_batches": len(batches),
        "production_publications": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.package), ensure_ascii=False))
