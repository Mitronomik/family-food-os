"""Issue #268 review evidence: independent actual-request and persistence projections.

These are test-only readback assertions. Never use this module to influence a
Planner request, choose a favorable output, or authorize nutrition/Prep/release.
The historic V1 semantic_events payload remains byte-semantically unchanged.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from scripts import pr10_ff_pre_generation_inputs as inputs

NO_GO = "NO_GO_FORWARD_FIXTURE_UNSTABLE"


class EvidenceNoGo(ValueError):
    """An actual input, provenance or persistence invariant has failed."""


def _eq(actual, expected, label):
    if actual != expected:
        raise EvidenceNoGo(f"{label} differs from frozen authority")


def _member_profile(member, ordinal):
    return {
        "ordinal": ordinal,
        "name": member.name,
        "active": member.active,
        "birth_date": member.birth_date.isoformat(),
        "sex": member.sex,
        "height_cm": inputs._decimal(member.height_cm),
        "weight_kg": inputs._decimal(member.weight_kg),
        "activity_level": member.activity_level,
        "goal": member.goal,
    }


def project_actual_request(
    request, *, planner, household_state, recipes, food, ordinals, b
):
    """Project the *working* SQLite PlannerRequest before generation, not preflight DB.

    Build every B decision input directly from the real request and current
    repository readbacks, then compare all fields to owner-pinned B. Capture raw
    UUID order separately so run-local identifiers cannot silently masquerade
    as equivalent logical inputs.
    """
    _eq(request.household_id, household_state.household.id, "Household FK")
    _eq(request.week_start.isoformat(), b["week_start"], "calendar start")
    _eq(
        (request.week_start + timedelta(days=6)).isoformat(),
        b["week_end"],
        "calendar end",
    )
    _eq(household_state.household.timezone, b["timezone"], "timezone")
    _eq(household_state.household.city, b["city"], "city")
    config = planner._config
    projected_config = {
        "version": config.version,
        "compatibility_version": config.compatibility_version,
        "preference_weight": inputs._decimal(config.preference_weight),
        "pantry_weight": inputs._decimal(config.pantry_weight),
        "batch_weight": inputs._decimal(config.batch_weight),
        "time_weight": inputs._decimal(config.time_weight),
        "repetition_weight": inputs._decimal(config.repetition_weight),
        "max_recipe_repetitions": config.max_recipe_repetitions,
    }
    _eq(projected_config, b["planner_config"], "actual PlannerConfig")
    _eq(config, inputs.PLANNER_CONFIG, "immutable PlannerConfig source")
    actual_members = {m.id: m for m in household_state.members}
    recipe_by_version = {}
    for row in recipes.list_all():
        if not row.is_active:
            raise EvidenceNoGo("unexpected inactive candidate source")
        detail = recipes.get_current_verified(row.id)
        if detail.version.id in recipe_by_version:
            raise EvidenceNoGo("duplicate RecipeVersion FK")
        recipe_by_version[detail.version.id] = (row, detail)
    candidates = []
    for candidate in request.candidates:
        if candidate.recipe_version_id not in recipe_by_version:
            raise EvidenceNoGo("candidate version outside current catalogue")
        recipe, detail = recipe_by_version[candidate.recipe_version_id]
        version = detail.version
        candidate_ingredients = sorted(
            food.get(identifier).canonical_code
            for identifier in candidate.food_ingredient_ids
        )
        _eq(
            candidate_ingredients,
            sorted(
                food.get(item.food_ingredient_id).canonical_code
                for item in detail.ingredients
            ),
            "candidate ingredient FK",
        )
        candidates.append(
            {
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
                "process_sha256": inputs.process_steps_sha256(
                    [step.instruction for step in detail.steps]
                ),
                "meal_type_code": candidate.meal_type_code.value,
                "kcal_per_base_serving": inputs._decimal(candidate.kcal_per_serving),
                "nutrition_status": candidate.nutrition_status.value,
                "exact_energy_ready": candidate.exact_energy_ready,
                "total_time_minutes": candidate.total_time_minutes,
                "batch_friendly": candidate.batch_friendly,
                "ingredient_codes": candidate_ingredients,
            }
        )
    admissions = [
        {
            "canonical_code": row.canonical_code,
            "eligible": row.eligible,
            "exact_energy_ready": row.exact_energy_ready,
            "blockers": [block.value for block in row.blockers],
        }
        for row in planner.compose_candidate_admission()
    ]
    _eq(candidates, b["candidate_inputs"], "actual candidate order/source/nutrition")
    _eq(admissions, b["candidate_admissions"], "actual admission order")
    if len(candidates) != 51 or len(admissions) != 51:
        raise EvidenceNoGo("incomplete actual candidate/admission inventory")
    members = []
    selection_ids = {}
    if len(request.members) != 3 or len(actual_members) != 3:
        raise EvidenceNoGo("actual Household member coverage")
    for item in request.members:
        ordinal = ordinals[item.member_id]
        member = actual_members[item.member_id]
        profile = _member_profile(member, ordinal)
        selection = item.selection
        if (
            selection.selection.household_id != request.household_id
            or selection.selection.member_id != item.member_id
        ):
            raise EvidenceNoGo("accepted pattern foreign FK")
        selection_ids[ordinal] = selection.selection.id
        opportunities = [
            {
                "weekday": opp.weekday,
                "position": opp.position,
                "role": opp.role.value,
                "energy_share": inputs._decimal(opp.energy_share),
            }
            for opp in sorted(
                selection.opportunities, key=lambda o: (o.weekday, o.position)
            )
        ]
        members.append(
            {
                "ordinal": ordinal,
                "profile": profile,
                "profile_sha256": inputs.sha(inputs.canonical_bytes(profile)),
                "member_id": str(item.member_id),
                "reference_energy_kcal": inputs._decimal(item.reference_energy_kcal),
                "selection_source_kind": selection.selection.source_kind.value,
                "selection_version_number": selection.selection.version_number,
                "opportunities": opportunities,
                "excluded_food_codes": sorted(
                    food.get(fid).canonical_code
                    for fid in item.excluded_food_ingredient_ids
                ),
                "preferred_recipe_version_ids": sorted(
                    str(rid) for rid in item.preferred_recipe_version_ids
                ),
            }
        )
    members.sort(key=lambda m: m["ordinal"])
    _eq(members, b["members"], "actual member/profile/pattern/energy/exclusions")
    if (
        request.pantry_food_ingredient_ids
        or request.recent_plan_ids
        or request.recent_recipe_version_ids
        or request.fixed_events
    ):
        raise EvidenceNoGo("unexpected actual Pantry/history/fixed event")
    _eq(b["pantry"], [], "frozen Pantry")
    _eq(b["history"], [], "frozen history")
    _eq(b["fixed_events"], [], "frozen fixed events")

    normalized = {
        "household_key": inputs.HOUSEHOLD_KEY,
        "week_start": request.week_start.isoformat(),
        "week_end": (request.week_start + timedelta(days=6)).isoformat(),
        "timezone": household_state.household.timezone,
        "city": household_state.household.city,
        "planner_config": projected_config,
        "members": members,
        "candidate_inputs": candidates,
        "candidate_admissions": admissions,
        "pantry": [],
        "history": [],
        "fixed_events": [],
    }
    # Record the exact UUID tie order that the actual planner sees. Version and
    # Member IDs must stay stable; Food and Selection IDs are run-local.
    uuid_order = {
        "candidate_input_uuid_order": [
            str(c.recipe_version_id) for c in request.candidates
        ],
        "candidate_tie_uuid_order": [
            str(c.recipe_version_id)
            for c in sorted(request.candidates, key=lambda c: c.recipe_version_id.hex)
        ],
        "candidate_tie_code_order": [
            recipe_by_version[c.recipe_version_id][0].canonical_code
            for c in sorted(request.candidates, key=lambda c: c.recipe_version_id.hex)
        ],
        "member_request_uuid_order": [str(m.member_id) for m in request.members],
        "member_request_ordinal_order": [
            ordinals[m.member_id] for m in request.members
        ],
        "selection_id_by_member_ordinal": {
            str(k): str(v) for k, v in sorted(selection_ids.items())
        },
        "food_ingredient_id_to_code": [
            {"id": str(fid), "code": food.get(fid).canonical_code}
            for fid in sorted(
                {fid for c in request.candidates for fid in c.food_ingredient_ids}
                | {
                    fid
                    for m in request.members
                    for fid in m.excluded_food_ingredient_ids
                }
                | set(request.pantry_food_ingredient_ids),
                key=lambda item: item.hex,
            )
        ],
    }
    return normalized, uuid_order


def assert_week_and_provenance(
    detail, *, generated, recipes, food, ordinals, b, expected_semantics
):
    """Validate every real persisted FK, participation, exclusion and source step.

    A second versioned witness adds metadata *without changing* V1 semantic_events
    or its historical SHA256. Return (source_rows, raw_fk_rows).
    """
    plan = detail.plan
    events = sorted(detail.events, key=lambda e: (e.local_date, e.position))
    serving_by_event = defaultdict(list)
    seen_serving_ids = set()
    seen_pairs = set()
    for s in detail.servings:
        if s.id in seen_serving_ids or (s.event_id, s.member_id) in seen_pairs:
            raise EvidenceNoGo("duplicate real Serving ID or event/member FK")
        seen_serving_ids.add(s.id)
        seen_pairs.add((s.event_id, s.member_id))
        serving_by_event[s.event_id].append(s)
    if (
        len(events) != 21
        or len(detail.servings) != 42
        or len({e.id for e in events}) != 21
        or len(detail.member_selections) != 3
    ):
        raise EvidenceNoGo("real 3/21/42 identity coverage")
    if (
        len({s.member_id for s in detail.member_selections}) != 3
        or {s.member_id for s in detail.member_selections} != set(ordinals)
        or any(s.plan_id != plan.id for s in detail.member_selections)
    ):
        raise EvidenceNoGo("real plan selection FK coverage")
    if any(s.event_id not in {e.id for e in events} for s in detail.servings):
        raise EvidenceNoGo("orphan Serving event FK")
    by_code = {c["canonical_code"]: c for c in b["candidate_inputs"]}
    current = {}
    for recipe in recipes.list_all():
        rd = recipes.get_current_verified(recipe.id)
        current[rd.version.id] = (recipe, rd)
    source_rows = []
    fk_rows = []
    expected_roles = {
        1: ("BREAKFAST", (1, 2)),
        2: ("LUNCH", (1,)),
        3: ("DINNER", (1, 2, 3)),
    }
    for event in events:
        if event.plan_id != plan.id or event.recipe_version_id not in current:
            raise EvidenceNoGo("event plan or RecipeVersion FK mismatch")
        if (
            event.source_kind.value != "COOK_RECIPE"
            or event.source_reference is not None
        ):
            raise EvidenceNoGo("unapproved event source kind/reference")
        if event.position not in expected_roles:
            raise EvidenceNoGo("unapproved event position")
        role, participants = expected_roles[event.position]
        if event.role.value != role:
            raise EvidenceNoGo("event role/position mismatch")
        if event.local_date < plan.week_start or event.local_date > (
            plan.week_start + timedelta(days=6)
        ):
            raise EvidenceNoGo("event outside seven local days")
        rows = serving_by_event[event.id]
        ordinals_here = tuple(sorted(ordinals[s.member_id] for s in rows))
        if ordinals_here != participants:
            raise EvidenceNoGo("event participation deviates from accepted 3/2/1 roles")
        recipe, rd = current[event.recipe_version_id]
        version = rd.version
        expected = by_code[recipe.canonical_code]
        actual = {
            "canonical_code": recipe.canonical_code,
            "recipe_version_id": str(version.id),
            "source_name": version.source_name,
            "source_recipe_id": version.source_recipe_id,
            "source_version": version.source_version,
            "source_document_sha256": version.source_document_sha256,
            "version_number": version.version_number,
            "process_sha256": inputs.process_steps_sha256(
                [step.instruction for step in rd.steps]
            ),
            "rights_review_status": version.rights_review_status.value,
            "verification_status": version.verification_status.value,
            "rights_basis": version.rights_basis,
            "ingredient_codes": sorted(
                food.get(i.food_ingredient_id).canonical_code for i in rd.ingredients
            ),
        }
        for k, value in actual.items():
            if expected[k] != value:
                raise EvidenceNoGo(f"selected source/version/Step/rights mismatch: {k}")
        exclusions = {
            i: set(member["excluded_food_codes"])
            for i, member in ((m["ordinal"], m) for m in b["members"])
        }
        for ordinal in ordinals_here:
            if exclusions[ordinal].intersection(actual["ingredient_codes"]):
                raise EvidenceNoGo("selected recipe violates individual exclusion")
        source_rows.append(
            {
                "date": event.local_date.isoformat(),
                "position": event.position,
                "role": event.role.value,
                "participant_ordinals": list(ordinals_here),
                **actual,
            }
        )
        fk_rows.append(
            {
                "event_id": str(event.id),
                "plan_id": str(event.plan_id),
                "recipe_version_id": str(event.recipe_version_id),
                "date": event.local_date.isoformat(),
                "position": event.position,
                "serving_rows": sorted(
                    [
                        {
                            "serving_id": str(s.id),
                            "event_id": str(s.event_id),
                            "member_id": str(s.member_id),
    if len({(r["date"], r["position"]) for r in source_rows}) != 21:
        raise EvidenceNoGo("duplicate date/position")
    if {r["date"] for r in source_rows} != {
        (plan.week_start + timedelta(days=i)).isoformat() for i in range(7)
    }:
        raise EvidenceNoGo("week date coverage incomplete")
    if [len(r["servings"]) for r in expected_semantics] != [
        len(row["serving_rows"]) for row in fk_rows
    ]:
        raise EvidenceNoGo("V1 semantic and FK Serving coverage diverged")
    # Check real authoritative Planner output rather than treating a persisted
    # semantic digest as proof by itself; no output-derived input is constructed.
    expected_generated = sorted(
        generated.events, key=lambda e: (e.local_date, e.position)
    )
    if len(expected_generated) != len(source_rows):
        raise EvidenceNoGo("generated and persisted event cardinality differs")
    for actual, planned, sem in zip(
        source_rows, expected_generated, expected_semantics
    ):
        if (
            actual["date"] != planned.local_date.isoformat()
            or actual["position"] != planned.position
            or actual["role"] != planned.role.value
            or actual["recipe_version_id"] != str(planned.recipe_version_id)
            or actual["participant_ordinals"]
            != sorted(ordinals[mid] for mid in planned.participant_member_ids)
            or sem["recipe"]["code"] != actual["canonical_code"]
        ):
            raise EvidenceNoGo(
                "true Planner events differ from persisted/source witness"
            )
        planned_portions = {
            ordinals[mid]: format(value, ".6f") for mid, value in planned.portions
        }
        actual_portions = {
            s["ordinal"]: s["portion"]
            for s in next(
                x
                for x in fk_rows
                if x["date"] == actual["date"] and x["position"] == actual["position"]
            )["serving_rows"]
        }
        if planned_portions != actual_portions:
            raise EvidenceNoGo("Planner allocation differs from persisted Serving")
    return source_rows, fk_rows


def compare_evidence(first, second, *, pin):
    """Fail closed, with no cross-run UUID equivalence assumption or reroll."""
    for name, receipt in (("first", first), ("second", second)):
        if receipt.get("schema") != "PR10_FF_TWO_PROCESS_PROOF_RECEIPT_V1":
            raise EvidenceNoGo(f"{name} invalid receipt schema")
        if receipt.get("input_sha256") != {
            "A": pin["raw_artifacts"]["publication_a"]["raw_sha256"],
            "B": pin["raw_artifacts"]["planner_b"]["raw_sha256"],
        }:
            raise EvidenceNoGo(f"{name} input SHA changed")
        for field, sha_key in (
            ("semantic_events", "semantic_sha256"),
            ("actual_request_normalized_v2", "request_normalized_sha256_v2"),
            ("provenance_semantic_v2", "provenance_sha256_v2"),
        ):
            if inputs.sha(inputs.canonical_bytes(receipt[field])) != receipt[sha_key]:
                raise EvidenceNoGo(f"{name} self-inconsistent {field}")
        if (
            len(receipt["semantic_events"]) != 21
            or len(receipt["provenance_semantic_v2"]) != 21
            or not receipt.get("input_parity_with_B")
        ):
            raise EvidenceNoGo(f"{name} invalid coverage/input parity")
    for field in (
        "semantic_events",
        "actual_request_normalized_v2",
        "provenance_semantic_v2",
    ):
        if first[field] != second[field]:
            raise EvidenceNoGo(f"first cross-process divergence: {field}")
    for key in (
        "candidate_input_uuid_order",
        "candidate_tie_uuid_order",
        "candidate_tie_code_order",
        "member_request_uuid_order",
        "member_request_ordinal_order",
    ):
        if first["uuid_order_witness_v2"][key] != second["uuid_order_witness_v2"][key]:
            raise EvidenceNoGo(f"first cross-process UUID ordering divergence: {key}")
    # Food/Selection UUIDs are expected to differ, but their *logical bindings*
    # must be identical and their identities must not affect current selections.
    for receipt in (first, second):
        witness = receipt["uuid_order_witness_v2"]
        if len(set(witness["selection_id_by_member_ordinal"].values())) != 3:
            raise EvidenceNoGo("duplicate run-local selection ID")
        food = witness["food_ingredient_id_to_code"]
        if len({row["id"] for row in food}) != len(food):
            raise EvidenceNoGo("duplicate run-local FoodIngredient ID")
        if len({row["code"] for row in food}) != len(food):
            raise EvidenceNoGo("non-bijective FoodIngredient mapping")
    if sorted(
        x["code"] for x in first["uuid_order_witness_v2"]["food_ingredient_id_to_code"]
    ) != sorted(
        x["code"] for x in second["uuid_order_witness_v2"]["food_ingredient_id_to_code"]
    ):
        raise EvidenceNoGo("run-local FoodIngredient logical membership mismatch")
    return {
        "semantic_sha256": first["semantic_sha256"],
        "request_normalized_sha256_v2": first["request_normalized_sha256_v2"],
        "provenance_sha256_v2": first["provenance_sha256_v2"],
        "raw_planner_fingerprint_parity": (
            first["planner_request_fingerprint"]
            == second["planner_request_fingerprint"]
            and first["planner_trace_fingerprint"]
            == second["planner_trace_fingerprint"]
        ),
        "run_local_uuid_difference_categories": [
            key
            for key in ("selection_id_by_member_ordinal", "food_ingredient_id_to_code")
            if first["uuid_order_witness_v2"][key]
            != second["uuid_order_witness_v2"][key]
        ],
    }
