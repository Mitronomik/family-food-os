"""Build exact first-queue source/form review, without runtime publication."""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/dc2-first-batch-review"
RECON = ROOT / "data/curation/corpus-v03-reconciliation/generated"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def unique(rows):
    output = {r["id"]: r for r in rows}
    if len(output) != len(rows):
        raise ValueError("duplicate input identity")
    return output


def require(value, message):
    if not value:
        raise ValueError(message)


def build(corpus, output):
    lock = json.loads((PACKAGE / "input-lock.json").read_text())
    for i in lock["inputs"]:
        require(sha(corpus / i["path"]) == i["sha256"], "changed source " + i["path"])
    decisions = json.loads((PACKAGE / "decisions.json").read_text())
    unique(decisions)
    groups = unique(read_rows(RECON / "food-review-groups.jsonl"))
    batch = json.loads((RECON / "review-batches.json").read_text())[0]
    require(
        {d["review_group_id"] for d in decisions} == set(batch["review_group_ids"])
        and len(decisions) == 25,
        "queue coverage changed",
    )
    foods = unique(
        read_rows(corpus / "packages/recipe-closure/normalized/food-identities.jsonl")
    )
    book = read_rows(corpus / "packages/book2002/normalized/food-profiles.jsonl")
    by_code = defaultdict(list)
    for r in book:
        by_code[r["source_code"]].append(r)
    manual = {
        r["source_code"]: r
        for r in read_rows(
            corpus / "packages/reference-profiles/normalized/profiles.jsonl"
        )
    }
    seed = {
        r["canonical_code"]: r
        for r in csv.DictReader(
            (ROOT / "data/seed/food_ingredients/nutrition.csv").open()
        )
    }
    results = []
    occurrences = []
    profile_reviews = {}
    for d in decisions:
        require(d["publication_ready"] is False, "publication promotion")
        g = groups[d["review_group_id"]]
        require(g["search_label"] == d["label"], "label/group mismatch")
        refs = []
        for code in d["book_source_codes"]:
            require(code in by_code, "unknown book source code " + code)
            for b in by_code[code]:
                refs.append(b["id"])
                v = manual.get(code)
                profile_reviews[b["id"]] = {
                    "id": b["id"],
                    "source_code": code,
                    "pages": [b["pdf_page_macro"], b["pdf_page_micro"]],
                    "visual_review_id": v["id"] if v else None,
                    "basis_g": v["basis_g"] if v else b["basis_g"],
                    "basis_reviewed": v is not None,
                    "field_states": {k: x["state"] for k, x in v["values"].items()}
                    if v
                    else {},
                    "value_type": v["value_type"] if v else "unreviewed_ocr_candidate",
                    "canonical_nutrient_mapping": None,
                    "carbohydrate_disposition": "SOURCE_NATIVE_METHOD_NOT_CANONICAL_CHOAVL_OR_CHOCDF",
                    "zero_disposition": "NONDETECTION_NOT_EXACT_ZERO",
                    "rights_disposition": "REFERENCE_ONLY_PUBLICATION_USE_UNRESOLVED",
                    "publication_ready": False,
                }
        existing = []
        for code in d["platform_code_candidates"]:
            require(code in seed, "unknown platform code " + code)
            r = seed[code]
            existing.append(
                {
                    "code": code,
                    "source_name": r["source_name"],
                    "source_id": r["source_id"],
                    "source_version": r["source_version"],
                    "source_description": r["source_description"],
                    "reuse_approved": False,
                }
            )
        scoped = []
        for identifier in g["occurrence_ids"]:
            p = foods[identifier]["payload"]
            fat = [
                e for e in p["source_form_evidence"] if e["attribute"] == "fat_percent"
            ]
            scoped.extend(fat)
            occurrences.append(
                {
                    "id": identifier,
                    "decision_id": d["id"],
                    "source_id": foods[identifier]["source_id"],
                    "card_id": p["source_card_id"],
                    "source_demand_id": p["source_demand_id"],
                    "locator": foods[identifier]["locator"],
                    "preparation_context_sha256": p["preparation_context_sha256"],
                    "source_form_evidence": p["source_form_evidence"],
                    "candidate_book_record_ids": sorted(refs),
                    "canonical_food_id": None,
                    "exact_mapping_accepted": False,
                    "publication_ready": False,
                }
            )
        results.append(
            {
                **d,
                "candidate_book_record_ids": sorted(refs),
                "existing_profile_evidence": existing,
                "occurrence_count": len(g["occurrence_ids"]),
                "affected_material_card_ids": g[
                    "affected_nonclinical_material_card_ids"
                ],
                "fat_specification_by_source": sorted(
                    {(f["source_id"], f["value"], f["pdf_page"]) for f in scoped}
                ),
                "rights_disposition": "REFERENCE_ONLY_PUBLICATION_USE_UNRESOLVED",
            }
        )
    chosen = {r["id"] for r in occurrences}
    routes = read_rows(RECON / "route-index.jsonl")
    impact = []
    for r in routes:
        if r["clinical_scope"] or not r["material_ready"]:
            continue
        ids = set(r["food_occurrence_ids"])
        included = sorted(ids & chosen)
        if included:
            impact.append(
                {
                    "id": r["id"],
                    "card_id": r["card_id"],
                    "reviewed_occurrence_ids": included,
                    "outside_batch_occurrence_ids": sorted(ids - chosen),
                    "all_dependencies_in_review_scope": ids <= chosen,
                    "actually_unblocked": False,
                }
            )
    summary = {
        "base_commit": lock["base_commit"],
        "queue": lock["queue"],
        "reviewed_groups": len(results),
        "occurrences_accounted_under_group_review": len(occurrences),
        "exact_book_record_candidates": len(profile_reviews),
        "visual_profile_candidates": sum(
            r["visual_review_id"] is not None for r in profile_reviews.values()
        ),
        "dispositions": dict(
            sorted(Counter(d["disposition"] for d in decisions).items())
        ),
        "affected_material_routes": len(impact),
        "routes_all_dependencies_in_review_scope": sum(
            r["all_dependencies_in_review_scope"] for r in impact
        ),
        "publication_ready_foods": 0,
        "actually_unblocked_recipes": 0,
        "production_changed": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "group-reviews.json": results,
        "profile-reviews.json": sorted(profile_reviews.values(), key=lambda r: r["id"]),
        "occurrence-reviews.json": sorted(occurrences, key=lambda r: r["id"]),
        "route-impact.json": sorted(impact, key=lambda r: r["id"]),
        "summary.json": summary,
    }
    files["input-receipt.json"] = {
        "external_inputs": lock["inputs"],
        "repository_inputs": [
            {"path": str(p.relative_to(ROOT)), "sha256": sha(p)}
            for p in [
                PACKAGE / "decisions.json",
                RECON / "food-review-groups.jsonl",
                RECON / "review-batches.json",
                RECON / "route-index.jsonl",
                ROOT / "data/seed/food_ingredients/nutrition.csv",
            ]
        ],
    }
    for name, value in files.items():
        (output / name).write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        )
    (output / "checksums.sha256").write_text(
        "".join(sha(output / n) + "  " + n + "\n" for n in sorted(files))
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.corpus, args.output), ensure_ascii=False, indent=2))
