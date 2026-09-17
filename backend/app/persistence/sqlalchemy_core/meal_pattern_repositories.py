"""SQLAlchemy Core repositories for the Meal Pattern Catalogue."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, insert, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.domain.meal_patterns import (
    MealPatternEvidence,
    MealPatternOpportunity,
    MealPatternProgram,
    MealPatternProgramDetail,
    MealPatternProgramVersion,
    MealPatternTag,
)
from app.persistence.sqlalchemy_core.meal_pattern_tables import (
    meal_pattern_evidence_table,
    meal_pattern_opportunities_table,
    meal_pattern_program_versions_table,
    meal_pattern_programs_table,
    meal_pattern_tags_table,
)
from app.services.meal_pattern_contracts import (
    MealPatternPersistenceConflictError,
    MealPatternPersistenceError,
)


class SqlAlchemyMealPatternProgramRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add(self, program: MealPatternProgram) -> None:
        try:
            self._connection.execute(
                insert(meal_pattern_programs_table).values(
                    id=program.id,
                    program_code=program.code,
                    created_at=program.created_at,
                )
            )
        except IntegrityError as exc:
            raise MealPatternPersistenceConflictError(
                "MealPatternProgram identity or code conflicts."
            ) from exc
        except DBAPIError as exc:
            raise MealPatternPersistenceError(
                "MealPatternProgram persistence failed."
            ) from exc

    def get(self, program_id: UUID) -> MealPatternProgram | None:
        row = (
            self._connection.execute(
                select(meal_pattern_programs_table).where(
                    meal_pattern_programs_table.c.id == program_id
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _program_from_row(row)

    def get_by_code(self, code: str) -> MealPatternProgram | None:
        row = (
            self._connection.execute(
                select(meal_pattern_programs_table).where(
                    meal_pattern_programs_table.c.program_code == code
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else _program_from_row(row)


class SqlAlchemyMealPatternVersionRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def add_detail(self, detail: MealPatternProgramDetail) -> None:
        previous_id = detail.version.created_from_version_id
        if previous_id is not None:
            previous_program = self._connection.scalar(
                select(meal_pattern_program_versions_table.c.program_id).where(
                    meal_pattern_program_versions_table.c.id == previous_id
                )
            )
            if previous_program != detail.program.id:
                raise MealPatternPersistenceConflictError(
                    "created_from_version_id must reference the same MealPatternProgram."
                )
        try:
            self._connection.execute(
                insert(meal_pattern_program_versions_table).values(
                    **_version_values(detail.version)
                )
            )
            if detail.opportunities:
                self._connection.execute(
                    insert(meal_pattern_opportunities_table),
                    [_opportunity_values(item) for item in detail.opportunities],
                )
            if detail.tags:
                self._connection.execute(
                    insert(meal_pattern_tags_table),
                    [_tag_values(item) for item in detail.tags],
                )
            if detail.evidence:
                self._connection.execute(
                    insert(meal_pattern_evidence_table),
                    [_evidence_values(item) for item in detail.evidence],
                )
        except IntegrityError as exc:
            raise MealPatternPersistenceConflictError(
                "MealPatternProgramVersion identity, order, or reference conflicts."
            ) from exc
        except DBAPIError as exc:
            raise MealPatternPersistenceError(
                "MealPatternProgramVersion aggregate persistence failed."
            ) from exc

    def get_detail(self, version_id: UUID) -> MealPatternProgramDetail | None:
        row = (
            self._connection.execute(
                select(meal_pattern_program_versions_table).where(
                    meal_pattern_program_versions_table.c.id == version_id
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._detail_from_row(row)

    def get_by_number(
        self, program_id: UUID, version_number: int
    ) -> MealPatternProgramDetail | None:
        row = (
            self._connection.execute(
                select(meal_pattern_program_versions_table).where(
                    meal_pattern_program_versions_table.c.program_id == program_id,
                    meal_pattern_program_versions_table.c.version_number
                    == version_number,
                )
            )
            .mappings()
            .one_or_none()
        )
        return None if row is None else self._detail_from_row(row)

    def list_for_program(self, program_id: UUID) -> list[MealPatternProgramVersion]:
        rows = self._connection.execute(
            select(meal_pattern_program_versions_table)
            .where(meal_pattern_program_versions_table.c.program_id == program_id)
            .order_by(meal_pattern_program_versions_table.c.version_number)
        ).mappings()
        return [_version_from_row(row) for row in rows]

    def get_current_published(
        self, program_id: UUID
    ) -> MealPatternProgramDetail | None:
        row = (
            self._connection.execute(
                select(meal_pattern_program_versions_table)
                .where(
                    meal_pattern_program_versions_table.c.program_id == program_id
                )
                .order_by(meal_pattern_program_versions_table.c.version_number.desc())
                .limit(1)
            )
            .mappings()
            .one_or_none()
        )
        if row is None or row["lifecycle"] != "PUBLISHED":
            return None
        return self._detail_from_row(row)

    def list_current_published(self) -> list[MealPatternProgramDetail]:
        latest = (
            select(
                meal_pattern_program_versions_table.c.program_id.label("program_id"),
                func.max(meal_pattern_program_versions_table.c.version_number).label(
                    "max_version"
                ),
            )
            .group_by(meal_pattern_program_versions_table.c.program_id)
            .subquery()
        )
        rows = self._connection.execute(
            select(meal_pattern_program_versions_table)
            .join(
                latest,
                and_(
                    meal_pattern_program_versions_table.c.program_id
                    == latest.c.program_id,
                    meal_pattern_program_versions_table.c.version_number
                    == latest.c.max_version,
                ),
            )
            .where(meal_pattern_program_versions_table.c.lifecycle == "PUBLISHED")
            .order_by(meal_pattern_program_versions_table.c.program_id)
        ).mappings()
        return [self._detail_from_row(row) for row in rows]

    def _detail_from_row(
        self, version_row: Mapping[str, Any]
    ) -> MealPatternProgramDetail:
        program_row = (
            self._connection.execute(
                select(meal_pattern_programs_table).where(
                    meal_pattern_programs_table.c.id == version_row["program_id"]
                )
            )
            .mappings()
            .one()
        )
        version_id = version_row["id"]
        opportunities = self._connection.execute(
            select(meal_pattern_opportunities_table)
            .where(meal_pattern_opportunities_table.c.version_id == version_id)
            .order_by(meal_pattern_opportunities_table.c.position)
        ).mappings()
        tags = self._connection.execute(
            select(meal_pattern_tags_table)
            .where(meal_pattern_tags_table.c.version_id == version_id)
            .order_by(meal_pattern_tags_table.c.kind, meal_pattern_tags_table.c.code)
        ).mappings()
        evidence = self._connection.execute(
            select(meal_pattern_evidence_table)
            .where(meal_pattern_evidence_table.c.version_id == version_id)
            .order_by(meal_pattern_evidence_table.c.position)
        ).mappings()
        return MealPatternProgramDetail(
            program=_program_from_row(program_row),
            version=_version_from_row(version_row),
            opportunities=tuple(
                _opportunity_from_row(row) for row in opportunities
            ),
            tags=tuple(_tag_from_row(row) for row in tags),
            evidence=tuple(_evidence_from_row(row) for row in evidence),
        )


def _program_from_row(row: Mapping[str, Any]) -> MealPatternProgram:
    return MealPatternProgram(
        id=row["id"],
        code=row["program_code"],
        created_at=row["created_at"],
    )


def _version_values(value: MealPatternProgramVersion) -> dict[str, object]:
    return {
        "id": value.id,
        "program_id": value.program_id,
        "version_number": value.version_number,
        "lifecycle": value.lifecycle.value,
        "scope_code": value.scope.value,
        "display_name_ru": value.display_name_ru,
        "explanation_ru": value.explanation_ru,
        "min_age_years": value.min_age_years,
        "max_age_years": value.max_age_years,
        "review_status": value.review_status.value,
        "reviewed_at": value.reviewed_at,
        "published_at": value.published_at,
        "created_from_version_id": value.created_from_version_id,
        "change_note": value.change_note,
        "created_at": value.created_at,
    }


def _version_from_row(row: Mapping[str, Any]) -> MealPatternProgramVersion:
    return MealPatternProgramVersion(
        id=row["id"],
        program_id=row["program_id"],
        version_number=row["version_number"],
        lifecycle=row["lifecycle"],
        scope=row["scope_code"],
        display_name_ru=row["display_name_ru"],
        explanation_ru=row["explanation_ru"],
        min_age_years=row["min_age_years"],
        max_age_years=row["max_age_years"],
        review_status=row["review_status"],
        reviewed_at=row["reviewed_at"],
        published_at=row["published_at"],
        created_from_version_id=row["created_from_version_id"],
        change_note=row["change_note"],
        created_at=row["created_at"],
    )


def _opportunity_values(value: MealPatternOpportunity) -> dict[str, object]:
    return {
        "version_id": value.version_id,
        "position": value.position,
        "role_code": value.role.value,
    }


def _opportunity_from_row(row: Mapping[str, Any]) -> MealPatternOpportunity:
    return MealPatternOpportunity(
        version_id=row["version_id"],
        position=row["position"],
        role=row["role_code"],
    )


def _tag_values(value: MealPatternTag) -> dict[str, object]:
    return {
        "version_id": value.version_id,
        "kind": value.kind.value,
        "code": value.code,
    }


def _tag_from_row(row: Mapping[str, Any]) -> MealPatternTag:
    return MealPatternTag(
        version_id=row["version_id"],
        kind=row["kind"],
        code=row["code"],
    )


def _evidence_values(value: MealPatternEvidence) -> dict[str, object]:
    return {
        "version_id": value.version_id,
        "position": value.position,
        "source_name": value.source_name,
        "source_title": value.source_title,
        "source_url": value.source_url,
        "source_version": value.source_version,
        "retrieved_on": value.retrieved_on,
        "evidence_scope": value.evidence_scope,
        "review_note_ru": value.review_note_ru,
    }


def _evidence_from_row(row: Mapping[str, Any]) -> MealPatternEvidence:
    return MealPatternEvidence(
        version_id=row["version_id"],
        position=row["position"],
        source_name=row["source_name"],
        source_title=row["source_title"],
        source_url=row["source_url"],
        source_version=row["source_version"],
        retrieved_on=row["retrieved_on"],
        evidence_scope=row["evidence_scope"],
        review_note_ru=row["review_note_ru"],
    )
