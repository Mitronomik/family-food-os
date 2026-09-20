"""Versioned selection of reviewed Russian population references, not prescriptions.

No corpus is loaded implicitly. Publication owns source and applicability review.
Values remain in their source definitions/units; this adapter never interpolates,
converts macro percentages, or maps NASEM activity categories to Russian KFA.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


SELECTOR_VERSION = "RU_GROUP_REFERENCE_SELECTOR_V1"


class ReferenceSelectionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    UNSUPPORTED = "UNSUPPORTED"


def _text(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Нужен непустой идентификатор или источник.")


def _decimal(value: Decimal, *, positive: bool = False) -> None:
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("Значение должно быть конечным Decimal.")
    if (
        value < 0
        or value > Decimal("1e24")
        or (positive and value == 0)
        or len(value.as_tuple().digits) > 40
        or value.as_tuple().exponent < -40
    ):
        raise ValueError("Недопустимое отрицательное или нулевое значение.")


@dataclass(frozen=True)
class RussianReferenceRow:
    id: str
    source_id: str
    source_version: str
    locator: str
    review_reference: str
    definition_code: str
    unit: str
    value: Decimal
    sex: str
    age_min_years: int
    age_max_years_exclusive: int | None
    physical_activity_coefficient: Decimal | None
    life_stage: str
    basis: str = "group_reference_daily"
    applicability: str = "wellness"

    def __post_init__(self) -> None:
        for item in (
            self.id,
            self.source_id,
            self.source_version,
            self.locator,
            self.review_reference,
            self.definition_code,
        ):
            _text(item)
        if self.unit not in ("kcal/day", "g/day", "mg/day", "µg/day", "percent_energy"):
            raise ValueError("Единица нормы не поддерживается.")
        _decimal(self.value)
        if self.unit == "percent_energy" and self.value > 100:
            raise ValueError("Доля энергии превышает 100 процентов.")
        if self.sex not in ("male", "female", "all"):
            raise ValueError("Неизвестная применимость по полу.")
        if type(self.age_min_years) is not int or self.age_min_years < 0:
            raise ValueError("Неверная нижняя граница возраста.")
        if self.age_max_years_exclusive is not None and (
            type(self.age_max_years_exclusive) is not int
            or self.age_max_years_exclusive <= self.age_min_years
        ):
            raise ValueError("Неверная верхняя граница возраста.")
        if self.physical_activity_coefficient is not None:
            _decimal(self.physical_activity_coefficient, positive=True)
        if self.life_stage not in ("adult", "child"):
            raise ValueError("Этап жизни вне поддерживаемого wellness-сценария.")
        if self.applicability != "wellness" or self.basis != "group_reference_daily":
            raise ValueError("Требуется суточная групповая wellness-норма.")


@dataclass(frozen=True)
class ReviewedRussianReferenceTable:
    methodology_version: str
    review_reference: str
    rows: tuple[RussianReferenceRow, ...]

    def __post_init__(self) -> None:
        _text(self.methodology_version)
        _text(self.review_reference)
        rows = tuple(self.rows)
        if not rows or any(not isinstance(row, RussianReferenceRow) for row in rows):
            raise ValueError("Требуются проверенные строки норм.")
        if len({row.id for row in rows}) != len(rows):
            raise ValueError("Идентификатор строки повторяется.")
        # Reject ambiguity before any member-specific lookup; no hidden priority.
        for index, left in enumerate(rows):
            for right in rows[index + 1 :]:
                if (
                    left.definition_code != right.definition_code
                    or left.life_stage != right.life_stage
                ):
                    continue
                if left.sex != right.sex and "all" not in (left.sex, right.sex):
                    continue
                if (
                    left.physical_activity_coefficient
                    != right.physical_activity_coefficient
                    and left.physical_activity_coefficient is not None
                    and right.physical_activity_coefficient is not None
                ):
                    continue
                left_end = left.age_max_years_exclusive
                right_end = right.age_max_years_exclusive
                if (left_end is None or right.age_min_years < left_end) and (
                    right_end is None or left.age_min_years < right_end
                ):
                    raise ValueError(
                        "Перекрывающиеся нормы требуют явного решения редактора."
                    )
        object.__setattr__(self, "rows", tuple(sorted(rows, key=lambda row: row.id)))


@dataclass(frozen=True)
class RussianReferenceSelection:
    methodology_version: str
    table_review_reference: str
    status: ReferenceSelectionStatus
    rows: tuple[RussianReferenceRow, ...]
    missing_definitions: tuple[str, ...]
    reason: str | None
    age_years: int | None
    sex: str | None
    physical_activity_coefficient: Decimal | None
    life_stage: str
    selector_version: str = SELECTOR_VERSION
    basis: str = "group_reference_daily"
    individualized: bool = False


def select_russian_reference_targets(
    table: ReviewedRussianReferenceTable,
    *,
    age_years: int | None,
    sex: str | None,
    physical_activity_coefficient: Decimal | None,
    life_stage: str,
    definition_codes: tuple[str, ...],
) -> RussianReferenceSelection:
    """Select exact approved applicability; None KFA means source is independent.

    Age is completed chronological years, explicitly supplied by the caller.
    No conversion of ambiguous source boundaries is performed here.
    """
    if not isinstance(table, ReviewedRussianReferenceTable):
        raise TypeError("Требуется проверенная таблица норм.")
    definitions = tuple(sorted(set(definition_codes)))
    if not definitions:
        raise ValueError("Нужен перечень показателей.")
    for code in definitions:
        _text(code)
    if physical_activity_coefficient is not None:
        _decimal(physical_activity_coefficient, positive=True)
    reason = None
    if type(age_years) is not int or age_years < 0:
        reason = "UNSUPPORTED_AGE"
    elif sex not in ("male", "female"):
        reason = "UNSUPPORTED_SEX"
    elif life_stage not in ("adult", "child"):
        reason = "UNSUPPORTED_LIFE_STAGE"
    selected = (
        ()
        if reason
        else tuple(
            row
            for row in table.rows
            if row.definition_code in definitions
            and row.life_stage == life_stage
            and row.sex in (sex, "all")
            and row.age_min_years <= age_years
            and (
                row.age_max_years_exclusive is None
                or age_years < row.age_max_years_exclusive
            )
            and (
                row.physical_activity_coefficient is None
                or row.physical_activity_coefficient == physical_activity_coefficient
            )
        )
    )
    missing = tuple(
        code
        for code in definitions
        if code not in {row.definition_code for row in selected}
    )
    status = (
        ReferenceSelectionStatus.COMPLETE
        if not missing
        else ReferenceSelectionStatus.INCOMPLETE
        if selected
        else ReferenceSelectionStatus.UNSUPPORTED
    )
    return RussianReferenceSelection(
        table.methodology_version,
        table.review_reference,
        status,
        selected,
        missing,
        reason or ("NO_APPLICABLE_REFERENCE" if not selected else None),
        age_years,
        sex,
        physical_activity_coefficient,
        life_stage,
    )
