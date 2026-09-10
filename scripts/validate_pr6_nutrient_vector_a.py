"""Offline research integrity checks. Never imports runtime or writes food data."""

import argparse
from collections import Counter
import csv
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = Path("data/curation/pr6-nutrient-vector-a")
BASE = "307ba3475581087b079ebcf2fa643e19a00bf06d"
MIGRATION_HEAD = "0027_recipe_same_source_revisions"
SEED = "data/seed/food_ingredients/nutrition.csv"
FIELDS = {
    "kcal": "ENERGY_KCAL",
    "protein_g": "PROTEIN",
    "fat_g": "FAT_TOTAL",
    "carbohydrates_g": "CARBOHYDRATE_BY_DIFFERENCE",
    "fiber_g": "FIBER_TOTAL_DIETARY",
}
UNITS_RU = {"kcal": "ккал", "g": "г", "mg": "мг", "µg": "мкг"}
STATUSES = {"APPROVED_FOR_VECTOR_B", "DEFINITION_BLOCKED", "DEFERRED_EXTENSION"}
MAPPING_STATUSES = {
    "EXACT",
    "METHOD_SPECIFIC",
    "DISTINCT_COMPONENT",
    "UNIT_CONVERSION_REQUIRED",
    "NO_ACCEPTABLE_MAPPING",
}
LEGACY_STATUSES = {
    "SOURCE_COMPONENT_CONFIRMED",
    "LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE",
    "VALUE_MISMATCH",
    "DEFINITION_AMBIGUOUS",
    "VALUE_ABSENT",
}
# Reviewed concept-to-component constraints, independently of human display names.
# Null means no FDC primary match, not that the canonical definition is absent.
PRIMARY = {
    "ENERGY_KCAL": "2048",
    "PROTEIN": "1003",
    "FAT_TOTAL": "1004",
    "CARBOHYDRATE_BY_DIFFERENCE": "1005",
    "CARBOHYDRATE_AVAILABLE": None,
    "FIBER_TOTAL_DIETARY": "1079",
    "SUGARS_TOTAL": "2000",
    "STARCH": "1009",
    "WATER": "1051",
    "FATTY_ACIDS_SATURATED_TOTAL": "1258",
    "FATTY_ACIDS_MONOUNSATURATED_TOTAL": "1292",
    "FATTY_ACIDS_POLYUNSATURATED_TOTAL": "1293",
    "FATTY_ACIDS_TRANS_TOTAL": "1257",
    "CHOLESTEROL": "1253",
    "LINOLEIC_ACID": "1316",
    "ALPHA_LINOLENIC_ACID": "1404",
    "EPA": "1278",
    "DHA": "1272",
    "CALCIUM": "1087",
    "IRON": "1089",
    "MAGNESIUM": "1090",
    "PHOSPHORUS": "1091",
    "POTASSIUM": "1092",
    "SODIUM": "1093",
    "ZINC": "1095",
    "COPPER": "1098",
    "MANGANESE": "1101",
    "SELENIUM": "1103",
    "IODINE": "1100",
    "CHLORIDE": None,
    "CHROMIUM": "1096",
    "MOLYBDENUM": "1102",
    "FLUORIDE": "1099",
    "VITAMIN_A_RAE": "1106",
    "RETINOL": "1105",
    "BETA_CAROTENE": "1107",
    "VITAMIN_C": "1162",
    "VITAMIN_D_D2_D3": "1114",
    "VITAMIN_E_ALPHA_TOCOPHEROL": "1109",
    "VITAMIN_K_PHYLLOQUINONE": "1185",
    "THIAMIN": "1165",
    "RIBOFLAVIN": "1166",
    "NIACIN": "1167",
    "PANTOTHENIC_ACID": "1170",
    "VITAMIN_B6": "1175",
    "FOLATE_TOTAL": "1177",
    "FOLATE_DFE": "1190",
    "FOLIC_ACID": "1186",
    "VITAMIN_B12": "1178",
    "BIOTIN": "1176",
    "CHOLINE_TOTAL": "1180",
}
METHOD_SPECIFIC = {
    "ENERGY_KCAL",
    "PROTEIN",
    "FAT_TOTAL",
    "CARBOHYDRATE_BY_DIFFERENCE",
    "CARBOHYDRATE_AVAILABLE",
    "FIBER_TOTAL_DIETARY",
    "SUGARS_TOTAL",
    "STARCH",
    "VITAMIN_A_RAE",
    "FOLATE_DFE",
    "VITAMIN_B6",
}
DERIVED = {
    "ENERGY_KCAL",
    "PROTEIN",
    "CARBOHYDRATE_BY_DIFFERENCE",
    "CARBOHYDRATE_AVAILABLE",
    "VITAMIN_A_RAE",
    "VITAMIN_D_D2_D3",
    "FOLATE_DFE",
}
REJECTIONS = {
    ("CARBOHYDRATE_AVAILABLE", "1005"),
    ("FAT_TOTAL", "1085"),
    ("LINOLEIC_ACID", "1269"),
    ("ALPHA_LINOLENIC_ACID", "1270"),
    ("VITAMIN_A_RAE", "1105"),
    ("VITAMIN_A_RAE", "1107"),
    ("VITAMIN_A_RAE", "1104"),
    ("VITAMIN_A_RAE", "1156"),
    ("FOLATE_DFE", "1177"),
    ("FOLATE_TOTAL", "1186"),
    ("VITAMIN_E_ALPHA_TOCOPHEROL", "1158"),
    ("VITAMIN_K_PHYLLOQUINONE", "1183"),
}
UNPROVEN = {
    ("SUGARS_TOTAL", "1063"),
    ("CHLORIDE", "1088"),
    ("CARBOHYDRATE_AVAILABLE", "1050"),
}
DIVISORS = {
    ("FLUORIDE", "1099"): "1000",
    ("ENERGY_KCAL", "1062"): "4.184",
    ("VITAMIN_D_D2_D3", "1110"): "40",
}
RELEASES = {
    "FDC-FOUNDATION": ("Foundation", "2026-04-30"),
    "FDC-SR": ("SR Legacy", "2018-04"),
}
RELEASE_HASHES = {
    "FDC-FOUNDATION": "70457ee9d9342f43bda2010318c85f04210c689fdeb9cd2da4c513b0e8dbc655",
    "FDC-SR": "b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0",
}
EXTRACT_HASHES = {
    "FDC-FOUNDATION": "8f6e4d366fbab399e9d7fac1e0251292e65cc0c023f94121ca58cdba3ff34375",
    "FDC-SR": "319e2202c7f20315cfbbf332293a045423bde7a39bae13fc32744f6907fd90ca",
}
INFOODS_HASH = "a2c36ff619f8670536c6074dc01a8cebd4a9307d5f4b504e5aecd05391009104"
FILES = (
    "nutrient-registry.json",
    "source-mappings.json",
    "legacy-v1-crosswalk.json",
    "source-manifest.json",
    "summary.json",
    "README.md",
)
ALLOWED_CHANGES = {str(DIRECTORY / name) for name in FILES} | {
    "scripts/validate_pr6_nutrient_vector_a.py",
    "backend/app/tests/test_pr6_nutrient_vector_a_registry.py",
    "docs/family-food/nutrition-core.md",
    "docs/family-food/food-composition-and-assembly.md",
    "docs/family-food/nutrition-data-readiness.md",
    "docs/family-food/master-roadmap.md",
    "state/current-focus.md",
    "state/progress.md",
    "state/handoff.md",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def profile_key(row):
    return tuple(
        row[k] for k in ("canonical_code", "source_name", "source_id", "source_version")
    )


def profile_inventory(root=ROOT):
    """Union every accepted seed revision, with no current-only filter."""
    inventory = {}
    history = []
    commits = git(root, "log", BASE, "--format=%H", "--", SEED).decode().splitlines()
    for commit in commits:
        raw = git(root, "show", f"{commit}:{SEED}")
        rows = list(csv.DictReader(io.StringIO(raw.decode())))
        history.append(
            {"commit": commit, "seed_sha256": digest(raw), "profile_count": len(rows)}
        )
        for row in rows:
            key = profile_key(row)
            require(
                key not in inventory or inventory[key] == row,
                f"Historical profile provenance was rewritten: {key}",
            )
            inventory[key] = row
    current = list(csv.DictReader(io.StringIO((root / SEED).read_text())))
    require(
        len({profile_key(r) for r in current}) == len(current),
        "Duplicate current profile provenance",
    )
    for row in current:
        require(inventory.get(profile_key(row)) == row, "Production seed changed")
    return inventory, history, current


def decimal_text(value):
    require(
        isinstance(value, str) and bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value)),
        "Source numeric comparison requires finite nonnegative Decimal text",
    )
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid Decimal text") from exc
    require(result.is_finite(), "Nonfinite Decimal")
    return result


def compare_numeric(legacy_value, source_value):
    """No tolerance and no ambient Decimal-context dependence."""
    with localcontext(Context(prec=80, rounding=ROUND_HALF_UP)):
        legacy = None if legacy_value is None else decimal_text(legacy_value)
        source = None if source_value is None else decimal_text(source_value)
        normalized = None if source is None else source.quantize(Decimal(".000001"))
        equal = None if legacy is None or normalized is None else legacy == normalized
        return {
            "contract": "DECIMAL_80_HALF_UP_6DP_V1",
            "normalized_source_value": None if normalized is None else str(normalized),
            "equal": equal,
            "result": "NOT_COMPARED_UNKNOWN"
            if legacy is None
            else "SOURCE_UNAVAILABLE"
            if source is None
            else "EQUAL"
            if equal
            else "DIFFERENT",
        }


def expected_mapping_status(code, nid):
    pair = (code, nid)
    if pair in DIVISORS:
        return "UNIT_CONVERSION_REQUIRED"
    if pair in REJECTIONS:
        return "DISTINCT_COMPONENT"
    if pair in UNPROVEN or nid is None:
        return "NO_ACCEPTABLE_MAPPING"
    if code == "ENERGY_KCAL" and nid in {"1008", "2047"}:
        return "METHOD_SPECIFIC"
    require(PRIMARY[code] == nid, f"Unreviewed semantic mapping: {pair}")
    return "METHOD_SPECIFIC" if code in METHOD_SPECIFIC else "EXACT"


def validate_sources(manifest):
    sources = {s["id"]: s for s in manifest["sources"]}
    require(len(sources) == len(manifest["sources"]), "Duplicate source manifest id")
    required = {
        "FDC-DICTIONARY",
        "FDC-DOWNLOADS",
        "FDC-FOUNDATION-DOC",
        "RU-MR",
        "USDA-AH74",
        "INFOODS-MATCHING",
        "INFOODS-CONVERSIONS",
        "INFOODS-ENERGY",
        "INFOODS-OCEANIA",
        "INFOODS-PART2",
        "INFOODS-PART3",
        "INFOODS-PART4",
    } | set(RELEASES)
    require(required <= sources.keys(), "Missing authoritative source")
    for s in sources.values():
        for field in (
            "source_authority",
            "document_or_dataset_name",
            "release_or_version",
            "retrieved_at",
            "source_reference",
            "license_usage_note",
            "exact_role",
        ):
            require(
                isinstance(s[field], str) and s[field].strip(), f"Empty source {field}"
            )
        require(
            s["source_reference"].startswith("https://"),
            "Source reference is not HTTPS",
        )
        h = s["content_sha256"]
        require(
            (h is None and bool(s["hash_limitation"]))
            or (isinstance(h, str) and re.fullmatch(r"[0-9a-f]{64}", h)),
            "Invalid or unexplained source hash",
        )
    require(
        sources["FDC-DOWNLOADS"]["verified_latest_foundation"] == "2026-04-30",
        "Current release verification changed",
    )
    extracts = manifest["fdc_selected_extracts"]
    require(
        {e["source_manifest_ref"] for e in extracts} == set(RELEASES)
        and len(extracts) == len(RELEASES),
        "Source extracts missing/duplicated",
    )
    for extract in extracts:
        sid = extract["source_manifest_ref"]
        require(
            sources[sid]["content_sha256"] == RELEASE_HASHES[sid],
            "Release hash changed",
        )
        require(
            (extract["source_data_type"], extract["source_release"]) == RELEASES[sid],
            "Source release/type mismatch",
        )
        require(
            digest(canonical(extract))
            == sources[sid]["selected_extract_sha256"]
            == EXTRACT_HASHES[sid],
            "Source extract changed or invented",
        )
    require(
        digest(canonical(manifest["infoods_selected_identifiers"]))
        == manifest["infoods_extract_sha256"]
        == INFOODS_HASH,
        "INFOODS evidence changed",
    )
    return sources


def validate_registry(registry, manifest, sources):
    rows = registry["entries"]
    codes = [r["canonical_code"] for r in rows]
    require(len(set(codes)) == len(codes), "Duplicate canonical code")
    require(set(codes) == set(PRIMARY), "Required initial universe differs")
    require(registry["unit_display_ru"] == UNITS_RU, "Russian unit display differs")
    require(
        len(registry["deferred_extension_categories"]) == 7, "Extension scope missing"
    )
    definitions = set()
    tags = {r["canonical_code"]: r for r in manifest["infoods_selected_identifiers"]}
    for r in rows:
        code = r["canonical_code"]
        require(re.fullmatch(r"[A-Z][A-Z0-9_]*", code), "Invalid internal identity")
        require(r["status"] in STATUSES, "Uncontrolled registry status")
        require(r["canonical_unit"] in UNITS_RU, "Invalid canonical unit")
        ru = r["display_name_ru"]
        require(
            isinstance(ru, str)
            and ru == ru.strip()
            and re.match(r"[А-ЯЁ]", ru)
            and not re.search(r"[A-Za-z]{2,}|_", ru),
            f"Russian display absent or English/code fallback: {code}",
        )
        require(
            r["definition_kind"]
            == ("DERIVED_COMPONENT" if code in DERIVED else "DIRECT_COMPONENT"),
            "Definition kind changed",
        )
        require(
            r["category"] in {"proximate", "lipid", "mineral", "vitamin"}, "Category"
        )
        require(
            r["product_tracking_tier"]
            in {"V1_COMPATIBILITY", "INITIAL_FOOD_TRACKING", "DETAILED_COMPONENT"},
            "Tracking tier",
        )
        definition = unicodedata.normalize("NFKC", r["definition"]).casefold().strip()
        require(
            definition and definition not in definitions,
            "Duplicate/empty semantic definition",
        )
        definitions.add(definition)
        require(
            r["source_evidence_refs"]
            and set(r["source_evidence_refs"]) <= sources.keys(),
            "Unresolved definition evidence",
        )
        require(
            r["infoods_mapping_status"] in MAPPING_STATUSES, "INFOODS mapping status"
        )
        t = tags.get(code)
        require(
            (
                t is None
                and r["infoods_tagname"] is None
                and r["infoods_mapping_status"] == "NO_ACCEPTABLE_MAPPING"
                and r["notes"]
            )
            or (
                t is not None
                and t["tagname"] == r["infoods_tagname"]
                and t["mapping_status"] == r["infoods_mapping_status"]
            ),
            "INFOODS identity",
        )
        if t:
            require(
                t["source_manifest_ref"] in r["source_evidence_refs"],
                "INFOODS source missing",
            )
        require(
            r["status"] == "APPROVED_FOR_VECTOR_B" or r["notes"],
            "Blocked definition unexplained",
        )
    return {r["canonical_code"]: r for r in rows}


def validate_mappings(mapping_document, registry, manifest):
    extracts = {e["source_manifest_ref"]: e for e in manifest["fdc_selected_extracts"]}
    source_ids = {s["id"] for s in manifest["sources"]}
    seen = set()
    for m in mapping_document["mappings"]:
        code, nid, sid = (
            m["canonical_code"],
            m["source_nutrient_id"],
            m["source_manifest_ref"],
        )
        require(code in registry, "Mapping references nonexistent registry entry")
        key = (code, nid, sid)
        require(key not in seen, "Duplicate mapping")
        seen.add(key)
        require(sid in extracts and m["source_name"] == "USDA_FDC", "Mapping source")
        require(
            (m["source_data_type"], m["source_release"]) == RELEASES[sid],
            "Mapping release/type",
        )
        require(
            m["mapping_status"] in MAPPING_STATUSES
            and m["mapping_status"] == expected_mapping_status(code, nid),
            "Mapping semantics fail closed",
        )
        require(
            m["canonical_unit"] == registry[code]["canonical_unit"],
            "Mapping unit conflict",
        )
        require(
            bool(m["mapping_rationale"]) and bool(m["method_requirement"]),
            "Missing mapping method",
        )
        if nid is None:
            require(
                PRIMARY[code] is None
                and all(
                    m[k] is None
                    for k in (
                        "source_nutrient_nbr",
                        "source_nutrient_name",
                        "source_unit",
                    )
                ),
                "Invented missing identifier",
            )
        else:
            n = next(
                (n for n in extracts[sid]["nutrient_rows"] if n["id"] == nid), None
            )
            require(n is not None, "Invented nutrient id")
            require(
                (m["source_nutrient_nbr"], m["source_nutrient_name"], m["source_unit"])
                == (n["nutrient_nbr"], n["name"], n["unit_name"]),
                "Source component metadata",
            )
        divisor = DIVISORS.get((code, nid))
        require(
            bool(m["definition_evidence_refs"])
            and set(m["definition_evidence_refs"]) <= source_ids,
            "Missing mapping definition evidence",
        )
        conversion_evidence = (
            {
                "ENERGY_KCAL": "USDA-AH74",
                "VITAMIN_D_D2_D3": "INFOODS-PART4",
                "FLUORIDE": "INFOODS-CONVERSIONS",
            }[code]
            if divisor is not None
            else None
        )
        require(
            m["conversion_evidence_ref"] == conversion_evidence,
            "Missing or incorrect conversion evidence",
        )
        require(
            m["unit_conversion_required"] is (divisor is not None)
            and m["conversion_divisor"] == divisor,
            "Conversion requirement",
        )
        if nid and m["mapping_status"] in {"EXACT", "METHOD_SPECIFIC"}:
            require(
                {"G": "g", "MG": "mg", "UG": "µg", "KCAL": "kcal"}.get(m["source_unit"])
                == m["canonical_unit"],
                "Unconverted unit",
            )
    pairs = (
        set(PRIMARY.items())
        | REJECTIONS
        | UNPROVEN
        | set(DIVISORS)
        | {("ENERGY_KCAL", "1008"), ("ENERGY_KCAL", "2047")}
    )
    require(
        seen == {(c, n, s) for c, n in pairs for s in RELEASES},
        "Incomplete source crosswalk",
    )


# Accepted byte snapshots, including complementary JSON of the same releases.
# JSON adds evidence only: a missing JSON record never substitutes a CSV value.
ZERO_SOURCE_FILES = {
    "foundation.zip": ("FDC-FOUNDATION", RELEASE_HASHES["FDC-FOUNDATION"]),
    "sr.zip": ("FDC-SR", RELEASE_HASHES["FDC-SR"]),
    "dictionary.xlsx": (
        "FDC-DICTIONARY",
        "84597b955d1d0b9ea4b407b0cc24a32b84f7bbc0ee06ef38a1d24011f3a281b4",
    ),
    "downloads.html": (
        "FDC-DOWNLOADS",
        "8611bb2030246fb0062622991213fc841c6ceb83b8761e5e5a9e81381102ba5d",
    ),
    "foundation-doc.html": (
        "FDC-FOUNDATION-DOC",
        "cc5dc67ee71a71860ebdc5c59774aa0642ef9f2dfecb81094a674d9837d691c9",
    ),
    "foundation-json.zip": (
        "FDC-FOUNDATION-JSON",
        "186e988ec542e913f51ef62b86a47758e8cdd0d1dc3889e7b055581f3c09c77a",
    ),
    "sr-json.zip": (
        "FDC-SR-JSON",
        "0fe8ae486a2c8eb42cb96413f058deb51863a46c8fb8eeb4b1fb45006dd338ef",
    ),
}
ZERO_EVIDENCE_HASH = "95190a0a2378aa04bafda5c0e3cc9230421704c97feeb5a4be480fabccaf91a3"
SOURCE_VALUE_STATES = {"NONZERO_REPORTED", "ZERO_REPORTED", "VALUE_ABSENT"}
CENSORING_STATES = {
    "EXPLICIT_NOT_CENSORED",
    "EXPLICIT_CENSORED",
    "LOQ_METADATA_PRESENT_STATUS_UNSPECIFIED",
    "NO_CENSORING_METADATA",
    "NOT_APPLICABLE",
    "NOT_REVIEWED_NONZERO",
}
ZERO_RESOLUTIONS = {"EXACT_ZERO_CONFIRMED", "BLOCKED_CENSORED", "UNRESOLVED"}


def replay_zero_sources(directory, crosswalk):
    """Reproduce selected evidence from hash-verified source bytes, without writes.

    CSV fields remain strings. JSON numeric lexemes also remain strings so no
    binary float/rounding can alter provenance. Hashes below are canonical row
    hashes, distinct from raw archive/member hashes.
    """
    for filename, (_, sha) in ZERO_SOURCE_FILES.items():
        require(
            digest((directory / filename).read_bytes()) == sha,
            f"Pinned source hash mismatch: {filename}",
        )
    zeros = [
        r
        for r in crosswalk["rows"]
        if r["source_value"] is not None and decimal_text(r["source_value"]) == 0
    ]
    evidence = {"source_files": ZERO_SOURCE_FILES, "exports": {}, "observations": []}
    # Convert tuples to the same JSON representation as committed evidence.
    evidence["source_files"] = {k: list(v) for k, v in ZERO_SOURCE_FILES.items()}
    for short, sid in [("foundation", "FDC-FOUNDATION"), ("sr", "FDC-SR")]:
        with zipfile.ZipFile(directory / (short + ".zip")) as archive:
            members = {
                Path(n).name: n for n in archive.namelist() if n.endswith(".csv")
            }
            needed = ["food_nutrient.csv", "food_attribute.csv"]
            needed += (
                [
                    "input_food.csv",
                    "sub_sample_food.csv",
                    "sub_sample_result.csv",
                    "lab_method.csv",
                    "lab_method_code.csv",
                ]
                if short == "foundation"
                else ["food_nutrient_derivation.csv", "food_nutrient_source.csv"]
            )
            tables, table_info = {}, {}
            for name in needed:
                raw = archive.read(members[name])
                reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
                tables[name] = list(reader)
                table_info[name] = {
                    "archive_member": members[name],
                    "sha256": digest(raw),
                    "columns": reader.fieldnames,
                    "row_count": len(tables[name]),
                }
        with zipfile.ZipFile(directory / (short + "-json.zip")) as archive:
            member = archive.namelist()[0]
            raw = archive.read(member)
            document = json.loads(raw, parse_int=str, parse_float=str)
            root_key = next(iter(document))
            foods = document[root_key]
            food_index = {f["fdcId"]: f for f in foods if f is not None}
            evidence["exports"][sid] = {
                "csv_tables": table_info,
                "json": {
                    "archive_member": member,
                    "sha256": digest(raw),
                    "root_key": root_key,
                    "food_slots": len(foods),
                    "null_food_slots": foods.count(None),
                },
            }
        for row in zeros:
            if row["profile_source_data_type"] != RELEASES[sid][0]:
                continue
            fid, nid = row["profile_source_id"], row["source_nutrient_id"]
            matches = [
                r
                for r in tables["food_nutrient.csv"]
                if (r["id"], r["fdc_id"], r["nutrient_id"])
                == (row["source_food_nutrient_id"], fid, nid)
            ]
            require(
                len(matches) == 1 and matches[0]["amount"] == row["source_value"],
                "Zero CSV replay identity/value mismatch",
            )
            source = matches[0]
            food = food_index.get(fid)
            matches = (
                [n for n in food["foodNutrients"] if n["id"] == source["id"]]
                if food
                else []
            )
            require(len(matches) <= 1, "Duplicate JSON source row")
            json_row = matches[0] if matches else None
            if json_row:
                require(
                    json_row["nutrient"]["id"] == nid
                    and decimal_text(json_row["amount"])
                    == decimal_text(source["amount"])
                    and json_row["nutrient"]["unitName"].upper() == row["source_unit"],
                    "JSON/CSV zero identity/unit/value mismatch",
                )
            related = {}
            examined_count = 0
            if short == "foundation":
                inputs = [r for r in tables["input_food.csv"] if r["fdc_id"] == fid]
                sample_ids = {r["fdc_of_input_food"] for r in inputs}
                subs = [
                    r
                    for r in tables["sub_sample_food.csv"]
                    if r["fdc_id_of_sample_food"] in sample_ids
                ]
                child_ids = sample_ids | {r["fdc_id"] for r in subs}
                examined_count = len(child_ids)
                values = [
                    r
                    for r in tables["food_nutrient.csv"]
                    if r["fdc_id"] in child_ids and r["nutrient_id"] == nid
                ]
                results = [
                    r
                    for r in tables["sub_sample_result.csv"]
                    if r["food_nutrient_id"] in {v["id"] for v in values}
                ]
                used_children = {r["fdc_id"] for r in values}
                used_subs = [r for r in subs if r["fdc_id"] in used_children]
                used_samples = used_children | {
                    r["fdc_id_of_sample_food"] for r in used_subs
                }
                methods = {r["lab_method_id"] for r in results}
                related = {
                    "input_food.csv": [
                        r for r in inputs if r["fdc_of_input_food"] in used_samples
                    ],
                    "sub_sample_food.csv": used_subs,
                    "food_nutrient.csv": values,
                    "sub_sample_result.csv": results,
                    "lab_method.csv": [
                        r for r in tables["lab_method.csv"] if r["id"] in methods
                    ],
                    "lab_method_code.csv": [
                        r
                        for r in tables["lab_method_code.csv"]
                        if r["lab_method_id"] in methods
                    ],
                    "food_attribute.csv": [
                        r
                        for r in tables["food_attribute.csv"]
                        if r["fdc_id"] in child_ids | {fid}
                    ],
                }
            else:
                derivations = [
                    r
                    for r in tables["food_nutrient_derivation.csv"]
                    if r["id"] == source["derivation_id"]
                ]
                related = {
                    "food_nutrient_derivation.csv": derivations,
                    "food_nutrient_source.csv": [
                        r
                        for r in tables["food_nutrient_source.csv"]
                        if r["id"] in {d["source_id"] for d in derivations}
                    ],
                    "food_attribute.csv": [
                        r for r in tables["food_attribute.csv"] if r["fdc_id"] == fid
                    ],
                }
            evidence["observations"].append(
                {
                    "evidence_ref": row["evidence_ref"],
                    "source_manifest_ref": sid,
                    "csv_row": source,
                    "csv_row_sha256": digest(canonical(source)),
                    "json_food_nutrient": json_row,
                    "json_match_state": "MATCHED"
                    if json_row
                    else "FOOD_ABSENT"
                    if food is None
                    else "NUTRIENT_ABSENT",
                    "json_row_sha256": digest(canonical(json_row))
                    if json_row
                    else None,
                    "examined_foundation_child_food_count": examined_count,
                    "related_csv_rows": related,
                }
            )
    evidence["observations"].sort(key=lambda e: e["evidence_ref"])
    return evidence


def source_value_state(source):
    if source is None:
        return "VALUE_ABSENT"
    return (
        "ZERO_REPORTED" if decimal_text(source["amount"]) == 0 else "NONZERO_REPORTED"
    )


def zero_semantics(evidence):
    """Interpret only reviewed release evidence; no analytical-zero inference.

    A bare LOQ number is conservatively metadata, not a censor flag. None of
    these 64 exact rows has a documented observation-level censor/not-censor
    marker. Adding such an adapter requires explicit evidence review, not a
    guessed marker name or derivation-code heuristic.
    """
    records = [evidence["csv_row"], evidence["json_food_nutrient"] or {}]
    records += evidence["related_csv_rows"].get("food_nutrient.csv", [])
    loq_present = any(r.get("loq") not in (None, "") for r in records)
    return {
        "censoring_evidence_state": (
            "LOQ_METADATA_PRESENT_STATUS_UNSPECIFIED"
            if loq_present
            else "NO_CENSORING_METADATA"
        ),
        "zero_resolution": "UNRESOLVED",
        "exact_zero_evidence_refs": [],
        "censoring_evidence_refs": [],
    }


def validate_zero_evidence(manifest):
    evidence = manifest["zero_provenance_evidence"]
    require(
        digest(canonical(evidence)) == ZERO_EVIDENCE_HASH,
        "Zero source evidence changed, stripped or invented",
    )
    sources = {s["id"]: s for s in manifest["sources"]}
    for _, (sid, sha) in ZERO_SOURCE_FILES.items():
        require(
            sources[sid]["content_sha256"] == sha, "Zero source snapshot hash changed"
        )
    seen = set()
    for e in evidence["observations"]:
        require(e["evidence_ref"] not in seen, "Duplicate zero evidence")
        seen.add(e["evidence_ref"])
        require(
            digest(canonical(e["csv_row"])) == e["csv_row_sha256"],
            "Zero source row hash mismatch",
        )
        require(
            (
                digest(canonical(e["json_food_nutrient"]))
                if e["json_food_nutrient"]
                else None
            )
            == e["json_row_sha256"],
            "Zero JSON row hash mismatch",
        )
    return {e["evidence_ref"]: e for e in evidence["observations"]}


def validate_observation_semantics(row, source, zero_evidence):
    state = source_value_state(source)
    require(
        row["source_value_state"] in SOURCE_VALUE_STATES
        and row["source_value_state"] == state,
        "Source value state does not replay the accepted observation",
    )
    require(
        row["censoring_evidence_state"] in CENSORING_STATES,
        "Unknown censoring evidence state",
    )
    if state == "ZERO_REPORTED":
        e = zero_evidence.get(row["evidence_ref"])
        require(
            e is not None and e["csv_row"] == source,
            "Zero source row identity/provenance mismatch",
        )
        require(
            row["source_observation"]
            == {"row": source, "row_sha256": digest(canonical(source))},
            "Zero source row hash or available metadata lost",
        )
        require(
            row["zero_provenance_ref"] == e["evidence_ref"], "Zero evidence link lost"
        )
        require(row["zero_resolution"] in ZERO_RESOLUTIONS, "Unknown zero resolution")
        for key, expected in zero_semantics(e).items():
            require(
                row[key] == expected, "Unsupported exact zero or censoring assertion"
            )
    else:
        require(
            row["source_observation"] is None
            and row["zero_provenance_ref"] is None
            and row["zero_resolution"] == "NOT_APPLICABLE"
            and row["exact_zero_evidence_refs"] == []
            and row["censoring_evidence_refs"] == [],
            "Nonzero/absent observation promoted to zero",
        )
        require(
            row["censoring_evidence_state"]
            == (
                "NOT_APPLICABLE" if state == "VALUE_ABSENT" else "NOT_REVIEWED_NONZERO"
            ),
            "Censoring review scope overstated",
        )


def summarize_zeros(rows):
    zeros = [r for r in rows if r["source_value_state"] == "ZERO_REPORTED"]
    partition_states = CENSORING_STATES - {"NOT_APPLICABLE", "NOT_REVIEWED_NONZERO"}
    partition = counts(zeros, "censoring_evidence_state", partition_states)
    resolutions = counts(zeros, "zero_resolution", ZERO_RESOLUTIONS)
    datasets = counts(zeros, "profile_source_data_type", {"Foundation", "SR Legacy"})
    require(
        sum(partition.values())
        == sum(resolutions.values())
        == sum(datasets.values())
        == len(zeros),
        "Zero categories/datasets do not partition the corpus",
    )
    return {
        "source_reported_zero_observations": len(zeros),
        "by_dataset": datasets,
        "censoring_evidence_partition": partition,
        "zero_resolution_partition": resolutions,
        "unresolved_observations": [
            r["audit_identity"] for r in zeros if r["zero_resolution"] == "UNRESOLVED"
        ],
    }


def validate_summary(actual, expected):
    require("known_zero_observations" not in actual, "Obsolete known-zero claim")
    require(actual == expected, "Summary is not derived from artifacts")


LEGACY_ROW_KEYS = {
    "audit_identity",
    "censoring_evidence_refs",
    "censoring_evidence_state",
    "evidence_ref",
    "exact_zero_evidence_refs",
    "food_ingredient_code",
    "legacy_field",
    "legacy_mapping_status",
    "legacy_value",
    "limitations",
    "numeric_comparison",
    "profile_basis_grams",
    "profile_estimated",
    "profile_source_data_type",
    "profile_source_id",
    "profile_source_name",
    "profile_source_version",
    "profile_verified_at",
    "source_derivation_id",
    "source_food_nutrient_id",
    "source_nutrient_id",
    "source_nutrient_name",
    "source_observation",
    "source_unit",
    "source_value",
    "source_value_state",
    "target_nutrient_code",
    "zero_provenance_ref",
    "zero_resolution",
}


def validate_legacy(crosswalk, inventory, manifest):
    """Accept a complete provenance inventory, including any historical rows."""
    zero_evidence = validate_zero_evidence(manifest)
    observations = {}
    foods = {}
    nutrients = {}
    for e in manifest["fdc_selected_extracts"]:
        sid = e["source_manifest_ref"]
        observations.update(
            {(sid, r["fdc_id"], r["nutrient_id"]): r for r in e["food_nutrient_rows"]}
        )
        foods.update({(sid, r["fdc_id"]): r for r in e["food_rows"]})
        nutrients.update({(sid, r["id"]): r for r in e["nutrient_rows"]})
    expected = {(*key, field) for key in inventory for field in FIELDS}
    seen = set()
    for row in crosswalk["rows"]:
        require(
            set(row) == LEGACY_ROW_KEYS,
            "Unrecognized or missing legacy observation field",
        )
        key = (
            row["food_ingredient_code"],
            row["profile_source_name"],
            row["profile_source_id"],
            row["profile_source_version"],
        )
        field = row["legacy_field"]
        identity = (*key, field)
        require(
            identity in expected and identity not in seen,
            "Legacy coverage missing/duplicate/unknown",
        )
        seen.add(identity)
        require(
            row["audit_identity"] == ":".join(identity),
            "Unstable audit identity / UUID",
        )
        p = inventory[key]
        code = FIELDS[field]
        require(row["target_nutrient_code"] == code, "Legacy concept changed")
        require(
            row["legacy_value"] == (p[field] or None), "Accepted legacy value changed"
        )
        require(
            row["profile_source_data_type"] == p["source_data_type"]
            and row["profile_basis_grams"] == p["basis_grams"]
            and row["profile_verified_at"] == p["verified_at"]
            and row["profile_estimated"] is None,
            "Profile provenance changed",
        )
        sid = next(
            (
                s
                for s, (dtype, version) in RELEASES.items()
                if (dtype, version) == (p["source_data_type"], p["source_version"])
            ),
            None,
        )
        require(sid is not None, "Profile source release unavailable")
        food = foods.get((sid, p["source_id"]))
        require(
            food is not None and food["description"] == p["source_description"],
            "FDC food identity mismatch",
        )
        require(
            food["data_type"]
            == ("foundation_food" if sid == "FDC-FOUNDATION" else "sr_legacy_food"),
            "Food belongs to wrong data type",
        )
        nid = p["energy_nutrient_id"] if field == "kcal" else PRIMARY[code]
        source = observations.get((sid, p["source_id"], nid))
        require(
            row["legacy_mapping_status"] in LEGACY_STATUSES,
            "Uncontrolled legacy result",
        )
        if source:
            n = nutrients[(sid, nid)]
            require(
                (
                    row["source_nutrient_id"],
                    row["source_nutrient_name"],
                    row["source_unit"],
                    row["source_value"],
                    row["source_food_nutrient_id"],
                    row["source_derivation_id"],
                )
                == (
                    nid,
                    n["name"],
                    n["unit_name"],
                    source["amount"],
                    source["id"],
                    source["derivation_id"],
                ),
                "Legacy source observation or component changed",
            )
        else:
            require(
                all(
                    row[k] is None
                    for k in (
                        "source_nutrient_id",
                        "source_nutrient_name",
                        "source_unit",
                        "source_value",
                        "source_food_nutrient_id",
                        "source_derivation_id",
                    )
                ),
                "Unknown source component was invented",
            )
        validate_observation_semantics(row, source, zero_evidence)
        comparison = compare_numeric(
            row["legacy_value"], source["amount"] if source else None
        )
        require(row["numeric_comparison"] == comparison, "Decimal comparison differs")
        status = (
            "VALUE_ABSENT"
            if row["legacy_value"] is None
            else (
                "SOURCE_COMPONENT_CONFIRMED"
                if comparison["equal"] is True
                else "VALUE_MISMATCH"
                if source
                else "LEGACY_PROFILE_VALUE_CONFIRMED_SOURCE_ID_UNAVAILABLE"
            )
        )
        require(row["legacy_mapping_status"] == status, "Legacy result misclassified")
        expected_ref = sid + (
            ":food_nutrient:" + source["id"] if source else ":food:" + p["source_id"]
        )
        require(
            row["evidence_ref"] == expected_ref and row["limitations"],
            "Legacy evidence locator",
        )
    require(seen == expected, "Not every profile and all five fields were audited")
    require(
        {
            r["evidence_ref"]
            for r in crosswalk["rows"]
            if r["source_value_state"] == "ZERO_REPORTED"
        }
        == set(zero_evidence),
        "Zero evidence corpus incomplete",
    )


def counts(rows, field, statuses=None):
    c = Counter(r[field] for r in rows)
    return {key: c[key] for key in sorted(statuses or c)}


def summarize(registry, mappings, crosswalk, manifest):
    entries, rows = registry["entries"], crosswalk["rows"]
    groups = {}
    for row in rows:
        key = row["audit_identity"].rsplit(":", 1)[0]
        groups.setdefault(key, []).append(row)
    full = sorted(
        k
        for k, rs in groups.items()
        if all(r["legacy_mapping_status"] == "SOURCE_COMPONENT_CONFIRMED" for r in rs)
    )
    unresolved = sorted(
        k
        for k, rs in groups.items()
        if any(
            r["legacy_mapping_status"]
            not in {"SOURCE_COMPONENT_CONFIRMED", "VALUE_ABSENT"}
            for r in rs
        )
    )
    return {
        "schema_version": 1,
        "operation": "PR6-NUTRIENT-VECTOR-A",
        "starting_main": BASE,
        "registry_candidate_count": len(entries),
        "registry_status_counts": counts(entries, "status", STATUSES),
        "counts_by_category": counts(entries, "category"),
        "counts_by_unit": counts(entries, "canonical_unit"),
        "fdc_mapping_counts": counts(
            mappings["mappings"], "mapping_status", MAPPING_STATUSES
        ),
        "infoods_mapping_counts": counts(
            entries, "infoods_mapping_status", MAPPING_STATUSES
        ),
        "profiles_audited": len(groups),
        "legacy_field_observations": len(rows),
        "legacy_mapping_counts": counts(rows, "legacy_mapping_status", LEGACY_STATUSES),
        "profiles_with_full_five_field_provenance": full,
        "profiles_with_unresolved_component_mapping": unresolved,
        "profiles_with_absent_legacy_values": sorted(
            k
            for k, rs in groups.items()
            if any(r["legacy_mapping_status"] == "VALUE_ABSENT" for r in rs)
        ),
        "historical_only_profile_count": manifest["profile_inventory"][
            "historical_only_count"
        ],
        "zero_provenance_audit": summarize_zeros(rows),
        "mismatch_rows": [
            r["audit_identity"]
            for r in rows
            if r["legacy_mapping_status"] == "VALUE_MISMATCH"
        ],
        "ambiguous_rows": [
            r["audit_identity"]
            for r in rows
            if r["legacy_mapping_status"] == "DEFINITION_AMBIGUOUS"
        ],
        "energy_source_component_counts": counts(
            [r for r in rows if r["legacy_field"] == "kcal"], "source_nutrient_id"
        ),
        "carbohydrate_definition_counts": counts(
            [r for r in rows if r["legacy_field"] == "carbohydrates_g"],
            "target_nutrient_code",
        ),
        "russian_display": {
            "present": len(entries),
            "missing": 0,
            "english_fallback": 0,
        },
    }


def validate_content(registry, mappings, crosswalk, manifest, root=ROOT):
    for artifact in (registry, mappings, crosswalk, manifest):
        require(
            artifact["starting_main"] == BASE and artifact["schema_version"] == 1,
            "Starting-main authority",
        )
    sources = validate_sources(manifest)
    definitions = validate_registry(registry, manifest, sources)
    validate_mappings(mappings, definitions, manifest)
    inventory, history, current = profile_inventory(root)
    mi = manifest["profile_inventory"]
    require(
        mi["seed_revisions"] == history
        and mi["current_count"] == len(current)
        and mi["distinct_provenance_count"] == len(inventory)
        and mi["historical_only_count"]
        == len(inventory.keys() - {profile_key(r) for r in current})
        and mi["nutrition_seed_sha256"] == digest((root / SEED).read_bytes()),
        "Profile inventory mismatch",
    )
    validate_legacy(crosswalk, inventory, manifest)
    return summarize(registry, mappings, crosswalk, manifest)


def validate_protected(root=ROOT, *, staged=False):
    require(
        git(root, "merge-base", BASE, "HEAD").decode().strip() == BASE,
        "Branch does not descend from exact starting main",
    )
    paths = git(root, "ls-tree", "-r", "--name-only", BASE).decode().splitlines()
    protected = [
        p for p in paths if p not in ALLOWED_CHANGES and Path(p).name != ".DS_Store"
    ]
    changed = set(git(root, "diff", "--name-only", BASE).decode().splitlines())
    changed |= set(
        git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()
    )
    changed = {p for p in changed if Path(p).name != ".DS_Store"}
    require(
        not (changed & set(protected)),
        "Protected production/runtime/schema/research baseline changed",
    )
    require(
        changed <= ALLOWED_CHANGES,
        f"Scope expansion: {sorted(changed - ALLOWED_CHANGES)}",
    )
    if staged:
        staged_paths = set(
            git(root, "diff", "--cached", "--name-only").decode().splitlines()
        )
        require(
            staged_paths <= ALLOWED_CHANGES,
            f"Staged scope expansion: {sorted(staged_paths - ALLOWED_CHANGES)}",
        )
        require(
            not git(
                root, "diff", "--name-only", "--", *sorted(ALLOWED_CHANGES)
            ).strip(),
            "Staged artifacts differ from validated working-tree bytes",
        )
    migration_file = (root / "backend/app/db/migrations.py").read_text()
    registered = re.findall(r'"app\.migrations\.versions\.([^\"]+)"', migration_file)
    require(registered[-1] == MIGRATION_HEAD, "Migration head changed")
    require(
        not list((root / "backend/app/migrations/versions").glob("0028*")),
        "Migration 0028 is unauthorized",
    )
    baseline = read_json(
        root / "data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json"
    )
    estimated_rows = [
        r
        for recipe in baseline["records"]
        for r in recipe["rows"]
        if "CONVERSION_ESTIMATE_NOT_ACCEPTED" in r["issues"]
    ]
    require(
        len(estimated_rows) == 43 and all(r["mass_g"] is None for r in estimated_rows),
        "43 estimate candidates changed or became executable",
    )
    return len(protected)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Write only the derived research summary",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Verify staged scope and identical validated bytes",
    )
    parser.add_argument(
        "--source-directory",
        type=Path,
        help="Replay zero evidence from all pinned raw files (read-only)",
    )
    args = parser.parse_args()
    directory = ROOT / DIRECTORY
    artifacts = [read_json(directory / name) for name in FILES[:4]]
    summary = validate_content(*artifacts)
    if args.source_directory:
        require(
            replay_zero_sources(args.source_directory, artifacts[2])
            == artifacts[3]["zero_provenance_evidence"],
            "Zero raw-source replay differs",
        )
        print("PASS: seven pinned raw source hashes and complete zero-source replay")
    if args.write_summary:
        (directory / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        )
    validate_summary(read_json(directory / "summary.json"), summary)
    protected = validate_protected(staged=args.staged)
    print(
        f"PASS VECTOR-A: {summary['registry_candidate_count']} registry candidates; "
        f"{summary['profiles_audited']} profiles / {summary['legacy_field_observations']} fields; "
        f"{protected} protected files unchanged; migration {MIGRATION_HEAD}; 43 estimates non-executable."
    )


if __name__ == "__main__":
    main()
