"""Offline validation of the bounded B2-B1 research; never writes production data."""

import argparse
from collections import Counter
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("data/curation/pr6-data-b2b1")
BASE = "7f17b1372bbd2e9f97fc025ac26b3f04a15cf837"
BASELINE = "data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json"
BASELINE_SHA256 = "baac9e19b0b6cd3f6990a059a098ab5d69162b9c5459db0e61d9e59e4b547100"
HEAD = "0027_recipe_same_source_revisions"
TARGET_ISSUES = {
    "FOOD_FORM_MISMATCH",
    "IDENTITY_MISMATCH",
    "PROFILE_REPRESENTATIVENESS_REVIEW",
}
RESOLUTIONS = {
    "CURRENT_PROFILE_CONFIRMED_COMPATIBLE",
    "REPLACE_CURRENT_PROFILE_SAFE",
    "REMAP_TO_EXISTING_FOOD_INGREDIENT",
    "ADD_NUTRITION_RELEVANT_FOOD_INGREDIENT",
    "EDIBLE_BASIS_OR_YIELD_REQUIRED",
    "SOURCE_FORM_AMBIGUOUS",
    "NO_ACCEPTABLE_PROFILE_SOURCE",
    "ARCHITECTURE_DECISION_REQUIRED",
}
CONVERSIONS = {
    "ALREADY_EXACT",
    "DIRECT_G_MASS",
    "STILL_EXACT_EVIDENCE_NEEDED",
    "STILL_ESTIMATE_ONLY",
    "STILL_MEASURE_OR_SIZE_AMBIGUOUS",
    "STILL_EDIBLE_YIELD_REQUIRED",
    "NOT_ASSESSED_IN_B2_B1",
}
UNRESOLVED = {
    "EDIBLE_BASIS_OR_YIELD_REQUIRED",
    "SOURCE_FORM_AMBIGUOUS",
    "NO_ACCEPTABLE_PROFILE_SOURCE",
    "ARCHITECTURE_DECISION_REQUIRED",
}
PROTECTED_PREFIXES = (
    "backend/",
    "frontend/",
    "launcher/",
    "data/seed/",
    "data/curation/",
    "scripts/",
)
ALLOWED_CHANGES = {
    str(DIRECTORY / name)
    for name in (
        "semantic-profile-audit.json",
        "source-manifest.json",
        "summary.json",
        "README.md",
    )
} | {
    "scripts/validate_pr6_data_b2b1.py",
    "backend/app/tests/test_pr6_data_b2b1_research.py",
    "docs/family-food/nutrition-data-readiness.md",
    "docs/family-food/architecture.md",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
}
RELEASE_HASHES = {
    "FOUNDATION-RELEASE": "70457ee9d9342f43bda2010318c85f04210c689fdeb9cd2da4c513b0e8dbc655",
    "SR-RELEASE": "b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0",
    "FNDDS-RELEASE": "dfb06ae7ddc397ccd570b91c14b75438ab2ba39f64f22d321f61d4a52a77f3eb",
}
RECIPE_PROVENANCE_KEYS = {
    "source_name",
    "source_recipe_id",
    "source_url",
    "source_version",
    "source_document_sha256",
    "source_retrieved_at",
}
NUTRIENTS = {
    "kcal": "1008",
    "protein_g": "1003",
    "fat_g": "1004",
    "carbohydrates_g": "1005",
    "fiber_g": "1079",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def stable(code, version, position):
    return f"{code}:v{version}:{position}"


def row_id(row):
    return stable(
        row["recipe_canonical_code"],
        row["current_recipe_version_number"],
        row["ingredient_position"],
    )


def normalized(values):
    return {k: None if v == "" else v for k, v in values.items()}


def csv_rows(root, name):
    with (root / "data/seed/food_ingredients" / name).open(
        encoding="utf-8", newline=""
    ) as source:
        return list(csv.DictReader(source))


def current_catalogue(root):
    recipes = {
        r["canonical_code"]: r
        for r in read_json(root / "data/seed/recipes/recipes.json")["recipes"]
    }
    for correction in read_json(
        root / "data/seed/recipe_corrections/pr6-data-b2a/corrections.json"
    )["corrections"]:
        recipes[correction["recipe_canonical_code"]] = correction["revision"]
    baseline = read_json(root / BASELINE)
    versions = {r["recipe"]: r["current_version_number"] for r in baseline["records"]}
    assessments = {
        stable(r["recipe"], r["current_version_number"], x["position"]): x
        for r in baseline["records"]
        for x in r["rows"]
    }
    ingredients = {}
    for code, recipe in recipes.items():
        for position, ingredient in enumerate(recipe["version"]["ingredients"], 1):
            ingredients[stable(code, versions[code], position)] = ingredient
    return recipes, versions, assessments, ingredients


def summarize(audit):
    rows = audit["rows"]
    selected = sorted(
        {
            r["candidate_profile_source_manifest_id"]
            for r in rows
            if r["candidate_profile_source_manifest_id"]
        }
    )

    def ids(predicate):
        return sorted(r["stable_row_identity"] for r in rows if predicate(r))

    result = {
        "schema_version": 1,
        "operation": "PR6-DATA-B2-B1",
        "starting_main": BASE,
        "current_audit_sha256": audit["current_audit_sha256"],
        "target_issue_occurrence_counts": dict(
            sorted(
                Counter(
                    i
                    for r in rows
                    for i in r["current_issue_codes"]
                    if i in TARGET_ISSUES
                ).items()
            )
        ),
        "distinct_target_row_count": sum(
            bool(TARGET_ISSUES.intersection(r["current_issue_codes"])) for r in rows
        ),
        "affected_recipe_codes": sorted({r["recipe_canonical_code"] for r in rows}),
        "affected_food_ingredient_codes": sorted(
            {r["food_ingredient_code"] for r in rows}
        ),
        "resolution_code_counts": {
            code: sum(r["resolution_code"] == code for r in rows)
            for code in sorted(RESOLUTIONS)
        },
        "rows_requiring_recipe_revision": ids(
            lambda r: r["recipe_revision_required"] is True
        ),
        "rows_requiring_catalogue_addition": ids(
            lambda r: r["resolution_code"] == "ADD_NUTRITION_RELEVANT_FOOD_INGREDIENT"
        ),
        "rows_requiring_existing_remap": ids(
            lambda r: r["proposed_existing_remap_code"] is not None
        ),
        "rows_where_profile_replacement_is_globally_safe": ids(
            lambda r: r["global_replacement_safe"]
        ),
        "rows_requiring_edible_yield_work": ids(
            lambda r: r["resolution_code"] == "EDIBLE_BASIS_OR_YIELD_REQUIRED"
        ),
        "unresolved_rows": ids(lambda r: r["resolution_code"] in UNRESOLVED),
        "candidate_new_food_ingredient_codes": sorted(
            {
                r["proposed_food_ingredient_code"]
                for r in rows
                if r["proposed_food_ingredient_code"]
            }
        ),
        "candidate_profile_manifest_ids": selected,
        "conversion_after_resolution_counts": {
            code: sum(r["conversion_after_semantic_resolution"] == code for r in rows)
            for code in sorted(CONVERSIONS)
        },
        "all_usage_row_count": sum(
            len(usages) for usages in audit["food_ingredient_usage_matrix"].values()
        ),
        "all_usage_recipe_count": len(
            {
                u["recipe_canonical_code"]
                for usages in audit["food_ingredient_usage_matrix"].values()
                for u in usages
            }
        ),
        "architecture_recommendation": audit["architecture_recommendation"],
        "estimate_boundary": audit["estimate_boundary"],
        "migration_head": audit["migration_head"],
        "production_mutations": 0,
        "protected_file_count": len(audit["protected_file_sha256"]),
        "count_interpretation": "Row requirements are proposed minimums, not authorizations; null requirements on unresolved rows are excluded. All candidates require project review. Unresolved includes yield, source and architecture dependencies.",
    }
    for key in (
        "rows_requiring_recipe_revision",
        "rows_requiring_catalogue_addition",
        "rows_requiring_existing_remap",
        "rows_where_profile_replacement_is_globally_safe",
        "rows_requiring_edible_yield_work",
        "unresolved_rows",
    ):
        result[key + "_count"] = len(result[key])
    result["affected_recipe_count"] = len(result["affected_recipe_codes"])
    result["affected_food_ingredient_count"] = len(
        result["affected_food_ingredient_codes"]
    )
    result["candidate_new_food_ingredient_count"] = len(
        result["candidate_new_food_ingredient_codes"]
    )
    result["candidate_profile_count"] = len(selected)
    return result


def validate_profiles(sources):
    for mid, expected_hash in RELEASE_HASHES.items():
        require(
            mid in sources and sources[mid]["archive_sha256"] == expected_hash,
            f"{mid}: official release archive hash mismatch",
        )
    for mid, source in sources.items():
        for key in (
            "source_type",
            "source_authority",
            "source_id",
            "source_version_or_release",
            "source_url",
            "license_or_terms_note",
        ):
            require(source.get(key), f"{mid}: missing provenance {key}")
        require("retrieved_at" in source, f"{mid}: retrieval metadata absent")
        if source["source_type"] != "OFFICIAL_NUTRITION_PROFILE":
            continue
        require(
            source["source_authority"] == "USDA ARS"
            and source["source_name"] == "USDA_FDC"
            and source["retrieved_at"],
            f"{mid}: official authority/retrieval missing",
        )
        require(
            source["source_url"]
            == "https://fdc.nal.usda.gov/food-details/"
            + source["source_id"]
            + "/nutrients",
            f"{mid}: official source URL mismatch",
        )
        release = sources.get(source["release_manifest_id"])
        require(
            release and release["source_type"] == "OFFICIAL_DATASET",
            f"{mid}: release missing",
        )
        require(
            source["source_version_or_release"] == release["source_version_or_release"],
            f"{mid}: release mismatch",
        )
        require(
            source["source_data_type"] and source["food_description"],
            f"{mid}: profile provenance absent",
        )
        raw = source["source_extract"]
        require(
            digest(canonical(raw)) == source["source_extract_sha256"],
            f"{mid}: source extract hash mismatch",
        )
        if "food.csv" in raw:
            food = raw["food.csv"]
            fid, description = food["fdc_id"], food["description"]
            require(
                source["source_data_type"]
                == {"foundation_food": "Foundation", "sr_legacy_food": "SR Legacy"}.get(
                    food["data_type"]
                )
                and source["publication_date"] == food["publication_date"],
                f"{mid}: source data type/publication mismatch",
            )
            values = {n["nutrient_id"]: n["amount"] for n in raw["food_nutrient.csv"]}
            require(
                all(n["fdc_id"] == fid for n in raw["food_nutrient.csv"]),
                f"{mid}: mixed source foods",
            )
        else:
            fid, description = str(raw["fdcId"]), raw["description"]
            require(
                source["source_data_type"] == raw["dataType"]
                and source["publication_date"] == raw["publicationDate"],
                f"{mid}: source data type/publication mismatch",
            )
            values = {
                str(n["nutrient"]["id"]): str(n["amount"]) for n in raw["foodNutrients"]
            }
            require(raw["inputFoods"], f"{mid}: generic survey inputs missing")
        require(
            fid == source["source_id"] and description == source["food_description"],
            f"{mid}: source identity mismatch",
        )
        profile = source["profile"]
        require(profile["basis_grams"] == "100", f"{mid}: unsupported basis")
        require(
            profile["estimated"] is None,
            f"{mid}: research cannot declare an estimated flag",
        )
        require(
            profile["energy_nutrient_id"] in ("1008", "2048"),
            f"{mid}: energy identifier",
        )
        for field, nutrient in NUTRIENTS.items():
            value = profile[field]
            nutrient = profile["energy_nutrient_id"] if field == "kcal" else nutrient
            require(
                value == values.get(nutrient),
                f"{mid}: {field} differs from retained source fact",
            )
            if value is None:
                require(field == "fiber_g", f"{mid}: missing required nutrient {field}")
                continue
            require(isinstance(value, str), f"{mid}: {field} must be Decimal text")
            try:
                number = Decimal(value)
            except InvalidOperation as exc:
                raise ValueError(f"{mid}: invalid Decimal {field}") from exc
            require(
                number.is_finite() and number >= 0,
                f"{mid}: invalid nonnegative {field}",
            )


def validate_content(audit, manifest, root=ROOT):
    require(audit["starting_main"] == BASE, "exact starting-main authority mismatch")
    require(
        audit["current_audit_path"] == BASELINE
        and audit["current_audit_sha256"] == BASELINE_SHA256,
        "B2-A authority mismatch",
    )
    require(
        digest((root / BASELINE).read_bytes()) == BASELINE_SHA256,
        "B2-A audit v3 bytes changed",
    )
    require(audit["migration_head"] == HEAD, "migration head claim changed")
    recipes, versions, assessments, ingredients = current_catalogue(root)
    targets = {
        key
        for key, value in assessments.items()
        if TARGET_ISSUES.intersection(value["issues"])
    }
    rows = audit["rows"]
    keys = [row_id(r) for r in rows]
    require(len(keys) == len(set(keys)), "duplicate stable row identity")
    require(targets <= set(keys), "target coverage incomplete")
    for r in rows:
        require(
            row_id(r) in targets or r.get("non_target_inclusion_justification"),
            "unjustified non-target row",
        )
    sources = {s["manifest_id"]: s for s in manifest["sources"]}
    require(len(sources) == len(manifest["sources"]), "duplicate manifest source")
    validate_profiles(sources)
    foods = {
        r["canonical_code"]: normalized(r) for r in csv_rows(root, "ingredients.csv")
    }
    profiles = {
        r["canonical_code"]: normalized(r) for r in csv_rows(root, "nutrition.csv")
    }
    aliases = csv_rows(root, "aliases.csv")
    pr4 = {
        s["recipe_source_id"]: s
        for s in read_json(root / "data/seed/recipes/source-manifest.json")["sources"]
    }
    data_a = {
        s["manifest_id"]: s
        for s in read_json(root / "data/curation/pr6-data-a/source-manifest.json")[
            "sources"
        ]
    }
    affected = {ingredients[k]["food_ingredient_code"] for k in targets}
    matrix = audit["food_ingredient_usage_matrix"]
    require(set(matrix) == affected, "affected FoodIngredient usage matrix mismatch")
    for food, usages in matrix.items():
        expected = {
            k for k, i in ingredients.items() if i["food_ingredient_code"] == food
        }
        require(
            len(usages) == len(expected) and {row_id(u) for u in usages} == expected,
            f"{food}: incomplete all-usage analysis",
        )
        for u in usages:
            identity = row_id(u)
            require(
                all(u.get(k) == v for k, v in ingredients[identity].items()),
                f"{identity}: current usage data mismatch",
            )
            require(
                u["source_form_review"] and u["global_profile_constraint"],
                f"{identity}: form review missing",
            )
            version = recipes[u["recipe_canonical_code"]]["version"]
            mid = "RECIPE-" + version["source_recipe_id"]
            require(
                u["recipe_source_manifest_id"] == mid and mid in sources,
                f"{identity}: original source reference missing",
            )
            source = sources[mid]
            require(
                source["source_type"] == "ORIGINAL_RECIPE"
                and all(
                    source[k] == version[v]
                    for k, v in {
                        "source_name": "source_name",
                        "source_id": "source_recipe_id",
                        "source_url": "source_url",
                        "source_version_or_release": "source_version",
                        "retrieved_at": "source_retrieved_at",
                    }.items()
                ),
                f"{identity}: original source provenance mismatch",
            )
            accepted = version["source_document_sha256"]
            require(
                source["accepted_sha256"]
                == source["reopened_sha256"]
                == accepted
                == pr4[version["source_recipe_id"]]["source_document_sha256"]
                == data_a[mid]["accepted_sha256"],
                f"{identity}: original artifact provenance/hash mismatch",
            )
            require(
                source["reopened_at"] and source["reviewed_location"],
                f"{identity}: original source inspection absent",
            )
            require(
                any(
                    f["ingredient_position"] == u["ingredient_position"]
                    and f["food_ingredient_code"] == food
                    and f["review"] == u["source_form_review"]
                    for f in source["reviewed_source_facts"]
                ),
                f"{identity}: original form reading missing",
            )
    for r in rows:
        identity = row_id(r)
        require(
            r["stable_row_identity"] == identity,
            "stable identity disagrees with current version/position",
        )
        require(identity in ingredients, f"{identity}: not a current production row")
        ingredient = ingredients[identity]
        food = ingredient["food_ingredient_code"]
        require(r["food_ingredient_code"] == food, f"{identity}: food mismatch")
        for key in (
            "quantity",
            "unit",
            "source_amount_text",
            "normalization_note",
            "prep_note",
            "optional",
        ):
            name = "recipe_" + key if key in ("quantity", "unit") else key
            require(
                r[name] == ingredient[key], f"{identity}: production {key} mismatch"
            )
        version = recipes[r["recipe_canonical_code"]]["version"]
        require(
            set(r["recipe_source"]) == RECIPE_PROVENANCE_KEYS
            and all(version[k] == v for k, v in r["recipe_source"].items()),
            f"{identity}: recipe source provenance mismatch",
        )
        require(
            r["current_profile"] == profiles[food],
            f"{identity}: current profile provenance mismatch",
        )
        require(
            r["food_ingredient"]
            == {
                **foods[food],
                "aliases": [a for a in aliases if a["canonical_code"] == food],
            },
            f"{identity}: catalogue facts mismatch",
        )
        require(
            r["current_issue_codes"] == assessments[identity]["issues"]
            and r["current_assessment_status"] == assessments[identity]["assessment"],
            f"{identity}: current issue occurrence/status mismatch",
        )
        require(
            r["all_current_food_ingredient_usages"] == matrix[food],
            f"{identity}: incomplete all-usage analysis",
        )
        code = r["resolution_code"]
        require(
            code in RESOLUTIONS and r["semantic_profile_resolution"] == code,
            f"{identity}: uncontrolled resolution",
        )
        require(
            r["resolution_rationale"]
            and r["source_form_preparation"]
            and r["follow_up"],
            f"{identity}: decision explanation absent",
        )
        conversion = r["conversion_after_semantic_resolution"]
        require(conversion in CONVERSIONS, f"{identity}: uncontrolled conversion")
        if code == "EDIBLE_BASIS_OR_YIELD_REQUIRED":
            require(
                conversion == "STILL_EDIBLE_YIELD_REQUIRED",
                f"{identity}: yield blocker hidden",
            )
        elif "CONVERSION_ESTIMATE_NOT_ACCEPTED" in r["current_issue_codes"]:
            require(
                conversion == "STILL_ESTIMATE_ONLY", f"{identity}: estimate promoted"
            )
        elif "MEASURE_OR_SIZE_AMBIGUOUS" in r["current_issue_codes"]:
            require(
                conversion == "STILL_MEASURE_OR_SIZE_AMBIGUOUS",
                f"{identity}: ambiguous conversion promoted",
            )
        if conversion == "DIRECT_G_MASS":
            require(r["recipe_unit"] == "g", f"{identity}: direct mass without grams")
        if conversion == "ALREADY_EXACT":
            require(
                assessments[identity]["mass_g"] is not None,
                f"{identity}: exact mass invented",
            )
        refs = r["profile_evidence"]["source_manifest_ids"]
        require(
            all(ref in sources for ref in refs),
            f"{identity}: source manifest reference missing",
        )
        require(
            all(identity in sources[ref]["decision_rows"] for ref in refs),
            f"{identity}: source reverse reference missing",
        )
        current = sources[r["profile_evidence"]["current_source_manifest_id"]]
        require(
            current["source_id"] == profiles[food]["source_id"]
            and current["food_description"]
            == r["current_profile_official_description"],
            f"{identity}: current source description mismatch",
        )
        selected = r["candidate_profile_source_manifest_id"]
        if selected:
            require(
                selected in refs
                and sources[selected]["source_type"] == "OFFICIAL_NUTRITION_PROFILE",
                f"{identity}: candidate source missing",
            )
        safe = code == "REPLACE_CURRENT_PROFILE_SAFE"
        require(
            r["global_replacement_safe"] is safe,
            f"{identity}: false global replacement claim",
        )
        if safe:
            proof = r["global_replacement_compatibility"]
            require(
                selected
                and len(proof) == len(matrix[food])
                and {p["stable_row_identity"] for p in proof}
                == {row_id(u) for u in matrix[food]},
                f"{identity}: global replacement misses usages",
            )
            require(
                all(
                    p["compatible"] is True and p["rationale"] and p["source_form"]
                    for p in proof
                ),
                f"{identity}: incompatible global replacement",
            )
        if code == "ADD_NUTRITION_RELEVANT_FOOD_INGREDIENT":
            require(
                selected
                and r["proposed_food_ingredient_code"] not in foods
                and r["proposed_food_ingredient_code"]
                and r["recipe_revision_required"] is True
                and r["food_catalogue_change_required"] is True,
                f"{identity}: invalid catalogue addition",
            )
        elif code == "REMAP_TO_EXISTING_FOOD_INGREDIENT":
            require(
                r["proposed_existing_remap_code"] in foods
                and r["proposed_existing_remap_code"] != food,
                f"{identity}: invalid existing remap",
            )
        else:
            require(
                r["proposed_food_ingredient_code"] is None
                and r["proposed_existing_remap_code"] is None,
                f"{identity}: hidden remap/addition",
            )
    for mid, source in sources.items():
        require(
            set(source["decision_rows"]) <= set(keys), f"{mid}: unknown decision row"
        )
        if source["source_type"] == "OFFICIAL_NUTRITION_PROFILE":
            expected = sorted(
                r["stable_row_identity"]
                for r in rows
                if r["candidate_profile_source_manifest_id"] == mid
            )
            require(
                source["selected_by_rows"] == expected,
                f"{mid}: selected source reverse references mismatch",
            )
    concepts = audit["proposed_food_ingredients"]
    require(
        len(concepts) == len({c["code"] for c in concepts})
        and {c["code"] for c in concepts}
        == {
            r["proposed_food_ingredient_code"]
            for r in rows
            if r["proposed_food_ingredient_code"]
        },
        "proposed concept inventory mismatch",
    )
    for concept in concepts:
        require(
            concept["name"]
            and concept["relationship_rationale"]
            and concept["shopping_pantry_follow_up"],
            "concept rationale incomplete",
        )
        require(
            concept["candidate_profile_source_manifest_id"] in sources,
            "concept profile missing",
        )
    recommendation = audit["architecture_recommendation"]
    require(
        recommendation["label"] == "RECOMMENDATION"
        and recommendation["recommended_option"] in {"A", "B", "C"},
        "architecture must be a recommendation",
    )
    require(
        set(recommendation["options"]) == {"A", "B", "C"},
        "architecture alternatives incomplete",
    )
    require(
        set(recommendation["alternatives_rejected"])
        == {"A", "B", "C"} - {recommendation["recommended_option"]},
        "rejected alternatives incomplete",
    )
    for key in ("facts", "assumptions", "reasons", "consequences", "open_questions"):
        require(recommendation[key], f"architecture {key} missing")
    dimensions = {
        "nutrition_correctness",
        "recipe_truth",
        "shopping",
        "pantry",
        "catalogue_complexity",
        "source_provenance",
        "implementation_migration_impact",
    }
    require(
        all(
            set(option) == dimensions and all(option.values())
            for option in recommendation["options"].values()
        ),
        "architecture comparison incomplete",
    )
    estimates = sorted(
        k
        for k, a in assessments.items()
        if "CONVERSION_ESTIMATE_NOT_ACCEPTED" in a["issues"]
    )
    boundary = audit["estimate_boundary"]
    require(
        len(estimates) == 43
        and boundary["current_non_executable_estimate_rows"] == estimates,
        "43-estimate boundary mismatch",
    )
    require(
        all(assessments[k]["mass_g"] is None for k in estimates),
        "estimated conversion became executable",
    )
    require(
        all(
            boundary[k] == 0
            for k in (
                "estimated_candidates_accepted",
                "new_measure_evidence",
                "new_assessments",
                "new_recipe_versions",
            )
        ),
        "production/estimate authority claimed",
    )
    return summarize(audit)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def validate_protected(audit, root=ROOT):
    require(
        git(root, "rev-parse", BASE + "^{commit}").decode().strip() == BASE,
        "accepted starting commit unavailable",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE, "HEAD"],
            cwd=root,
            capture_output=True,
        ).returncode
        == 0,
        "HEAD is not descended from accepted main",
    )
    entries = {}
    for line in git(root, "ls-tree", "-r", BASE).decode().splitlines():
        metadata, path = line.split("\t", 1)
        if path.startswith(PROTECTED_PREFIXES) and not path.endswith(".DS_Store"):
            entries[path] = metadata.split()[2]
    require(
        set(entries) == set(audit["protected_file_sha256"]),
        "protected inventory differs from exact main",
    )
    object_ids = list(dict.fromkeys(entries.values()))
    batch = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=root,
        input=("\n".join(object_ids) + "\n").encode(),
        capture_output=True,
        check=True,
    ).stdout
    hashes = {}
    offset = 0
    for oid in object_ids:
        end = batch.index(b"\n", offset)
        size = int(batch[offset:end].split()[-1])
        body = batch[end + 1 : end + 1 + size]
        hashes[oid] = digest(body)
        offset = end + size + 2
    for path, oid in entries.items():
        expected = hashes[oid]
        require(
            audit["protected_file_sha256"][path] == expected,
            f"{path}: protected hash differs from accepted main",
        )
        require(
            (root / path).is_file() and digest((root / path).read_bytes()) == expected,
            f"{path}: protected production bytes changed",
        )
    changed = set(git(root, "diff", "--name-only", BASE).decode().splitlines()) - {
        ".DS_Store"
    }
    changed |= set(
        git(root, "diff", "--cached", "--name-only", BASE).decode().splitlines()
    ) - {".DS_Store"}
    added = set(
        git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()
    ) - {".DS_Store"}
    changed |= added
    require(
        changed <= ALLOWED_CHANGES,
        f"scope expansion outside research: {sorted(changed - ALLOWED_CHANGES)}",
    )
    migrations = sorted(
        p.stem for p in (root / "backend/app/migrations/versions").glob("[0-9]*.py")
    )
    require(migrations[-1] == HEAD, "migration head is not 0027")
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Regenerate summary only after validating research and protected bytes.",
    )
    args = parser.parse_args()
    audit = read_json(ROOT / DIRECTORY / "semantic-profile-audit.json")
    manifest = read_json(ROOT / DIRECTORY / "source-manifest.json")
    summary = validate_content(audit, manifest)
    count = validate_protected(audit)
    path = ROOT / DIRECTORY / "summary.json"
    if args.write_summary:
        path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    require(
        read_json(path) == summary, "summary differs from deterministic row derivation"
    )
    print(
        f"PASS B2-B1: {summary['distinct_target_row_count']} target rows; {summary['affected_recipe_count']} recipes; {summary['affected_food_ingredient_count']} foods; {count} protected files unchanged; migration {HEAD}; 43 estimates non-executable."
    )


if __name__ == "__main__":
    main()
