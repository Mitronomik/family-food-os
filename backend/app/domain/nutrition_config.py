"""Pinned PR6 calculation policy; changes require a new version.

Sources and interpretation: docs/family-food/nutrition-core.md.
Only the coefficients/table values used by this engine are transcribed here.
"""

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_UP
from types import MappingProxyType


@dataclass(frozen=True)
class NutritionConfig:
    version: str = "FAMILY_FOOD_NUTRITION_V1"
    eer_version: str = "NASEM_EER_2023_V1"
    amdr_version: str = "DRI_AMDR_2002_2005_V1"
    fiber_version: str = "DRI_TOTAL_FIBER_AI_2002_2005_V1"
    atwater_version: str = "ATWATER_GENERAL_4_4_9_V1"
    age_policy_version: str = "COMPLETED_CHRONOLOGICAL_YEARS_V1"
    rounding_version: str = "DECIMAL_80_HALF_UP_6DP_V1"


CONFIG = NutritionConfig()
RESULT_QUANTUM = Decimal("0.000001")
# Fresh Context (including traps/exponents) isolates calculations from callers.
DECIMAL_PRECISION = 80
MAX_INPUT = Decimal("1e24")
MIN_INPUT = Decimal("1e-18")
NUTRIENTS = ("kcal", "protein_g", "fat_g", "carbohydrates_g", "fiber_g")
PAL_CATEGORIES = ("inactive", "low_active", "active", "very_active")
EER_SOURCE = "https://www.nationalacademies.org/read/26818/chapter/7"
DRI_SOURCE = "https://www.ncbi.nlm.nih.gov/books/NBK545442/"
ATWATER_SOURCE = "https://www.fao.org/4/y5022e/y5022e04.htm"


@dataclass(frozen=True)
class ReferenceSource:
    config_version: str
    url: str
    locator: str


REFERENCE_SOURCES = (
    ReferenceSource(
        CONFIG.eer_version, EER_SOURCE, "Tables 5-15, 5-16; growth footnotes b/c"
    ),
    ReferenceSource(
        CONFIG.amdr_version,
        DRI_SOURCE + "table/appJ_tab5/",
        "Appendix J: AMDR summary table (2002/2005)",
    ),
    ReferenceSource(
        CONFIG.fiber_version,
        DRI_SOURCE + "table/appJ_tab4/",
        "Appendix J: Recommended Intakes, Macronutrients (2002/2005)",
    ),
    ReferenceSource(
        CONFIG.atwater_version, ATWATER_SOURCE, "Section 3.5.1: general Atwater factors"
    ),
)

# NASEM 2023 Tables 5-15 / 5-16: intercept, age(y), height(cm), weight(kg).
# Rows within each group follow PAL_CATEGORIES. Child growth is separate below.
EER_COEFFICIENTS = MappingProxyType(
    {
        ("child", "male"): tuple(
            tuple(map(Decimal, row))
            for row in (
                ("-447.51", "3.68", "13.01", "13.15"),
                ("19.12", "3.68", "8.62", "20.28"),
                ("-388.19", "3.68", "12.66", "20.46"),
                ("-671.75", "3.68", "15.38", "23.25"),
            )
        ),
        ("child", "female"): tuple(
            tuple(map(Decimal, row))
            for row in (
                ("55.59", "-22.25", "8.43", "17.07"),
                ("-297.54", "-22.25", "12.77", "14.73"),
                ("-189.55", "-22.25", "11.74", "18.34"),
                ("-709.59", "-22.25", "18.22", "14.25"),
            )
        ),
        ("adult", "male"): tuple(
            tuple(map(Decimal, row))
            for row in (
                ("753.07", "-10.83", "6.50", "14.10"),
                ("581.47", "-10.83", "8.30", "14.94"),
                ("1004.82", "-10.83", "6.52", "15.91"),
                ("-517.88", "-10.83", "15.61", "19.11"),
            )
        ),
        ("adult", "female"): tuple(
            tuple(map(Decimal, row))
            for row in (
                ("584.90", "-7.01", "5.72", "11.71"),
                ("575.77", "-7.01", "6.60", "12.14"),
                ("710.25", "-7.01", "6.54", "12.34"),
                ("511.83", "-7.01", "9.07", "12.56"),
            )
        ),
    }
)
# Inclusive upper age; boys/girls kcal per day (Table 5-15 and p. 98).
GROWTH_BANDS = (
    (3, Decimal(20), Decimal(15)),
    (8, Decimal(15), Decimal(15)),
    (13, Decimal(25), Decimal(30)),
    (18, Decimal(20), Decimal(20)),
)
# Inclusive upper age, carbohydrate/protein/fat fractions of energy.
AMDR_BANDS = tuple(
    (age, tuple((Decimal(lo), Decimal(hi)) for lo, hi in ranges))
    for age, ranges in (
        (3, ((".45", ".65"), (".05", ".20"), (".30", ".40"))),
        (18, ((".45", ".65"), (".10", ".30"), (".25", ".35"))),
        (None, ((".45", ".65"), (".10", ".35"), (".20", ".35"))),
    )
)
ATWATER_FACTORS = (Decimal(4), Decimal(4), Decimal(9))
# DRI Total Fiber AI; inclusive upper age, male/female grams per day.
FIBER_BANDS = (
    (3, Decimal(19), Decimal(19)),
    (8, Decimal(25), Decimal(25)),
    (13, Decimal(31), Decimal(26)),
    (18, Decimal(38), Decimal(26)),
    (50, Decimal(38), Decimal(25)),
    (None, Decimal(30), Decimal(21)),
)


def calculation_context() -> Context:
    return Context(prec=DECIMAL_PRECISION, rounding=ROUND_HALF_UP)
