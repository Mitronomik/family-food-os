"""One reusable deterministic DAG calculator, independent of recipes and drivers."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from uuid import UUID

from app.domain.food_composition import (
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
    YieldModel,
    calculation_context,
    exact_product,
    exact_sum,
)
from app.services.food_composition_contracts import CompositionReader
from app.services.nutrient_vector_contracts import NutrientVectorReader


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
