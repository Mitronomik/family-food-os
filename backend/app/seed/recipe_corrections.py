"""Bounded B2-A correction and explicit assessment promotion, never runtime policy.

Run each loader after its prerequisites. Both loaders are atomic and idempotent;
parents are pinned historical versions, not whatever happens to be current.
"""

from collections import Counter
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import hashlib
import json
from uuid import uuid4

from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_recipe_uow import (
    SqlAlchemyRecipeCatalogueUnitOfWork,
)
from app.persistence.sqlalchemy_core.nutrition_evidence_uow import (
    SqlAlchemyNutritionEvidenceUnitOfWork,
)
from app.seed.food_recipes import load_seed_entries as load_recipe_seeds
from app.seed.nutrition_measure_evidence import (
    ROOT,
    _instant,
    _prototype,
    _require,
    _resolve,
    load_seed_entries as load_b1,
)
from app.services.food_recipes import _seed_matches

OPERATION = "PR6-DATA-B2-A"
STARTING_MAIN = "74bc80eb3ef0e34e17751856638ac58bbccb840e"
DIRECTORY = ROOT / "data/seed/recipe_corrections/pr6-data-b2a"
CURATION = "data/curation/pr6-data-b2a/source-quantity-corrections.json"
PR4 = "data/seed/recipes/recipes.json"
B1 = "data/seed/nutrition_measure_evidence"
INPUT_PATHS = {
    PR4,
    "data/seed/food_ingredients/nutrition.csv",
    f"{B1}/manifest.json",
    f"{B1}/evidence.json",
    f"{B1}/assessments.json",
    "data/curation/pr6-data-a/conversion-gap-audit.json",
    "data/curation/pr6-data-a/source-manifest.json",
    CURATION,
}
FINDINGS = {
    ("HARV6_FRESH_TOMATO_SALSA", 1),
    ("SNAP6_SPINACH_APPLE_SALAD", 1),
    ("SNAP6_SPINACH_APPLE_SALAD", 2),
    ("SNAP6_SEARED_GREENS", 1),
    ("WIC1_OVERNIGHT_OATS_CINNAMON_APPLE", 5),
    ("SNAP4_BROWN_RICE_PILAF", 1),
}
ROW_FIELDS = (
    "food_ingredient_code",
    "quantity",
    "unit",
    "source_amount_text",
    "normalization_note",
    "prep_note",
    "optional",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_descriptor(row, profile):
    """Stable proof includes the complete row and pinned profile provenance/values."""
    return {field: row[field] for field in ROW_FIELDS} | {"profile": profile}


def build_promotion(curation, recipes, b1_rows):
    """Offline deterministic promotion; changed rows require curation decisions.

    Also rechecked at import, before a write scope is opened. This function does
    not choose quantities, accept estimates, or resolve food/profile defects.
    """
    _require(
        curation["schema_version"] == 1 and curation["operation"] == OPERATION,
        "Invalid B2-A review authority.",
    )
    records = curation["records"]
    keys = [(r["recipe_canonical_code"], r["ingredient_position"]) for r in records]
    _require(
        len(keys) == len(set(keys)) and set(keys) == FINDINGS,
        "B2-A must review exactly the six authorized findings.",
    )
    by_code = {r["canonical_code"]: r for r in recipes}
    reviews = {
        (a["recipe_canonical_code"], a["ingredient_position"]): a for a in b1_rows
    }
    corrections, assessments = [], []
    for code in sorted({key[0] for key in keys}):
        findings = [r for r in records if r["recipe_canonical_code"] == code]
        parent = by_code[code]
        for finding in findings:
            position = finding["ingredient_position"]
            old = parent["version"]["ingredients"][position - 1]
            _require(finding["parent_version_number"] == 1, "B2-A parent must be v1.")
            _require(
                finding["resolution_status"]
                in {"CORRECTED", "CONFIRMED_CURRENT", "UNRESOLVED_SOURCE_AMBIGUITY"},
                "Invalid resolution status.",
            )
            _require(
                all(
                    finding[f] == parent["version"][f]
                    for f in (
                        "source_name",
                        "source_recipe_id",
                        "source_version",
                        "source_document_sha256",
                    )
                ),
                "Review provenance differs from PR4.",
            )
            _require(
                finding["old_quantity"] == old["quantity"]
                and finding["old_unit"] == old["unit"]
                and finding["source_amount_text"] == old["source_amount_text"],
                "Review old quantity/unit/source text differs.",
            )
            _require(
                finding["source_audit_key"]
                == reviews[code, position]["source_audit_key"],
                "Review does not address the historical B1 row.",
            )
            _require(
                finding["source_evidence_reference"]["reopened_sha256"]
                == finding["source_document_sha256"],
                "Reopened artifact differs.",
            )
        # The gate is per recipe: an ambiguous row suppresses the entire revision.
        if any(
            r["resolution_status"] == "UNRESOLVED_SOURCE_AMBIGUITY" for r in findings
        ):
            continue
        changes = [r for r in findings if r["resolution_status"] == "CORRECTED"]
        if not changes:
            continue
        revision = deepcopy(parent)
        revision["version"]["change_note"] = (
            f"{OPERATION}: reviewed FamilyFoodOS source-quantity normalization correction "
            f"at ingredient positions {', '.join(str(r['ingredient_position']) for r in changes)}; "
            "same external artifact, immutable v1 retained."
        )
        revision["version"]["verified_at"] = curation["reviewed_at"]
        changed = {r["ingredient_position"]: r for r in changes}
        for position, row in enumerate(revision["version"]["ingredients"], 1):
            old_review = reviews[code, position]
            old = parent["version"]["ingredients"][position - 1]
            before = row_descriptor(old, old_review["profile"])
            b1_descriptor = {
                f: old_review[
                    {"quantity": "recipe_quantity", "unit": "recipe_unit"}.get(f, f)
                ]
                for f in ROW_FIELDS
            } | {"profile": old_review["profile"]}
            _require(
                before == b1_descriptor,
                "Historical B1 descriptor differs from PR4 row.",
            )
            assessment = deepcopy(old_review)
            if position in changed:
                finding = changed[position]
                row.update(
                    quantity=finding["corrected_quantity"],
                    unit=finding["corrected_unit"],
                    normalization_note=finding["corrected_normalization_note"],
                )
                _require(
                    Decimal(row["quantity"]).is_finite()
                    and Decimal(row["quantity"]) > 0
                    and row["unit"] in ("g", "ml", "pcs"),
                    "Invalid reviewed quantity/unit.",
                )
                assessment.update(finding["nutrition_review"])
                mode = "NEW_QUANTITY_REVIEW"
            else:
                _require(
                    before == row_descriptor(row, assessment["profile"]),
                    "Carry-forward requires complete row/profile equality.",
                )
                assessment["review_note"] = (
                    "Explicit B2-A carry-forward after deterministic equality of FoodIngredient, "
                    "quantity, unit, source amount, normalization/prep notes, optional flag and "
                    "pinned FoodNutritionProfile. Historical B1 decision: "
                    + old_review["review_note"]
                )
                mode = "EXPLICIT_EQUAL_ROW_CARRY_FORWARD"
            assessment.update(
                recipe_quantity=row["quantity"],
                recipe_unit=row["unit"],
                normalization_note=row["normalization_note"],
                source_audit_operation=OPERATION,
                source_audit_key=f"{code}:v2:{position}",
                reviewed_at=curation["reviewed_at"],
                created_at=curation["reviewed_at"],
            )
            _prototype(assessment)  # Enforce existing domain status/issue invariants.
            assessments.append(
                dict(
                    recipe_version_number=2,
                    parent_version_number=1,
                    promotion_mode=mode,
                    parent_source_audit_key=old_review["source_audit_key"],
                    compared_parent=before,
                    compared_revision=row_descriptor(row, assessment["profile"]),
                    assessment=assessment,
                )
            )
        corrections.append(
            dict(
                recipe_canonical_code=code,
                parent_version_number=1,
                version_number=2,
                created_at=curation["reviewed_at"],
                parent=parent,
                revision=revision,
            )
        )
    return (
        dict(schema_version=1, corrections=corrections),
        dict(schema_version=1, assessments=assessments),
    )


def load_entries(directory=DIRECTORY):
    manifest = read_json(directory / "manifest.json")
    _require(
        manifest["schema_version"] == 1
        and manifest["operation"] == OPERATION
        and manifest["starting_main"] == STARTING_MAIN,
        "B2-A manifest authority differs.",
    )
    _require(
        set(manifest["input_sha256"]) == INPUT_PATHS, "Invalid B2-A input inventory."
    )
    for name, expected in manifest["input_sha256"].items():
        _require(
            digest(ROOT / name) == expected,
            "B2-A protected input hash differs: " + name,
        )
    _require(
        set(manifest["payload_sha256"]) == {"corrections.json", "assessments.json"},
        "Invalid B2-A payload inventory.",
    )
    for name, expected in manifest["payload_sha256"].items():
        _require(
            digest(directory / name) == expected, "B2-A payload hash differs: " + name
        )
    _, _, b1_rows = load_b1()
    expected = build_promotion(
        read_json(ROOT / CURATION), read_json(ROOT / PR4)["recipes"], b1_rows
    )
    actual = tuple(
        read_json(directory / name) for name in ("corrections.json", "assessments.json")
    )
    _require(
        actual == expected,
        "B2-A payload differs from reviewed deterministic promotion.",
    )
    _require(
        manifest["recipe_version_count"] == len(actual[0]["corrections"])
        and manifest["assessment_count"] == len(actual[1]["assessments"]),
        "B2-A manifest counts differ.",
    )
    return actual[0]["corrections"], actual[1]["assessments"], b1_rows


def _revision(parent, entry):
    """Clone an immutable aggregate; replace only reviewed fields and identities."""
    now = _instant(entry["created_at"])
    version_id = uuid4()
    reviewed = entry["revision"]["version"]
    return replace(
        parent,
        version=replace(
            parent.version,
            id=version_id,
            version_number=entry["version_number"],
            created_from_version_id=parent.version.id,
            created_at=now,
            verified_at=_instant(reviewed["verified_at"]),
            change_note=reviewed["change_note"],
        ),
        ingredients=tuple(
            replace(
                row,
                id=uuid4(),
                recipe_version_id=version_id,
                created_at=now,
                quantity=Decimal(reviewed["ingredients"][row.position - 1]["quantity"]),
                unit=reviewed["ingredients"][row.position - 1]["unit"],
                normalization_note=reviewed["ingredients"][row.position - 1][
                    "normalization_note"
                ],
            )
            for row in parent.ingredients
        ),
        steps=tuple(
            replace(row, id=uuid4(), recipe_version_id=version_id, created_at=now)
            for row in parent.steps
        ),
        equipment=tuple(
            replace(row, recipe_version_id=version_id) for row in parent.equipment
        ),
    )


def _same_revision(existing, expected):
    """Compare all facts, tolerating only locally generated UUIDs."""
    if len(existing.ingredients) != len(expected.ingredients) or len(
        existing.steps
    ) != len(expected.steps):
        return False
    version_id = existing.version.id
    return existing == replace(
        expected,
        version=replace(expected.version, id=version_id),
        ingredients=tuple(
            replace(b, id=a.id, recipe_version_id=version_id)
            for a, b in zip(existing.ingredients, expected.ingredients)
        ),
        steps=tuple(
            replace(b, id=a.id, recipe_version_id=version_id)
            for a, b in zip(existing.steps, expected.steps)
        ),
        equipment=tuple(
            replace(b, recipe_version_id=version_id) for b in expected.equipment
        ),
    )


def _reviewed_revision(uow, entry, seeds):
    """Resolve and verify the complete pinned parent in the active transaction."""
    code = entry["recipe_canonical_code"]
    recipe = uow.recipes.get_by_code(code)
    _require(
        recipe is not None
        and recipe.is_active
        and recipe.canonical_name == seeds[code].canonical_name,
        "Missing/changed parent Recipe: " + code,
    )
    versions = uow.versions.list_for_recipe(recipe.id)
    parent_version = next(
        (v for v in versions if v.version_number == entry["parent_version_number"]),
        None,
    )
    _require(parent_version is not None, "Missing explicit parent version: " + code)
    parent = uow.versions.get_detail(parent_version.id)
    _require(
        parent.version.created_from_version_id is None
        and all(s.stage_code is None for s in parent.steps)
        and _seed_matches(uow, parent, seeds[code].version),
        "Complete reviewed parent differs: " + code,
    )
    expected = _revision(parent, entry)
    existing = next(
        (v for v in versions if v.version_number == entry["version_number"]), None
    )
    if existing is not None:
        _require(
            _same_revision(uow.versions.get_detail(existing.id), expected),
            "Conflicting existing v2: " + code,
        )
    return parent, expected, existing, versions


def seed_recipe_corrections(config=None, *, seed_directory=DIRECTORY):
    entries, _, _ = load_entries(seed_directory)
    seeds = {r.canonical_code: r for r in load_recipe_seeds()}
    engine = create_sqlite_engine(config)
    inserted = 0
    try:
        with SqlAlchemyRecipeCatalogueUnitOfWork(engine) as uow:
            for entry in entries:
                code = entry["recipe_canonical_code"]
                parent, expected, existing, versions = _reviewed_revision(
                    uow, entry, seeds
                )
                if existing is None:
                    _require(
                        versions[-1].id == parent.version.id,
                        "Unexpected later history: " + code,
                    )
                    uow.versions.add_detail(expected)
                    inserted += 1
            uow.commit()
        return {"inserted_versions": inserted, "reviewed_versions": len(entries)}
    finally:
        engine.dispose()


def seed_correction_assessments(config=None, *, seed_directory=DIRECTORY):
    corrections, entries, b1_rows = load_entries(seed_directory)
    seeds = {r.canonical_code: r for r in load_recipe_seeds()}
    parents = {
        (a["recipe_canonical_code"], a["ingredient_position"]): a for a in b1_rows
    }
    engine = create_sqlite_engine(config)
    inserted = 0
    try:
        with SqlAlchemyNutritionEvidenceUnitOfWork(engine) as uow:
            # Verify exact v2 contents and parent/provenance chains before binding any row.
            for entry in corrections:
                _, _, existing, _ = _reviewed_revision(uow, entry, seeds)
                _require(
                    existing is not None, "B2-A correction prerequisite is absent."
                )
            evidence = {}
            for entry in entries:
                descriptor = entry["assessment"]
                parent_descriptor = parents[
                    descriptor["recipe_canonical_code"],
                    descriptor["ingredient_position"],
                ]
                for d in (parent_descriptor, descriptor):
                    key = d["evidence_key"]
                    if key:
                        evidence[key] = uow.evidence.get_by_key(key)
                        _require(
                            evidence[key] is not None,
                            "Missing historical B1 evidence: " + key,
                        )
                parent = _resolve(
                    uow,
                    parent_descriptor,
                    evidence,
                    version_number=entry["parent_version_number"],
                )
                sealed = uow.evidence.get_current_assessment(
                    parent.recipe_ingredient_id
                )
                _require(
                    sealed is not None and replace(parent, id=sealed.id) == sealed,
                    "Historical B1 assessment differs.",
                )
                assessment = _resolve(
                    uow,
                    descriptor,
                    evidence,
                    version_number=entry["recipe_version_number"],
                )
                _require(
                    assessment.recipe_ingredient_id != parent.recipe_ingredient_id,
                    "B2-A assessment must address a new row.",
                )
                existing = uow.evidence.get_current_assessment(
                    assessment.recipe_ingredient_id
                )
                if existing is None:
                    uow.evidence.add_assessment(assessment)
                    inserted += 1
                else:
                    _require(
                        replace(assessment, id=existing.id) == existing,
                        "Conflicting B2-A assessment.",
                    )
            uow.commit()
        return {
            "inserted_assessments": inserted,
            "assessment_count": len(entries),
            "status_counts": dict(
                sorted(Counter(e["assessment"]["status_code"] for e in entries).items())
            ),
        }
    finally:
        engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("corrections", "assessments"))
    args = parser.parse_args()
    loader = (
        seed_recipe_corrections
        if args.operation == "corrections"
        else seed_correction_assessments
    )
    print(json.dumps(loader(), sort_keys=True))
