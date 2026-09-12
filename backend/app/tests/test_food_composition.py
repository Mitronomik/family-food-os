"""Adversarial deterministic composition tests with explicit synthetic fixtures."""

from dataclasses import replace, FrozenInstanceError
from decimal import Decimal, localcontext, ROUND_DOWN, Inexact
from importlib import import_module
from pathlib import Path
import ast
import shutil
import sqlite3
from uuid import uuid4

import pytest
from sqlalchemy import select, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Select

from app.db.config import DatabaseConfig
from app.domain.food_composition import (
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
    YieldModel,
    exact_sum,
    snapshot_digest,
)
from app.domain.nutrient_vector import NutrientVectorUnavailableError
from app.persistence.sqlalchemy_core.engine import create_sqlite_engine
from app.persistence.sqlalchemy_core.food_composition_scope import (
    SqlAlchemyCompositionReadScope,
    SqlAlchemyCompositionUnitOfWork,
)
from app.persistence.sqlalchemy_core import food_composition_tables as tables
from app.persistence.sqlalchemy_core.food_ingredient_uow import (
    SqlAlchemyFoodCatalogueUnitOfWork,
)
from app.seed.food_ingredients import seed_food_ingredients
from app.services.food_composition import CompositionCalculator, load_dag
from app.tests.test_nutrient_vector import vector

D = Decimal
P = CompositionProvenance("synthetic-test", "1", "test-fixture", "explicit-test-review")
MIGRATION = import_module("app.migrations.versions.0029_food_composition_core")


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    config = DatabaseConfig(path=tmp_path_factory.mktemp("composition") / "seed.sqlite")
    seed_food_ingredients(config)
    return config


@pytest.fixture
def database(seeded, tmp_path):
    config = DatabaseConfig(path=tmp_path / "test.sqlite")
    shutil.copyfile(seeded.path, config.path)
    engine = create_sqlite_engine(config)
    yield config, engine
    engine.dispose()


def atomic(v, *, version=1, state=MassState.RAW, **kwargs):
    return FoodCompositionVersion(
        uuid4(),
        v.profile.food_ingredient_id,
        version,
        CompositionKind.ATOMIC,
        state,
        P,
        profile_id=v.profile_id,
        **kwargs,
    )


def node(child, mass="100", position=0, state=MassState.RAW):
    return CompositionNode(uuid4(), position, child.id, D(mass), state)


def composite(v, children, *, version=2, steps=()):
    return FoodCompositionVersion(
        uuid4(),
        v.profile.food_ingredient_id,
        version,
        CompositionKind.COMPOSITE,
        MassState.INPUT,
        P,
        nodes=tuple(children),
        steps=steps,
    )


class Memory:
    """Unit-test port: numeric test values are never inserted into production data."""

    def __init__(self, v, versions):
        self.v = v
        self.versions = {c.id: c for c in versions}
        self.transforms = {}
        self.yields = {}
        self.retentions = {}
        self.definitions = {x.definition.code: x.definition for x in v.values}

    def get(self, key):
        return self.versions[key]

    def transformation(self, key):
        return self.transforms[key]

    def yield_model(self, key):
        return self.yields[key]

    def retention_profile(self, key):
        return self.retentions[key]

    def nutrient_definition(self, code):
        return self.definitions[code]

    @property
    def vectors(self):
        owner = self

        class Reader:
            def get(self, key):
                assert key == owner.v.profile_id
                return owner.v

        return Reader()


def synthetic(v):
    values = tuple(
        replace(x, amount=D("12") if x.definition.code == "PROTEIN" else D("120"))
        for x in v.values
        if x.definition.code in ("ENERGY_KCAL", "PROTEIN")
    )
    assert len(values) == 2
    return replace(v, values=values)


def calculate(memory, root, codes=("PROTEIN", "ENERGY_KCAL")):
    return CompositionCalculator(memory, memory.vectors).calculate(
        root.id, nutrient_codes=codes
    )


def transformed(
    memory, base, yield_factor="1", retention="1", *, output=MassState.COOKED
):
    y = (
        None
        if yield_factor is None
        else YieldModel(uuid4(), 1, D(yield_factor), base.input_state, output, P)
    )
    r = (
        None
        if retention is None
        else NutrientRetentionProfile(
            uuid4(),
            1,
            base.input_state,
            output,
            P,
            tuple(RetentionValue(c, D(retention), P) for c in memory.definitions),
        )
    )
    t = FoodTransformation(
        uuid4(),
        1,
        "TEST_PROCESS",
        base.input_state,
        output,
        P,
        None if y is None else y.id,
        None if r is None else r.id,
    )
    if y:
        memory.yields[y.id] = y
    if r:
        memory.retentions[r.id] = r
    memory.transforms[t.id] = t
    new = replace(base, steps=(CompositionStep(uuid4(), 0, t.id),))
    memory.versions[new.id] = new
    return new, y, r, t


def test_atomic_exact_profile_complete_sparse_and_immutable(database):
    _, engine = database
    v = vector(engine)
    a = atomic(v)
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_versions((a,))
        uow.commit()
    with SqlAlchemyCompositionReadScope(engine) as read:
        result = CompositionCalculator(
            read.compositions, read.nutrient_vectors
        ).calculate(a.id, nutrient_codes=("PROTEIN", "CALCIUM"))
    assert result.status == CompositionStatus.PARTIAL
    assert len(result.nutrients) == 2
    assert result.nutrients[0].amount is None
    assert result.nutrients[1].amount == v.amount("PROTEIN")
    assert result.atomic_evidence[0].profile_id == v.profile_id
    assert result.output_mass_g == D(100)
    assert result.output_mass_state == MassState.RAW
    with pytest.raises(FrozenInstanceError):
        result.output_mass_g = D(2)


@pytest.mark.parametrize(
    "bad",
    [0.5, 1, "1", True, None, D(0), D(-1), D("NaN"), D("Infinity"), D("-Infinity")],
)
def test_mass_and_yield_reject_non_decimal_nonpositive_nonfinite(database, bad):
    _, engine = database
    a = atomic(vector(engine))
    expected = ValueError if isinstance(bad, D) else TypeError
    with pytest.raises(expected):
        replace(node(a), input_mass_g=bad)
    with pytest.raises(expected):
        YieldModel(uuid4(), 1, bad, MassState.RAW, MassState.COOKED, P)


def test_no_fractions_exact_mass_sum_and_shared_nested_dag(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    b = composite(v, [node(a, "1", 0), node(a, "2", 1)])
    root = composite(v, [node(b, "1", 0, MassState.INPUT), node(a, "2", 1)], version=3)
    memory = Memory(v, (root, b, a))
    result = calculate(memory, root)
    assert result.input_mass_g == D(3)
    assert result.output_mass_g == D(3)
    assert result.nutrients[1].amount == D("0.36")
    assert result.nutrients[1].per_100_g == D(12)
    assert result.status == CompositionStatus.COMPLETE
    assert len(result.compositions) == 3
    assert all(not hasattr(n, "fraction") for c in result.compositions for n in c.nodes)
    with localcontext() as ctx:
        ctx.prec = 2
        assert exact_sum((D("1e100"), D("0.0000000000000000001"))) == D(
            "1" + "0" * 100 + ".0000000000000000001"
        )


def test_invalid_node_identity_order_and_authority(database):
    _, engine = database
    v = vector(engine)
    a = atomic(v)
    n = node(a)
    for children in ((n, n), (n, replace(n, id=uuid4())), (n, replace(n, position=1))):
        with pytest.raises(ValueError):
            composite(v, children)
    for position in (True, -1, D(1)):
        with pytest.raises(ValueError):
            replace(n, position=position)
    with pytest.raises(ValueError):
        replace(a, nodes=(n,))
    with pytest.raises(ValueError):
        replace(a, profile_id=None)
    with pytest.raises(ValueError):
        composite(v, ())


@pytest.mark.parametrize("length", [1, 2, 3, 6])
def test_build_time_and_runtime_cycle_defense(database, length):
    _, engine = database
    v = vector(engine)
    cycle = [composite(v, [node(atomic(v))], version=i + 1) for i in range(length)]
    cycle = [
        replace(
            c, nodes=(replace(c.nodes[0], child_version_id=cycle[(i + 1) % length].id),)
        )
        for i, c in enumerate(cycle)
    ]
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        with pytest.raises(CompositionUnavailableError) as error:
            uow.compositions.add_versions(tuple(cycle))
        assert error.value.issue_code == "COMPOSITION_CYCLE"
        assert not uow.adapter_connection.execute(select(tables.versions)).all()
    with pytest.raises(CompositionUnavailableError) as error:
        calculate(Memory(v, cycle), cycle[0])
    assert error.value.issue_code == "COMPOSITION_CYCLE"


@pytest.mark.parametrize(
    "yield_factor,retention,mass,protein",
    [
        ("0.5", "1", "50", "24"),
        ("1", "0.5", "100", "6"),
        ("0.5", "0.25", "50", "6"),
        ("2", "1", "200", "6"),
        ("1", "2", "100", "24"),
        ("1", "0", "100", "0"),
        (None, "1", None, None),
        ("1", None, "100", None),
    ],
)
def test_yield_and_retention_independent_no_implicit_defaults(
    database, yield_factor, retention, mass, protein
):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    memory = Memory(v, (a,))
    root, *_ = transformed(memory, a, yield_factor, retention)
    result = calculate(memory, root)
    assert result.output_mass_g == (None if mass is None else D(mass))
    assert result.nutrients[1].per_100_g == (None if protein is None else D(protein))
    assert result.output_mass_state == MassState.COOKED
    assert result.stages[0].amounts == (("ENERGY_KCAL", D(120)), ("PROTEIN", D(12)))
    if mass is None or protein is None:
        assert result.status == CompositionStatus.INCOMPLETE
        assert result.issues
    else:
        assert result.status == CompositionStatus.COMPLETE


def test_sparse_retention_keeps_other_nutrient_and_diagnostic_input(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    memory = Memory(v, (a,))
    root, _, retention, _ = transformed(memory, a, "0.5", "0.5")
    memory.retentions[retention.id] = replace(
        retention, values=(RetentionValue("PROTEIN", D("0.25"), P),)
    )
    result = calculate(memory, root)
    assert result.status == CompositionStatus.PARTIAL
    assert result.nutrients[0].amount is None
    assert result.nutrients[1].amount == D(3)
    assert result.nutrients[1].per_100_g == D(6)
    assert result.stages[0].amounts[0] == ("ENERGY_KCAL", D(120))
    b = composite(
        v, [node(root, "25", state=MassState.COOKED), node(a, "25", 1)], version=2
    )
    # The sibling must be a separate untransformed immutable version.
    sibling = replace(a, id=uuid4(), version=3)
    b = replace(b, nodes=(b.nodes[0], replace(b.nodes[1], child_version_id=sibling.id)))
    memory.versions.update({b.id: b, sibling.id: sibling})
    aggregate = calculate(memory, b)
    assert aggregate.status == CompositionStatus.PARTIAL
    assert aggregate.nutrients[0].amount is None
    assert aggregate.nutrients[1].amount == D("4.5")


def test_caller_context_and_order_do_not_change_result(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    b = composite(v, [node(a, "1", 0), node(a, "2", 1)])
    memory = Memory(v, (a, b))
    b, *_ = transformed(memory, b, "1.3", "1")
    expected = calculate(memory, b)
    assert expected.nutrients[1].per_100_g == D("9.230769")
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.rounding = ROUND_DOWN
        ctx.traps[Inexact] = True
        assert calculate(memory, b) == expected
    memory.versions = dict(reversed(tuple(memory.versions.items())))
    memory.versions[b.id] = replace(b, nodes=tuple(reversed(b.nodes)))
    memory.v = replace(v, values=tuple(reversed(v.values)))
    assert calculate(memory, b, ("ENERGY_KCAL", "PROTEIN")) == expected


def test_state_continuity_and_evidence_applicability(database):
    _, engine = database
    v = vector(engine)
    a = atomic(v)
    memory = Memory(v, (a,))
    root, y, _, t = transformed(memory, a)
    memory.yields[y.id] = replace(y, input_state=MassState.DRAINED)
    with pytest.raises(CompositionUnavailableError):
        calculate(memory, root)
    memory.yields[y.id] = y
    memory.transforms[t.id] = replace(t, input_state=MassState.INPUT)
    with pytest.raises(CompositionUnavailableError):
        calculate(memory, root)
    memory.transforms[t.id] = t
    b = composite(v, [node(root, state=MassState.RAW)])
    memory.versions[b.id] = b
    with pytest.raises(CompositionUnavailableError):
        calculate(memory, b)


def test_history_profile_child_and_transformations_pinned(database):
    config, engine = database
    v = vector(engine)
    a = atomic(v)
    memory = Memory(v, (a,))
    a, y, r, t = transformed(memory, a, "0.8", "0.9")
    b = composite(v, [node(a, "80", state=MassState.COOKED)])
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        repo = uow.compositions
        repo.add_yield_model(y)
        repo.add_retention_profile(r)
        repo.add_transformation(t)
        repo.add_versions((b, a))
        uow.commit()

    def replay():
        with SqlAlchemyCompositionReadScope(engine) as read:
            return CompositionCalculator(
                read.compositions, read.nutrient_vectors
            ).calculate(b.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN"))

    expected = replay()
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as uow:
        uow.nutrition_profiles.clear_current(v.profile.food_ingredient_id)
        uow.nutrition_profiles.add(
            replace(v.profile, id=uuid4(), source_version="new-unreviewed")
        )
        uow.commit()
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        repo = uow.compositions
        y2 = replace(y, id=uuid4(), version=2, factor=D("0.2"))
        r2 = replace(
            r,
            id=uuid4(),
            version=2,
            values=tuple(replace(x, factor=D("0.1")) for x in r.values),
        )
        t2 = replace(
            t, id=uuid4(), version=2, yield_model_id=y2.id, retention_profile_id=r2.id
        )
        repo.add_yield_model(y2)
        repo.add_retention_profile(r2)
        repo.add_transformation(t2)
        repo.add_versions(
            (
                replace(
                    a,
                    id=uuid4(),
                    version=3,
                    steps=(CompositionStep(uuid4(), 0, t2.id),),
                ),
            )
        )
        uow.commit()
    assert replay() == expected
    assert snapshot_digest(replay()) == snapshot_digest(expected)
    with sqlite3.connect(config.path) as db:
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_unsealed_atomic_and_wrong_food_fail_closed(database):
    _, engine = database
    v = vector(engine)
    with SqlAlchemyFoodCatalogueUnitOfWork(engine) as uow:
        profile = replace(
            v.profile, id=uuid4(), is_current=False, source_version="unreviewed"
        )
        uow.nutrition_profiles.add(profile)
        uow.commit()
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        with pytest.raises(NutrientVectorUnavailableError):
            uow.compositions.add_versions((replace(atomic(v), profile_id=profile.id),))
        other = vector(engine, "ALMONDS_RAW")
        with pytest.raises(CompositionUnavailableError):
            uow.compositions.add_versions(
                (
                    replace(
                        atomic(v), food_ingredient_id=other.profile.food_ingredient_id
                    ),
                )
            )


def test_missing_nutrient_child_never_becomes_zero(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    other = replace(a, id=uuid4(), version=2, profile_id=uuid4())
    b = composite(v, [node(a), node(other, position=1)], version=3)
    memory = Memory(v, (a, other, b))
    sparse = replace(
        v,
        profile=replace(v.profile, id=other.profile_id),
        values=tuple(x for x in v.values if x.definition.code != "PROTEIN"),
    )

    class Vectors:
        def get(self, key):
            return v if key == a.profile_id else sparse

    result = CompositionCalculator(memory, Vectors()).calculate(
        b.id, nutrient_codes=("ENERGY_KCAL", "PROTEIN")
    )
    assert result.status == CompositionStatus.PARTIAL
    assert result.nutrients[0].amount == D(240)
    assert result.nutrients[1].amount is None


def test_deep_dag_uses_iterative_traversal(database):
    _, engine = database
    v = vector(engine)
    versions = [atomic(v)]
    for i in range(1100):
        versions.append(
            composite(
                v, [node(versions[-1], state=versions[-1].input_state)], version=i + 2
            )
        )
    assert len(load_dag(versions[-1].id, Memory(v, versions))) == 1101


def test_architecture_no_drivers_ai_future_context_or_floats():
    app = Path(__file__).parents[1]
    paths = [
        app / "domain/food_composition.py",
        *list((app / "services").glob("food_composition*.py")),
    ]
    for path in paths:
        tree = ast.parse(path.read_text())
        for item in ast.walk(tree):
            if isinstance(item, ast.ImportFrom):
                assert not (item.module or "").startswith(
                    ("sqlalchemy", "sqlite3", "app.persistence", "app.models", "openai")
                )
            if isinstance(item, ast.Import):
                assert all(
                    not x.name.startswith(("sqlalchemy", "sqlite3", "openai"))
                    for x in item.names
                )
            assert not (
                isinstance(item, ast.Constant) and isinstance(item.value, float)
            )
        assert "RecipeVersion" not in path.read_text()
    for path in (app / "persistence/sqlalchemy_core").glob("food_composition*.py"):
        assert all(
            x not in path.read_text()
            for x in (
                "sqlalchemy.orm",
                "create_all(",
                ".commit(",
                "alembic",
                "async def",
            )
        )


def published(engine):
    v = vector(engine)
    a = atomic(v)
    memory = Memory(v, (a,))
    a, y, r, t = transformed(memory, a, "0.75", "0.8")
    b = composite(
        v,
        [node(a, "0.123456789012345678901234567890123456789", state=MassState.COOKED)],
    )
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        repo = uow.compositions
        repo.add_yield_model(y)
        repo.add_retention_profile(r)
        repo.add_transformation(t)
        repo.add_versions((b, a))
        uow.commit()
    return a, b, y, r, t


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "REPLACE"])
def test_all_seven_snapshot_tables_protected(database, operation):
    config, engine = database
    published(engine)
    with sqlite3.connect(config.path) as db:
        for table in MIGRATION.TABLES:
            with pytest.raises(sqlite3.IntegrityError):
                if operation == "UPDATE":
                    col = "factor" if table == "food_retention_values" else "id"
                    db.execute(f"UPDATE {table} SET {col} = {col}")
                elif operation == "DELETE":
                    db.execute(f"DELETE FROM {table}")
                else:
                    db.execute(f"INSERT OR REPLACE INTO {table} SELECT * FROM {table}")


def test_late_inserts_and_replace_unique_identity_cannot_rewrite_history(database):
    config, engine = database
    a, b, y, r, t = published(engine)
    with sqlite3.connect(config.path) as db:
        for sql, args in (
            (
                "INSERT INTO food_retention_values VALUES (?, ?, ?, ?)",
                (r.id.hex, "CALCIUM", "1", "{}"),
            ),
            (
                "INSERT INTO food_composition_nodes VALUES (?, ?, ?, ?, ?, ?)",
                (uuid4().hex, b.id.hex, 99, a.id.hex, "1", "COOKED"),
            ),
            (
                "INSERT INTO food_composition_steps VALUES (?, ?, ?, ?)",
                (uuid4().hex, a.id.hex, 99, t.id.hex),
            ),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(sql, args)
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        with pytest.raises(IntegrityError):
            uow.compositions.add_versions((replace(a, id=uuid4(), steps=()),))


@pytest.mark.parametrize("length", [1, 2, 3])
def test_database_cycle_guard_without_repository(database, length):
    config, _ = database
    ids = [uuid4().hex for _ in range(length)]
    with sqlite3.connect(config.path) as db:
        # Unsealed fixtures intentionally have missing deferred parents until rollback.
        db.execute("PRAGMA foreign_keys=ON")
        try:
            for i in range(length - 1):
                db.execute(
                    "INSERT INTO food_composition_nodes VALUES (?, ?, ?, ?, ?, ?)",
                    (uuid4().hex, ids[i], 0, ids[i + 1], "1", "INPUT"),
                )
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(
                    "INSERT INTO food_composition_nodes VALUES (?, ?, ?, ?, ?, ?)",
                    (uuid4().hex, ids[-1], 0, ids[0], "1", "INPUT"),
                )
        finally:
            db.rollback()


def test_runtime_catches_corrupted_persisted_cycle(database):
    config, engine = database
    v = vector(engine)
    a = atomic(v, state=MassState.INPUT)
    b = composite(v, [node(a, state=MassState.INPUT)])
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_versions((a, b))
        uow.commit()
    corrupted = replace(
        a,
        kind=CompositionKind.COMPOSITE,
        profile_id=None,
        nodes=(node(b, state=MassState.INPUT),),
    )
    with sqlite3.connect(config.path) as db:
        # Simulate external corruption that bypasses both immutability and digests.
        for (name,) in db.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'food_composition_%'"
        ).fetchall():
            db.execute(f"DROP TRIGGER {name}")
        n = corrupted.nodes[0]
        db.execute(
            "INSERT INTO food_composition_nodes VALUES (?, ?, ?, ?, ?, ?)",
            (n.id.hex, a.id.hex, 0, b.id.hex, "100", "INPUT"),
        )
        db.execute(
            "UPDATE food_composition_versions SET kind='COMPOSITE', profile_id=NULL, node_count=1, snapshot_sha256=? WHERE id=?",
            (snapshot_digest(corrupted), a.id.hex),
        )
    with SqlAlchemyCompositionReadScope(engine) as read:
        with pytest.raises(CompositionUnavailableError) as error:
            CompositionCalculator(read.compositions, read.nutrient_vectors).calculate(
                b.id, nutrient_codes=("PROTEIN",)
            )
    assert error.value.issue_code == "COMPOSITION_CYCLE"


def test_filtered_composition_and_vector_reads_fail_closed(database):
    _, engine = database
    a, b, *_ = published(engine)
    for table in (tables.nodes,):

        def filtered(connection, clause, multiparams, params, options):
            if isinstance(clause, Select) and table.name in str(clause):
                clause = clause.where(table.c.id == uuid4())
            return clause, multiparams, params

        event.listen(engine, "before_execute", filtered, retval=True)
        try:
            with SqlAlchemyCompositionReadScope(engine) as read:
                with pytest.raises(CompositionUnavailableError):
                    read.compositions.get(b.id)
        finally:
            event.remove(engine, "before_execute", filtered)
    from app.persistence.sqlalchemy_core.nutrient_vector_tables import nutrient_values

    def omit_vector(connection, clause, multiparams, params, options):
        if isinstance(clause, Select) and "nutrient_values" in str(clause):
            clause = clause.where(nutrient_values.c.nutrient_code != "PROTEIN")
        return clause, multiparams, params

    event.listen(engine, "before_execute", omit_vector, retval=True)
    try:
        with SqlAlchemyCompositionReadScope(engine) as read:
            with pytest.raises(NutrientVectorUnavailableError):
                CompositionCalculator(
                    read.compositions, read.nutrient_vectors
                ).calculate(a.id, nutrient_codes=("PROTEIN",))
    finally:
        event.remove(engine, "before_execute", omit_vector)


def test_exact_decimal_roundtrip_and_uncommitted_uow_rollback(database):
    config, engine = database
    v = vector(engine)
    a = atomic(v)
    mass = D("0.123456789012345678901234567890123456789")
    b = composite(v, [node(a, str(mass))])
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_versions((b, a))
        assert uow.compositions.get(b.id).nodes[0].input_mass_g == mass
        with SqlAlchemyCompositionReadScope(engine) as read:
            with pytest.raises(CompositionUnavailableError):
                read.compositions.get(b.id)
    with sqlite3.connect(config.path) as db:
        assert (
            db.execute("SELECT count(*) FROM food_composition_versions").fetchone()[0]
            == 0
        )
        assert (
            db.execute("SELECT count(*) FROM food_composition_nodes").fetchone()[0] == 0
        )
        db.execute("PRAGMA foreign_keys=ON")
        db.execute(
            "INSERT INTO food_composition_nodes VALUES (?, ?, ?, ?, ?, ?)",
            (uuid4().hex, b.id.hex, 0, a.id.hex, "1", "RAW"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.commit()
        db.rollback()


@pytest.mark.parametrize("bad", [D("-1"), D("NaN"), D("Infinity"), 0.5])
def test_invalid_retention_factors(bad):
    with pytest.raises((TypeError, ValueError)):
        RetentionValue("PROTEIN", bad, P)


def test_retention_uses_canonical_registry_and_all_states_explicit(database):
    _, engine = database
    assert {"RAW", "INPUT", "DRAINED", "COOKED", "YIELDED"} <= {
        s.value for s in MassState
    }
    r = NutrientRetentionProfile(
        uuid4(),
        1,
        MassState.INPUT,
        MassState.DRAINED,
        P,
        (RetentionValue("INVENTED_NUTRIENT", D(1), P),),
    )
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        with pytest.raises(CompositionUnavailableError):
            uow.compositions.add_retention_profile(r)
    with pytest.raises(ValueError):
        replace(r, values=(r.values[0], r.values[0]))


def test_persisted_insertion_order_and_vector_integrity(database, tmp_path):
    config, engine = database
    from scripts.audit_pr6_nutrient_vector_b import snapshot

    before = snapshot(config)
    v = vector(engine)
    a = atomic(v)
    b = composite(v, [node(a, "1"), node(a, "2", 1)])
    copy = DatabaseConfig(path=tmp_path / "opposite.sqlite")
    shutil.copyfile(config.path, copy.path)
    other_engine = create_sqlite_engine(copy)
    results = []
    try:
        for e, values in ((engine, (a, b)), (other_engine, (b, a))):
            with SqlAlchemyCompositionUnitOfWork(e) as uow:
                uow.compositions.add_versions(values)
                uow.commit()
            if e is other_engine:
                with sqlite3.connect(copy.path) as db:
                    trigger_rows = db.execute(
                        "SELECT name,sql FROM sqlite_master WHERE type='trigger' AND name IN ('food_composition_nodes_no_delete','food_composition_nodes_no_late_insert')"
                    ).fetchall()
                    for name, _ in trigger_rows:
                        db.execute(f"DROP TRIGGER {name}")
                    physical = db.execute(
                        "SELECT * FROM food_composition_nodes ORDER BY position DESC"
                    ).fetchall()
                    db.execute("DELETE FROM food_composition_nodes")
                    db.executemany(
                        "INSERT INTO food_composition_nodes VALUES (?,?,?,?,?,?)",
                        physical,
                    )
                    for _, sql in trigger_rows:
                        db.execute(sql)
                    assert db.execute(
                        "SELECT position FROM food_composition_nodes ORDER BY rowid"
                    ).fetchall() == [(1,), (0,)]
            with SqlAlchemyCompositionReadScope(e) as read:
                results.append(
                    CompositionCalculator(
                        read.compositions, read.nutrient_vectors
                    ).calculate(b.id, nutrient_codes=("PROTEIN",))
                )
        assert results[0] == results[1]
    finally:
        other_engine.dispose()
    after = snapshot(config)
    assert all(
        after[name] == rows
        for name, rows in before.items()
        if name not in MIGRATION.TABLES
    )
    assert vector(engine) == v


def test_mass_and_retention_chained_steps_keep_explicit_states(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    memory = Memory(v, (a,))
    root, *_ = transformed(memory, a, "0.5", "0.8", output=MassState.DRAINED)
    y = YieldModel(uuid4(), 1, D("2"), MassState.DRAINED, MassState.COOKED, P)
    r = NutrientRetentionProfile(
        uuid4(),
        1,
        MassState.DRAINED,
        MassState.COOKED,
        P,
        tuple(RetentionValue(c, D("0.5"), P) for c in memory.definitions),
    )
    t = FoodTransformation(
        uuid4(), 1, "TEST_COOK", MassState.DRAINED, MassState.COOKED, P, y.id, r.id
    )
    memory.yields[y.id] = y
    memory.retentions[r.id] = r
    memory.transforms[t.id] = t
    root = replace(root, steps=root.steps + (CompositionStep(uuid4(), 1, t.id),))
    memory.versions[root.id] = root
    result = calculate(memory, root)
    assert result.output_mass_g == D(100)
    assert result.nutrients[1].amount == D("4.8")
    assert tuple(s.mass_state for s in result.stages) == (
        MassState.RAW,
        MassState.DRAINED,
        MassState.COOKED,
    )


def test_valid_empty_sealed_vector_is_incomplete_without_invented_zero(database):
    _, engine = database
    v = vector(engine, "SALT")
    assert v.values == ()
    a = atomic(v)
    with SqlAlchemyCompositionUnitOfWork(engine) as uow:
        uow.compositions.add_versions((a,))
        uow.commit()
    with SqlAlchemyCompositionReadScope(engine) as read:
        result = CompositionCalculator(
            read.compositions, read.nutrient_vectors
        ).calculate(a.id, nutrient_codes=("PROTEIN",))
    assert result.status == CompositionStatus.INCOMPLETE
    assert result.nutrients[0].amount is None
    assert result.atomic_evidence[0].values == ()


def test_incompatible_nutrient_definition_fails_closed(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    memory = Memory(v, (a,))
    memory.definitions["PROTEIN"] = replace(memory.definitions["PROTEIN"], unit="mg")
    with pytest.raises(CompositionUnavailableError) as error:
        calculate(memory, a)
    assert error.value.issue_code == "NUTRIENT_DEFINITION_MISMATCH"


def test_unknown_yield_in_child_cannot_be_used_as_unit_mass(database):
    _, engine = database
    v = synthetic(vector(engine))
    a = atomic(v)
    memory = Memory(v, (a,))
    root, *_ = transformed(memory, a, None, "1")
    b = composite(v, [node(root, "50", state=MassState.COOKED)])
    memory.versions[b.id] = b
    result = calculate(memory, b)
    assert result.output_mass_g == D(50)  # Explicit new input, no inferred child yield.
    assert result.status == CompositionStatus.INCOMPLETE
    assert all(n.amount is None for n in result.nutrients)
    assert any(i.code == "YIELD_UNAVAILABLE" for i in result.issues)


def test_public_ports_are_driver_independent_context_managers(database):
    from app.services.food_composition_contracts import (
        CompositionReadScope,
        CompositionUnitOfWork,
    )

    _, engine = database
    reader: CompositionReadScope = SqlAlchemyCompositionReadScope(engine)
    writer: CompositionUnitOfWork = SqlAlchemyCompositionUnitOfWork(engine)
    with reader as read:
        assert read.compositions.nutrient_definition("PROTEIN").unit == "g"
    with writer as write:
        write.rollback()


@pytest.mark.parametrize(
    "table,column,method",
    [
        ("food_composition_nodes", "input_mass_g", "composition"),
        ("food_retention_values", "factor", "retention"),
    ],
)
def test_corrupt_value_with_unchanged_count_fails_digest(
    database, table, column, method
):
    config, engine = database
    _, b, _, retention, _ = published(engine)
    with sqlite3.connect(config.path) as db:
        db.execute(f"DROP TRIGGER {table}_no_update")
        db.execute(f"UPDATE {table} SET {column} = '999'")
    with SqlAlchemyCompositionReadScope(engine) as read:
        with pytest.raises(CompositionUnavailableError) as error:
            if method == "composition":
                read.compositions.get(b.id)
            else:
                read.compositions.retention_profile(retention.id)
    assert error.value.issue_code == "COMPOSITION_SNAPSHOT_CORRUPT"
