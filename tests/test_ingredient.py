import pytest
from source.ingredient import (
    Ingredient,
    IngredientWithAmountsDisabled,
    get_value_of_dict_with_different_naming_conventions,
)


@pytest.fixture
def ingredient_raw_data_with_higher_quantity(ingredient_raw_base_data: dict) -> dict:
    ingredient_raw_base_data["quantity"] = 2.0
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_unit_abbreviation_instead_of_name(
    ingredient_raw_base_data: dict,
) -> dict:
    ingredient_raw_base_data["unit"]["use_abbreviation"] = True
    return ingredient_raw_base_data


@pytest.fixture
def ingredient_raw_data_with_unit_abbreviation_instead_of_name_and_higher_quantity(
    ingredient_raw_base_data: dict,
) -> dict:
    ingredient_raw_base_data["unit"]["use_abbreviation"] = True
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
        "note": ingredient_with_disabled_amounts_display,
        "original_text": None,
        "quantity": 1.0,
        "unit": None,
    }


@pytest.fixture
def ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero(food_name_plural) -> dict:
    return {
        "checked": False,
        "display": food_name_plural,
        "food": None,
        "note": food_name_plural,
        "quantity": 0,
        "unit": None,
    }


@pytest.fixture
def ingredient_from_shopping_list_with_no_food_with_quantity(
    ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero,
) -> dict:
    ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero["quantity"] = 5
    return ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero


@pytest.fixture
def ingredient_from_shopping_list_with_no_food_with_quantity_and_with_unit(
    ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero, unit
) -> dict:
    ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero["quantity"] = 5
    ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero["unit"] = unit
    return ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero


@pytest.mark.parametrize(
    argnames="ingredient_input, recipe_scale, expected_name, expected_specification",
    argvalues=[
        # Basic cases with different recipe scales
        ("ingredient_raw_base_data", 1, "food_name_singular", "1 Gram"),
        ("ingredient_raw_base_data", 1.5, "food_name_plural", "1.5 Grams"),
        ("ingredient_raw_base_data", 2, "food_name_plural", "2 Grams"),
        ("ingredient_raw_data_with_higher_quantity", 1, "food_name_plural", "2 Grams"),
        # Unit abbreviation cases
        ("ingredient_raw_data_with_unit_abbreviation_instead_of_name", 1, "food_name_singular", "1g"),
        ("ingredient_raw_data_with_unit_abbreviation_instead_of_name_and_higher_quantity", 1, "food_name_plural", "2g"),
        # Note case
        ("ingredient_raw_data_with_note", 1, "food_name_singular", "1 Gram (test note)"),
        # None quantity case
        # When quantity is None, is_one is False, so plural is used, even with None quantity, the unit is still included
        ("ingredient_raw_data_with_none_quantity", 1, "food_name_plural", "Grams"),
        # None unit case
        ("ingredient_raw_data_with_none_unit", 1, "food_name_singular", "1"),
        # Ingredients manually entered into the shopping list have no food attached
        ("ingredient_from_shopping_list_with_no_food_with_quantity_set_to_zero", 1, "food_name_plural", ""),
        ("ingredient_from_shopping_list_with_no_food_with_quantity", 1, "food_name_plural", "5"),
        ("ingredient_from_shopping_list_with_no_food_with_quantity_and_with_unit", 1, "food_name_plural", "5 Grams"),
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
    argvalues=[0, 1.0, 1.5, 2.0],
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


@pytest.mark.parametrize(
    "input_dict, key, expected_value",
    [
        ({"this_is_a_key": "value"}, "this_is_a_key", "value"),
        ({"thisIsAKey": "value"}, "this_is_a_key", "value"),
        ({"other_key": "value"}, "this_is_a_key", None),
    ],
)
def test_get_value_of_dict_with_different_naming_conventions(input_dict, key, expected_value):
    result = get_value_of_dict_with_different_naming_conventions(input_dict, key)
    assert result == expected_value
