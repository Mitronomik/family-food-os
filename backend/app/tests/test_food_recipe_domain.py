from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid1, uuid4

import pytest

from app.domain.errors import DomainValidationError
from app.domain.food_recipes import (
    MealTypeCode,
    Recipe,
    RecipeEquipment,
    RecipeIngredient,
    RecipeStep,
    RecipeVersion,
    RecipeVersionDetail,
    RightsReviewStatus,
    VerificationStatus,
    scale_recipe,
)

NOW = datetime(2026, 9, 4, tzinfo=timezone.utc)


def _detail() -> RecipeVersionDetail:
    recipe = Recipe(
        uuid4(), "TEST_RECIPE", "Test Recipe", "test recipe", True, NOW, NOW
    )
    version = RecipeVersion(
        id=uuid4(),
        recipe_id=recipe.id,
        version_number=1,
        base_servings=Decimal("6"),
        meal_type_code=MealTypeCode.MAIN,
        prep_time_minutes=None,
        cook_time_minutes=None,
        total_time_minutes=None,
        difficulty_code=None,
        batch_friendly=None,
        freezable=None,
        storage_days_fridge=None,
        storage_days_freezer=None,
        verification_status=VerificationStatus.SOURCE_VERIFIED,
        verified_at=NOW,
        source_name="USDA_FNS",
        source_recipe_id="source-1",
        source_url="https://example.test/recipe.pdf",
        source_version="sha256:test",
        source_retrieved_at=NOW,
        source_document_sha256="a" * 64,
        source_original_servings=Decimal("6"),
        rights_review_status=RightsReviewStatus.REVIEWED,
        rights_basis="Reviewed government work.",
        created_from_version_id=None,
        change_note="Initial version.",
        created_at=NOW,
    )
    ingredients = (
        RecipeIngredient(
            uuid4(),
            version.id,
            uuid4(),
            1,
            Decimal("600"),
            "g",
            "600 g rice",
            None,
            None,
            False,
            NOW,
        ),
        RecipeIngredient(
            uuid4(),
            version.id,
            uuid4(),
            2,
            Decimal("1"),
            "pcs",
            "1 bay leaf",
            None,
            None,
            False,
            NOW,
        ),
    )
    return RecipeVersionDetail(
        recipe,
        version,
        ingredients,
        (RecipeStep(uuid4(), version.id, 1, "Cook until done.", None, NOW),),
        (RecipeEquipment(version.id, 1, "saucepan"),),
    )


def test_scaling_is_read_only_exact_decimal_and_does_not_round_pieces():
    original = _detail()

    half = scale_recipe(original, Decimal("3"))
    one_and_half = scale_recipe(original, Decimal("9"))

    assert [item.quantity for item in half.ingredients] == [
        Decimal("300.000000"),
        Decimal("0.500000"),
    ]
    assert [item.quantity for item in one_and_half.ingredients] == [
        Decimal("900.000000"),
        Decimal("1.500000"),
    ]
    assert original.ingredients[0].quantity == Decimal("600.000000")
    assert half.version is original.version
    assert half.steps == original.steps


@pytest.mark.parametrize(
    "target",
    [
        Decimal("0"),
        Decimal("-1"),
        1.5,
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("1E+999999"),
    ],
)
def test_scaling_rejects_invalid_or_hostile_target_servings(target):
    with pytest.raises(DomainValidationError):
        scale_recipe(_detail(), target)


def test_recipe_identity_and_name_key_are_validated():
    with pytest.raises(DomainValidationError):
        replace(_detail().recipe, canonical_code="bad code")
    with pytest.raises(DomainValidationError):
        replace(_detail().recipe, canonical_name=" ")
    with pytest.raises(DomainValidationError):
        replace(_detail().recipe, canonical_name_key="wrong")


def test_recipe_and_version_require_uuidv4_identity():
    with pytest.raises(DomainValidationError, match="UUIDv4"):
        replace(_detail().recipe, id=uuid1())
    with pytest.raises(DomainValidationError, match="UUIDv4"):
        replace(_detail().version, id=uuid1())


@pytest.mark.parametrize(
    "value", [Decimal("0"), Decimal("-1"), 2.5, Decimal("NaN"), Decimal("1E+999999")]
)
def test_version_rejects_invalid_base_servings(value):
    with pytest.raises(DomainValidationError):
        replace(_detail().version, base_servings=value)


def test_version_rejects_invalid_number_negative_time_and_storage():
    with pytest.raises(DomainValidationError):
        replace(_detail().version, version_number=0)
    with pytest.raises(DomainValidationError):
        replace(_detail().version, prep_time_minutes=-1)
    with pytest.raises(DomainValidationError):
        replace(_detail().version, storage_days_fridge=-1)


def test_verified_version_requires_complete_reviewed_provenance():
    with pytest.raises(DomainValidationError, match="SOURCE_VERIFIED"):
        replace(_detail().version, verified_at=None)
    with pytest.raises(DomainValidationError, match="rights_basis"):
        replace(_detail().version, rights_basis=None)
    with pytest.raises(DomainValidationError, match="SHA-256"):
        replace(_detail().version, source_document_sha256="bad")


def test_version_owned_children_reject_percent_duplicates_and_blank_steps():
    detail = _detail()
    with pytest.raises(DomainValidationError, match="percent"):
        replace(detail.ingredients[0], unit="percent")
    with pytest.raises(DomainValidationError):
        replace(detail.ingredients[0], quantity=Decimal("0"))
    with pytest.raises(DomainValidationError):
        replace(detail.ingredients[0], quantity=1.5)
    with pytest.raises(DomainValidationError):
        replace(detail.ingredients[0], quantity=Decimal("NaN"))
    with pytest.raises(DomainValidationError):
        replace(detail.ingredients[0], quantity=Decimal("Infinity"))
    with pytest.raises(DomainValidationError):
        replace(detail.steps[0], instruction=" ")
    with pytest.raises(DomainValidationError, match="positions"):
        replace(
            detail,
            ingredients=(
                detail.ingredients[0],
                replace(detail.ingredients[1], position=1),
            ),
        )
    with pytest.raises(DomainValidationError, match="positions"):
        replace(detail, steps=(detail.steps[0], replace(detail.steps[0], id=uuid4())))


def test_unknown_metadata_remains_none():
    version = _detail().version
    assert version.difficulty_code is None
    assert version.batch_friendly is None
    assert version.freezable is None
    assert version.storage_days_fridge is None
    assert version.storage_days_freezer is None
