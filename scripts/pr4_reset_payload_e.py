#!/usr/bin/env python3
from pathlib import Path


def patch(path_name: str, replacements: list[tuple[str, str, bool]]) -> None:
    path = Path(path_name)
    text = path.read_text(encoding="utf-8")
    for old, new, required in replacements:
        if old in text:
            text = text.replace(old, new)
        elif required:
            raise SystemExit(f"Expected test block not found in {path_name}: {old!r}")
    path.write_text(text, encoding="utf-8")


patch(
    "backend/app/tests/test_food_recipe_application.py",
    [
        ("from decimal import Decimal\n", "from decimal import Decimal, ROUND_HALF_UP\n", True),
        (
            '(original_line.quantity / Decimal("2")).quantize(Decimal("0.000001"))',
            '(original_line.quantity / Decimal("2")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)',
            True,
        ),
    ],
)

patch(
    "backend/app/tests/test_food_recipe_seed.py",
    [
        ("from decimal import Decimal\n", "from decimal import Decimal, ROUND_HALF_UP\n", True),
        (
            'assert half.ingredients[0].quantity == original.ingredients[0].quantity / 2',
            'assert half.ingredients[0].quantity == (original.ingredients[0].quantity / 2).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)',
            True,
        ),
        (
            'assert one_and_half.ingredients[0].quantity == original.ingredients[0].quantity * Decimal("1.5")',
            'assert one_and_half.ingredients[0].quantity == (original.ingredients[0].quantity * Decimal("1.5")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)',
            False,
        ),
    ],
)
