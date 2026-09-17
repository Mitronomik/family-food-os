from dataclasses import replace
from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from app.domain.errors import DomainValidationError
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

NOW = datetime(2026, 9, 17, 4, 19, tzinfo=timezone.utc)


def _detail() -> MealPatternProgramDetail:
    program = MealPatternProgram(id=uuid4(), code="ADULT_TEST", created_at=NOW)
    version = MealPatternProgramVersion(
        id=uuid4(),
        program_id=program.id,
        version_number=1,
        lifecycle=MealPatternLifecycle.PUBLISHED,
        scope=MealPatternScope.WELLNESS_SCHEDULE,
        display_name_ru="Тестовый режим питания",
        explanation_ru="Нейтральный режим для проверки расписания без медицинских обещаний.",
        min_age_years=19,
        max_age_years=None,
        review_status=MealPatternReviewStatus.REVIEWED,
        reviewed_at=NOW,
        published_at=NOW,
        created_from_version_id=None,
        change_note="Synthetic test fixture.",
        created_at=NOW,
    )
    opportunities = tuple(
        MealPatternOpportunity(version_id=version.id, position=position, role=role)
        for position, role in enumerate(
            (MealRole.BREAKFAST, MealRole.SNACK, MealRole.SNACK, MealRole.DINNER),
            start=1,
        )
    )
    evidence = (
        MealPatternEvidence(
            version_id=version.id,
            position=1,
            source_name="Synthetic evidence",
            source_title="Synthetic review",
            source_url="https://example.test/evidence",
            source_version="v1",
            retrieved_on=date(2026, 9, 17),
            evidence_scope="FREQUENCY_OUTCOME_UNCERTAINTY",
            review_note_ru="Синтетическая заметка только для теста валидатора.",
        ),
    )
    tags = (
        MealPatternTag(
            version_id=version.id,
            kind=MealPatternTagKind.CONTEXT,
            code="GENERAL_WELLNESS_SCHEDULE",
        ),
    )
    return MealPatternProgramDetail(
        program=program,
        version=version,
        opportunities=opportunities,
        tags=tags,
        evidence=evidence,
    )


def test_publishable_allows_repeated_semantic_roles_when_positions_are_distinct():
    detail = _detail()
    validate_publishable(detail)
    assert [item.role for item in detail.opportunities].count(MealRole.SNACK) == 2


def test_publishable_fails_closed_without_evidence_or_russian_display_text():
    detail = _detail()
    with pytest.raises(DomainValidationError, match="evidence"):
        validate_publishable(replace(detail, evidence=()))

    english = replace(detail.version, display_name_ru="Three meals")
    with pytest.raises(DomainValidationError, match="Russian"):
        validate_publishable(replace(detail, version=english))


def test_wellness_scope_and_age_bounds_fail_closed():
    detail = _detail()
    with pytest.raises(DomainValidationError):
        replace(detail.version, scope="THERAPEUTIC")
    with pytest.raises(DomainValidationError, match="max_age_years"):
        replace(detail.version, max_age_years=18)


def test_eligibility_never_inherits_adult_program_to_child():
    detail = _detail()
    assert not detail_is_eligible(detail, MealPatternEligibilityQuery(age_years=18))
    assert detail_is_eligible(
        detail,
        MealPatternEligibilityQuery(
            age_years=19,
            context_codes=("GENERAL_WELLNESS_SCHEDULE",),
        ),
    )
    assert not detail_is_eligible(
        detail,
        MealPatternEligibilityQuery(age_years=19, context_codes=("UNSUPPORTED",)),
    )
