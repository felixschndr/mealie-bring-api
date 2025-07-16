import pytest
from ingredient import Ingredient


@pytest.fixture
def food_name_singular() -> str:
    return "Berry"


@pytest.fixture
def food_name_plural() -> str:
    return "Berries"


@pytest.fixture
def ingredient_raw_base_data(food_name_singular, food_name_plural) -> dict:
    return {
        "disable_amount": False,
        "display": f"1 gram {food_name_singular}",
        "food": {
            "aliases": [],
            "created_at": "2025-07-16T19:37:10.688281+00:00",
            "description": "",
            "extras": {},
            "households_with_ingredient_food": [],
            "id": "00ba16f1-5d1e-4c2a-8a69-91e6af493cb4",
            "label": {
                "color": "#959595",
                "group_id": "173140fd-c29b-438a-9f9f-c689fb2c8919",
                "id": "e4cedfe5-523d-4c93-93a2-644de17bdc74",
                "name": "Baking",
            },
            "label_id": "e4cedfe5-523d-4c93-93a2-644de17bdc74",
            "name": food_name_singular,
            "plural_name": food_name_plural,
            "updated_at": "2025-07-16T19:37:10.688286+00:00",
        },
        "is_food": True,
        "note": "",
        "original_text": None,
        "quantity": 1.0,
        "reference_id": "4e6da2ee-782a-4e1d-b520-3a3f7ac0423e",
        "title": "",
        "unit": {
            "abbreviation": "g",
            "aliases": [],
            "created_at": "2025-07-16T19:36:59.820124+00:00",
            "description": "",
            "extras": {},
            "fraction": True,
            "id": "e98b35ec-b9e1-4c2d-a81f-274167acad98",
            "name": "Gram",
            "plural_abbreviation": "g",
            "plural_name": "Grams",
            "updated_at": "2025-07-16T19:36:59.820130+00:00",
            "use_abbreviation": False,
        },
    }


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


@pytest.mark.parametrize(
    argnames="ingredient_input, recipe_scale, expected_name, expected_specification",
    argvalues=[
        ("ingredient_raw_base_data", 1, "food_name_singular", "1 Gram"),
        ("ingredient_raw_base_data", 2, "food_name_plural", "2 Grams"),
        ("ingredient_raw_data_with_higher_quantity", 1, "food_name_plural", "2 Grams"),
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
    ],
)
def test_parse_ingredient(
    ingredient_input, recipe_scale, expected_name, expected_specification, request
):
    expected_ingredient = Ingredient(
        name=request.getfixturevalue(expected_name),
        specification=expected_specification,
    )

    actual_ingredient = Ingredient.from_raw_data(
        request.getfixturevalue(ingredient_input), recipe_scale
    )

    assert actual_ingredient == expected_ingredient
