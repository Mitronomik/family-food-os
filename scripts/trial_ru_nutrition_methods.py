"""Run/verify Russian method policies for the five PR74-reviewed profiles.

External numeric source rows stay outside Git while source reuse is unresolved.
Repository acceptance uses only nonnumeric PR74 evidence and current policy code.
"""

import argparse
from collections import Counter
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/russian-methodology"
PR74_PACKAGE = ROOT / "data/curation/dc2-first-profile-payload"
PROFILE_REVIEW = (
    ROOT / "data/curation/dc2-first-batch-review/generated/profile-reviews.json"
)

sys.path.insert(0, str(ROOT / "backend"))
from app.domain.nutrition_methodology import (  # noqa: E402
    NutrientKind as N,
    ObservationMethod as M,
    ObservationState as S,
    ObservationSource,
    SourceObservation,
    RussianNutritionPolicy as P,
    evaluate_observation,
)

CODES = {"10.1.1", "8.1.5.1", "8.1.2.1", "8.1.5.12", "6.5.3"}
FIELDS = {
    "energy_kcal": (N.PUBLISHED_ENERGY, M.PUBLISHED),
    "protein_g": (N.PROTEIN, M.PUBLISHED),
    "fat_g": (N.FAT, M.PUBLISHED),
    "carbohydrates_g": (
        N.AVAILABLE_CARBOHYDRATE,
        M.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED,
    ),
    "fiber_g": (N.FIBRE, M.PUBLISHED),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def selected_reviews():
    rows = [row for row in load(PROFILE_REVIEW) if row["source_code"] in CODES]
    if len(rows) != 5 or {row["source_code"] for row in rows} != CODES:
        raise ValueError("Изменился набор пяти проверенных профилей.")
    selected = {row["source_code"]: row for row in rows}
    for row in selected.values():
        if (
            row["basis_g"] != 100
            or row["basis_reviewed"] is not True
            or row["publication_ready"] is not False
            or row["canonical_nutrient_mapping"] is not None
            or row["rights_disposition"]
            != "REFERENCE_ONLY_PUBLICATION_USE_UNRESOLVED"
            or row["carbohydrate_disposition"]
            != "SOURCE_NATIVE_METHOD_NOT_CANONICAL_CHOAVL_OR_CHOCDF"
            or row["zero_disposition"] != "NONDETECTION_NOT_EXACT_ZERO"
        ):
            raise ValueError("Изменился принятый PR74 review contract.")
    return selected


def expected_summary():
    reviews = selected_reviews()
    states = Counter()
    for row in reviews.values():
        for field in FIELDS:
            states[row["field_states"][field]] += 1
    if states != Counter({"published_positive": 22, "below_detection": 3}):
        raise ValueError("Изменились состояния core-наблюдений.")
    if any(
        row["field_states"]["carbohydrates_g"] != "published_positive"
        for row in reviews.values()
    ):
        raise ValueError("Усвояемые углеводы больше не имеют пяти reviewed values.")
    return {
        "acceptance_evidence": "repository_metadata_only",
        "approved_policies": [
            P.STRICT_V1.value,
            P.PUBLISHED_ZERO_ESTIMATE_V1.value,
        ],
        "canonical_profiles_imported": 0,
        "explicit_zero_estimates": 3,
        "external_trial_a_b_hashes": None,
        "external_trial_claim_used_for_acceptance": False,
        "numeric_trial_retained_in_repository": False,
        "policy_results": 50,
        "production_ready": False,
        "profiles": 5,
        "source_core_observations": 25,
        "source_native_available_carbohydrate_accepted_per_policy": 5,
        "source_rights_status": "BLOCKED_PENDING_RIGHTS_REVIEW",
        "strict_unknown_values": 3,
    }


def expected_receipt():
    pr74_receipt = load(PR74_PACKAGE / "verification-receipt.json")
    pr74_summary = load(PR74_PACKAGE / "verification-summary.json")
    if (
        pr74_receipt["production_publication_ready"] is not False
        or pr74_receipt["numeric_payload_retained_in_repository"] is not False
        or pr74_receipt["database_write_attempted"] is not False
        or pr74_summary["rights_status"] != "BLOCKED_PENDING_RIGHTS_REVIEW"
        or pr74_summary["imported_profiles"] != 0
        or pr74_summary["canonical_numeric_values"] != 0
    ):
        raise ValueError("PR74 evidence boundary no longer blocks publication.")
    return {
        "acceptance_evidence": "repository_metadata_only",
        "approved_zero_policy": P.PUBLISHED_ZERO_ESTIMATE_V1.value,
        "approved_zero_policy_constraints": [
            "original_state_remains_below_detection",
            "detection_limit_remains_unknown",
            "interpreted_amount_is_estimated_not_exact",
            "not_allergen_absence",
            "not_default_planner_truth_without_pinned_methodology",
        ],
        "canonical_profiles_imported": 0,
        "external_trial_a_b_hashes": None,
        "external_trial_claim_used_for_acceptance": False,
        "methodology_module_sha256": sha(
            ROOT / "backend/app/domain/nutrition_methodology.py"
        ),
        "numeric_trial_retained_in_repository": False,
        "pr74_input_lock_sha256": sha(PR74_PACKAGE / "input-lock.json"),
        "pr74_verification_receipt_sha256": sha(
            PR74_PACKAGE / "verification-receipt.json"
        ),
        "profile_review_sha256": sha(PROFILE_REVIEW),
        "production_ready": False,
        "source_rights_status": "BLOCKED_PENDING_RIGHTS_REVIEW",
        "trial_builder_sha256": sha(Path(__file__)),
        "trial_summary_sha256": sha(PACKAGE / "trial-summary.json"),
    }


def validate_repository_contract():
    expected = expected_summary()
    if load(PACKAGE / "trial-summary.json") != expected:
        raise ValueError("trial-summary не соответствует repository evidence.")
    receipt = expected_receipt()
    if load(PACKAGE / "trial-verification-receipt.json") != receipt:
        raise ValueError("trial verification receipt устарел.")
    return receipt


def build(corpus):
    validate_repository_contract()
    lock = load(PR74_PACKAGE / "input-lock.json")
    entry = next(
        row
        for row in lock["inputs"]
        if row["root"] == "corpus"
        and row["path"] == "packages/reference-profiles/normalized/profiles.jsonl"
    )
    path = corpus / entry["path"]
    if sha(path) != entry["sha256"]:
        raise ValueError("Исходные профили изменились.")
    profiles = [
        row
        for row in map(json.loads, path.read_text().splitlines())
        if row["source_code"] in CODES
    ]
    if len(profiles) != 5 or {row["source_code"] for row in profiles} != CODES:
        raise ValueError("Неполный набор профилей.")

    reviews = selected_reviews()
    results = []
    for row in sorted(profiles, key=lambda item: item["source_code"]):
        review = reviews[row["source_code"]]
        if row["basis_g"] != 100 or row["basis_part"] != "edible":
            raise ValueError("Изменилась база.")
        for field, (kind, method) in FIELDS.items():
            cell = row["values"][field]
            if cell["state"] != review["field_states"][field]:
                raise ValueError("Numeric source state расходится с PR74 review.")
            state = {
                "published_positive": S.VALUE,
                "below_detection": S.BELOW_DETECTION,
                "missing": S.MISSING,
            }[cell["state"]]
            if state != S.VALUE and cell["value"] is not None:
                raise ValueError("Неизвестное подменено числом.")
            observation = SourceObservation(
                kind,
                method,
                state,
                Decimal(cell["value"]) if cell["value"] is not None else None,
                cell["unit"],
                Decimal(100),
                ObservationSource(
                    "SC-BOOK-2002",
                    "2002",
                    json.dumps(
                        row["provenance"], sort_keys=True, ensure_ascii=False
                    ),
                    row["id"] + ":" + field,
                    row["id"] + ":source-form",
                    cell["definition_code"],
                ),
                cell["published_value"],
            )
            for policy in P:
                results.append(asdict(evaluate_observation(observation, policy)))

    summary = dict(
        profiles=5,
        source_core_observations=25,
        policy_results=len(results),
        canonical_profiles_imported=0,
        source_native_available_carbohydrate_accepted_per_policy=5,
        strict_unknown_values=sum(
            row["amount"] is None
            for row in results
            if row["policy"] == P.STRICT_V1
        ),
        explicit_zero_estimates=sum(
            row["estimated"]
            for row in results
            if row["policy"] == P.PUBLISHED_ZERO_ESTIMATE_V1
        ),
        production_ready=False,
        reference_profiles_sha256=entry["sha256"],
        builder_sha256=sha(Path(__file__)),
    )
    return {"summary": summary, "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-repository", action="store_true")
    args = parser.parse_args()

    if args.validate_repository:
        print(json.dumps(validate_repository_contract(), ensure_ascii=False, sort_keys=True))
    elif args.corpus is not None and args.output is not None:
        output = args.output.resolve()
        if output == ROOT or ROOT in output.parents:
            parser.error("Числовой пакет должен оставаться вне публичного репозитория.")
        if output.exists():
            parser.error("Выберите новый файл; предыдущие результаты сохраняются.")
        result = build(args.corpus)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                default=lambda value: (
                    format(value, "f") if isinstance(value, Decimal) else value
                ),
            )
            + "\n"
        )
        print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    else:
        parser.error(
            "--validate-repository or both --corpus and --output are required"
        )
