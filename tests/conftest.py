import logging
from unittest.mock import MagicMock

import pytest
from source.ingredient import Ingredient
from source.logger_mixin import LoggerMixin


@pytest.fixture
def mock_logger() -> MagicMock:
    logger = MagicMock(spec=LoggerMixin)
    logger.log = MagicMock(spec=logging.Logger)
    return logger


@pytest.fixture
def food_name_singular() -> str:
    return "Berry"


@pytest.fixture
def food_name_plural() -> str:
    return "Berries"


@pytest.fixture
def unit() -> dict:
    return {
        "abbreviation": "g",
        "name": "Gram",
        "plural_abbreviation": "g",
        "plural_name": "Grams",
        "use_abbreviation": False,
    }


@pytest.fixture
def ingredient_raw_base_data(food_name_singular: str, food_name_plural: str, unit: dict) -> dict:
    return {
        "display": f"1 gram {food_name_singular}",
        "food": {
            "name": food_name_singular,
            "plural_name": food_name_plural,
        },
        "note": "",
        "quantity": 1.0,
        "unit": unit,
    }


@pytest.fixture
def example_request(ingredient_raw_base_data: dict, unit: dict) -> dict:
    return {
        "content": {
            "recipe_servings": 5.0,
            "recipe_yield_quantity": 0.0,
            "recipe_yield": None,
            "recipe_ingredient": [
                ingredient_raw_base_data,
                {
                    "quantity": 1.0,
                    "unit": None,
                    "food": {
                        "name": "Apple",
                        "plural_name": None,
                    },
                    "note": "",
                    "display": "1 Agavendicksaft",
                },
                {
                    "quantity": 5.0,
                    "unit": {
                        "name": "Spoon",
                        "plural_name": "Spoons",
                    },
                    "food": {
                        "name": "Salt",
                        "plural_name": "Salt",
                    },
                    "note": "",
                    "display": "5 Spoons Salt",
                },
                {
                    "display": 4,
                    "food": None,
                    "note": "",
                    "quantity": 4.0,
                    "referenced_recipe": {
                        "name": "Test Recipe 2",
                        "recipe_ingredient": [
                            {
                                "display": "1 gram Pepper",
                                "food": {
                                    "name": "Pepper",
                                    "plural_name": "Pepper",
                                },
                                "note": "",
                                "quantity": 1.0,
                                "title": "",
                                "unit": unit,
                            },
                            {
                                "display": "1.5 Liters Water",
                                "food": {
                                    "name": "Water",
                                    "plural_name": "Water",
                                },
                                "note": "",
                                "quantity": 1.5,
                                "title": "",
                                "unit": {
                                    "abbreviation": "l",
                                    "name": "Liter",
                                    "plural_abbreviation": "",
                                    "plural_name": "Liters",
                                    "use_abbreviation": False,
                                },
                            },
                            {
                                "referenced_recipe": {
                                    "name": "Test Recipe 3",
                                    "recipe_ingredient": [
                                        {
                                            "display": "0.5 Kilograms Sugar",
                                            "food": {"name": "Sugar", "plural_name": "Sugar"},
                                            "note": "",
                                            "quantity": 0.5,
                                            "unit": {
                                                "abbreviation": "kg",
                                                "name": "Kilogram",
                                                "plural_abbreviation": "",
                                                "plural_name": "Kilograms",
                                                "use_abbreviation": False,
                                            },
                                        },
                                        {
                                            "display": "Chocolate",
                                            "food": {"name": "Chocolate"},
                                            "note": "",
                                            "quantity": None,
                                            "unit": None,
                                        },
                                    ],
                                },
                                "recipe_servings": 1.0,
                                "recipe_yield": None,
                                "recipe_yield_quantity": 0.0,
                            },
                        ],
                        "recipe_servings": 1.0,
                        "recipe_yield": None,
                        "recipe_yield_quantity": 0.0,
                    },
                    "title": "",
                    "unit": None,
                },
            ],
            "settings": {},
        },
        "scaled_amount": 2.0,
    }


@pytest.fixture
def first_ingredient(food_name_singular: str) -> Ingredient:
    return Ingredient(name=food_name_singular)


@pytest.fixture
def second_ingredient() -> Ingredient:
    return Ingredient(name="Bread")
