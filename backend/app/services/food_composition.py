"""One reusable deterministic DAG calculator, independent of recipes and drivers."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from uuid import UUID

from app.domain.food_composition import (
    APPLICABILITY_CALCULATION_VERSION,
    CALCULATION_VERSION,
    CompositionIssue,
    CalculatedNutrient,
    AtomicEvidence,
    StageEvidence,
    CompositionResult,
    CompositionStatus,
    CompositionUnavailableError,
    FoodCompositionVersion,
    FoodTransformation,
    MassState,
    NutrientRetentionProfile,
    SeasonScope,
    YieldModel,
    calculation_context,
    exact_product,
    exact_sum,
)
from app.services.food_composition_contracts import CompositionReader
from app.domain.nutrient_vector import V2_REGISTRY_VERSION
from app.services.nutrient_vector_contracts import (
    NutrientRegistryReader,
    NutrientVectorReader,
)


def load_dag(
    root_id: UUID, reader: CompositionReader
) -> tuple[FoodCompositionVersion, ...]:
    """Iterative postorder: a gray ancestor is a cycle, a black sibling is reuse."""
    colors: dict[UUID, int] = {}
    found: dict[UUID, FoodCompositionVersion] = {}
    result = []
    stack = [(root_id, False)]
    while stack:
        key, exiting = stack.pop()
        if exiting:
            colors[key] = 2
            result.append(found[key])
            continue
        if colors.get(key) == 1:
            raise CompositionUnavailableError("COMPOSITION_CYCLE")
        if colors.get(key) == 2:
            continue
        value = reader.get(key)
        if value.id != key:
            raise CompositionUnavailableError("COMPOSITION_ID_MISMATCH")
        colors[key] = 1
        found[key] = value
        stack.append((key, True))
        stack.extend((n.child_version_id, False) for n in reversed(value.nodes))
    return tuple(result)


def transformation_chain(
    value: FoodCompositionVersion, reader: CompositionReader
) -> tuple[FoodTransformation, ...]:
    state = value.input_state
    chain = []
    for step in value.steps:
        transformation = reader.transformation(step.transformation_id)
        if (
            transformation.id != step.transformation_id
            or transformation.input_state != state
        ):
            raise CompositionUnavailableError("MASS_STATE_DISCONTINUITY")
        for key, resolve in (
            (transformation.yield_model_id, reader.yield_model),
            (transformation.retention_profile_id, reader.retention_profile),
        ):
            if key is not None:
                evidence = resolve(key)
                if evidence.id != key or (
                    evidence.input_state,
                    evidence.output_state,
                ) != (transformation.input_state, transformation.output_state):
                    raise CompositionUnavailableError(
                        "TRANSFORMATION_EVIDENCE_MISMATCH"
                    )
        state = transformation.output_state
        chain.append(transformation)
    return tuple(chain)


@dataclass
class _Evaluation:
    input_mass: Decimal
    output_mass: Decimal | None
    state: MassState
    amounts: dict[str, Decimal | None]


class CompositionCalculator:
    def __init__(
        self, compositions: CompositionReader, nutrient_vectors: NutrientVectorReader
    ) -> None:
        self._reader = compositions
        self._vectors = nutrient_vectors

    def calculate(
        self, root_version_id: UUID, *, nutrient_codes: tuple[str, ...]
    ) -> CompositionResult:
        # A request set defines completeness without densifying the registry.
        requested = tuple(sorted(set(nutrient_codes)))
        if not requested:
            raise ValueError("Нужно явно указать требуемые нутриенты.")
        with localcontext(calculation_context()):
            return self._calculate(root_version_id, requested)

    def _calculate(
        self, root_id: UUID, requested: tuple[str, ...]
    ) -> CompositionResult:
        reader = self._reader
        definitions = {c: reader.nutrient_definition(c) for c in requested}
        graph = load_dag(root_id, reader)
        computed: dict[UUID, _Evaluation] = {}
        atomic = []
        issues = []
        stages = []
        transforms: dict[UUID, FoodTransformation] = {}
        yields: dict[UUID, YieldModel] = {}
        retentions: dict[UUID, NutrientRetentionProfile] = {}
        for composition in graph:
            amounts: dict[str, Decimal | None] = {}
            if composition.profile_id is not None:
                vector = self._vectors.get(composition.profile_id)
                if (
                    vector.profile_id != composition.profile_id
                    or vector.profile.food_ingredient_id
                    != composition.food_ingredient_id
                ):
                    raise CompositionUnavailableError("ATOMIC_PROFILE_MISMATCH")
                # is_current is mutable selector metadata and never enters replay.
                atomic.append(
                    AtomicEvidence(
                        composition.id,
                        vector.profile_id,
                        vector.profile.food_ingredient_id,
                        vector.profile.basis_grams,
                        vector.registry_version,
                        tuple(sorted(vector.values, key=lambda v: v.definition.code)),
                        vector.observations_json,
                    )
                )
                for v in vector.values:
                    if (
                        v.definition.code in definitions
                        and v.definition != definitions[v.definition.code]
                    ):
                        raise CompositionUnavailableError(
                            "NUTRIENT_DEFINITION_MISMATCH"
                        )
                mass = vector.profile.basis_grams
                amounts = {c: vector.amount(c) for c in requested}
                for c in requested:
                    if amounts[c] is None:
                        issues.append(
                            CompositionIssue(
                                "ATOMIC_NUTRIENT_UNKNOWN", composition.id, c
                            )
                        )
            else:
                mass = exact_sum(tuple(n.input_mass_g for n in composition.nodes))
                for node in composition.nodes:
                    if computed[node.child_version_id].state != node.mass_state:
                        raise CompositionUnavailableError("NODE_MASS_STATE_MISMATCH")
                for c in requested:
                    contributions = []
                    for node in composition.nodes:
                        child = computed[node.child_version_id]
                        amount = child.amounts[c]
                        if child.output_mass is None or amount is None:
                            break
                        contributions.append(
                            exact_product(amount, node.input_mass_g) / child.output_mass
                        )
                    if len(contributions) == len(composition.nodes):
                        amounts[c] = exact_sum(tuple(contributions))
                    else:
                        amounts[c] = None
                        issues.append(
                            CompositionIssue(
                                "CHILD_NUTRIENT_UNAVAILABLE", composition.id, c
                            )
                        )
            input_mass = mass
            output_mass: Decimal | None = mass
            state = composition.input_state
            stages.append(
                StageEvidence(composition.id, None, mass, state, tuple(amounts.items()))
            )
            for transformation in transformation_chain(composition, reader):
                transforms[transformation.id] = transformation
                if transformation.yield_model_id is None:
                    output_mass = None
                    issues.append(
                        CompositionIssue(
                            "YIELD_UNAVAILABLE",
                            composition.id,
                            transformation_id=transformation.id,
                        )
                    )
                else:
                    model = reader.yield_model(transformation.yield_model_id)
                    yields[model.id] = model
                    output_mass = (
                        None
                        if output_mass is None
                        else exact_product(output_mass, model.factor)
                    )
                factors = {}
                if transformation.retention_profile_id is not None:
                    profile = reader.retention_profile(
                        transformation.retention_profile_id
                    )
                    retentions[profile.id] = profile
                    factors = {v.nutrient_code: v.factor for v in profile.values}
                for c in requested:
                    if c not in factors:
                        amounts[c] = None
                        issues.append(
                            CompositionIssue(
                                "RETENTION_UNAVAILABLE",
                                composition.id,
                                c,
                                transformation.id,
                            )
                        )
                    else:
                        known_amount = amounts[c]
                        if known_amount is not None:
                            amounts[c] = exact_product(known_amount, factors[c])
                state = transformation.output_state
                stages.append(
                    StageEvidence(
                        composition.id,
                        transformation.id,
                        output_mass,
                        state,
                        tuple(amounts.items()),
                    )
                )
            computed[composition.id] = _Evaluation(
                input_mass, output_mass, state, amounts
            )
        root = computed[root_id]
        nutrients = []
        for c in requested:
            amount = root.amounts[c]
            concentration = (
                None
                if amount is None or root.output_mass is None
                else exact_product(amount, Decimal(100)) / root.output_mass
            )

            # Same six-place output convention as v1, only at the public result boundary.
            def rounded(value: Decimal | None) -> Decimal | None:
                if value is None:
                    return None
                with localcontext(calculation_context()) as ctx:
                    ctx.prec = max(80, value.adjusted() + 8)
                    return value.quantize(Decimal("0.000001"))

            nutrients.append(
                CalculatedNutrient(
                    definitions[c], rounded(amount), rounded(concentration)
                )
            )
        available = sum(n.availability == "AVAILABLE" for n in nutrients)
        status = (
            CompositionStatus.COMPLETE
            if available == len(nutrients)
            else CompositionStatus.PARTIAL
            if available
            else CompositionStatus.INCOMPLETE
        )
        return CompositionResult(
            root_id,
            CALCULATION_VERSION,
            requested,
            root.input_mass,
            root.output_mass,
            root.state,
            Decimal(100),
            tuple(nutrients),
            status,
            tuple(
                sorted(
                    set(issues),
                    key=lambda i: (
                        str(i.composition_id),
                        i.code,
                        i.nutrient_code or "",
                        str(i.transformation_id or ""),
                    ),
                )
            ),
            tuple(sorted(graph, key=lambda c: str(c.id))),
            tuple(sorted(atomic, key=lambda a: str(a.composition_id))),
            tuple(transforms[k] for k in sorted(transforms, key=str)),
            tuple(yields[k] for k in sorted(yields, key=str)),
            tuple(retentions[k] for k in sorted(retentions, key=str)),
            tuple(stages),
        )


class ApplicabilityAwareCompositionCalculator:
    """Explicit V2 calculation path; legacy CompositionCalculator stays V1-pinned."""

    def __init__(
        self,
        compositions: CompositionReader,
        nutrient_vectors: NutrientVectorReader,
        nutrient_registry: NutrientRegistryReader,
    ) -> None:
        self._reader = compositions
        self._vectors = nutrient_vectors
        self._registry = nutrient_registry

    def calculate(
        self,
        root_version_id: UUID,
        *,
        registry_version: str,
        nutrient_codes: tuple[str, ...],
        season_reference: str | None = None,
    ) -> CompositionResult:
        if registry_version != V2_REGISTRY_VERSION:
            raise CompositionUnavailableError("NUTRIENT_REGISTRY_UNSUPPORTED")
        requested = tuple(sorted(set(nutrient_codes)))
        if not requested:
            raise ValueError("Нужно явно указать требуемые нутриенты.")
        if season_reference is not None and (
            not isinstance(season_reference, str) or not season_reference.strip()
        ):
            raise ValueError("Ссылка на сезон должна быть непустой.")
        with localcontext(calculation_context()):
            return self._calculate(
                root_version_id,
                registry_version,
                requested,
                season_reference,
            )

    def _calculate(
        self,
        root_id: UUID,
        registry_version: str,
        requested: tuple[str, ...],
        season_reference: str | None,
    ) -> CompositionResult:
        reader = self._reader
        definitions = {
            code: self._registry.get(registry_version, code) for code in requested
        }
        graph = load_dag(root_id, reader)
        computed: dict[UUID, _Evaluation] = {}
        atomic = []
        issues = []
        stages = []
        transforms: dict[UUID, FoodTransformation] = {}
        yields: dict[UUID, YieldModel] = {}
        retentions: dict[UUID, NutrientRetentionProfile] = {}

        for composition in graph:
            amounts: dict[str, Decimal | None] = {}
            if composition.profile_id is not None:
                vector = self._vectors.get(composition.profile_id)
                if (
                    vector.profile_id != composition.profile_id
                    or vector.profile.food_ingredient_id
                    != composition.food_ingredient_id
                ):
                    raise CompositionUnavailableError("ATOMIC_PROFILE_MISMATCH")
                if vector.registry_version != registry_version:
                    raise CompositionUnavailableError("NUTRIENT_REGISTRY_MISMATCH")
                atomic.append(
                    AtomicEvidence(
                        composition.id,
                        vector.profile_id,
                        vector.profile.food_ingredient_id,
                        vector.profile.basis_grams,
                        vector.registry_version,
                        tuple(sorted(vector.values, key=lambda v: v.definition.code)),
                        vector.observations_json,
                    )
                )
                for nutrient in vector.values:
                    definition = definitions.get(nutrient.definition.code)
                    if (
                        definition is not None
                        and nutrient.definition.semantic_identity
                        != definition.semantic_identity
                    ):
                        raise CompositionUnavailableError(
                            "NUTRIENT_DEFINITION_MISMATCH"
                        )
                mass = vector.profile.basis_grams
                amounts = {code: vector.amount(code) for code in requested}
                for code in requested:
                    if amounts[code] is None:
                        issues.append(
                            CompositionIssue(
                                "ATOMIC_NUTRIENT_UNKNOWN",
                                composition.id,
                                code,
                            )
                        )
            else:
                mass = exact_sum(tuple(node.input_mass_g for node in composition.nodes))
                for node in composition.nodes:
                    if computed[node.child_version_id].state != node.mass_state:
                        raise CompositionUnavailableError("NODE_MASS_STATE_MISMATCH")
                for code in requested:
                    contributions = []
                    for node in composition.nodes:
                        child = computed[node.child_version_id]
                        amount = child.amounts[code]
                        if child.output_mass is None or amount is None:
                            break
                        contributions.append(
                            exact_product(amount, node.input_mass_g)
                            / child.output_mass
                        )
                    if len(contributions) == len(composition.nodes):
                        amounts[code] = exact_sum(tuple(contributions))
                    else:
                        amounts[code] = None
                        issues.append(
                            CompositionIssue(
                                "CHILD_NUTRIENT_UNAVAILABLE",
                                composition.id,
                                code,
                            )
                        )

            input_mass = mass
            output_mass: Decimal | None = mass
            state = composition.input_state
            stages.append(
                StageEvidence(
                    composition.id,
                    None,
                    mass,
                    state,
                    tuple(amounts.items()),
                )
            )
            evidence_scopes: set[str] = set()

            for step in composition.steps:
                transformation = reader.transformation(step.transformation_id)
                if (
                    transformation.id != step.transformation_id
                    or transformation.input_state != state
                ):
                    raise CompositionUnavailableError("MASS_STATE_DISCONTINUITY")
                applicability = reader.applicability(transformation.id)
                if applicability.food_ingredient_id != composition.food_ingredient_id:
                    raise CompositionUnavailableError(
                        "TRANSFORMATION_APPLICABILITY_FOOD_MISMATCH"
                    )
                if applicability.evidence_scope_id in evidence_scopes:
                    raise CompositionUnavailableError(
                        "TRANSFORMATION_EVIDENCE_SCOPE_OVERLAP"
                    )
                evidence_scopes.add(applicability.evidence_scope_id)
                if (
                    applicability.season_scope
                    == SeasonScope.EXACT_SOURCE_PERIOD
                    and applicability.season_reference != season_reference
                ):
                    raise CompositionUnavailableError(
                        "TRANSFORMATION_SEASON_MISMATCH"
                    )

                transforms[transformation.id] = transformation
                if transformation.yield_model_id is None:
                    output_mass = None
                    issues.append(
                        CompositionIssue(
                            "YIELD_UNAVAILABLE",
                            composition.id,
                            transformation_id=transformation.id,
                        )
                    )
                else:
                    model = reader.yield_model(transformation.yield_model_id)
                    if (model.input_state, model.output_state) != (
                        transformation.input_state,
                        transformation.output_state,
                    ):
                        raise CompositionUnavailableError(
                            "TRANSFORMATION_EVIDENCE_MISMATCH"
                        )
                    yields[model.id] = model
                    output_mass = (
                        None
                        if output_mass is None
                        else exact_product(output_mass, model.factor)
                    )

                factors = {}
                if transformation.retention_profile_id is not None:
                    if applicability.retention_registry_version != registry_version:
                        raise CompositionUnavailableError(
                            "RETENTION_REGISTRY_MISMATCH"
                        )
                    profile = reader.retention_profile_for_registry(
                        transformation.retention_profile_id,
                        registry_version,
                    )
                    if (profile.input_state, profile.output_state) != (
                        transformation.input_state,
                        transformation.output_state,
                    ):
                        raise CompositionUnavailableError(
                            "TRANSFORMATION_EVIDENCE_MISMATCH"
                        )
                    retentions[profile.id] = profile
                    factors = {
                        value.nutrient_code: value.factor for value in profile.values
                    }
                elif applicability.retention_registry_version is not None:
                    raise CompositionUnavailableError("RETENTION_REGISTRY_MISMATCH")

                for code in requested:
                    if code not in factors:
                        amounts[code] = None
                        issues.append(
                            CompositionIssue(
                                "RETENTION_UNAVAILABLE",
                                composition.id,
                                code,
                                transformation.id,
                            )
                        )
                    else:
                        known_amount = amounts[code]
                        if known_amount is not None:
                            amounts[code] = exact_product(
                                known_amount,
                                factors[code],
                            )
                state = transformation.output_state
                stages.append(
                    StageEvidence(
                        composition.id,
                        transformation.id,
                        output_mass,
                        state,
                        tuple(amounts.items()),
                    )
                )

            computed[composition.id] = _Evaluation(
                input_mass,
                output_mass,
                state,
                amounts,
            )

        root = computed[root_id]
        nutrients = []
        for code in requested:
            amount = root.amounts[code]
            concentration = (
                None
                if amount is None or root.output_mass is None
                else exact_product(amount, Decimal(100)) / root.output_mass
            )

            def rounded(value: Decimal | None) -> Decimal | None:
                if value is None:
                    return None
                with localcontext(calculation_context()) as ctx:
                    ctx.prec = max(80, value.adjusted() + 8)
                    return value.quantize(Decimal("0.000001"))

            nutrients.append(
                CalculatedNutrient(
                    definitions[code],
                    rounded(amount),
                    rounded(concentration),
                )
            )

        available = sum(
            nutrient.availability == "AVAILABLE" for nutrient in nutrients
        )
        status = (
            CompositionStatus.COMPLETE
            if available == len(nutrients)
            else CompositionStatus.PARTIAL
            if available
            else CompositionStatus.INCOMPLETE
        )
        return CompositionResult(
            root_id,
            APPLICABILITY_CALCULATION_VERSION,
            requested,
            root.input_mass,
            root.output_mass,
            root.state,
            Decimal(100),
            tuple(nutrients),
            status,
            tuple(
                sorted(
                    set(issues),
                    key=lambda issue: (
                        str(issue.composition_id),
                        issue.code,
                        issue.nutrient_code or "",
                        str(issue.transformation_id or ""),
                    ),
                )
            ),
            tuple(sorted(graph, key=lambda composition: str(composition.id))),
            tuple(sorted(atomic, key=lambda value: str(value.composition_id))),
            tuple(transforms[key] for key in sorted(transforms, key=str)),
            tuple(yields[key] for key in sorted(yields, key=str)),
            tuple(retentions[key] for key in sorted(retentions, key=str)),
            tuple(stages),
        )
