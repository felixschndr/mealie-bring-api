import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from source.bring_handler import BringHandler
from source.mealie_bring_api import Flask, MealieBringAPI


@pytest.fixture
def mock_event_loop():
    loop = MagicMock(spec=asyncio.AbstractEventLoop)
    loop.run_until_complete = MagicMock()
    return loop


@pytest.fixture
def mock_bring_handler():
    handler = MagicMock(spec=BringHandler)
    handler.add_items = AsyncMock()
    handler.notify_users_about_changes_in_list = AsyncMock()
    return handler


@pytest.fixture
def mock_flask_app():
    app = MagicMock(spec=Flask)
    app.register_blueprint = MagicMock()
    app.run = MagicMock()
    return app


@pytest.fixture
def mealie_app(monkeypatch, mock_logger, mock_event_loop, mock_bring_handler, mock_flask_app):
    monkeypatch.setattr(MealieBringAPI, "_create_logger", lambda self: mock_logger)
    monkeypatch.setattr(MealieBringAPI, "_create_event_loop", lambda self: mock_event_loop)
    monkeypatch.setattr(MealieBringAPI, "_create_bring_handler", lambda self, loop: mock_bring_handler)
    monkeypatch.setattr(MealieBringAPI, "_create_app", lambda self: mock_flask_app)

    return MealieBringAPI()


def test_process_recipe_data_with_enabled_amount(mealie_app, example_request):
    example_request["content"]["settings"]["disable_amount"] = False

    with patch("source.mealie_bring_api.Ingredient.in_household", return_value=False):
        with patch("source.mealie_bring_api.Ingredient.from_raw_data") as mock_from_raw_data:
            with patch(
                "source.mealie_bring_api.IngredientWithAmountsDisabled.from_raw_data"
            ) as mock_disabled_from_raw_data:
                result = mealie_app.process_recipe_data(example_request)

                expected_ingredient_calls = 0
                expected_disabled_calls = 0

                for ingredient in example_request["content"]["recipe_ingredient"]:
                    if ingredient["food"] is None:
                        expected_disabled_calls += 1
                    else:
                        expected_ingredient_calls += 1

                assert mock_from_raw_data.call_count == expected_ingredient_calls
                assert mock_disabled_from_raw_data.call_count == expected_disabled_calls
                assert len(result) == mock_from_raw_data.call_count + mock_disabled_from_raw_data.call_count


def test_process_recipe_data_with_disabled_amount(mealie_app, example_request):
    example_request["content"]["settings"]["disable_amount"] = True

    with patch("source.mealie_bring_api.IngredientWithAmountsDisabled.from_raw_data") as mock_from_raw_data:
        result = mealie_app.process_recipe_data(example_request)

        assert mock_from_raw_data.call_count == len(example_request["content"]["recipe_ingredient"])
        assert len(result) == mock_from_raw_data.call_count


def test_process_recipe_data_with_household_ingredient(mealie_app, example_request):
    example_request["content"]["settings"]["disable_amount"] = False

    def mock_in_household(ingredient_data):
        return ingredient_data == example_request["content"]["recipe_ingredient"][0]

    with patch("source.mealie_bring_api.Ingredient.in_household", side_effect=mock_in_household):
        with patch("source.mealie_bring_api.Ingredient.from_raw_data") as mock_from_raw_data:
            mealie_app.process_recipe_data(example_request)

            assert mock_from_raw_data.call_count == len(example_request["content"]["recipe_ingredient"]) - 1


def test_add_ingredients_to_bring_empty_list(mealie_app):
    mealie_app._add_ingredients_to_bring([])

    mealie_app.bring_handler.add_items.assert_not_called()
    mealie_app.bring_handler.notify_users_about_changes_in_list.assert_not_called()


def test_add_ingredients_to_bring_with_ingredients(mealie_app, first_ingredient, second_ingredient):
    ingredients = [first_ingredient, second_ingredient]

    mealie_app._add_ingredients_to_bring(ingredients)

    mealie_app.bring_handler.add_items.assert_called_once_with(ingredients)
    mealie_app.bring_handler.notify_users_about_changes_in_list.assert_called_once()
