"""Complete vector reads on the existing project read transaction."""

from dataclasses import asdict
from decimal import Decimal
from functools import lru_cache
import hashlib
import json
from uuid import UUID

from sqlalchemy import and_, column, insert, select, table
from sqlalchemy.engine import Connection

from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.nutrient_vector import (
    NutrientDefinition,
    NutrientProvenance,
    NutrientValue,
    NutrientVector,
    NutrientVectorUnavailableError,
)
from app.domain.nutrient_vector_backfill_v1 import (
    REGISTRY_VERSION,
    prepare_profile,
    value_set_digest,
)
from app.persistence.sqlalchemy_core.food_ingredient_tables import (
    food_ingredients_table,
)
from app.persistence.sqlalchemy_core.nutrient_vector_tables import (
    nutrient_definitions,
    nutrient_values,
    registry_snapshots,
    vector_seals,
)


@lru_cache(maxsize=1)
def _verified_bundle(encoded: str, expected_hash: str) -> dict:
    if hashlib.sha256(encoded.encode()).hexdigest() != expected_hash:
        raise ValueError("Нарушена целостность снимка реестра нутриентов.")
    return json.loads(encoded)


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


def initialize_audited_profile(
    connection: Connection, profile: FoodNutritionProfile
) -> None:
    """Only called while initially inserting a profile, in the same write UoW.

    No append/enrich API exists. Unreviewed new v1 profiles remain explicitly
    unavailable to vector readers. Pre-0028 callers retain their v1 behavior.
    """
    migrations = table("schema_migrations", column("migration_id"))
    if (
        connection.execute(
            select(migrations.c.migration_id).where(
                migrations.c.migration_id == "0028_normalized_nutrient_vector"
            )
        ).first()
        is None
    ):
        return
    snapshot = (
        connection.execute(
            select(registry_snapshots).where(
                registry_snapshots.c.version == REGISTRY_VERSION
            )
        )
        .mappings()
        .one()
    )
    bundle = _verified_bundle(snapshot["bundle_json"], snapshot["bundle_sha256"])
    food_code = connection.execute(
        select(food_ingredients_table.c.canonical_code).where(
            food_ingredients_table.c.id == profile.food_ingredient_id
        )
    ).scalar_one()
    prepared = prepare_profile(asdict(profile), food_code, bundle)
    if prepared is None:
        return
    values, observations = prepared
    if values:
        versioned = _versioned_registry_schema_available(connection)
        rows = []
        for value in values:
            row = dict(value, profile_id=profile.id)
            if versioned:
                row["registry_version"] = REGISTRY_VERSION
            rows.append(row)
        connection.execute(insert(nutrient_values), rows)
    connection.execute(
        insert(vector_seals).values(
            profile_id=profile.id,
            registry_version=REGISTRY_VERSION,
            value_count=len(values),
            value_sha256=value_set_digest(values),
            observations_json=observations,
        )
    )


def _definition_from_row(row) -> NutrientDefinition:
    payload = json.loads(row["definition_json"])
    return NutrientDefinition(
        row["code"],
        row["display_name_ru"],
        row["unit"],
        row["registry_version"],
        payload.get("definition"),
        payload.get("definition_kind"),
    )


class SqlAlchemyNutrientRegistryRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def get(self, registry_version: str, code: str) -> NutrientDefinition:
        row = (
            self._connection.execute(
                select(nutrient_definitions).where(
                    nutrient_definitions.c.registry_version == registry_version,
                    nutrient_definitions.c.code == code,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise NutrientVectorUnavailableError(
                "Определение нутриента для версии реестра недоступно."
            )
        return _definition_from_row(row)


class SqlAlchemyNutrientVectorRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def get(self, profile_id: UUID) -> NutrientVector:
        # Local import avoids coupling the profile write adapter to this reader.
        from app.persistence.sqlalchemy_core.food_ingredient_repositories import (
            SqlAlchemyFoodNutritionProfileRepository,
        )

        profile = SqlAlchemyFoodNutritionProfileRepository(
            self._connection
        ).get_nutrition_profile_by_id(profile_id)
        seal = (
            self._connection.execute(
                select(vector_seals).where(vector_seals.c.profile_id == profile_id)
            )
            .mappings()
            .one_or_none()
        )
        if profile is None or seal is None:
            raise NutrientVectorUnavailableError(
                "Полный проверенный набор нутриентов недоступен."
            )
        if _versioned_registry_schema_available(self._connection):
            statement = (
                select(nutrient_values, nutrient_definitions)
                .select_from(
                    nutrient_values.join(
                        nutrient_definitions,
                        and_(
                            nutrient_values.c.registry_version
                            == nutrient_definitions.c.registry_version,
                            nutrient_values.c.nutrient_code
                            == nutrient_definitions.c.code,
                        ),
                    )
                )
                .where(
                    nutrient_values.c.profile_id == profile_id,
                    nutrient_values.c.registry_version == seal["registry_version"],
                )
                .order_by(nutrient_values.c.nutrient_code)
            )
        else:
            statement = (
                select(
                    nutrient_values.c.profile_id,
                    nutrient_values.c.nutrient_code,
                    nutrient_values.c.amount,
                    nutrient_values.c.provenance_json,
                    nutrient_definitions,
                )
                .select_from(
                    nutrient_values.join(
                        nutrient_definitions,
                        nutrient_values.c.nutrient_code == nutrient_definitions.c.code,
                    )
                )
                .where(nutrient_values.c.profile_id == profile_id)
                .order_by(nutrient_values.c.nutrient_code)
            )
        rows = list(self._connection.execute(statement).mappings())
        if (
            len(rows) != seal["value_count"]
            or value_set_digest([dict(row) for row in rows]) != seal["value_sha256"]
        ):
            raise NutrientVectorUnavailableError(
                "Набор нутриентов неполон или повреждён."
            )
        values = []
        for row in rows:
            evidence = json.loads(row["provenance_json"])
            observation, mapping = evidence["observation"], evidence["mapping"]
            if row["registry_version"] != seal["registry_version"]:
                raise NutrientVectorUnavailableError(
                    "Определение нутриента не соответствует версии снимка."
                )
            values.append(
                NutrientValue(
                    definition=_definition_from_row(row),
                    amount=row["amount"],
                    provenance=NutrientProvenance(
                        registry_version=seal["registry_version"],
                        audit_identity=observation["audit_identity"],
                        source_name=observation["profile_source_name"],
                        source_food_id=observation["profile_source_id"],
                        source_release=observation["profile_source_version"],
                        source_data_type=observation["profile_source_data_type"],
                        source_nutrient_id=observation["source_nutrient_id"],
                        source_nutrient_name=observation["source_nutrient_name"],
                        source_nutrient_nbr=mapping["source_nutrient_nbr"],
                        source_unit=observation["source_unit"],
                        source_amount=Decimal(observation["source_value"]),
                        source_observation_id=observation["source_food_nutrient_id"],
                        source_derivation_id=observation["source_derivation_id"],
                        mapping_status=mapping["mapping_status"],
                        estimated=profile.estimated,
                        evidence_json=row["provenance_json"],
                    ),
                )
            )
        return NutrientVector(
            profile, seal["registry_version"], tuple(values), seal["observations_json"]
        )
