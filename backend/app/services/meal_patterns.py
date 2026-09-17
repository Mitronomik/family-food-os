"""Application operations for the platform Meal Pattern Catalogue."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from app.domain.meal_patterns import (
    MealPatternEligibilityQuery,
    MealPatternEvidence,
    MealPatternLifecycle,
    MealPatternOpportunity,
    MealPatternProgram,
    MealPatternProgramDetail,
    MealPatternProgramVersion,
    MealPatternReviewStatus,
    MealPatternScope,
    MealPatternTag,
    MealPatternTagKind,
    MealRole,
    detail_is_eligible,
    validate_publishable,
)
from app.services.meal_pattern_contracts import (
    MealPatternCatalogueReadScope,
    MealPatternCatalogueUnitOfWork,
)

WriteFactory = Callable[[], MealPatternCatalogueUnitOfWork]
ReadFactory = Callable[[], MealPatternCatalogueReadScope]


class MealPatternNotFoundError(LookupError):
    pass


class MealPatternCatalogueConflictError(ValueError):
    pass


@dataclass(frozen=True)
class TrustedMealPatternEvidenceSeed:
    source_name: str
    source_title: str
    source_url: str
    source_version: str
    retrieved_on: date
    evidence_scope: str
    review_note_ru: str


@dataclass(frozen=True)
class TrustedMealPatternVersionSeed:
    lifecycle: MealPatternLifecycle | str
    scope: MealPatternScope | str
    display_name_ru: str
    explanation_ru: str
    min_age_years: int
    max_age_years: int | None
    review_status: MealPatternReviewStatus | str
    reviewed_at: datetime | None
    published_at: datetime | None
    change_note: str
    opportunity_roles: tuple[MealRole | str, ...]
    tags: tuple[tuple[MealPatternTagKind | str, str], ...]
    evidence: tuple[TrustedMealPatternEvidenceSeed, ...]


@dataclass(frozen=True)
class TrustedMealPatternSeed:
    code: str
    version: TrustedMealPatternVersionSeed


@dataclass(frozen=True)
class MealPatternSeedSummary:
    programs_inserted: int = 0
    programs_existing: int = 0
    versions_inserted: int = 0
    versions_existing: int = 0


@dataclass(frozen=True)
class MealPatternEligibilityResult:
    programs: tuple[MealPatternProgramDetail, ...]
    unsupported_reason: str | None


class MealPatternCatalogueService:
    def __init__(
        self,
        write_scope_factory: WriteFactory,
        read_scope_factory: ReadFactory,
        *,
        id_factory: Callable[[], UUID] = uuid4,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._write = write_scope_factory
        self._read = read_scope_factory
        self._id = id_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get_exact(self, code: str, version_number: int) -> MealPatternProgramDetail:
        with self._read() as scope:
            program = scope.programs.get_by_code(code)
            if program is None:
                raise MealPatternNotFoundError(code)
            detail = scope.versions.get_by_number(program.id, version_number)
            if detail is None:
                raise MealPatternNotFoundError((code, version_number))
            return detail

    def get_current_published(self, code: str) -> MealPatternProgramDetail:
        with self._read() as scope:
            program = scope.programs.get_by_code(code)
            if program is None:
                raise MealPatternNotFoundError(code)
            detail = scope.versions.get_current_published(program.id)
            if detail is None:
                raise MealPatternNotFoundError(code)
            return detail

    def list_eligible(
        self, query: MealPatternEligibilityQuery
    ) -> MealPatternEligibilityResult:
        with self._read() as scope:
            candidates = scope.versions.list_current_published()
        eligible = tuple(
            detail
            for detail in candidates
            if detail_is_eligible(detail, query)
        )
        return MealPatternEligibilityResult(
            programs=eligible,
            unsupported_reason=None
            if eligible
            else "NO_ELIGIBLE_PUBLISHED_MEAL_PATTERN",
        )

    def create_trusted(self, seed: TrustedMealPatternSeed) -> MealPatternProgramDetail:
        now = self._clock()
        with self._write() as scope:
            if scope.programs.get_by_code(seed.code) is not None:
                raise MealPatternCatalogueConflictError("MealPatternProgram code exists.")
            program = MealPatternProgram(id=self._id(), code=seed.code, created_at=now)
            scope.programs.add(program)
            detail = self._new_detail(
                program=program,
                seed=seed.version,
                version_number=1,
                previous_id=None,
                now=now,
            )
            self._validate_for_lifecycle(detail)
            scope.versions.add_detail(detail)
            scope.commit()
            return detail

    def append_trusted_version(
        self, code: str, seed: TrustedMealPatternVersionSeed
    ) -> MealPatternProgramDetail:
        now = self._clock()
        with self._write() as scope:
            program = scope.programs.get_by_code(code)
            if program is None:
                raise MealPatternNotFoundError(code)
            versions = scope.versions.list_for_program(program.id)
            previous = versions[-1] if versions else None
            detail = self._new_detail(
                program=program,
                seed=seed,
                version_number=1 if previous is None else previous.version_number + 1,
                previous_id=None if previous is None else previous.id,
                now=now,
            )
            self._validate_for_lifecycle(detail)
            scope.versions.add_detail(detail)
            scope.commit()
            return detail

    def deactivate(self, code: str, *, change_note: str) -> MealPatternProgramDetail:
        current = self.get_current_published(code)
        seed = TrustedMealPatternVersionSeed(
            lifecycle=MealPatternLifecycle.INACTIVE,
            scope=current.version.scope,
            display_name_ru=current.version.display_name_ru,
            explanation_ru=current.version.explanation_ru,
            min_age_years=current.version.min_age_years,
            max_age_years=current.version.max_age_years,
            review_status=MealPatternReviewStatus.REVIEWED,
            reviewed_at=self._clock(),
            published_at=None,
            change_note=change_note,
            opportunity_roles=tuple(item.role for item in current.opportunities),
            tags=tuple((item.kind, item.code) for item in current.tags),
            evidence=tuple(
                TrustedMealPatternEvidenceSeed(
                    source_name=item.source_name,
                    source_title=item.source_title,
                    source_url=item.source_url,
                    source_version=item.source_version,
                    retrieved_on=item.retrieved_on,
                    evidence_scope=item.evidence_scope,
                    review_note_ru=item.review_note_ru,
                )
                for item in current.evidence
            ),
        )
        return self.append_trusted_version(code, seed)

    def reconcile_seed(
        self, seeds: Iterable[TrustedMealPatternSeed]
    ) -> MealPatternSeedSummary:
        entries = tuple(seeds)
        codes = [entry.code for entry in entries]
        if len(codes) != len(set(codes)):
            raise MealPatternCatalogueConflictError(
                "Seed contains duplicate MealPatternProgram code."
            )
        inserted_programs = existing_programs = inserted_versions = existing_versions = 0
        now = self._clock()
        with self._write() as scope:
            for entry in entries:
                program = scope.programs.get_by_code(entry.code)
                if program is None:
                    program = MealPatternProgram(
                        id=self._id(), code=entry.code, created_at=now
                    )
                    scope.programs.add(program)
                    detail = self._new_detail(
                        program=program,
                        seed=entry.version,
                        version_number=1,
                        previous_id=None,
                        now=now,
                    )
                    self._validate_for_lifecycle(detail)
                    scope.versions.add_detail(detail)
                    inserted_programs += 1
                    inserted_versions += 1
                    continue

                existing_programs += 1
                existing = scope.versions.get_by_number(program.id, 1)
                if existing is None:
                    detail = self._new_detail(
                        program=program,
                        seed=entry.version,
                        version_number=1,
                        previous_id=None,
                        now=now,
                    )
                    self._validate_for_lifecycle(detail)
                    scope.versions.add_detail(detail)
                    inserted_versions += 1
                    continue
                if not _seed_matches(existing, entry.version):
                    raise MealPatternCatalogueConflictError(
                        "Existing MealPatternProgram v1 differs from trusted seed."
                    )
                existing_versions += 1
            scope.commit()
        return MealPatternSeedSummary(
            programs_inserted=inserted_programs,
            programs_existing=existing_programs,
            versions_inserted=inserted_versions,
            versions_existing=existing_versions,
        )

    def _new_detail(
        self,
        *,
        program: MealPatternProgram,
        seed: TrustedMealPatternVersionSeed,
        version_number: int,
        previous_id: UUID | None,
        now: datetime,
    ) -> MealPatternProgramDetail:
        version_id = self._id()
        version = MealPatternProgramVersion(
            id=version_id,
            program_id=program.id,
            version_number=version_number,
            lifecycle=seed.lifecycle,  # type: ignore[arg-type]
            scope=seed.scope,  # type: ignore[arg-type]
            display_name_ru=seed.display_name_ru,
            explanation_ru=seed.explanation_ru,
            min_age_years=seed.min_age_years,
            max_age_years=seed.max_age_years,
            review_status=seed.review_status,  # type: ignore[arg-type]
            reviewed_at=seed.reviewed_at,
            published_at=seed.published_at,
            created_from_version_id=previous_id,
            change_note=seed.change_note,
            created_at=now,
        )
        opportunities = tuple(
            MealPatternOpportunity(
                version_id=version_id,
                position=position,
                role=role,  # type: ignore[arg-type]
            )
            for position, role in enumerate(seed.opportunity_roles, start=1)
        )
        tags = tuple(
            MealPatternTag(
                version_id=version_id,
                kind=kind,  # type: ignore[arg-type]
                code=code,
            )
            for kind, code in seed.tags
        )
        evidence = tuple(
            MealPatternEvidence(
                version_id=version_id,
                position=position,
                source_name=item.source_name,
                source_title=item.source_title,
                source_url=item.source_url,
                source_version=item.source_version,
                retrieved_on=item.retrieved_on,
                evidence_scope=item.evidence_scope,
                review_note_ru=item.review_note_ru,
            )
            for position, item in enumerate(seed.evidence, start=1)
        )
        return MealPatternProgramDetail(
            program=program,
            version=version,
            opportunities=opportunities,
            tags=tags,
            evidence=evidence,
        )

    @staticmethod
    def _validate_for_lifecycle(detail: MealPatternProgramDetail) -> None:
        if detail.version.lifecycle is MealPatternLifecycle.PUBLISHED:
            validate_publishable(detail)


def _seed_matches(
    detail: MealPatternProgramDetail, seed: TrustedMealPatternVersionSeed
) -> bool:
    version = detail.version
    if (
        version.lifecycle != MealPatternLifecycle(seed.lifecycle)
        or version.scope != MealPatternScope(seed.scope)
        or version.display_name_ru != seed.display_name_ru
        or version.explanation_ru != seed.explanation_ru
        or version.min_age_years != seed.min_age_years
        or version.max_age_years != seed.max_age_years
        or version.review_status != MealPatternReviewStatus(seed.review_status)
        or version.reviewed_at != seed.reviewed_at
        or version.published_at != seed.published_at
        or version.change_note != seed.change_note
    ):
        return False
    if tuple(item.role for item in detail.opportunities) != tuple(
        MealRole(value) for value in seed.opportunity_roles
    ):
        return False
    if tuple((item.kind, item.code) for item in detail.tags) != tuple(
        (MealPatternTagKind(kind), code) for kind, code in seed.tags
    ):
        return False
    return tuple(
        (
            item.source_name,
            item.source_title,
            item.source_url,
            item.source_version,
            item.retrieved_on,
            item.evidence_scope,
            item.review_note_ru,
        )
        for item in detail.evidence
    ) == tuple(
        (
            item.source_name,
            item.source_title,
            item.source_url,
            item.source_version,
            item.retrieved_on,
            item.evidence_scope,
            item.review_note_ru,
        )
        for item in seed.evidence
    )
