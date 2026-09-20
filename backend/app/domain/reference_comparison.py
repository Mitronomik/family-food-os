"""Dimension- and definition-safe comparison to an explicit group reference."""

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from app.domain.russian_reference_targets import RussianReferenceRow


@dataclass(frozen=True)
class DailyNutrientAmount:
    definition_code: str
    unit: str
    amount: Decimal | None
    calculation_version: str
    source_references: tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.source_references, (tuple, list)):
            raise TypeError("Нужен список ссылок на источники.")
        if (
            any(
                not isinstance(s, str) or not s.strip()
                for s in (
                    self.definition_code,
                    self.calculation_version,
                    *self.source_references,
                )
            )
            or not self.source_references
        ):
            raise ValueError(
                "Нужны определение, версия и происхождение суточного результата."
            )
        if self.unit not in {"kcal/day", "g/day", "mg/day", "µg/day"}:
            raise ValueError("Нужна поддерживаемая единица суточного количества.")
        if self.amount is not None and (
            not isinstance(self.amount, Decimal)
            or not self.amount.is_finite()
            or self.amount < 0
            or self.amount > Decimal("1e24")
            or len(self.amount.as_tuple().digits) > 40
            or self.amount.as_tuple().exponent < -40
        ):
            raise ValueError("Недопустимое суточное количество.")
        object.__setattr__(self, "source_references", tuple(self.source_references))


@dataclass(frozen=True)
class ReferenceComparison:
    status: str
    percent_of_group_reference: Decimal | None
    amount: DailyNutrientAmount
    reference: RussianReferenceRow
    version: str = "EXACT_DEFINITION_REFERENCE_COMPARISON_V1"
    individualized: bool = False


def compare_daily_reference(
    amount: DailyNutrientAmount, reference: RussianReferenceRow
) -> ReferenceComparison:
    if not isinstance(amount, DailyNutrientAmount) or not isinstance(
        reference, RussianReferenceRow
    ):
        raise TypeError("Нужны типизированные суточное количество и норма.")
    if amount.definition_code != reference.definition_code:
        return ReferenceComparison("INCOMPATIBLE_DEFINITION", None, amount, reference)
    # Unit conversion never establishes chemical equivalence (RE != RAE, NE != niacin).
    scale = {
        "g/day": Decimal(1),
        "mg/day": Decimal(".001"),
        "µg/day": Decimal(".000001"),
    }
    if (
        amount.unit != reference.unit
        and not {amount.unit, reference.unit} <= scale.keys()
    ):
        return ReferenceComparison("INCOMPATIBLE_UNIT", None, amount, reference)
    if amount.amount is None or reference.value == 0:
        return ReferenceComparison("UNAVAILABLE", None, amount, reference)
    with localcontext(Context(prec=80, rounding=ROUND_HALF_UP)):
        ratio = amount.amount / reference.value
        if amount.unit != reference.unit:
            ratio *= scale[amount.unit] / scale[reference.unit]
        percent = (ratio * 100).quantize(Decimal(".000001"))
    return ReferenceComparison("COMPARABLE_GROUP_REFERENCE", percent, amount, reference)
