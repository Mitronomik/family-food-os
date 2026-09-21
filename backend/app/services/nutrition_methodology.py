"""Explicit Russian-method read path over pinned existing composition/profile IDs.

Does not select a current profile, import external observations, or reinterpret
an old registry snapshot. No fallback from total to available carbohydrate.
"""

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID
import json

from app.domain.food_composition import (
    CompositionKind,
    CompositionUnavailableError,
    MassState,
    snapshot_digest,
)
from app.domain.nutrient_method_adapters import (
    NutrientMethodAdapterError,
    canonical_code_for_kind,
    resolve_method,
    supported_registry,
)
from app.domain.nutrition_methodology import (
    NutrientKind,
    ObservationMethod,
    ObservationState,
    ObservationSource,
    SourceObservation,
    ObservationContribution,
    MethodologyTotal,
    RussianNutritionPolicy,
    aggregate_observations,
)
from app.services.food_composition_contracts import CompositionReadScope

@dataclass(frozen=True)
class AtomicMethodologyResult:
    composition_version_id: UUID
    nutrition_profile_id: UUID
    food_ingredient_id: UUID
    registry_version: str
    mass_state: MassState
    policy: RussianNutritionPolicy
    values: tuple[MethodologyTotal, ...]
    receipt_sha256: str
    source_observations_json: str


class NutritionMethodologyService:
    def __init__(self, scope_factory: Callable[[], CompositionReadScope]):
        self._scope = scope_factory

    def atomic_input(
        self,
        composition_version_id: UUID,
        *,
        mass_g: Decimal,
        mass_state: MassState,
        nutrients: tuple[NutrientKind, ...],
        policy: RussianNutritionPolicy,
    ) -> AtomicMethodologyResult:
        if not isinstance(policy, RussianNutritionPolicy):
            raise TypeError("Нужна явно выбранная версия методики.")
        if not isinstance(mass_state, MassState):
            raise TypeError("Нужно явное состояние массы.")
        if not nutrients or any(not isinstance(n, NutrientKind) for n in nutrients):
            raise ValueError("Нужен поддерживаемый перечень показателей.")
        if len(set(nutrients)) != len(nutrients):
            raise ValueError("Показатель повторяется.")
        with self._scope() as scope:
            composition = scope.compositions.get(composition_version_id)
            if (
                composition.id != composition_version_id
                or composition.kind != CompositionKind.ATOMIC
                or composition.steps
            ):
                raise CompositionUnavailableError(
                    "METHOD_REQUIRES_UNTRANSFORMED_ATOMIC_INPUT"
                )
            if mass_state != composition.input_state or mass_state in {
                MassState.GROSS_PURCHASE,
                MassState.DISCARD,
            }:
                raise CompositionUnavailableError("METHOD_INPUT_MASS_STATE_MISMATCH")
            vector = scope.nutrient_vectors.get(composition.profile_id)
            profile = vector.profile
            if (
                vector.profile_id != composition.profile_id
                or profile.food_ingredient_id != composition.food_ingredient_id
            ):
                raise CompositionUnavailableError("METHOD_PROFILE_IDENTITY_MISMATCH")
            if not supported_registry(vector.registry_version):
                raise CompositionUnavailableError("METHOD_REGISTRY_ADAPTER_UNAVAILABLE")
            form = f"{composition.food_ingredient_id}:{composition.input_state.value}"
            by_code = {v.definition.code: v for v in vector.values}
            source_observations = json.loads(vector.observations_json)
            if not isinstance(source_observations, list):
                raise CompositionUnavailableError("METHOD_SOURCE_OBSERVATIONS_INVALID")
            totals = []
            for kind in sorted(nutrients, key=lambda k: k.value):
                try:
                    code = canonical_code_for_kind(vector.registry_version, kind)
                except NutrientMethodAdapterError as exc:
                    raise CompositionUnavailableError(
                        "METHOD_REGISTRY_ADAPTER_UNAVAILABLE"
                    ) from exc
                value = by_code.get(code)
                held = [
                    r
                    for r in source_observations
                    if isinstance(r, dict)
                    and isinstance(r.get("observation"), dict)
                    and (
                        r["observation"].get("target_nutrient_code") == code
                        or r["observation"].get("nutrient_code") == code
                    )
                ]
                method_evidence = (
                    value.provenance.evidence_json
                    if value is not None
                    else next(
                        (
                            json.dumps(
                                {"method_code": r["observation"]["method_code"]},
                                sort_keys=True,
                            )
                            for r in held
                            if isinstance(r.get("observation", {}).get("method_code"), str)
                        ),
                        None,
                    )
                )
                try:
                    method = resolve_method(
                        vector.registry_version,
                        kind,
                        evidence_json=method_evidence,
                    )
                except NutrientMethodAdapterError as exc:
                    raise CompositionUnavailableError(
                        "METHOD_REGISTRY_ADAPTER_UNAVAILABLE"
                    ) from exc
                held_state = bool(
                    held and any(r.get("origin") != "VALUE_ABSENT" for r in held)
                )
                source = ObservationSource(
                    source_id=profile.source_name,
                    release=profile.source_version,
                    locator=value.provenance.evidence_json
                    if value
                    else json.dumps(held, sort_keys=True, ensure_ascii=False)
                    if held
                    else f"sealed-vector:{profile.id}",
                    observation_id=value.provenance.source_observation_id
                    if value
                    else f"{profile.id}:absent:{code}",
                    food_form_id=form,
                    method_reference=(
                        f"{vector.registry_version}:{code}:{method.value}"
                    ),
                )
                observation = SourceObservation(
                    nutrient=kind,
                    method=method,
                    state=ObservationState.VALUE
                    if value
                    else ObservationState.HELD
                    if held_state
                    else ObservationState.MISSING,
                    amount=value.amount if value else None,
                    unit=value.definition.unit
                    if value
                    else ("kcal" if kind == NutrientKind.PUBLISHED_ENERGY else "g"),
                    basis_g=profile.basis_grams,
                    source=source,
                    source_literal=str(value.provenance.source_amount)
                    if value
                    else None,
                    source_estimated=value.provenance.estimated if value else None,
                )
                totals.append(
                    aggregate_observations(
                        (ObservationContribution(observation, mass_g, form),), policy
                    )
                )
            payload = (
                composition,
                profile.id,
                vector.registry_version,
                mass_state,
                policy,
                tuple(totals),
                vector.observations_json,
            )
            return AtomicMethodologyResult(
                composition.id,
                profile.id,
                profile.food_ingredient_id,
                vector.registry_version,
                mass_state,
                policy,
                tuple(totals),
                snapshot_digest(payload),
                vector.observations_json,
            )
