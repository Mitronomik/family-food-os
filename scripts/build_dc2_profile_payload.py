"""Prepare five source-native profiles and probe current domain compatibility.

Numeric outputs belong outside the repository while source reuse is unresolved.
No database, seed, registry or runtime publication is modified.
"""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/dc2-first-profile-payload"
PROFILE_REVIEW = (
    ROOT / "data/curation/dc2-first-batch-review/generated/profile-reviews.json"
)
PR73_FORMS = ROOT / "data/curation/dc2-exact-input-mappings/forms.json"
INGREDIENT_SEED = ROOT / "data/seed/food_ingredients/ingredients.csv"

sys.path.insert(0, str(ROOT / "backend"))
from app.domain.errors import DomainValidationError
from app.domain.food_ingredients import FoodNutritionProfile

VERSION = "dc2-profile-payload-v1"
FIELDS = {
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbohydrates_g",
    "fiber_g",
    "ash_g",
    "water_g",
    "organic_acids_g",
    "starch_g",
    "sugars_g",
    "cholesterol_mg",
    "saturated_fat_g",
}
SELECTED_CODES = {"10.1.1", "8.1.5.1", "8.1.2.1", "8.1.5.12", "6.5.3"}
EXPECTED_IDENTITY = {
    "school2022:input-form:sugar": (
        "reuse_candidate_requires_existing_form_check",
        "SUGAR",
    ),
    "school2022:input-form:carrot": (
        "reuse_candidate_requires_existing_form_check",
        "CARROT",
    ),
    "school2022:input-form:cabbage": (
        "reuse_candidate_requires_existing_form_check",
        "CABBAGE_GREEN",
    ),
    "school2022:input-form:beet": (
        "reuse_candidate_requires_existing_form_check",
        "BEET",
    ),
    "school2022:input-form:rice": (
        "propose_new_generic_form",
        "RICE_POLISHED_DRY",
    ),
}
EXPECTED_REPO_INPUTS = {
    "data/curation/dc2-exact-input-mappings/forms.json",
    "data/curation/dc2-first-batch-review/generated/profile-reviews.json",
    "data/seed/food_ingredients/ingredients.csv",
    "backend/app/domain/food_ingredients.py",
    "backend/app/domain/decimal_utils.py",
    "backend/app/domain/errors.py",
}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def unique(items, key="id"):
    result = {item[key]: item for item in items}
    if len(result) != len(items):
        raise ValueError("duplicate " + key)
    return result


def validate_cell(cell):
    state = cell["state"]
    if state not in {"published_positive", "below_detection", "missing"}:
        raise ValueError("unreviewed value state")
    if state == "published_positive":
        value = Decimal(cell["value"])
        if (
            not value.is_finite()
            or value <= 0
            or cell["value"] != cell["published_value"]
        ):
            raise ValueError("invalid published positive")
    elif cell["value"] is not None:
        raise ValueError("unknown is not a number")
    if state == "below_detection" and (
        cell["published_value"] != "0" or cell["detection_limit"] is not None
    ):
        raise ValueError("changed below-detection semantics")


def _load_seed():
    with INGREDIENT_SEED.open() as source:
        rows = list(csv.DictReader(source))
    by_code = {row["canonical_code"]: row for row in rows}
    if len(by_code) != len(rows):
        raise ValueError("duplicate ingredient seed code")
    return by_code


def _selected_profile_reviews():
    rows = load(PROFILE_REVIEW)
    selected = [row for row in rows if row["source_code"] in SELECTED_CODES]
    if len(selected) != 5:
        raise ValueError("selected profile review coverage changed")
    by_code = {row["source_code"]: row for row in selected}
    if set(by_code) != SELECTED_CODES:
        raise ValueError("selected profile review codes changed")
    for row in selected:
        if (
            row["basis_g"] != 100
            or row["basis_reviewed"] is not True
            or row["publication_ready"] is not False
            or row["canonical_nutrient_mapping"] is not None
            or row["rights_disposition"]
            != "REFERENCE_ONLY_PUBLICATION_USE_UNRESOLVED"
            or row["carbohydrate_disposition"]
            != "SOURCE_NATIVE_METHOD_NOT_CANONICAL_CHOAVL_OR_CHOCDF"
        ):
            raise ValueError("selected profile review authority changed")
    return by_code


def validate_identity_plan():
    forms = unique(load(PR73_FORMS))
    plan = unique(load(PACKAGE / "identity-plan.json"))
    if set(plan) != set(EXPECTED_IDENTITY):
        raise ValueError("identity plan coverage changed")
    seed = _load_seed()
    for form_id, identity in plan.items():
        form = forms.get(form_id)
        if form is None:
            raise ValueError("identity plan form missing from PR73")
        for field in (
            "id",
            "book_candidate_id",
            "book_source_code",
            "canonical_food_id",
            "display_name_ru",
            "evidence_pdf_pages",
            "expected_occurrences",
            "nutrient_equivalence_accepted",
            "source_input_form",
        ):
            if identity[field] != form[field]:
                raise ValueError("identity plan drift: " + field)
        if (
            identity["canonical_food_id"] is not None
            or identity["nutrient_equivalence_accepted"] is not False
        ):
            raise ValueError("identity plan authority promotion")
        expected_action, expected_code = EXPECTED_IDENTITY[form_id]
        if (
            identity["identity_action"] != expected_action
            or identity["proposed_canonical_code"] != expected_code
        ):
            raise ValueError("identity action/code drift")
        if expected_action == "reuse_candidate_requires_existing_form_check":
            if expected_code not in seed:
                raise ValueError("reuse candidate missing from ingredient seed")
        else:
            if expected_code in seed:
                raise ValueError("proposed new food code already exists")
            rice = seed.get("RICE_WHITE")
            if rice is None or "длиннозёрный" not in rice["canonical_name"]:
                raise ValueError("existing RICE_WHITE identity changed")
    return plan


def validate_rights_review():
    review = load(PACKAGE / "source-use-review.json")
    if (
        review["rights_status"] != "BLOCKED_PENDING_RIGHTS_REVIEW"
        or review["explicit_reuse_permission"] != "not_found"
        or review["factual_use_legal_conclusion"] != "not_adjudicated"
        or review["outbound_request_sent"] is not False
        or review["production_use_disposition"] != "pending_scope_review"
        or review["public_redistribution_disposition"] != "pending_scope_review"
        or review["source_edition"] != "ISBN 5-94343-028-8"
        or set(review["scope_food_codes"]) != SELECTED_CODES
    ):
        raise ValueError("rights review status drift")
    return review


def expected_verification_summary():
    reviews = _selected_profile_reviews()
    states = Counter()
    for review in reviews.values():
        states.update(review["field_states"].values())
    if states != Counter({"published_positive": 45, "below_detection": 15}):
        raise ValueError("selected source-state counts changed")
    return {
        "additional_reviewed_source_fields_per_profile": 6,
        "canonical_numeric_values": 0,
        "domain_rejections": 5,
        "evidence_basis": (
            "accepted_nonnumeric_profile_review_metadata_plus_current_domain_contract"
        ),
        "external_full_build_claim_used_for_acceptance": False,
        "external_full_build_hashes_retained": False,
        "full_book_nutrient_coverage": False,
        "imported_profiles": 0,
        "numeric_payload_retained_in_repository": False,
        "observations": 60,
        "profiles": 5,
        "required_source_fields_per_profile": 6,
        "rights_status": "BLOCKED_PENDING_RIGHTS_REVIEW",
        "scope": (
            "all twelve fields in five reviewed reference profiles; "
            "additional book columns remain separate"
        ),
        "source_states": {
            "below_detection": 15,
            "published_positive": 45,
        },
    }


def validate_verification_summary():
    expected = expected_verification_summary()
    if load(PACKAGE / "verification-summary.json") != expected:
        raise ValueError("verification summary drift")
    return expected


def expected_domain_blockers():
    reviews = _selected_profile_reviews()
    blockers = []
    for source_code in sorted(SELECTED_CODES):
        unsupported = ["carbohydrates_g"]
        states = reviews[source_code]["field_states"]
        if states["protein_g"] == "below_detection":
            unsupported.insert(0, "protein_g")
        if states["fat_g"] == "below_detection":
            insert_at = 1 if "protein_g" in unsupported else 0
            unsupported.insert(insert_at, "fat_g")
        blockers.append(
            {
                "database_write_attempted": False,
                "source_code": source_code,
                "unsupported_legacy_fields": unsupported,
            }
        )
    return blockers


def build_metadata_receipt():
    lock = load(PACKAGE / "input-lock.json")
    external_inputs = [
        item for item in lock["inputs"] if item["root"] == "corpus"
    ]
    return {
        "acceptance_evidence": "repository_metadata_only",
        "builder_sha256": digest(Path(__file__)),
        "database_write_attempted": False,
        "domain_blockers": expected_domain_blockers(),
        "external_full_build_a_b_hashes": None,
        "external_full_build_claim_used_for_acceptance": False,
        "external_inputs": external_inputs,
        "identity_plan_sha256": digest(PACKAGE / "identity-plan.json"),
        "input_lock_sha256": digest(PACKAGE / "input-lock.json"),
        "numeric_payload_retained_in_repository": False,
        "production_publication_ready": False,
        "profile_review_sha256": digest(PROFILE_REVIEW),
        "rights_review_sha256": digest(PACKAGE / "source-use-review.json"),
        "verification_summary_sha256": digest(
            PACKAGE / "verification-summary.json"
        ),
    }


def validate_repository_contract():
    lock = load(PACKAGE / "input-lock.json")
    repo_inputs = {item["path"] for item in lock["inputs"] if item["root"] == "repo"}
    if repo_inputs != EXPECTED_REPO_INPUTS:
        raise ValueError("repository dependency lock drift")
    for item in lock["inputs"]:
        if item["root"] == "repo":
            path = ROOT / item["path"]
            if digest(path) != item["sha256"]:
                raise ValueError("changed repository input: " + item["path"])
    validate_identity_plan()
    validate_rights_review()
    validate_verification_summary()
    expected_receipt = build_metadata_receipt()
    if load(PACKAGE / "verification-receipt.json") != expected_receipt:
        raise ValueError("verification receipt drift")
    return expected_receipt


def probe_profile(profile):
    """Use real domain validation with ephemeral UUID4-shaped IDs, not persisted IDs."""
    cells = {row["source_field"]: row for row in profile["observations"]}

    def amount(field):
        value = cells[field]["source_value"]["value"]
        return Decimal(value) if value is not None else None

    missing = [
        field for field in ["protein_g", "fat_g"] if amount(field) is None
    ]
    # Source-native carbohydrate is preserved but is not silently cast to legacy.
    missing.append("carbohydrates_g")
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    try:
        FoodNutritionProfile(
            id=UUID("10000000-0000-4000-8000-000000000001"),
            food_ingredient_id=UUID("10000000-0000-4000-8000-000000000002"),
            basis_grams=Decimal("100"),
            kcal=amount("energy_kcal"),
            protein_g=amount("protein_g"),
            fat_g=amount("fat_g"),
            carbohydrates_g=None,
            fiber_g=amount("fiber_g"),
            source_name="SC-BOOK-2002",
            source_id=profile["source_code"],
            source_version="2002",
            source_data_type="published_compositional_profile",
            verified_at=now,
            estimated=None,
            is_current=False,
            created_at=now,
        )
    except DomainValidationError as exc:
        if exc.issue.field not in missing or exc.issue.code.value != "invalid_decimal":
            raise
        return {
            "profile_id": profile["id"],
            "status": "rejected_by_current_domain",
            "unsupported_legacy_fields": missing,
            "first_rejected_field": exc.issue.field,
            "domain_issue_code": exc.issue.code.value,
            "database_write_attempted": False,
        }
    raise ValueError("Domain contract changed: rerun explicit compatibility review")


def build(corpus):
    validate_repository_contract()
    lock = load(PACKAGE / "input-lock.json")
    for item in lock["inputs"]:
        path = (corpus if item["root"] == "corpus" else ROOT) / item["path"]
        if digest(path) != item["sha256"]:
            raise ValueError("changed input: " + item["path"])
    source_rows = [
        json.loads(line)
        for line in (
            corpus / "packages/reference-profiles/normalized/profiles.jsonl"
        ).read_text().splitlines()
    ]
    source = {row["source_code"]: row for row in source_rows}
    if len(source) != len(source_rows):
        raise ValueError("duplicate source codes")
    output = []
    counts = Counter()
    for identity in load(PACKAGE / "identity-plan.json"):
        row = source[identity["book_source_code"]]
        if (
            row["basis_g"] != 100
            or row["basis_part"] != "edible"
            or set(row["values"]) != FIELDS
        ):
            raise ValueError("changed source basis or fields")
        observations = []
        for field, cell in sorted(row["values"].items()):
            validate_cell(cell)
            counts[cell["state"]] += 1
            observations.append(
                {
                    "id": row["id"] + ":" + field,
                    "source_field": field,
                    "source_value": cell,
                    "canonical_nutrient_code": None,
                    "canonical_mapping_status": (
                        "source_native_only_pending_component_review"
                    ),
                    "method": (
                        "unspecified_with_book_general_method"
                        if field == "carbohydrates_g"
                        else "source_definition_reference"
                    ),
                    "independently_measured": False,
                    "planner_usable": False,
                }
            )
        output.append(
            {
                "id": "dc2-profile-draft:" + row["source_code"] + ":v1",
                "source_reference_id": row["id"],
                "source_code": row["source_code"],
                "source_name": row["source_name"],
                "source_edition": "2002",
                "basis_g": "100",
                "basis_part": "edible",
                "identity_plan": identity,
                "profile_uuid": None,
                "provenance": row["provenance"],
                "observations": observations,
                "source_value_type": row["value_type"],
                "rights_status": "BLOCKED_PENDING_RIGHTS_REVIEW",
                "publication_ready": False,
                "transformation_version": VERSION,
            }
        )
    output.sort(key=lambda row: row["id"])
    probes = [probe_profile(profile) for profile in output]
    summary = {
        "profiles": len(output),
        "observations": sum(counts.values()),
        "source_states": dict(counts),
        "required_source_fields_per_profile": 6,
        "additional_reviewed_source_fields_per_profile": 6,
        "canonical_numeric_values": 0,
        "imported_profiles": 0,
        "domain_rejections": len(probes),
        "rights_status": "BLOCKED_PENDING_RIGHTS_REVIEW",
        "full_book_nutrient_coverage": False,
        "scope": (
            "all twelve fields in five reviewed reference profiles; "
            "additional book columns remain separate"
        ),
    }
    return {
        "profiles.json": output,
        "domain-probe.json": probes,
        "summary.json": summary,
        "receipt.json": {
            "input_lock": lock,
            "builder_sha256": digest(Path(__file__)),
            "identity_plan_sha256": digest(PACKAGE / "identity-plan.json"),
            "transformation_version": VERSION,
        },
    }


def write(result, directory):
    directory = directory.resolve()
    if directory == ROOT or ROOT in directory.parents:
        raise ValueError("numeric payload must remain outside public repository")
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("output directory must be empty; preserve previous packages")
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in result.items():
        (directory / name).write_text(encoded(value))
    (directory / "checksums.json").write_text(
        encoded({name: digest(directory / name) for name in sorted(result)})
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-repository", action="store_true")
    args = parser.parse_args()
    if args.validate_repository:
        print(encoded(validate_repository_contract()))
    elif args.corpus is not None and args.output is not None:
        result = build(args.corpus)
        write(result, args.output)
        print(encoded(result["summary.json"]))
    else:
        parser.error(
            "--validate-repository or both --corpus and --output are required"
        )
