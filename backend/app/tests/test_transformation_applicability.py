"""Adversarial Step 7 applicability-aware calculator tests with synthetic evidence."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.domain.food_composition import (
    APPLICABILITY_CALCULATION_VERSION,
    CompositionKind,
    CompositionNode,
    CompositionProvenance,
    CompositionStatus,
    CompositionStep,
    CompositionUnavailableError,
    FoodCompositionVersion,
    FoodTransformation,
    MassState,
    NutrientRetentionProfile,
    RetentionValue,
    SeasonScope,
    TransformationApplicability,
    YieldModel,
)
from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.nutrient_vector import (
    V2_REGISTRY_VERSION,
    NutrientDefinition,
    NutrientProvenance,
    NutrientValue,
    NutrientVector,
)
from app.domain.nutrient_vector_backfill_v1 import REGISTRY_VERSION as REGISTRY_V1
from app.services.food_composition import (
    ApplicabilityAwareCompositionCalculator,
    CompositionCalculator,
)

D = Decimal
P = CompositionProvenance(
    "synthetic-step7",
    "1",
    "test-only-evidence",
    "explicit-test-review",
)

NUTRIENTS = {
    "PROTEIN": ("Белок", "g", D("10")),
    "ENERGY_KCAL": ("Энергия", "kcal", D("100")),
    "CARBOHYDRATE_AVAILABLE": ("Доступные углеводы", "g", D("20")),
    "VITAMIN_A_RE": ("Витамин А эквивалент", "µg", D("30")),
}


def vector(
    registry_version: str,
    *,
    food_ingredient_id: UUID | None = None,
    codes: tuple[str, ...] = tuple(NUTRIENTS),
) -> NutrientVector:
    food_id = food_ingredient_id or uuid4()
    profile = FoodNutritionProfile(
        id=uuid4(),
        food_ingredient_id=food_id,
        basis_grams=D("100"),
        kcal=None,
        protein_g=None,
        fat_g=None,
        carbohydrates_g=None,
        fiber_g=None,
        source_name="synthetic-step7",
        source_id=str(uuid4()),
        source_version="1",
        source_data_type="test",
        verified_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        estimated=False,
        is_current=False,
        created_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
    )
    values = []
    for code in codes:
        name, unit, amount = NUTRIENTS[code]
        definition = NutrientDefinition(
            code,
            name,
            unit,
            registry_version,
            f"Тестовое определение {name.lower()}.",
            "SYNTHETIC_TEST",
        )
        provenance = NutrientProvenance(
            registry_version=registry_version,
            audit_identity=f"audit-{code}",
            source_name=profile.source_name,
            source_food_id=profile.source_id,
            source_release=profile.source_version,
            source_data_type=profile.source_data_type,
            source_nutrient_id=code,
            source_nutrient_name=name,
            source_nutrient_nbr=None,
            source_unit=unit,
            source_amount=amount,
            source_observation_id=f"obs-{code}",
            source_derivation_id=None,
            mapping_status="EXACT",
            estimated=False,
            evidence_json="{}",
        )
        values.append(NutrientValue(definition, amount, provenance))
    return NutrientVector(profile, registry_version, tuple(values), "[]")


def atomic(value: NutrientVector, *, version: int = 1) -> FoodCompositionVersion:
    return FoodCompositionVersion(
        id=uuid4(),
        food_ingredient_id=value.profile.food_ingredient_id,
        version=version,
        kind=CompositionKind.ATOMIC,
        input_state=MassState.INPUT,
        provenance=P,
        profile_id=value.profile_id,
    )


class Memory:
    def __init__(
        self,
        vectors: tuple[NutrientVector, ...],
        versions: tuple[FoodCompositionVersion, ...],
    ) -> None:
        self.vector_map = {value.profile_id: value for value in vectors}
        self.versions = {value.id: value for value in versions}
        self.transforms: dict[UUID, FoodTransformation] = {}
        self.yields: dict[UUID, YieldModel] = {}
        self.retentions: dict[UUID, NutrientRetentionProfile] = {}
        self.retention_registries: dict[UUID, str] = {}
        self.applicabilities: dict[UUID, TransformationApplicability] = {}
        self.definitions = {
            (item.definition.registry_version, item.definition.code): item.definition
            for value in vectors
            for item in value.values
        }

    def get(self, key: UUID) -> FoodCompositionVersion:
        return self.versions[key]

    def transformation(self, key: UUID) -> FoodTransformation:
        return self.transforms[key]

    def yield_model(self, key: UUID) -> YieldModel:
        return self.yields[key]

    def retention_profile(self, key: UUID) -> NutrientRetentionProfile:
        return self.retentions[key]

    def retention_profile_for_registry(
        self, key: UUID, registry_version: str
    ) -> NutrientRetentionProfile:
        if self.retention_registries.get(key) != registry_version:
            raise CompositionUnavailableError("RETENTION_REGISTRY_MISMATCH")
        return self.retentions[key]

    def applicability(self, key: UUID) -> TransformationApplicability:
        try:
            return self.applicabilities[key]
        except KeyError as exc:
            raise CompositionUnavailableError(
                "TRANSFORMATION_APPLICABILITY_MISSING"
            ) from exc

    def nutrient_definition(self, code: str) -> NutrientDefinition:
        return self.definitions[(REGISTRY_V1, code)]

    @property
    def vectors(self):
        owner = self

        class Reader:
            def get(self, key: UUID) -> NutrientVector:
                return owner.vector_map[key]

        return Reader()

    @property
    def registry(self):
        owner = self

        class Reader:
            def get(self, registry_version: str, code: str) -> NutrientDefinition:
                return owner.definitions[(registry_version, code)]

        return Reader()


def retention(
    input_state: MassState,
    output_state: MassState,
    codes: tuple[str, ...],
    *,
    factor: str = "0.5",
) -> NutrientRetentionProfile:
    return NutrientRetentionProfile(
        uuid4(),
        1,
        input_state,
        output_state,
        P,
        tuple(RetentionValue(code, D(factor), P) for code in codes),
    )


def transformation(
    memory: Memory,
    composition: FoodCompositionVersion,
    *,
    input_state: MassState = MassState.INPUT,
    output_state: MassState = MassState.COOKED,
    retention_codes: tuple[str, ...] | None = ("PROTEIN",),
    retention_registry: str = V2_REGISTRY_VERSION,
    yield_factor: str | None = "1",
    applicability: bool = True,
    applicability_food_id: UUID | None = None,
    applicability_registry: str | None = None,
    season_scope: SeasonScope = SeasonScope.ALL_SEASONS,
    season_reference: str | None = None,
    evidence_scope_id: str = "scope-1",
) -> tuple[FoodTransformation, CompositionStep]:
    yield_model = None
    if yield_factor is not None:
        yield_model = YieldModel(
            uuid4(),
            1,
            D(yield_factor),
            input_state,
            output_state,
            P,
        )
        memory.yields[yield_model.id] = yield_model

    profile = None
    if retention_codes is not None:
        profile = retention(input_state, output_state, retention_codes)
        memory.retentions[profile.id] = profile
        memory.retention_registries[profile.id] = retention_registry

    value = FoodTransformation(
        uuid4(),
        1,
        "SYNTHETIC_PROCESS",
        input_state,
        output_state,
        P,
        None if yield_model is None else yield_model.id,
        None if profile is None else profile.id,
    )
    memory.transforms[value.id] = value
    if applicability:
        bound_registry = applicability_registry
        if bound_registry is None and profile is not None:
            bound_registry = retention_registry
        memory.applicabilities[value.id] = TransformationApplicability(
            value.id,
            applicability_food_id or composition.food_ingredient_id,
            bound_registry,
            season_scope,
            season_reference,
            evidence_scope_id,
            P,
        )
    return value, CompositionStep(uuid4(), 0, value.id)


def v2_calculator(memory: Memory) -> ApplicabilityAwareCompositionCalculator:
    return ApplicabilityAwareCompositionCalculator(
        memory,
        memory.vectors,
        memory.registry,
    )


def test_legacy_v1_calculator_needs_no_applicability_and_replay_stays_numeric():
    v1 = vector(REGISTRY_V1, codes=("PROTEIN",))
    base = atomic(v1)
    memory = Memory((v1,), (base,))
    _, step = transformation(
        memory,
        base,
        retention_registry=REGISTRY_V1,
        applicability=False,
    )
    cooked = replace(base, id=uuid4(), version=2, steps=(step,))
    memory.versions[cooked.id] = cooked

    result = CompositionCalculator(memory, memory.vectors).calculate(
        cooked.id,
        nutrient_codes=("PROTEIN",),
    )

    assert result.calculation_version == "FOOD_COMPOSITION_V1"
    assert result.nutrients[0].amount == D("5.000000")


def test_v2_atomic_calculation_uses_explicit_registry_path():
    v2 = vector(V2_REGISTRY_VERSION, codes=("PROTEIN",))
    base = atomic(v2)
    memory = Memory((v2,), (base,))

    result = v2_calculator(memory).calculate(
        base.id,
        registry_version=V2_REGISTRY_VERSION,
        nutrient_codes=("PROTEIN",),
    )

    assert result.calculation_version == APPLICABILITY_CALCULATION_VERSION
    assert result.status == CompositionStatus.COMPLETE
    assert result.nutrients[0].definition.semantic_identity == (
        V2_REGISTRY_VERSION,
        "PROTEIN",
    )
    assert result.nutrients[0].amount == D("10.000000")


def test_transformed_v2_requires_exact_applicability_and_food_identity():
    v2 = vector(V2_REGISTRY_VERSION, codes=("PROTEIN",))
    base = atomic(v2)
    memory = Memory((v2,), (base,))
    _, step = transformation(memory, base, applicability=False)
    cooked = replace(base, id=uuid4(), version=2, steps=(step,))
    memory.versions[cooked.id] = cooked

    with pytest.raises(CompositionUnavailableError) as missing:
        v2_calculator(memory).calculate(
            cooked.id,
            registry_version=V2_REGISTRY_VERSION,
            nutrient_codes=("PROTEIN",),
        )
    assert missing.value.issue_code == "TRANSFORMATION_APPLICABILITY_MISSING"

    memory.applicabilities[step.transformation_id] = TransformationApplicability(
        step.transformation_id,
        uuid4(),
        V2_REGISTRY_VERSION,
        SeasonScope.ALL_SEASONS,
        None,
        "scope-1",
        P,
    )
    with pytest.raises(CompositionUnavailableError) as wrong_food:
        v2_calculator(memory).calculate(
            cooked.id,
            registry_version=V2_REGISTRY_VERSION,
            nutrient_codes=("PROTEIN",),
        )
    assert (
        wrong_food.value.issue_code
        == "TRANSFORMATION_APPLICABILITY_FOOD_MISMATCH"
    )


def test_wrong_retention_registry_and_v1_factor_never_carry_into_v2():
    v2 = vector(
        V2_REGISTRY_VERSION,
        codes=("PROTEIN", "CARBOHYDRATE_AVAILABLE"),
    )
    base = atomic(v2)
    memory = Memory((v2,), (base,))
    _, step = transformation(
        memory,
        base,
        retention_codes=("PROTEIN", "CARBOHYDRATE_AVAILABLE"),
        retention_registry=REGISTRY_V1,
        applicability_registry=V2_REGISTRY_VERSION,
    )
    cooked = replace(base, id=uuid4(), version=2, steps=(step,))
    memory.versions[cooked.id] = cooked

    with pytest.raises(CompositionUnavailableError) as error:
        v2_calculator(memory).calculate(
            cooked.id,
            registry_version=V2_REGISTRY_VERSION,
            nutrient_codes=("PROTEIN", "CARBOHYDRATE_AVAILABLE"),
        )
    assert error.value.issue_code == "RETENTION_REGISTRY_MISMATCH"


def test_mixed_v1_v2_atomic_vectors_fail_closed():
    food_id = uuid4()
    v2 = vector(V2_REGISTRY_VERSION, food_ingredient_id=food_id, codes=("PROTEIN",))
    v1 = vector(REGISTRY_V1, food_ingredient_id=food_id, codes=("PROTEIN",))
    a = atomic(v2)
    b = atomic(v1, version=2)
    parent = FoodCompositionVersion(
        uuid4(),
        food_id,
        3,
        CompositionKind.COMPOSITE,
        MassState.INPUT,
        P,
        nodes=(
            CompositionNode(uuid4(), 0, a.id, D("50"), MassState.INPUT),
            CompositionNode(uuid4(), 1, b.id, D("50"), MassState.INPUT),
        ),
    )
    memory = Memory((v2, v1), (a, b, parent))

    with pytest.raises(CompositionUnavailableError) as error:
        v2_calculator(memory).calculate(
            parent.id,
            registry_version=V2_REGISTRY_VERSION,
            nutrient_codes=("PROTEIN",),
        )
    assert error.value.issue_code == "NUTRIENT_REGISTRY_MISMATCH"


def test_missing_retention_is_unknown_not_implicit_one_hundred_percent():
    v2 = vector(
        V2_REGISTRY_VERSION,
        codes=("PROTEIN", "ENERGY_KCAL", "VITAMIN_A_RE"),
    )
    base = atomic(v2)
    memory = Memory((v2,), (base,))
    _, step = transformation(memory, base, retention_codes=("PROTEIN",))
    cooked = replace(base, id=uuid4(), version=2, steps=(step,))
    memory.versions[cooked.id] = cooked

    result = v2_calculator(memory).calculate(
        cooked.id,
        registry_version=V2_REGISTRY_VERSION,
        nutrient_codes=("PROTEIN", "ENERGY_KCAL", "VITAMIN_A_RE"),
    )
    by_code = {value.definition.code: value for value in result.nutrients}

    assert by_code["PROTEIN"].amount == D("5.000000")
    assert by_code["ENERGY_KCAL"].amount is None
    assert by_code["VITAMIN_A_RE"].amount is None
    assert result.status == CompositionStatus.PARTIAL
    assert {
        issue.nutrient_code
        for issue in result.issues
        if issue.code == "RETENTION_UNAVAILABLE"
    } >= {"ENERGY_KCAL", "VITAMIN_A_RE"}


def test_transformation_without_retention_profile_does_not_imply_retention():
    v2 = vector(V2_REGISTRY_VERSION, codes=("PROTEIN",))
    base = atomic(v2)
    memory = Memory((v2,), (base,))
    _, step = transformation(memory, base, retention_codes=None)
    cooked = replace(base, id=uuid4(), version=2, steps=(step,))
    memory.versions[cooked.id] = cooked

    result = v2_calculator(memory).calculate(
        cooked.id,
        registry_version=V2_REGISTRY_VERSION,
        nutrient_codes=("PROTEIN",),
    )

    assert result.nutrients[0].amount is None
    assert result.status == CompositionStatus.INCOMPLETE


def test_missing_yield_keeps_output_mass_unknown():
    v2 = vector(V2_REGISTRY_VERSION, codes=("PROTEIN",))
    base = atomic(v2)
    memory = Memory((v2,), (base,))
    _, step = transformation(memory, base, yield_factor=None)
    cooked = replace(base, id=uuid4(), version=2, steps=(step,))
    memory.versions[cooked.id] = cooked

    result = v2_calculator(memory).calculate(
        cooked.id,
        registry_version=V2_REGISTRY_VERSION,
        nutrient_codes=("PROTEIN",),
    )

    assert result.output_mass_g is None
    assert result.nutrients[0].amount == D("5.000000")
    assert result.nutrients[0].per_100_g is None
    assert any(issue.code == "YIELD_UNAVAILABLE" for issue in result.issues)


def test_all_seasons_and_exact_source_period_have_explicit_semantics():
    v2 = vector(V2_REGISTRY_VERSION, codes=("PROTEIN",))
    base = atomic(v2)

    all_memory = Memory((v2,), (base,))
    _, all_step = transformation(
        all_memory,
        base,
        season_scope=SeasonScope.ALL_SEASONS,
    )
    all_cooked = replace(base, id=uuid4(), version=2, steps=(all_step,))
    all_memory.versions[all_cooked.id] = all_cooked
    assert (
        v2_calculator(all_memory)
        .calculate(
            all_cooked.id,
            registry_version=V2_REGISTRY_VERSION,
            nutrient_codes=("PROTEIN",),
        )
        .status
        == CompositionStatus.COMPLETE
    )

    exact_memory = Memory((v2,), (base,))
    _, exact_step = transformation(
        exact_memory,
        base,
        season_scope=SeasonScope.EXACT_SOURCE_PERIOD,
        season_reference="SOURCE-WINTER",
    )
    exact_cooked = replace(base, id=uuid4(), version=2, steps=(exact_step,))
    exact_memory.versions[exact_cooked.id] = exact_cooked

    result = v2_calculator(exact_memory).calculate(
        exact_cooked.id,
        registry_version=V2_REGISTRY_VERSION,
        nutrient_codes=("PROTEIN",),
        season_reference="SOURCE-WINTER",
    )
    assert result.status == CompositionStatus.COMPLETE

    for wrong in (None, "SOURCE-SUMMER"):
        with pytest.raises(CompositionUnavailableError) as error:
            v2_calculator(exact_memory).calculate(
                exact_cooked.id,
                registry_version=V2_REGISTRY_VERSION,
                nutrient_codes=("PROTEIN",),
                season_reference=wrong,
            )
        assert error.value.issue_code == "TRANSFORMATION_SEASON_MISMATCH"


def test_duplicate_evidence_scope_in_one_chain_fails_but_siblings_do_not_overlap():
    v2 = vector(V2_REGISTRY_VERSION, codes=("PROTEIN",))
    base = atomic(v2)

    sequential = Memory((v2,), (base,))
    first, first_step = transformation(
        sequential,
        base,
        input_state=MassState.INPUT,
        output_state=MassState.DRAINED,
        evidence_scope_id="same-reviewed-scope",
    )
    second, second_step = transformation(
        sequential,
        base,
        input_state=MassState.DRAINED,
        output_state=MassState.COOKED,
        evidence_scope_id="same-reviewed-scope",
    )
    chain = replace(
        base,
        id=uuid4(),
        version=2,
        steps=(
            first_step,
            replace(second_step, position=1),
        ),
    )
    sequential.versions[chain.id] = chain

    with pytest.raises(CompositionUnavailableError) as error:
        v2_calculator(sequential).calculate(
            chain.id,
            registry_version=V2_REGISTRY_VERSION,
            nutrient_codes=("PROTEIN",),
        )
    assert error.value.issue_code == "TRANSFORMATION_EVIDENCE_SCOPE_OVERLAP"

    sibling_memory = Memory((v2,), ())
    left = atomic(v2)
    right = replace(left, id=uuid4(), version=2)
    sibling_memory.versions.update({left.id: left, right.id: right})
    _, left_step = transformation(
        sibling_memory,
        left,
        evidence_scope_id="shared-source-scope",
    )
    _, right_step = transformation(
        sibling_memory,
        right,
        evidence_scope_id="shared-source-scope",
    )
    left_cooked = replace(left, id=uuid4(), version=3, steps=(left_step,))
    right_cooked = replace(right, id=uuid4(), version=4, steps=(right_step,))
    sibling_memory.versions.update(
        {left_cooked.id: left_cooked, right_cooked.id: right_cooked}
    )
    parent = FoodCompositionVersion(
        uuid4(),
        v2.profile.food_ingredient_id,
        5,
        CompositionKind.COMPOSITE,
        MassState.INPUT,
        P,
        nodes=(
            CompositionNode(
                uuid4(), 0, left_cooked.id, D("50"), MassState.COOKED
            ),
            CompositionNode(
                uuid4(), 1, right_cooked.id, D("50"), MassState.COOKED
            ),
        ),
    )
    sibling_memory.versions[parent.id] = parent

    result = v2_calculator(sibling_memory).calculate(
        parent.id,
        registry_version=V2_REGISTRY_VERSION,
        nutrient_codes=("PROTEIN",),
    )
    assert result.root_version_id == parent.id
