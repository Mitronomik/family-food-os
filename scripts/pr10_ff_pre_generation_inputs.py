"""PR10-FF test-only pre-generation A/B input materialization.

Never calls Planner.generate_authoritative / pure generate_week. This tool emits
*proposed* source and logical-input bytes for independent review and external
SHA approval. Its own calculated hashes are OBSERVATIONS, not approval pins.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.db.config import DatabaseConfig
from app.domain.meal_patterns import MealRole
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.household_uow import (
    SqlAlchemyHouseholdReadScope,
    SqlAlchemyHouseholdUnitOfWork,
)
from app.seed import dc4_a3_russian_step_corrections as dc4
from app.seed import r1f_prepared_output as r1f
from app.seed import r1h_school2022_main as r1h
from app.seed import r2_breakfast_capacity as r2
from app.seed import r2b_fish_main_diversity as r2b
from app.seed import r2c_breakfast_grain_diversity as r2c
from app.seed import r2e_cottage_casserole as r2e
from app.seed import r2f_cheese_sandwich as r2f
from app.seed import r3a_school2022_main_batch as r3a
from app.seed import r3b_school2022_breakfast_batch as r3b
from app.seed import r3c_school2022_main_batch as r3c
from app.seed import r3d_final_dc3_batch as r3d
from app.services.households import HouseholdService
from app.services.pr10_ff_manifest_loader import (
    SCHEMA_VERSION,
    _expected_recipe_allowlist,
    load_pinned_publication_manifest,
    process_steps_sha256,
    project_trusted_version_seed,
)
from app.services.pr10_ff_typed_ids import FIXTURE_ID, NAMESPACE, POLICY

from scripts.audit_dc4_corpus_readiness_rerun import (
    GATE1_ROLE_SHAPES,
    PLANNER_CONFIG,
    _accept_custom_pattern,
    _fixture_exclusions,
    _services,
)

SOURCE_COMMIT = "0d390bdf0d620f711916287cf0d656aa9c8a6844"
INPUT_SCHEMA = "PR10_FF_INPUT_MANIFEST_V1"
WEEK_START = date(2026, 11, 2)
HOUSEHOLD_KEY = "PR10_FF_FORWARD_SYNTHETIC_3M_V1"
CORRECTION_SHA256 = "157f2ce76cc86baae2b288ce80da069154bc6d44ca1620b2b9f0c521b92e7759"
CORRECTION_GIT_BLOB = "ec1f8fca9ff8d3c4ac844f6eab0c3411ece54c68"
EXPECTED_SOURCE_CODES = 51
EXPECTED_CORRECTION_CODES = 7


class PreflightNoGo(ValueError):
    """Unapproved or mismatching pre-generation logical input."""


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, Decimal) or not value.is_finite():
        raise PreflightNoGo("nonfinite or unsupported Decimal input")
    return "0" if value.is_zero() else format(value.normalize(), "f")


def _source_stages() -> list[tuple[str, tuple]]:
    """Source-checked existing frozen seed loaders; never read Planner output."""
    return [
        ("r1f", r1f._recipe_seeds(r1f._load_evidence())),
        ("r1h", r1h._recipe_seeds_and_specs(r1h._load_contract()[0])[0]),
        ("r2", r2._recipe_seeds_and_specs(r2._load_contract()[2])[0]),
        ("r2b", r2b._recipe_seeds_and_specs(r2b._load_contract()[2])[0]),
        ("r2c", r2c._recipe_seeds_and_specs(r2c._load_contract()[2])[0]),
        ("r2e", (r2e._recipe_seed_and_spec(r2e._load_contract()[-1])[0],)),
        ("r2f", (r2f._recipe_seed_and_spec(r2f._load_contract()[-1])[0],)),
        ("r3a", r3a._recipe_seeds_and_specs(r3a._load_contract()[4])[0]),
        ("r3b", r3b._recipe_seeds_and_specs(r3b._load_contract()[4])[0]),
        ("r3c", r3c._recipe_seeds_and_specs(r3c._load_contract()[0])[0]),
        ("r3d", r3d._recipe_seeds_and_specs(
            r3d._load_contract()[0], r3d._load_contract()[2],
        )[0]),
    ]


def _version_key(recipe, *, number=1, predecessor=None, correction_sha=None):
    version = recipe.version
    return {
        "canonical_code": recipe.canonical_code,
        "source_record_key": {
            "canonical_code": recipe.canonical_code,
            "source_name": version.source_name,
            "source_recipe_id": version.source_recipe_id,
            "source_version": version.source_version,
            "source_document_sha256": version.source_document_sha256,
        },
        "version_number": number,
        "predecessor_version_key": predecessor,
        "publication_kind": "ORIGINAL" if number == 1 else "REVIEWED_CORRECTION",
        "publication_process_sha256": process_steps_sha256(version.steps),
        "correction_revision_sha256": correction_sha,
    }


def _member_profile(ordinal: int) -> dict[str, object]:
    if ordinal not in (1, 2, 3):
        raise PreflightNoGo("unapproved synthetic member ordinal")
    return {
        "ordinal": ordinal,
        "name": f"Участник {ordinal}",
        "active": True,
        "birth_date": f"1990-01-0{ordinal}",
        "sex": "female" if ordinal % 2 else "male",
        "height_cm": "170",
        "weight_kg": "65",
        "activity_level": "active",
        "goal": "maintain",
    }


def build_source_proposal() -> tuple[dict, dict[int, dict]]:
    stages = _source_stages()
    if len(stages) != 11:
        raise PreflightNoGo("source stage inventory not 11")
    recipes = [recipe for _, rows in stages for recipe in rows]
    originals = {row.canonical_code: row for row in recipes}
    if len(originals) != len(recipes) or len(recipes) != EXPECTED_SOURCE_CODES:
        raise PreflightNoGo("not the 51 unique original RecipeVersions")
    correction_artifact = dc4._load_corrections()
    if sha(dc4.CORRECTIONS_PATH.read_bytes()) != CORRECTION_SHA256:
        raise PreflightNoGo("DC4-A3 raw correction SHA drift")
    corrected = {row["canonical_code"]: row for row in correction_artifact["recipes"]}
    if set(corrected) != set(dc4.CORRECTION_CODES) or len(corrected) != 7:
        raise PreflightNoGo("correction source membership drift")

    stages_map: dict[str, list[str]] = {}
    records = []
    for stage, rows in stages:
        stages_map[stage] = []
        for row in rows:
            records.append({
                "stage": stage,
                "canonical_code": row.canonical_code,
                "version_number": 1,
                "version_key": _version_key(row),
                "seed_projection": json.loads(project_trusted_version_seed(row.version)),
            })
            stages_map[stage].append(f"{row.canonical_code}@1")
    stages_map["dc4_a3"] = []
    for code in dc4.CORRECTION_CODES:
        predecessor = originals[code]
        successor = replace(
            predecessor,
            version=replace(
                predecessor.version,
                steps=tuple(corrected[code]["new_steps"]),
                change_note=correction_artifact["change_note"],
            ),
        )
        records.append({
            "stage": "dc4_a3",
            "canonical_code": code,
            "version_number": 2,
            "version_key": _version_key(
                successor, number=2, predecessor=_version_key(predecessor),
                correction_sha=CORRECTION_SHA256,
            ),
            "seed_projection": json.loads(project_trusted_version_seed(successor.version)),
        })
        stages_map["dc4_a3"].append(f"{code}@2")
    if len(records) != 58 or len(stages_map) != 12:
        raise PreflightNoGo("incomplete v1/v2 source lineage")

    profiles = {ordinal: _member_profile(ordinal) for ordinal in (1, 2, 3)}
    keys = [
        {"kind": obj["kind"], "key": obj["key"]}
        for obj in (
            json.loads(item)
            for item in sorted(_expected_recipe_allowlist(records))
        )
    ]
    keys.append({"kind": "HOUSEHOLD", "key": {"household_key": HOUSEHOLD_KEY}})
    for ordinal, profile in profiles.items():
        keys.append({
            "kind": "HOUSEHOLD_MEMBER",
            "key": {
                "household_key": HOUSEHOLD_KEY, "ordinal": ordinal,
                "profile_sha256": sha(canonical_bytes(profile)),
            },
        })
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "policy": POLICY,
        "namespace": NAMESPACE,
        "fixture_id": FIXTURE_ID,
        "source_commit": SOURCE_COMMIT,
        "review_reference": "PROPOSED / reviewer must pin raw bytes externally",
        "approved_ids": keys,
        "publications": records,
        "stages": stages_map,
    }
    return manifest, profiles


def _household_service(engine, identity_factory):
    """Exactly one semantic-key factory for exactly one Household operation."""
    return HouseholdService(
        lambda: SqlAlchemyHouseholdUnitOfWork(engine),
        lambda: SqlAlchemyHouseholdReadScope(engine),
        id_factory=identity_factory,
    )


def _check_input(proposal: dict, *, actual_candidates: int) -> None:
    if proposal["week_start"] != WEEK_START.isoformat():
        raise PreflightNoGo("unreviewed week_start")
    if len(proposal["members"]) != 3 or actual_candidates != 51:
        raise PreflightNoGo("incomplete members or current Planner candidates")
    if sum(len(member["opportunities"]) for member in proposal["members"]) != 42:
        raise PreflightNoGo("invalid 3/2/1 daily opportunity inventory")
    if len(proposal["candidate_inputs"]) != actual_candidates:
        raise PreflightNoGo("candidate coverage changed")
    if proposal["pantry"] or proposal["history"] or proposal["fixed_events"]:
        raise PreflightNoGo("hidden Pantry/history/fixed-event inputs")
    for member in proposal["members"]:
        if member["reference_energy_kcal"] is None:
            raise PreflightNoGo("unsupported member reference energy")
    if any(
        row["kcal_per_base_serving"] is None or not row["exact_energy_ready"]
        for row in proposal["candidate_inputs"]
    ):
        raise PreflightNoGo("missing exact candidate energy authority")


def materialize_pre_generation(
    output_dir: Path, *, expected_base: str = SOURCE_COMMIT
) -> dict[str, str]:
    """Emit proposals A and B and run-bound UUID witness. NEVER generates a week."""
    if expected_base != SOURCE_COMMIT:
        raise PreflightNoGo("source commit differs from reviewed proposal")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise PreflightNoGo("output directory must be empty (no overwrite/retry)")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest, profiles = build_source_proposal()
    source_bytes = canonical_bytes(manifest)
    source_path = output_dir / "publication-A-PROPOSED.json"
    source_path.write_bytes(source_bytes)
    # This local calculated digest is NOT an independently accepted SHA pin.
    provider = load_pinned_publication_manifest(
        source_path,
        expected_sha256=sha(source_bytes),
        expected_source_commit=expected_base,
        expected_stage_membership=manifest["stages"],
        correction_path=dc4.CORRECTIONS_PATH,
        expected_correction_sha256=CORRECTION_SHA256,
        expected_correction_blob_sha1=CORRECTION_GIT_BLOB,
    )

    with tempfile.TemporaryDirectory(prefix="pr10_ff_pre_input_") as tmp:
        db = DatabaseConfig(path=Path(tmp) / "source-only.sqlite")
        dc4.seed_dc4_a3_russian_step_corrections(db, id_provider=provider)
        engine = create_sqlite_engine(db)
        try:
            planner, meal_plans, _, recipes, _ = _services(engine)
            from app.persistence.sqlalchemy_core.food_ingredient_composition import (
                create_food_catalogue_service,
            )
            food_catalogue = create_food_catalogue_service(engine)
            household_key = {"household_key": HOUSEHOLD_KEY}
            hh_service = _household_service(
                engine, lambda: provider.id_for("HOUSEHOLD", household_key)
            )
            household = hh_service.create_household(
                name="PR10-FF проверочная семья",
                timezone_name="Europe/Moscow",
                city="Санкт-Петербург",
            )
            if household.id != provider.id_for("HOUSEHOLD", household_key):
                raise PreflightNoGo("persisted Household identity mismatch")
            member_rows = []
            members = []
            for ordinal, roles in enumerate(GATE1_ROLE_SHAPES[2], start=1):
                profile = profiles[ordinal]
                key = {
                    "household_key": HOUSEHOLD_KEY,
                    "ordinal": ordinal,
                    "profile_sha256": sha(canonical_bytes(profile)),
                }
                scoped_service = _household_service(
                    engine, lambda key=key: provider.id_for("HOUSEHOLD_MEMBER", key)
                )
                member = scoped_service.add_household_member(
                    household.id,
                    name=profile["name"],
                    birth_date=date.fromisoformat(profile["birth_date"]),
                    sex=profile["sex"],
                    height_cm=Decimal(profile["height_cm"]),
                    weight_kg=Decimal(profile["weight_kg"]),
                    activity_level=profile["activity_level"],
                    goal=profile["goal"],
                )
                if member.id != provider.id_for("HOUSEHOLD_MEMBER", key):
                    raise PreflightNoGo("persisted Member identity mismatch")
                state = scoped_service.get_household(household.id)
                if member not in state.members:
                    raise PreflightNoGo("missing persisted member readback")
                selection = _accept_custom_pattern(
                    meal_plans, household.id, member.id, roles,
                )
                members.append(member)
                member_rows.append((ordinal, profile, member, selection))
            from app.services.planner import AuthoritativeGenerationRequest
            command = AuthoritativeGenerationRequest(
                household.id, WEEK_START,
                _fixture_exclusions(3, members, food_catalogue),
            )
            request = planner.compose_authoritative_request(command)
            admissions = planner.compose_candidate_admission()
            if len(request.candidates) != 51 or len(admissions) != 51:
                raise PreflightNoGo("full candidate admission not confirmed")
            if any(not row.eligible or not row.exact_energy_ready for row in admissions):
                raise PreflightNoGo("candidate source/nutrition admission incomplete")
            by_version = {}
            for recipe in recipes.list_all():
                if not recipe.is_active:
                    raise PreflightNoGo("unexpected inactive trusted Recipe")
                detail = recipes.get_current_verified(recipe.id)
                by_version[detail.version.id] = (recipe, detail)
            candidate_records = []
            for candidate in request.candidates:
                recipe, detail = by_version[candidate.recipe_version_id]
                version = detail.version
                if version.rights_review_status.value != "REVIEWED":
                    raise PreflightNoGo("candidate rights not reviewed")
                candidate_records.append({
                    "canonical_code": recipe.canonical_code,
                    "recipe_version_id": str(candidate.recipe_version_id),
                    "source_name": version.source_name,
                    "source_recipe_id": version.source_recipe_id,
                    "source_version": version.source_version,
                    "source_document_sha256": version.source_document_sha256,
                    "rights_review_status": version.rights_review_status.value,
                    "verification_status": version.verification_status.value,
                    "rights_basis": version.rights_basis,
                    "version_number": version.version_number,
                    "process_sha256": process_steps_sha256(
                        [step.instruction for step in detail.steps]
                    ),
                    "meal_type_code": candidate.meal_type_code.value,
                    "kcal_per_base_serving": _decimal(candidate.kcal_per_serving),
                    "nutrition_status": candidate.nutrition_status.value,
                    "exact_energy_ready": candidate.exact_energy_ready,
                    "total_time_minutes": candidate.total_time_minutes,
                    "batch_friendly": candidate.batch_friendly,
                    "ingredient_codes": sorted(
                        food_catalogue.get(ingredient_id).canonical_code
                        for ingredient_id in candidate.food_ingredient_ids
                    ),
                })
            member_records = []
            selection_witness = []
            for ordinal, profile, member, selection in member_rows:
                matched = next(x for x in request.members if x.member_id == member.id)
                if matched.selection != selection:
                    raise PreflightNoGo("member accepted-pattern readback mismatch")
                opportunities = [
                    {
                        "weekday": item.weekday,
                        "position": item.position,
                        "role": item.role.value,
                        "energy_share": _decimal(item.energy_share),
                    }
                    for item in sorted(
                        selection.opportunities,
                        key=lambda item: (item.weekday, item.position),
                    )
                ]
                member_records.append({
                    "ordinal": ordinal,
                    "profile": profile,
                    "profile_sha256": sha(canonical_bytes(profile)),
                    "member_id": str(member.id),
                    "reference_energy_kcal": _decimal(matched.reference_energy_kcal),
                    "selection_source_kind": selection.selection.source_kind.value,
                    "selection_version_number": selection.selection.version_number,
                    "opportunities": opportunities,
                    "excluded_food_codes": sorted(
                        food_catalogue.get(uid).canonical_code
                        for uid in matched.excluded_food_ingredient_ids
                    ),
                    "preferred_recipe_version_ids": sorted(
                        str(uid) for uid in matched.preferred_recipe_version_ids
                    ),
                })
                selection_witness.append({
                    "ordinal": ordinal,
                    "member_id": str(member.id),
                    "selection_id": str(selection.selection.id),
                })
            if set(request.pantry_food_ingredient_ids):
                raise PreflightNoGo("unexpected nonempty pantry")
            if request.fixed_events or request.recent_plan_ids or request.recent_recipe_version_ids:
                raise PreflightNoGo("unexpected historical/fixed events")
            config = PLANNER_CONFIG
            proposal = {
                "schema_version": INPUT_SCHEMA,
                "fixture_id": FIXTURE_ID,
                "publication_manifest_sha256": sha(source_bytes),
                "source_commit": expected_base,
                "week_start": WEEK_START.isoformat(),
                "week_end": date(2026, 11, 8).isoformat(),
                "timezone": household.timezone,
                "city": household.city,
                "planner_domain_blob_sha1": "7793e6d55f475b06b15e01e902e3144e3f5d1944",
                "planner_service_blob_sha1": "1dde67b026b3c2cab99622482979f3e1fe2d0751",
                "planner_config": {
                    "version": config.version,
                    "compatibility_version": config.compatibility_version,
                    "preference_weight": _decimal(config.preference_weight),
                    "pantry_weight": _decimal(config.pantry_weight),
                    "batch_weight": _decimal(config.batch_weight),
                    "time_weight": _decimal(config.time_weight),
                    "repetition_weight": _decimal(config.repetition_weight),
                    "max_recipe_repetitions": config.max_recipe_repetitions,
                },
                "members": member_records,
                "candidate_inputs": candidate_records,
                "candidate_admissions": [
                    {
                        "canonical_code": row.canonical_code,
                        "eligible": row.eligible,
                        "exact_energy_ready": row.exact_energy_ready,
                        "blockers": [block.value for block in row.blockers],
                    }
                    for row in admissions
                ],
                "pantry": [],
                "history": [],
                "fixed_events": [],
                "expected_structural": {
                    "household_members": 3,
                    "local_days": 7,
                    "genuine_cook_recipe_events": 21,
                    "exact_decimal_servings": 42,
                },
            }
            _check_input(proposal, actual_candidates=len(request.candidates))
            logical_bytes = canonical_bytes(proposal)
            (output_dir / "planner-B-PROPOSED.json").write_bytes(logical_bytes)
            (output_dir / "run-bound-uuid-witness-NOT-PIN.json").write_bytes(
                canonical_bytes({
                    "household_id": str(household.id),
                    "selection_ids": selection_witness,
                    "food_uuid_to_code": [
                        {
                            "id": str(food_id),
                            "code": food_catalogue.get(food_id).canonical_code,
                        }
                        for food_id in sorted(
                            {
                                ingredient_id
                                for candidate in request.candidates
                                for ingredient_id in candidate.food_ingredient_ids
                            }
                            | {
                                ingredient_id
                                for member in request.members
                                for ingredient_id in member.excluded_food_ingredient_ids
                            },
                            key=lambda value: value.hex,
                        )
                    ],
                })
            )
        finally:
            engine.dispose()
    results = {
        "status": "PROPOSED_INPUT_ONLY_NOT_INDEPENDENTLY_APPROVED",
        "publication_A_sha256_OBSERVED_NOT_PIN": sha(source_bytes),
        "planner_B_sha256_OBSERVED_NOT_PIN": sha(logical_bytes),
        "source_commit": expected_base,
        "planner_generation_performed": "NO",
    }
    (output_dir / "observed-digests-NOT-APPROVAL.json").write_bytes(
        canonical_bytes(results)
    )
    return results


def validate_externally_pinned_proposals(
    output_dir: Path,
    *,
    expected_a_sha256: str,
    expected_b_sha256: str,
    expected_source_commit: str,
    expected_stage_membership: dict[str, list[str]],
) -> dict[str, object]:
    """Only caller-supplied independent pins count. No internal self-approval.

    Cross-check A/B against source-keyed typed UUIDs and full closed inventory.
    Does not generate, read or choose any Planner week.
    """
    if expected_source_commit != SOURCE_COMMIT:
        raise PreflightNoGo("unaccepted source revision")
    raw_a = (output_dir / "publication-A-PROPOSED.json").read_bytes()
    raw_b = (output_dir / "planner-B-PROPOSED.json").read_bytes()
    if sha(raw_a) != expected_a_sha256 or sha(raw_b) != expected_b_sha256:
        raise PreflightNoGo("external A/B raw SHA mismatch")
    def reject_duplicates(items):
        seen = {}
        for key, value in items:
            if key in seen:
                raise PreflightNoGo("duplicate JSON input key")
            seen[key] = value
        return seen

    def reject_float(_):
        raise PreflightNoGo("floating-point input is prohibited")

    a = json.loads(
        raw_a.decode("utf-8"), object_pairs_hook=reject_duplicates,
        parse_float=reject_float,
    )
    b = json.loads(
        raw_b.decode("utf-8"), object_pairs_hook=reject_duplicates,
        parse_float=reject_float,
    )
    if a["stages"] != expected_stage_membership:
        raise PreflightNoGo("external stage membership mismatch")
    if (
        b.get("schema_version") != INPUT_SCHEMA
        or b.get("publication_manifest_sha256") != expected_a_sha256
        or b.get("source_commit") != expected_source_commit
        or b.get("fixture_id") != FIXTURE_ID
    ):
        raise PreflightNoGo("B is not bound to externally accepted A and source")
    provider = load_pinned_publication_manifest(
        output_dir / "publication-A-PROPOSED.json",
        expected_sha256=expected_a_sha256,
        expected_source_commit=expected_source_commit,
        expected_stage_membership=expected_stage_membership,
        correction_path=dc4.CORRECTIONS_PATH,
        expected_correction_sha256=CORRECTION_SHA256,
        expected_correction_blob_sha1=CORRECTION_GIT_BLOB,
    )
    version_keys = {
        (row["canonical_code"], row["version_number"]): row["version_key"]
        for row in a["publications"]
    }
    current_codes = {
        code for code, version in version_keys if version == 2
    }
    all_codes = {code for code, _ in version_keys}
    if len(all_codes) != 51 or len(current_codes) != 7:
        raise PreflightNoGo("expected 51 active and seven corrected versions")
    if len(b["candidate_inputs"]) != 51:
        raise PreflightNoGo("incomplete source candidate coverage")
    if len({r["canonical_code"] for r in b["candidate_inputs"]}) != 51:
        raise PreflightNoGo("duplicate candidate code")
    if {r["canonical_code"] for r in b["candidate_inputs"]} != all_codes:
        raise PreflightNoGo("source/candidate membership mismatch")
    for row in b["candidate_inputs"]:
        code = row["canonical_code"]
        number = 2 if code in current_codes else 1
        expected_key = version_keys[(code, number)]
        expected_version_id = provider.id_for("RECIPE_VERSION", expected_key)
        if row["recipe_version_id"] != str(expected_version_id):
            raise PreflightNoGo("candidate UUID is not source-keyed")
        if row["source_document_sha256"] != expected_key["source_record_key"][
            "source_document_sha256"
        ]:
            raise PreflightNoGo("candidate source-document drift")
        if row["process_sha256"] != expected_key["publication_process_sha256"]:
            raise PreflightNoGo("candidate RecipeStep content drift")
        if row["rights_review_status"] != "REVIEWED" or not row["rights_basis"]:
            raise PreflightNoGo("unapproved candidate source rights")
    if set(b["planner_config"]) != {
        "version", "compatibility_version", "preference_weight",
        "pantry_weight", "batch_weight", "time_weight", "repetition_weight",
        "max_recipe_repetitions",
    }:
        raise PreflightNoGo("unreviewed planner config")
    if b["planner_config"]["version"] != "planner-v0.5":
        raise PreflightNoGo("planner version drift")
    if b.get("timezone") != "Europe/Moscow":
        raise PreflightNoGo("timezone drift")
    if b.get("week_start") != WEEK_START.isoformat():
        raise PreflightNoGo("week_start drift")
    _check_input(b, actual_candidates=len(b["candidate_inputs"]))
    if [m["ordinal"] for m in b["members"]] != [1, 2, 3]:
        raise PreflightNoGo("member ordinal ordering drift")
    for member in b["members"]:
        ordinal = member["ordinal"]
        expected_profile = _member_profile(ordinal)
        if member["profile"] != expected_profile:
            raise PreflightNoGo("synthetic profile drift")
        profile_sha = sha(canonical_bytes(expected_profile))
        if member["profile_sha256"] != profile_sha:
            raise PreflightNoGo("member profile SHA drift")
        expected_id = provider.id_for("HOUSEHOLD_MEMBER", {
            "household_key": HOUSEHOLD_KEY,
            "ordinal": ordinal,
            "profile_sha256": profile_sha,
        })
        if member["member_id"] != str(expected_id):
            raise PreflightNoGo("member persisted UUID binding drift")
        expected_roles = GATE1_ROLE_SHAPES[2][ordinal - 1]
        shares = {
            MealRole.BREAKFAST: "0.3",
            MealRole.LUNCH: "0.35",
            MealRole.DINNER: "0.25",
        }
        expected_opps = [
            {
                "weekday": weekday,
                "position": pos,
                "role": role.value,
                "energy_share": shares[role],
            }
            for weekday in range(1, 8)
            for pos, role in enumerate(expected_roles, start=1)
        ]
        if member["opportunities"] != expected_opps:
            raise PreflightNoGo("accepted member pattern/share drift")
        if member["excluded_food_codes"] != (
            ["BEEF_CATEGORY_1_RAW"] if ordinal == 3 else []
        ):
            raise PreflightNoGo("member exclusion drift")
    if b.get("expected_structural") != {
        "household_members": 3, "local_days": 7,
        "genuine_cook_recipe_events": 21, "exact_decimal_servings": 42,
    }:
        raise PreflightNoGo("structural contract drift")
    return {
        "status": "VALIDATED_AGAINST_CALLER_PINS_NOT_OWNER_APPROVED",
        "a_sha256": expected_a_sha256,
        "b_sha256": expected_b_sha256,
        "candidate_count": len(b["candidate_inputs"]),
        "member_count": len(b["members"]),
        "no_Planner_generation": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    results = materialize_pre_generation(args.output_dir)
    print(json.dumps(results, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
