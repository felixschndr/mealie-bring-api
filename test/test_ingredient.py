import pytest

from source.ingredient import Ingredient, IngredientWithAmountsDisabled


@pytest.fixture
def ingredient_raw_data_with_higher_quantity(ingredient_raw_base_data: dict) -> dict:
    ingredient_raw_base_data["quantity"] = 2.0
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_unit_abbreviation_instead_of_name(
    ingredient_raw_base_data: dict,
) -> dict:
    ingredient_raw_base_data["unit"]["name"] = ""
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_unit_abbreviation_instead_of_name_and_higher_quantity(
    ingredient_raw_base_data: dict,
) -> dict:
    ingredient_raw_base_data["unit"]["plural_name"] = ""
    ingredient_raw_base_data["quantity"] = 2.0
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_note(ingredient_raw_base_data: dict) -> dict:
    ingredient_raw_base_data["note"] = "test note"
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_none_quantity(ingredient_raw_base_data: dict) -> dict:
    ingredient_raw_base_data["quantity"] = None
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_none_unit(ingredient_raw_base_data: dict) -> dict:
    ingredient_raw_base_data["unit"] = None
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_household(ingredient_raw_base_data: dict) -> dict:
    ingredient_raw_base_data["food"]["households_with_ingredient_food"] = ["household1"]
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_with_disabled_amounts_display(food_name_plural) -> str:
    return f"10 Grams of {food_name_plural}"


@pytest.fixture
def ingredient_raw_data_with_disabled_amounts(
    ingredient_with_disabled_amounts_display,
) -> dict:
    return {
        "disable_amount": True,
        "display": ingredient_with_disabled_amounts_display,
        "food": None,
        "is_food": False,
        "note": ingredient_with_disabled_amounts_display,
        "original_text": None,
        "quantity": 1.0,
        "reference_id": "8ea582b8-1518-4089-9f1a-f3540a83b6e7",
        "title": None,
        "unit": None,
    }


@pytest.mark.parametrize(
    argnames="ingredient_input, recipe_scale, expected_name, expected_specification",
    argvalues=[
        # Basic cases with different recipe scales
        ("ingredient_raw_base_data", 1, "food_name_singular", "1 Gram"),
        ("ingredient_raw_base_data", 1.5, "food_name_plural", "1.5 Grams"),
        ("ingredient_raw_base_data", 2, "food_name_plural", "2 Grams"),
        ("ingredient_raw_data_with_higher_quantity", 1, "food_name_plural", "2 Grams"),
        # Unit abbreviation cases
        (
            "ingredient_raw_data_with_unit_abbreviation_instead_of_name",
            1,
            "food_name_singular",
            "1g",
        ),
        (
            "ingredient_raw_data_with_unit_abbreviation_instead_of_name_and_higher_quantity",
            1,
            "food_name_plural",
            "2g",
        ),
        # Note case
        (
            "ingredient_raw_data_with_note",
            1,
            "food_name_singular",
            "1 Gram (test note)",
        ),
        # None quantity case
        (
            "ingredient_raw_data_with_none_quantity",
            1,
            "food_name_plural",  # When quantity is None, is_one is False, so plural is used
            "Grams",  # Even with None quantity, the unit is still included
        ),
        # None unit case
        (
            "ingredient_raw_data_with_none_unit",
            1,
            "food_name_singular",
            "1",
        ),
    ],
)
def test_parse_ingredient(ingredient_input, recipe_scale, expected_name, expected_specification, request):
    expected_ingredient = Ingredient(
        name=request.getfixturevalue(expected_name),
        specification=expected_specification,
    )

    actual_ingredient = Ingredient.from_raw_data(request.getfixturevalue(ingredient_input), recipe_scale)

    assert actual_ingredient == expected_ingredient


@pytest.mark.parametrize(
    argnames="recipe_scale",
    argvalues=[1.0, 1.5, 2.0],
)
def test_ingredient_with_amounts_disabled(
    ingredient_raw_data_with_disabled_amounts,
    ingredient_with_disabled_amounts_display,
    recipe_scale,
):
    expected_ingredient = IngredientWithAmountsDisabled(
        name=ingredient_with_disabled_amounts_display, specification=None
    )

    actual_ingredient = IngredientWithAmountsDisabled.from_raw_data(
        ingredient_raw_data_with_disabled_amounts, recipe_scale
    )

    assert actual_ingredient == expected_ingredient


@pytest.mark.parametrize(
    "ingredient_raw_data, expected_in_household",
    [("ingredient_raw_base_data", False), ("ingredient_raw_data_with_household", True)],
)
def test_in_household(ingredient_raw_data, expected_in_household, request):
    assert Ingredient.in_household(request.getfixturevalue(ingredient_raw_data)) == expected_in_household


def test_to_dict(food_name_singular):
    ingredient = Ingredient(name=food_name_singular, specification="1 Gram")

    result = ingredient.to_dict()

    assert result["itemId"] == food_name_singular
    assert result["spec"] == "1 Gram"
    assert isinstance(result["uuid"], str)
