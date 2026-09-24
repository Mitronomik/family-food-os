"""Append-only snapshots on the existing UoW connection; never commits."""

from dataclasses import asdict
import json
from typing import Any
from uuid import UUID

from sqlalchemy import Table, column, insert, select, table
from sqlalchemy.engine import Connection

from app.domain.food_composition import (
    CompositionNode,
    CompositionProvenance,
    CompositionStep,
    CompositionUnavailableError,
    FoodCompositionVersion,
    FoodTransformation,
    NutrientRetentionProfile,
    RetentionValue,
    TransformationApplicability,
    YieldModel,
    snapshot_digest,
    snapshot_json,
)
from app.domain.nutrient_vector import (
    V2_REGISTRY_VERSION,
    NutrientDefinition,
)
from app.domain.nutrient_vector_backfill_v1 import REGISTRY_VERSION as REGISTRY_V1
from app.persistence.sqlalchemy_core import food_composition_tables as t
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_ingredients_table,
)
from app.persistence.sqlalchemy_core.nutrient_vector_repository import (
    SqlAlchemyNutrientRegistryRepository,
    SqlAlchemyNutrientVectorRepository,
)
from app.persistence.sqlalchemy_core.nutrient_vector_tables import nutrient_definitions
from app.services.food_composition import load_dag, transformation_chain


def _versioned_registry_schema_available(connection: Connection) -> bool:
    migrations = table("schema_migrations", column("migration_id"))
    return (
        connection.execute(
            select(migrations.c.migration_id).where(
                migrations.c.migration_id == "0035_versioned_nutrient_registry"
            )
        ).first()
        is not None
    )


class SqlAlchemyFoodCompositionRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection
        self._pending: dict[UUID, FoodCompositionVersion] = {}

    def _row(self, table: Table, key: UUID) -> dict[str, Any]:
        row = (
            self._connection.execute(select(table).where(table.c.id == key))
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise CompositionUnavailableError("COMPOSITION_DEPENDENCY_MISSING")
        return dict(row)

    def _common(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "version": row["version"],
            "input_state": row["input_state"],
            "provenance": CompositionProvenance(**json.loads(row["provenance_json"])),
        }

    def _verify(self, value: Any, row: dict[str, Any]) -> Any:
        if snapshot_digest(value) != row["snapshot_sha256"]:
            raise CompositionUnavailableError("COMPOSITION_SNAPSHOT_CORRUPT")
        return value

    def get(self, version_id: UUID) -> FoodCompositionVersion:
        if version_id in self._pending:
            return self._pending[version_id]
        row = self._row(t.versions, version_id)
        children = (
            self._connection.execute(
                select(t.nodes).where(t.nodes.c.composition_id == version_id)
            )
            .mappings()
            .all()
        )
        processes = (
            self._connection.execute(
                select(t.steps).where(t.steps.c.composition_id == version_id)
            )
            .mappings()
            .all()
        )
        if len(children) != row["node_count"] or len(processes) != row["step_count"]:
            raise CompositionUnavailableError("COMPOSITION_SNAPSHOT_INCOMPLETE")
        value = FoodCompositionVersion(
            **self._common(row),
            food_ingredient_id=row["food_ingredient_id"],
            kind=row["kind"],
            profile_id=row["profile_id"],
            nodes=tuple(
                CompositionNode(**{k: v for k, v in n.items() if k != "composition_id"})
                for n in children
            ),
            steps=tuple(
                CompositionStep(**{k: v for k, v in s.items() if k != "composition_id"})
                for s in processes
            ),
        )
        return self._verify(value, row)

    def yield_model(self, version_id: UUID) -> YieldModel:
        row = self._row(t.yield_models, version_id)
        value = YieldModel(
            **self._common(row), factor=row["factor"], output_state=row["output_state"]
        )
        return self._verify(value, row)

    def retention_profile(self, version_id: UUID) -> NutrientRetentionProfile:
        row = self._row(t.retention_profiles, version_id)
        if _versioned_registry_schema_available(self._connection):
            statement = select(t.retention_values).where(
                t.retention_values.c.profile_id == version_id
            )
        else:
            statement = select(
                t.retention_values.c.profile_id,
                t.retention_values.c.nutrient_code,
                t.retention_values.c.factor,
                t.retention_values.c.provenance_json,
            ).where(t.retention_values.c.profile_id == version_id)
        values = self._connection.execute(statement).mappings().all()
        if len(values) != row["value_count"]:
            raise CompositionUnavailableError("RETENTION_SNAPSHOT_INCOMPLETE")
        value = NutrientRetentionProfile(
            **self._common(row),
            output_state=row["output_state"],
            values=tuple(
                RetentionValue(
                    v["nutrient_code"],
                    v["factor"],
                    CompositionProvenance(**json.loads(v["provenance_json"])),
                )
                for v in values
            ),
        )
        return self._verify(value, row)

    def transformation(self, version_id: UUID) -> FoodTransformation:
        row = self._row(t.transformations, version_id)
        value = FoodTransformation(
            **self._common(row),
            output_state=row["output_state"],
            transformation_type=row["transformation_type"],
            yield_model_id=row["yield_model_id"],
            retention_profile_id=row["retention_profile_id"],
        )
        return self._verify(value, row)

    def applicability(self, transformation_id: UUID) -> TransformationApplicability:
        row = (
            self._connection.execute(
                select(t.applicability).where(
                    t.applicability.c.transformation_id == transformation_id
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise CompositionUnavailableError("TRANSFORMATION_APPLICABILITY_MISSING")
        value = TransformationApplicability(
            transformation_id=row["transformation_id"],
            food_ingredient_id=row["food_ingredient_id"],
            retention_registry_version=row["retention_registry_version"],
            season_scope=row["season_scope"],
            season_reference=row["season_reference"],
            evidence_scope_id=row["evidence_scope_id"],
            provenance=CompositionProvenance(**json.loads(row["provenance_json"])),
        )
        return self._verify(value, row)

    def retention_profile_for_registry(
        self, version_id: UUID, registry_version: str
    ) -> NutrientRetentionProfile:
        if registry_version != V2_REGISTRY_VERSION:
            raise CompositionUnavailableError("RETENTION_REGISTRY_UNSUPPORTED")
        value = self.retention_profile(version_id)
        rows = (
            self._connection.execute(
                select(t.retention_values.c.registry_version).where(
                    t.retention_values.c.profile_id == version_id
                )
            )
            .scalars()
            .all()
        )
        if len(rows) != len(value.values) or any(
            row != registry_version for row in rows
        ):
            raise CompositionUnavailableError("RETENTION_REGISTRY_MISMATCH")
        return value

    def nutrient_definition(self, code: str) -> NutrientDefinition:
        row = (
            self._connection.execute(
                select(nutrient_definitions).where(
                    nutrient_definitions.c.registry_version == REGISTRY_V1,
                    nutrient_definitions.c.code == code,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise CompositionUnavailableError("NUTRIENT_DEFINITION_MISSING")
        payload = json.loads(row["definition_json"])
        return NutrientDefinition(
            row["code"],
            row["display_name_ru"],
            row["unit"],
            row["registry_version"],
            payload.get("definition"),
            payload.get("definition_kind"),
        )

    def _record(self, value: Any) -> dict[str, Any]:
        result = asdict(value)
        result["provenance_json"] = snapshot_json(value.provenance)
        del result["provenance"]
        result["snapshot_sha256"] = snapshot_digest(value)
        return result

    def add_yield_model(self, value: YieldModel) -> None:
        self._connection.execute(insert(t.yield_models).values(**self._record(value)))

    def add_retention_profile(self, value: NutrientRetentionProfile) -> None:
        for factor in value.values:
            self.nutrient_definition(factor.nutrient_code)
        profile_row = self._record(value)
        del profile_row["values"]
        for factor in value.values:
            value_row = {
                "profile_id": value.id,
                "nutrient_code": factor.nutrient_code,
                "factor": factor.factor,
                "provenance_json": snapshot_json(factor.provenance),
            }
            if _versioned_registry_schema_available(self._connection):
                value_row["registry_version"] = REGISTRY_V1
            self._connection.execute(
                insert(t.retention_values).values(**value_row)
            )
        self._connection.execute(
            insert(t.retention_profiles).values(
                **profile_row, value_count=len(value.values)
            )
        )

    def add_retention_profile_for_registry(
        self, value: NutrientRetentionProfile, registry_version: str
    ) -> None:
        if registry_version != V2_REGISTRY_VERSION:
            raise CompositionUnavailableError("RETENTION_REGISTRY_UNSUPPORTED")
        registry = SqlAlchemyNutrientRegistryRepository(self._connection)
        for factor in value.values:
            registry.get(registry_version, factor.nutrient_code)
        profile_row = self._record(value)
        del profile_row["values"]
        for factor in value.values:
            self._connection.execute(
                insert(t.retention_values).values(
                    profile_id=value.id,
                    registry_version=registry_version,
                    nutrient_code=factor.nutrient_code,
                    factor=factor.factor,
                    provenance_json=snapshot_json(factor.provenance),
                )
            )
        self._connection.execute(
            insert(t.retention_profiles).values(
                **profile_row, value_count=len(value.values)
            )
        )

    def add_transformation(self, value: FoodTransformation) -> None:
        for key, resolve in (
            (value.yield_model_id, self.yield_model),
            (value.retention_profile_id, self.retention_profile),
        ):
            if key is not None:
                evidence = resolve(key)
                if (evidence.input_state, evidence.output_state) != (
                    value.input_state,
                    value.output_state,
                ):
                    raise CompositionUnavailableError(
                        "TRANSFORMATION_EVIDENCE_MISMATCH"
                    )
        self._connection.execute(
            insert(t.transformations).values(**self._record(value))
        )

    def add_applicability(self, value: TransformationApplicability) -> None:
        transformation = self.transformation(value.transformation_id)
        if (
            self._connection.execute(
                select(food_ingredients_table.c.id).where(
                    food_ingredients_table.c.id == value.food_ingredient_id
                )
            ).first()
            is None
        ):
            raise CompositionUnavailableError("FOOD_INGREDIENT_MISSING")
        if (
            self._connection.execute(
                select(t.steps.c.id).where(
                    t.steps.c.transformation_id == value.transformation_id
                )
            ).first()
            is not None
        ):
            raise CompositionUnavailableError("TRANSFORMATION_APPLICABILITY_LATE")
        if transformation.retention_profile_id is None:
            if value.retention_registry_version is not None:
                raise CompositionUnavailableError("RETENTION_REGISTRY_MISMATCH")
        else:
            if value.retention_registry_version != V2_REGISTRY_VERSION:
                raise CompositionUnavailableError("RETENTION_REGISTRY_MISMATCH")
            self.retention_profile_for_registry(
                transformation.retention_profile_id,
                value.retention_registry_version,
            )
        row = asdict(value)
        row["provenance_json"] = snapshot_json(value.provenance)
        del row["provenance"]
        row["snapshot_sha256"] = snapshot_digest(value)
        self._connection.execute(insert(t.applicability).values(**row))

    def _validate_versions_for_registry(
        self,
        versions: tuple[FoodCompositionVersion, ...],
        registry_version: str,
    ) -> None:
        if registry_version != V2_REGISTRY_VERSION:
            raise CompositionUnavailableError("NUTRIENT_REGISTRY_UNSUPPORTED")
        pending = {value.id: value for value in versions}
        if len(pending) != len(versions):
            raise ValueError("Версия состава повторяется.")
        overlay = SqlAlchemyFoodCompositionRepository(self._connection)
        overlay._pending = pending
        vector_reader = SqlAlchemyNutrientVectorRepository(self._connection)
        for requested_root in versions:
            graph = load_dag(requested_root.id, overlay)
            for composition in graph:
                if composition.profile_id is not None:
                    vector = vector_reader.get(composition.profile_id)
                    if vector.registry_version != registry_version:
                        raise CompositionUnavailableError(
                            "NUTRIENT_REGISTRY_MISMATCH"
                        )
                state = composition.input_state
                evidence_scopes: set[str] = set()
                for step in composition.steps:
                    transformation = overlay.transformation(step.transformation_id)
                    if (
                        transformation.id != step.transformation_id
                        or transformation.input_state != state
                    ):
                        raise CompositionUnavailableError(
                            "MASS_STATE_DISCONTINUITY"
                        )
                    applicability = overlay.applicability(transformation.id)
                    if (
                        applicability.food_ingredient_id
                        != composition.food_ingredient_id
                    ):
                        raise CompositionUnavailableError(
                            "TRANSFORMATION_APPLICABILITY_FOOD_MISMATCH"
                        )
                    if applicability.evidence_scope_id in evidence_scopes:
                        raise CompositionUnavailableError(
                            "TRANSFORMATION_EVIDENCE_SCOPE_OVERLAP"
                        )
                    evidence_scopes.add(applicability.evidence_scope_id)
                    if transformation.yield_model_id is not None:
                        model = overlay.yield_model(transformation.yield_model_id)
                        if (model.input_state, model.output_state) != (
                            transformation.input_state,
                            transformation.output_state,
                        ):
                            raise CompositionUnavailableError(
                                "TRANSFORMATION_EVIDENCE_MISMATCH"
                            )
                    if transformation.retention_profile_id is None:
                        if applicability.retention_registry_version is not None:
                            raise CompositionUnavailableError(
                                "RETENTION_REGISTRY_MISMATCH"
                            )
                    else:
                        if (
                            applicability.retention_registry_version
                            != registry_version
                        ):
                            raise CompositionUnavailableError(
                                "RETENTION_REGISTRY_MISMATCH"
                            )
                        profile = overlay.retention_profile_for_registry(
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
                    state = transformation.output_state

    def add_versions_for_registry(
        self,
        versions: tuple[FoodCompositionVersion, ...],
        registry_version: str,
    ) -> None:
        self._validate_versions_for_registry(versions, registry_version)
        self.add_versions(versions)

    def add_versions(self, versions: tuple[FoodCompositionVersion, ...]) -> None:
        """Validate the entire pending graph before publishing any snapshot.

        Any persistence failure must abort the enclosing UoW, as for other project
        repositories. Deferred FKs and seal-last insertion prevent half snapshots.
        """
        pending = {v.id: v for v in versions}
        if len(pending) != len(versions) or len(
            {(v.food_ingredient_id, v.version) for v in versions}
        ) != len(versions):
            raise ValueError("Версия состава повторяется.")
        overlay = SqlAlchemyFoodCompositionRepository(self._connection)
        overlay._pending = pending
        for value in versions:
            if (
                self._connection.execute(
                    select(t.versions.c.id).where(t.versions.c.id == value.id)
                ).first()
                is not None
            ):
                raise ValueError("Версия состава уже существует.")
            if (
                self._connection.execute(
                    select(food_ingredients_table.c.id).where(
                        food_ingredients_table.c.id == value.food_ingredient_id
                    )
                ).first()
                is None
            ):
                raise CompositionUnavailableError("FOOD_INGREDIENT_MISSING")
            graph = load_dag(value.id, overlay)
            states = {}
            for dependency in graph:
                chain = transformation_chain(dependency, overlay)
                states[dependency.id] = (
                    chain[-1].output_state if chain else dependency.input_state
                )
                for node in dependency.nodes:
                    if node.mass_state != states[node.child_version_id]:
                        raise CompositionUnavailableError("NODE_MASS_STATE_MISMATCH")
                if dependency.profile_id is not None:
                    vector = SqlAlchemyNutrientVectorRepository(self._connection).get(
                        dependency.profile_id
                    )
                    if (
                        vector.profile.food_ingredient_id
                        != dependency.food_ingredient_id
                    ):
                        raise CompositionUnavailableError("ATOMIC_PROFILE_MISMATCH")
        for value in sorted(versions, key=lambda v: str(v.id)):
            for node in value.nodes:
                self._connection.execute(
                    insert(t.nodes).values(**asdict(node), composition_id=value.id)
                )
            for step in value.steps:
                self._connection.execute(
                    insert(t.steps).values(**asdict(step), composition_id=value.id)
                )
            row = self._record(value)
            del row["nodes"], row["steps"]
            self._connection.execute(
                insert(t.versions).values(
                    **row, node_count=len(value.nodes), step_count=len(value.steps)
                )
            )
