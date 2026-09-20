"""Build metadata-only DC1 reconciliation; never publish runtime data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/corpus-v03-reconciliation"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key(label: str) -> str:
    # Search hints only: intentionally no synonyms, fuzzy matching or form inference.
    return " ".join(label.casefold().split())


def unique(rows: list[dict], field: str = "id") -> dict:
    result = {}
    for row in rows:
        identifier = row[field]
        if not identifier or identifier in result:
            raise ValueError(f"duplicate/empty {field}: {identifier}")
        result[identifier] = row
    return result


def git_csv(ref: str, path: str, receipts: list) -> list[dict]:
    data = subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)
    receipts.append({"commit": ref, "path": path, "sha256": digest(data)})
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"))))


def build(corpus: Path, output: Path) -> dict:
    lock = json.loads((PACKAGE / "input-lock.json").read_text())
    if (
        digest((corpus / "manifest.json").read_bytes())
        != lock["corpus_manifest_sha256"]
    ):
        raise ValueError("corpus manifest changed")
    inputs = {}
    for item in lock["inputs"]:
        data = (corpus / item["path"]).read_bytes()
        if digest(data) != item["sha256"]:
            raise ValueError(f"changed source: {item['path']}")
        inputs[item["path"]] = data

    def rows(package: str, name: str) -> list[dict]:
        data = inputs[f"packages/{package}/normalized/{name}.jsonl"]
        return [json.loads(line) for line in data.decode().splitlines() if line]

    receipts = []
    old_recipes = git_csv(
        lock["pr70_commit"],
        "data/curation/data-corpus-v1-dc1/candidate-recipes.csv",
        receipts,
    )
    old_foods = git_csv(
        lock["pr70_commit"],
        "data/curation/data-corpus-v1-dc1/food-demand.csv",
        receipts,
    )
    canonical = git_csv(
        lock["base_commit"], "data/seed/food_ingredients/ingredients.csv", receipts
    )
    aliases = git_csv(
        lock["base_commit"], "data/seed/food_ingredients/aliases.csv", receipts
    )
    profiles = git_csv(
        lock["base_commit"], "data/seed/food_ingredients/nutrition.csv", receipts
    )
    unique(old_recipes, "source_recipe_id")
    unique(old_foods, "external_ingredient_id")
    canonical_by_code = unique(canonical, "canonical_code")
    lookup = defaultdict(set)
    for row in canonical:
        lookup[key(row["canonical_name"])].add(row["canonical_code"])
    for row in aliases:
        if row["canonical_code"] not in canonical_by_code:
            raise ValueError("dangling accepted alias")
        lookup[key(row["alias"])].add(row["canonical_code"])
    drafts = unique(rows("recipe-closure", "food-identities"))
    bindings = unique(rows("recipe-closure", "ingredient-bindings"))
    routes = unique(rows("recipe-closure", "resolved-executions"))
    books = unique(rows("book2002", "food-profiles"))
    manual = rows("reference-profiles", "profiles")
    consensus = rows("consensus-profiles", "profiles")
    reference_index = defaultdict(list)
    for layer, values in [("visual", manual), ("dual_ocr", consensus)]:
        unique(values)
        for row in values:
            k = (
                row["source_id"],
                row["source_code"],
                row["provenance"]["source_pdf_sha256"],
            )
            reference_index[k].append({"id": row["id"], "layer": layer})
    book_hints = defaultdict(list)
    reference_rows = []
    for record in books.values():
        k = (
            record["source_id"],
            record["source_code"],
            "e9c302fea52547222b778a3313d876135190131a4f2a04bf59f9b0751a4388d5",
        )
        refs = reference_index.get(k, [])
        reference_rows.append(
            {
                "id": record["id"],
                "source_id": record["source_id"],
                "source_code": record["source_code"],
                "source_pdf_sha256": k[2],
                "pdf_pages": [record["pdf_page_macro"], record["pdf_page_micro"]],
                "review_layers": refs,
                "canonical_food_id": None,
                "publication_ready": False,
            }
        )
        book_hints[key(record["source_name_ocr"])].append(record["id"])
    for record in manual:
        # A manual label improves discovery, not canonical mapping authority.
        matches = [
            r["id"]
            for r in reference_rows
            if r["source_code"] == record["source_code"]
            and r["source_id"] == record["source_id"]
        ]
        book_hints[key(record["source_name"])].extend(matches)
    route_rows = []
    used = defaultdict(set)
    ready_cards = defaultdict(set)
    for record in routes.values():
        p = record["payload"]
        ids = sorted({i["food_identity_id"] for i in p["ingredients"]})
        if not set(ids) <= drafts.keys():
            raise ValueError("route references missing food occurrence")
        for identifier in ids:
            used[identifier].add(record["id"])
            if p["material_execution_ready"] and not p["clinical_scope"]:
                ready_cards[identifier].add(p["card_id"])
        route_rows.append(
            {
                "id": record["id"],
                "source_id": record["source_id"],
                "card_id": p["card_id"],
                "source_variant_id": p["source_variant_id"],
                "selection_id": p["selection_id"],
                "food_occurrence_ids": ids,
                "clinical_scope": p["clinical_scope"],
                "material_ready": p["material_execution_ready"],
                "procurement_ready": p["procurement_mass_ready"],
                "process_choice_count": len(p["process_choices"]),
                "material_blockers": p["material_blockers"],
                "nutrition_blockers": p["nutrition_blockers"],
                "publication_ready": False,
            }
        )
    by_draft = defaultdict(list)
    for b in bindings.values():
        identifier = b["payload"]["food_identity_id"]
        if identifier not in drafts:
            raise ValueError("binding references missing occurrence")
        by_draft[identifier].append(b)
    groups = defaultdict(list)
    for record in drafts.values():
        groups[key(record["payload"]["source_name"])].append(record["id"])
    demand_rows = []
    work_groups = []
    for label, ids in sorted(groups.items()):
        gid = "label-review:" + digest(label.encode())[:20]
        cards = sorted(set().union(*(ready_cards[i] for i in ids)))
        hints = sorted(lookup.get(label, []))
        book = sorted(set(book_hints.get(label, [])))
        work_groups.append(
            {
                "id": gid,
                "search_label": label,
                "occurrence_ids": sorted(ids),
                "affected_nonclinical_material_card_ids": cards,
                "canonical_code_search_hints": hints,
                "book_record_search_hints": book,
                "is_semantic_equivalence": False,
                "publication_ready": False,
            }
        )
        for identifier in sorted(ids):
            r = drafts[identifier]
            p = r["payload"]
            demand_rows.append(
                {
                    "id": identifier,
                    "source_id": r["source_id"],
                    "card_id": p["source_card_id"],
                    "demand_id": p["source_demand_id"],
                    "locator": r["locator"],
                    "preparation_context_sha256": p["preparation_context_sha256"],
                    "review_group_id": gid,
                    "route_ids": sorted(used[identifier]),
                    "binding_ids": sorted(b["id"] for b in by_draft[identifier]),
                    "nutrition_blockers": sorted(
                        {
                            v
                            for b in by_draft[identifier]
                            for v in b["payload"]["nutrition_blockers"]
                        }
                    ),
                    "canonical_food_id": None,
                    "mapping_disposition": "UNRESOLVED_FORM_AND_AUTHORITY",
                    "rights_disposition": "REFERENCE_ONLY_PENDING_PUBLICATION_REVIEW",
                    "publication_ready": False,
                }
            )
    old_rows = []
    for row in old_foods:
        code = row["familyfoodos_food_code"]
        if code and code not in canonical_by_code:
            raise ValueError("PR70 mapping absent on accepted base")
        old_rows.append(
            {
                "id": "pr70:" + row["external_ingredient_id"],
                "external_id": row["external_ingredient_id"],
                "existing_food_code": code or None,
                "existing_mapping_status": row["accepted_identity_mapping_status"],
                "profile_form_status": row["profile_suitability_for_recipe_form"],
                "authority_record": row["authority_record_candidate"] or None,
                "authority_status": row["authority_assignment_status"],
                "rights_status": row["rights_status"],
                "v03_label_review_hints": sorted(
                    g["id"]
                    for g in work_groups
                    if g["search_label"]
                    in {
                        key(row["v22_13_external_name"]),
                        key(row["v22_5_canonical_labels"]),
                    }
                ),
                "exact_v03_mapping": None,
                "publication_ready": False,
            }
        )
    crosswalk = []
    for row in old_recipes:
        if not row["source_recipe_id"].startswith("USSR82-"):
            raise ValueError("unreviewed PR70 edition")
        crosswalk.append(
            {
                "id": "pr70:" + row["source_recipe_id"],
                "source_record_id": row["source_recipe_id"],
                "edition_namespace": "USSR82",
                "disposition": "HISTORICAL_SEPARATE_EDITION_NO_EXACT_V03_JOIN",
                "v03_card_id": None,
                "ingredient_ids": sorted(
                    row["all_variant_union_ingredient_ids"].split(" | ")
                ),
                "branch_review_status": row["variant_selection_status"],
                "publication_ready": False,
            }
        )
    for source, card in sorted({(r["source_id"], r["card_id"]) for r in route_rows}):
        crosswalk.append(
            {
                "id": "v03:" + card,
                "source_record_id": card,
                "edition_namespace": source,
                "disposition": "V03_SEPARATE_EDITION_NO_EXACT_PR70_JOIN",
                "pr70_recipe_id": None,
                "route_ids": sorted(
                    r["id"] for r in route_rows if r["card_id"] == card
                ),
                "publication_ready": False,
            }
        )
    ranked = sorted(
        work_groups,
        key=lambda g: (-len(g["affected_nonclinical_material_card_ids"]), g["id"]),
    )
    batches = []
    for offset in range(0, len(ranked), 25):
        selected = ranked[offset : offset + 25]
        batches.append(
            {
                "id": f"DC2-REVIEW-{offset // 25 + 1:03}",
                "kind": "food_review_queue_not_publication",
                "review_group_ids": [g["id"] for g in selected],
                "food_occurrence_ids": sorted(
                    i for g in selected for i in g["occurrence_ids"]
                ),
                "required_decisions": [
                    "exact_form_identity",
                    "source_record_authority",
                    "nutrient_definition_and_zero_policy",
                    "retained_use_scope",
                    "sealed_vector_atomic_binding",
                ],
                "publication_ready": False,
            }
        )
    food_batch = {i: b["id"] for b in batches for i in b["food_occurrence_ids"]}
    eligible = sorted(
        (r for r in route_rows if r["material_ready"] and not r["clinical_scope"]),
        key=lambda r: (len(r["food_occurrence_ids"]), r["id"]),
    )
    for offset in range(0, len(eligible), 10):
        selected = eligible[offset : offset + 10]
        batches.append(
            {
                "id": f"DC3-REVIEW-{offset // 10 + 1:03}",
                "kind": "recipe_route_review_queue_not_publication",
                "route_ids": [r["id"] for r in selected],
                "dependencies": sorted(
                    {food_batch[i] for r in selected for i in r["food_occurrence_ids"]}
                ),
                "required_decisions": [
                    "product_role_and_variety_review",
                    "selected_branch_review",
                    "nutrition_process_authority",
                    "allergen_exclusion_applicability",
                    "rights",
                    "immutable_recipe_publication",
                ],
                "publication_ready": False,
            }
        )
    result = {
        "base_commit": lock["base_commit"],
        "pr70_commit": lock["pr70_commit"],
        "pr70_merged": False,
        "corpus_version": lock["corpus_version"],
        "pr70_recipe_families": len(old_recipes),
        "pr70_food_identities": len(old_foods),
        "v03_cards": len({r["card_id"] for r in route_rows}),
        "v03_routes": len(route_rows),
        "food_occurrences_not_canonical_foods": len(drafts),
        "lexical_review_groups_not_food_equivalence": len(groups),
        "source_book_records": len(books),
        "reference_unique_source_codes": len(reference_index),
        "nonclinical_material_routes": len(eligible),
        "nonclinical_procurement_routes": sum(
            r["procurement_ready"] and not r["clinical_scope"] for r in route_rows
        ),
        "accepted_seed_food_rows": len(canonical),
        "accepted_seed_nutrition_rows": len(profiles),
        "exact_cross_edition_joins": 0,
        "publication_ready_foods": 0,
        "publication_ready_recipes": 0,
        "production_changed": False,
        "remaining": [
            "review queues are not accepted publication manifests",
            "exact forms and authority unresolved",
            "nutrient semantics and source zero policy unresolved",
            "source retention/publication rights unresolved",
            "menu role/diversity acceptance not performed",
            "allergen and household storage readiness not granted",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    objects = {
        "summary.json": result,
        "git-inputs.json": receipts,
        "review-batches.json": batches,
    }
    datasets = {
        "recipe-crosswalk.jsonl": crosswalk,
        "food-demand.jsonl": demand_rows,
        "pr70-food-crosswalk.jsonl": old_rows,
        "route-index.jsonl": route_rows,
        "food-review-groups.jsonl": work_groups,
        "book-reference-index.jsonl": reference_rows,
    }
    for name, obj in objects.items():
        (output / name).write_text(
            json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
    for name, values in datasets.items():
        unique(values)
        (output / name).write_text(
            "".join(
                json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n"
                for v in sorted(values, key=lambda r: r["id"])
            )
        )
    (output / "checksums.sha256").write_text(
        "".join(
            digest((output / n).read_bytes()) + "  " + n + "\n"
            for n in sorted(objects.keys() | datasets.keys())
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.corpus, args.output), ensure_ascii=False, indent=2))
