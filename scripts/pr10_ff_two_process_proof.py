"""Issue #268: fail-closed, two-process technical Planner witness.

NOT a Prep, Gate2, nutrition-completeness or release authority.
Run with PYTHONPATH=backend:. python scripts/pr10_ff_two_process_proof.py --output-dir /tmp/proof
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from scripts import pr10_ff_mobile_preview as mobile_preview
from scripts import pr10_ff_one_lunch_courses as one_lunch
from scripts import pr10_ff_one_soup_case as one_soup
from scripts import pr10_ff_portion_reality as portion_reality
from scripts import pr10_ff_pre_generation_inputs as inputs
from scripts import pr10_ff_proof_evidence as evidence
from scripts import pr10_ff_week_preview as week_preview

ROOT = Path(__file__).resolve().parents[1]
PIN_PATH = ROOT / "docs/family-food/evidence/pr10-ff-forward-input-v1-pins.json"
INPUT_DIR = PIN_PATH.parent / "pr10-ff-forward-input-v1"


class ProofNoGo(ValueError):
    """An immutable input or generated semantic invariant was violated."""


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def checked_inputs() -> tuple[dict, dict, dict]:
    pin = json.loads(PIN_PATH.read_bytes())
    if pin["schema_version"] != "PR10_FF_FROZEN_INPUT_PIN_V1":
        raise ProofNoGo("Unsupported external input pin schema")
    observed = {}
    for key in ("publication_a", "planner_b"):
        entry = pin["raw_artifacts"][key]
        path = ROOT / entry["repository_path"]
        if not path.is_file() or path.parent != INPUT_DIR:
            raise ProofNoGo("Missing or foreign frozen input path")
        raw = path.read_bytes()
        git_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()
        if (
            len(raw) != entry["byte_count"]
            or digest(raw) != entry["raw_sha256"]
            or git_blob != entry["git_blob_sha1"]
        ):
            raise ProofNoGo(f"Frozen input drift: {key}")
        observed[key] = json.loads(raw)
    if (
        pin["source_commit"] != inputs.SOURCE_COMMIT
        or pin["raw_artifacts"]["publication_a"]["raw_sha256"]
        != observed["planner_b"]["publication_manifest_sha256"]
    ):
        raise ProofNoGo("Frozen input cross-reference drift")
    return pin, observed["publication_a"], observed["planner_b"]


def portion(value: Decimal) -> str:
    if not isinstance(value, Decimal) or not value.is_finite() or value <= 0:
        raise ProofNoGo("Nonpositive or nonfinite persisted Decimal Serving")
    if value != value.quantize(Decimal("0.000001")):
        raise ProofNoGo("Serving exceeds six-place Decimal precision")
    return format(value, ".6f")


def canonical_persisted(detail, recipes, member_ids: dict) -> list[dict]:
    source_codes = {}
    for recipe in recipes.list_all():
        current = recipes.get_current_verified(recipe.id)
        source_codes[current.version.id] = {
            "code": recipe.canonical_code,
            "version": current.version.version_number,
            "source_recipe_id": current.version.source_recipe_id,
            "source_document_sha256": current.version.source_document_sha256,
        }
    served = {}
    for item in detail.servings:
        served.setdefault(item.event_id, []).append(
            {
                "member_ordinal": member_ids[item.member_id],
                "portion_servings": portion(item.portion_servings),
            }
        )
    result = []
    for event in detail.events:
        if event.recipe_version_id not in source_codes:
            raise ProofNoGo("Selected RecipeVersion outside source authority")
        result.append(
            {
                "date": event.local_date.isoformat(),
                "position": event.position,
                "role": event.role.value,
                "source_kind": event.source_kind.value,
                "recipe": source_codes[event.recipe_version_id],
                "servings": sorted(
                    served.get(event.id, []), key=lambda r: r["member_ordinal"]
                ),
            }
        )
    return sorted(result, key=lambda r: (r["date"], r["position"]))


def witness(output: Path) -> dict:
    from app.db.config import DatabaseConfig
    from app.domain.planner import PlannerSuccess
    from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
    from app.persistence.sqlalchemy_core.food_ingredient_composition import (
        create_food_catalogue_service,
    )
    from app.services.planner import AuthoritativeGenerationRequest

    from scripts.audit_dc4_corpus_readiness_rerun import (
        GATE1_ROLE_SHAPES,
        _accept_custom_pattern,
        _fixture_exclusions,
        _services,
    )

    pin, source_a, planner_b = checked_inputs()
    # Preflight is independent of output. Regenerate from currently pinned source and
    # validate all source/rights/energy/PlannerConfig/candidate/admission fields.
    with tempfile.TemporaryDirectory(prefix="pr10_ff_preflight_") as temp:
        regenerated_dir = Path(temp) / "proposals"
        inputs.materialize_pre_generation(regenerated_dir)
        if any(
            (regenerated_dir / filename).read_bytes()
            != (INPUT_DIR / filename).read_bytes()
            for filename in ("publication-A-PROPOSED.json", "planner-B-PROPOSED.json")
        ):
            raise ProofNoGo("Fresh input preflight differs from frozen raw A/B")
        inputs.validate_externally_pinned_proposals(
            regenerated_dir,
            expected_a_sha256=pin["raw_artifacts"]["publication_a"]["raw_sha256"],
            expected_b_sha256=pin["raw_artifacts"]["planner_b"]["raw_sha256"],
            expected_source_commit=pin["source_commit"],
            expected_stage_membership=source_a["stages"],
        )
    if planner_b["expected_structural"] != {
        "household_members": 3,
        "local_days": 7,
        "genuine_cook_recipe_events": 21,
        "exact_decimal_servings": 42,
    } or any(
        row["nutrition_status"] != "INCOMPLETE" for row in planner_b["candidate_inputs"]
    ):
        raise ProofNoGo("Input scope or energy-only restriction changed")

    provider = inputs.load_pinned_publication_manifest(
        INPUT_DIR / "publication-A-PROPOSED.json",
        expected_sha256=pin["raw_artifacts"]["publication_a"]["raw_sha256"],
        expected_source_commit=pin["source_commit"],
        expected_stage_membership=source_a["stages"],
        correction_path=inputs.dc4.CORRECTIONS_PATH,
        expected_correction_sha256=inputs.CORRECTION_SHA256,
        expected_correction_blob_sha1=inputs.CORRECTION_GIT_BLOB,
    )
    with tempfile.TemporaryDirectory(prefix="pr10_ff_planner_db_") as temp:
        db = DatabaseConfig(path=Path(temp) / "fresh.sqlite")
        inputs.dc4.seed_dc4_a3_russian_step_corrections(db, id_provider=provider)
        engine = create_sqlite_engine(db)
        try:
            planner, meal_plans, _, recipes, _ = _services(engine)
            food = create_food_catalogue_service(engine)
            key = {"household_key": inputs.HOUSEHOLD_KEY}
            households = inputs._household_service(
                engine, lambda: provider.id_for("HOUSEHOLD", key)
            )
            household = households.create_household(
                name="PR10-FF проверочная семья",
                timezone_name="Europe/Moscow",
                city="Санкт-Петербург",
            )
            members = []
            member_ordinals = {}
            for ordinal, roles in enumerate(GATE1_ROLE_SHAPES[2], start=1):
                profile = inputs._member_profile(ordinal)
                member_key = {
                    "household_key": inputs.HOUSEHOLD_KEY,
                    "ordinal": ordinal,
                    "profile_sha256": inputs.sha(inputs.canonical_bytes(profile)),
                }
                one_operation = inputs._household_service(
                    engine, lambda k=member_key: provider.id_for("HOUSEHOLD_MEMBER", k)
                )
                member = one_operation.add_household_member(
                    household.id,
                    name=profile["name"],
                    birth_date=date.fromisoformat(profile["birth_date"]),
                    sex=profile["sex"],
                    height_cm=Decimal(profile["height_cm"]),
                    weight_kg=Decimal(profile["weight_kg"]),
                    activity_level=profile["activity_level"],
                    goal=profile["goal"],
                )
                _accept_custom_pattern(meal_plans, household.id, member.id, roles)
                members.append(member)
                member_ordinals[member.id] = ordinal
            command = AuthoritativeGenerationRequest(
                household.id, inputs.WEEK_START, _fixture_exclusions(3, members, food)
            )
            # Assert full *working* request/B parity BEFORE real generation.
            # The preflight materializer uses a different SQLite instance.
            actual_request = planner.compose_authoritative_request(command)
            normalized_input, uuid_order = evidence.project_actual_request(
                actual_request,
                planner=planner,
                household_state=households.get_household(household.id),
                recipes=recipes,
                food=food,
                ordinals=member_ordinals,
                b=planner_b,
            )
            # Only generate after independently proving the working request.
            generated, persisted = planner.generate_authoritative(command)
            if not isinstance(generated, PlannerSuccess) or persisted is None:
                raise ProofNoGo("Real Planner did not generate a persisted success")
            readback = meal_plans.get_current_plan(household.id, inputs.WEEK_START)
            if readback != persisted:
                raise ProofNoGo("Persisted readback differs from authoritative service")
            events = canonical_persisted(readback, recipes, member_ordinals)
            if (
                len(events) != 21
                or {row["date"] for row in events}
                != {
                    (inputs.WEEK_START + timedelta(days=d)).isoformat()
                    for d in range(7)
                }
                or len({(row["date"], row["position"]) for row in events}) != 21
                or sum(len(row["servings"]) for row in events) != 42
                or any(row["source_kind"] != "COOK_RECIPE" for row in events)
            ):
                raise ProofNoGo("Real Planner 3/7/21/42 structural condition failed")
            provenance_rows, fk_rows = evidence.assert_week_and_provenance(
                readback,
                generated=generated,
                recipes=recipes,
                food=food,
                ordinals=member_ordinals,
                b=planner_b,
                expected_semantics=events,
            )
            # Separate user-readable projection of the *same* persisted plan.
            # This does not mutate the frozen V1 semantic event digest or approve
            # any source RecipeStep or real-family use.
            product_preview = week_preview.project_week(
                engine=engine,
                plan=readback,
                semantic_events=events,
                candidate_inputs=planner_b["candidate_inputs"],
                timezone=household.timezone,
            )
            # Read-only source audit of real persisted Servings: do not infer
            # physical mass, a member bound, or consumer portion readiness.
            selected_details = {}
            for source_recipe in recipes.list_all():
                detail = recipes.get_current_verified(source_recipe.id)
                selected_details[detail.version.id] = detail
            portion_audit = portion_reality.inspect(
                plan=readback,
                semantic_events=events,
                details=selected_details,
                candidate_inputs=planner_b["candidate_inputs"],
                member_ordinals=member_ordinals,
            )
            if (
                portion_audit["meal_events"] != 21
                or portion_audit["individual_servings"] != 42
                or portion_audit["physically_reviewed_servings"] != 0
            ):
                raise ProofNoGo(
                    "Portion audit may not promote fixture to physical PASS"
                )
            # ONE concrete source/portion case, using the accepted R3-D source
            # archive and actual persisted MealPlan/Serving evidence above.
            # No physical-PASS or MealPlan rewrite follows from this comparison.
            one_soup_versions = [
                detail
                for detail in selected_details.values()
                if detail.recipe.canonical_code == one_soup.RECIPE_CODE
            ]
            if len(one_soup_versions) != 1:
                raise ProofNoGo("Missing exact one-soup RecipeVersion identity")
            source_frozen, _, _ = inputs.r3d._load_contract()
            # Bind actual persisted RecipeIngredient.food_ingredient_id UUIDs
            # to current canonical FoodIngredient readback from this same DB.
            # Do not re-create identities from the R3-D seed or source card.
            soup_foods = {
                row.food_ingredient_id: food.get(row.food_ingredient_id)
                for row in one_soup_versions[0].ingredients
            }
            soup_receipt = one_soup.check_one_soup(
                portion_audit=portion_audit,
                source_frozen=source_frozen,
                recipe_detail=one_soup_versions[0],
                foods_by_id=soup_foods,
            )
            # One user-approved, developer-only three-course home lunch.
            # Home attendance comes from frozen accepted member selections:
            # only member 1 opted for LUNCH on 2026-11-03; members 2/3 do
            # NOT receive invented outside-food events, quantities or energy.
            lunch_foods = {}
            for _, code, _ in one_lunch.COURSES:
                selected = [
                    detail
                    for detail in selected_details.values()
                    if detail.recipe.canonical_code == code
                ]
                if len(selected) != 1:
                    raise ProofNoGo("Missing immutable source for lunch course")
                for ingredient in selected[0].ingredients:
                    fid = ingredient.food_ingredient_id
                    if fid not in lunch_foods:
                        lunch_foods[fid] = food.get(fid)
            lunch_proposal = one_lunch.build_lunch(
                plan=readback,
                member_ordinals=member_ordinals,
                members=planner_b["members"],
                candidate_inputs=planner_b["candidate_inputs"],
                details=selected_details,
                foods=lunch_foods,
            )
            result = {
                "schema": "PR10_FF_TWO_PROCESS_PROOF_RECEIPT_V1",
                "status": "TECHNICAL_ENERGY_ONLY_NOT_RELEASE",
                "input_sha256": {
                    "A": pin["raw_artifacts"]["publication_a"]["raw_sha256"],
                    "B": pin["raw_artifacts"]["planner_b"]["raw_sha256"],
                },
                "planner_trace_fingerprint": generated.trace.fingerprint,
                "planner_request_fingerprint": generated.trace.request_fingerprint,
                "semantic_events": events,
                "semantic_sha256": digest(inputs.canonical_bytes(events)),
                "product_preview_v1": product_preview,
                "product_preview_sha256": digest(
                    inputs.canonical_bytes(product_preview)
                ),
                "portion_audit_v1": portion_audit,
                "portion_audit_sha256": digest(inputs.canonical_bytes(portion_audit)),
                "one_soup_source_case_v1": soup_receipt,
                "one_soup_source_case_sha256": digest(
                    inputs.canonical_bytes(soup_receipt)
                ),
                "one_home_lunch_three_courses_v1": lunch_proposal,
                "one_home_lunch_three_courses_sha256": digest(
                    inputs.canonical_bytes(lunch_proposal)
                ),
                # V2 supplemental witness: original V1 semantic digest is unchanged.
                "input_parity_with_B": True,
                "actual_request_normalized_v2": normalized_input,
                "request_normalized_sha256_v2": digest(
                    inputs.canonical_bytes(normalized_input)
                ),
                "uuid_order_witness_v2": uuid_order,
                "provenance_semantic_v2": provenance_rows,
                "provenance_sha256_v2": digest(inputs.canonical_bytes(provenance_rows)),
                "persisted_fk_witness_v2": {
                    "plan_id": str(readback.plan.id),
                    "household_id": str(readback.plan.household_id),
                    "member_selection_rows": [
                        {
                            "plan_id": str(item.plan_id),
                            "member_id": str(item.member_id),
                            "selection_id": str(item.selection_id),
                            "ordinal": member_ordinals[item.member_id],
                        }
                        for item in readback.member_selections
                    ],
                    "event_rows": fk_rows,
                },
                "gate": "NO_GO_TO_PR10_CORE_RUNTIME",
            }
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(inputs.canonical_bytes(result))
            return result
        finally:
            engine.dispose()


def compare(output_dir: Path) -> int:
    """One attempt per process, always leave a structured NO_GO on failures."""
    pin, _, _ = checked_inputs()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ProofNoGo("Output directory must be empty; no favorable reroll")
    output_dir.mkdir(parents=True, exist_ok=True)
    decision = {
        "status": "NO_GO_FORWARD_FIXTURE_UNSTABLE",
        "two_independent_processes": False,
        "PR10_FF_FIXTURE_REPRODUCIBLE": "NOT_PROVEN",
        "NO_GO_TO_PR10_CORE_RUNTIME": True,
        "APPROVED_IMMEDIATE": 0,
        "SAFE_BATCH_READY": False,
        "PORTION_RELEASE_READY": "NOT_PROVEN",
        "input_pin_schema": pin["schema_version"],
    }
    exit_code = 1
    try:
        for index in (1, 2):
            # Never retry or cherry-pick a favorable independent run.
            subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--output",
                    str(output_dir / f"process-{index}.json"),
                ],
                check=True,
                cwd=ROOT,
                env={
                    **os.environ,
                    "PYTHONPATH": str(ROOT / "backend") + os.pathsep + str(ROOT),
                },
            )
        first = json.loads((output_dir / "process-1.json").read_bytes())
        second = json.loads((output_dir / "process-2.json").read_bytes())
        findings = evidence.compare_evidence(first, second, pin=pin)
        previews = (first.get("product_preview_v1"), second.get("product_preview_v1"))
        for receipt, preview in ((first, previews[0]), (second, previews[1])):
            if preview is None or receipt.get("product_preview_sha256") != digest(
                inputs.canonical_bytes(preview)
            ):
                raise ProofNoGo("Missing or inconsistent product preview witness")
        if previews[0] != previews[1]:
            raise ProofNoGo("Cross-process product menu/shopping preview diverged")
        audits = (first.get("portion_audit_v1"), second.get("portion_audit_v1"))
        for receipt, audit in ((first, audits[0]), (second, audits[1])):
            if audit is None or receipt.get("portion_audit_sha256") != digest(
                inputs.canonical_bytes(audit)
            ):
                raise ProofNoGo("Missing or inconsistent source-based portion audit")
            if (
                audit.get("meal_events") != 21
                or audit.get("individual_servings") != 42
                or audit.get("physically_reviewed_servings") != 0
            ):
                raise ProofNoGo("Portion audit cannot imply physical eligibility")
        if audits[0] != audits[1]:
            raise ProofNoGo("Two independent source-based portion audits differ")
        (output_dir / "portion-review.json").write_bytes(
            inputs.canonical_bytes(audits[0])
        )
        (output_dir / "portion-review.md").write_text(
            portion_reality.render_markdown(audits[0]), encoding="utf-8"
        )
        cases = (
            first.get("one_soup_source_case_v1"),
            second.get("one_soup_source_case_v1"),
        )
        for receipt, source_case in ((first, cases[0]), (second, cases[1])):
            if source_case is None or receipt.get(
                "one_soup_source_case_sha256"
            ) != digest(inputs.canonical_bytes(source_case)):
                raise ProofNoGo("Missing or corrupt one-soup source evidence")
            if (
                source_case.get("decision") != one_soup.NO_GO
                or source_case.get("physical_portion_approval") != "NOT_PROVEN"
            ):
                raise ProofNoGo("One soup has no positive physical portion authority")
        if cases[0] != cases[1]:
            raise ProofNoGo("One-soup source evidence differs between processes")
        (output_dir / "soup-case.json").write_bytes(inputs.canonical_bytes(cases[0]))
        (output_dir / "soup-case.md").write_text(
            one_soup.render_case(cases[0]), encoding="utf-8"
        )
        lunches = (
            first.get("one_home_lunch_three_courses_v1"),
            second.get("one_home_lunch_three_courses_v1"),
        )
        for receipt, lunch in ((first, lunches[0]), (second, lunches[1])):
            if lunch is None or receipt.get(
                "one_home_lunch_three_courses_sha256"
            ) != digest(inputs.canonical_bytes(lunch)):
                raise ProofNoGo("Missing, inconsistent 3-course home lunch witness")
            if (
                lunch.get("status") != "STRUCTURALLY_COMPOSED_DIAGNOSTIC_ONLY"
                or lunch.get("home_participant_ordinals") != [1]
                or lunch.get("non_lunch_member_ordinals") != [2, 3]
                or lunch.get("physical_serving_approval") != "NOT_PROVEN"
                or lunch.get("shopping_authority") != "NONE"
                or lunch.get("authoritative_mealplan") is not False
            ):
                raise ProofNoGo("One-home-lunch release boundary changed")
        if lunches[0] != lunches[1]:
            raise ProofNoGo("Home-lunch composition differs across two processes")
        (output_dir / "lunch-three-courses.json").write_bytes(
            inputs.canonical_bytes(lunches[0])
        )
        (output_dir / "lunch-three-courses.md").write_text(
            one_lunch.render_markdown(lunches[0]), encoding="utf-8"
        )
        markdown = week_preview.render_markdown(previews[0])
        (output_dir / "week-preview.md").write_text(markdown, encoding="utf-8")
        mobile_html = mobile_preview.render_html(previews[0])
        (output_dir / "week-preview.html").write_text(mobile_html, encoding="utf-8")
        decision.update(findings)
        decision["two_independent_processes"] = True
        decision["status"] = "MATCH_PENDING_INDEPENDENT_REVIEW"
        exit_code = 0
    except (
        subprocess.CalledProcessError,
        evidence.EvidenceNoGo,
        ValueError,
        OSError,
        KeyError,
        TypeError,
    ) as exc:
        # Preserve first failure and partial raw receipts rather than rerunning.
        decision["failure_class"] = type(exc).__name__
        decision["first_failure"] = str(exc)
        decision["worker_receipts_present"] = [
            (output_dir / f"process-{index}.json").exists() for index in (1, 2)
        ]
    (output_dir / "comparison.json").write_bytes(inputs.canonical_bytes(decision))
    print(json.dumps(decision, sort_keys=True))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        if args.worker:
            if args.output is None:
                parser.error("--worker requires --output")
            witness(args.output)
            return 0
        if args.output_dir is None:
            parser.error("--output-dir is required")
        return compare(args.output_dir)
    except (
        ProofNoGo,
        inputs.PreflightNoGo,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"NO_GO_FORWARD_FIXTURE_UNSTABLE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
