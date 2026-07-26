import asyncio
import copy
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from source.bring_handler import BringHandler
from source.ingredient import Ingredient
from source.logger_mixin import LoggerMixin
from source.mealie_bring_api import Flask, MealieBringAPI
from source.mealie_handler import MealieHandler


@pytest.fixture
def mock_event_loop():
    loop = MagicMock(spec=asyncio.AbstractEventLoop)
    loop.run_until_complete = MagicMock()
    loop.stop = MagicMock()
    return loop


@pytest.fixture
def mock_bring_handler():
    handler = MagicMock(spec=BringHandler)
    handler.add_items = AsyncMock()
    handler.notify_users_about_changes_in_list = AsyncMock()
    handler.logout = AsyncMock()
    return handler


@pytest.fixture
def mock_flask_app():
    app = MagicMock(spec=Flask)
    app.register_blueprint = MagicMock()
    app.run = MagicMock()
    return app


@pytest.fixture
def mock_mealie_handler():
    return MagicMock(spec=MealieHandler)


@pytest.fixture
def mealie_app(monkeypatch, mock_event_loop, mock_bring_handler, mock_flask_app, mock_mealie_handler):
    monkeypatch.setattr(MealieBringAPI, "_create_logger", lambda self: LoggerMixin())
    monkeypatch.setattr(MealieBringAPI, "_create_event_loop", lambda self: mock_event_loop)
    monkeypatch.setattr(MealieBringAPI, "_create_bring_handler", lambda self, loop: mock_bring_handler)
    monkeypatch.setattr(MealieBringAPI, "_create_app", lambda self: mock_flask_app)
    monkeypatch.setattr("source.mealie_bring_api.MealieHandler", lambda: mock_mealie_handler)

    return MealieBringAPI()


def test_process_recipe_data_with_enabled_amount(mealie_app, example_request):
    def __eq__(self, other):
        return self.name == other.name and self.specification == other.specification

    Ingredient.__eq__ = __eq__
    expected_ingredients = [
        Ingredient(name="Berry", specification="1 Gram"),
        Ingredient(name="Apple", specification="1"),
        Ingredient(name="Salt", specification="5 Spoons"),
        Ingredient(name="Pepper", specification="4 Grams"),
        Ingredient(name="Water", specification="6 Liters"),
        Ingredient(name="Sugar", specification="2 Kilograms"),
        Ingredient(name="Chocolate", specification=""),
    ]

    result = mealie_app.process_recipe_data(example_request)

    assert result == expected_ingredients


def test_process_recipe_data_with_disabled_amount(mealie_app, example_request):
    example_request["content"]["settings"]["disable_amount"] = True

    with patch("source.mealie_bring_api.IngredientWithAmountsDisabled.from_raw_data") as mock_from_raw_data:
        unparsed_ingredients = mealie_app._extract_ingredients_data_from_recipe_data(
            example_request["content"]["recipe_ingredient"]
        )

        result = mealie_app.process_recipe_data(example_request)

        assert mock_from_raw_data.call_count == len(unparsed_ingredients)
        assert len(result) == mock_from_raw_data.call_count


def test_process_recipe_data_with_household_ingredient(mealie_app, example_request):
    unparsed_ingredients_ = mealie_app._extract_ingredients_data_from_recipe_data(
        example_request["content"]["recipe_ingredient"]
    )
    target_ingredient = unparsed_ingredients_[0]

    def mock_in_household(ingredient_data):
        return ingredient_data == target_ingredient

    with patch("source.mealie_bring_api.Ingredient.in_household", side_effect=mock_in_household):
        with patch("source.mealie_bring_api.Ingredient.from_raw_data") as mock_from_raw_data:
            mealie_app.process_recipe_data(example_request)

            expected_total_with_amount = len([i for i in unparsed_ingredients_ if i.get("food") is not None])
            assert mock_from_raw_data.call_count == expected_total_with_amount - 1


def test_process_recipe_data_ignores_empty_parsed_ingredient(mealie_app, example_request, caplog):
    result_without_empty_ingredient = mealie_app.process_recipe_data(copy.deepcopy(example_request))
    emtpy_ingredient_data = {
        "display": "",
        "food": None,
        "note": "",
        "quantity": 0.0,
        "unit": None,
    }
    example_request["content"]["recipe_ingredient"].append(emtpy_ingredient_data)

    result_with_empty_ingredient = mealie_app.process_recipe_data(example_request)

    assert result_with_empty_ingredient == result_without_empty_ingredient
    assert f"Ignoring empty ingredient {emtpy_ingredient_data}" in caplog.text


def test_add_ingredients_to_bring_empty_list(mealie_app):
    mealie_app._add_ingredients_to_bring([])

    mealie_app.bring_handler.add_items.assert_not_called()
    mealie_app.bring_handler.notify_users_about_changes_in_list.assert_not_called()


def test_add_ingredients_to_bring_with_ingredients(mealie_app, first_ingredient, second_ingredient):
    ingredients = [first_ingredient, second_ingredient]

    mealie_app._add_ingredients_to_bring(ingredients)

    mealie_app.bring_handler.add_items.assert_called_once_with(ingredients)
    mealie_app.bring_handler.notify_users_about_changes_in_list.assert_called_once()


def test_move_ingredients_from_shopping_list_to_bring(mealie_app):
    items_on_shopping_list = [{"id": "1"}, {"id": "2"}]
    mealie_app.mealie_handler.get_items_on_shopping_list.return_value = items_on_shopping_list

    with (
        patch("source.mealie_bring_api.Ingredient.from_raw_data") as mock_from_raw_data,
        patch.object(mealie_app, "_add_ingredients_to_bring") as mock_add_ingredients_to_bring,
    ):
        mealie_app._move_ingredients_from_shopping_list_to_bring()

    assert mock_from_raw_data.call_count == len(items_on_shopping_list)
    mock_add_ingredients_to_bring.assert_called_once()
    mealie_app.mealie_handler.delete_items_from_shopping_list.assert_called_once_with(items_on_shopping_list)


def test_schedule_move_ingredients_runs_immediately_when_debounce_disabled(mealie_app):
    mealie_app.move_ingredients_debounce_seconds = 0

    with patch.object(mealie_app, "_move_ingredients_from_shopping_list_to_bring") as mock_move:
        mealie_app._schedule_move_ingredients_from_shopping_list()

    mock_move.assert_called_once()
    assert mealie_app.move_debounce_timer is None


def test_schedule_move_ingredients_starts_timer_when_debounce_enabled(mealie_app):
    mealie_app.move_ingredients_debounce_seconds = 2

    with patch("source.mealie_bring_api.threading.Timer") as mock_timer_cls:
        mock_timer_instance = MagicMock()
        mock_timer_cls.return_value = mock_timer_instance

        mealie_app._schedule_move_ingredients_from_shopping_list()

    mock_timer_cls.assert_called_once_with(2, mealie_app._run_debounced_move_ingredients_from_shopping_list)
    mock_timer_instance.start.assert_called_once()
    assert mealie_app.move_debounce_timer is mock_timer_instance


def test_schedule_move_ingredients_cancels_previous_pending_timer(mealie_app):
    mealie_app.move_ingredients_debounce_seconds = 2
    previous_timer = MagicMock()
    mealie_app.move_debounce_timer = previous_timer

    with patch("source.mealie_bring_api.threading.Timer") as mock_timer_cls:
        mock_timer_cls.return_value = MagicMock()
        mealie_app._schedule_move_ingredients_from_shopping_list()

    previous_timer.cancel.assert_called_once()


def test_run_debounced_move_ingredients_clears_timer_and_moves(mealie_app):
    mealie_app.move_debounce_timer = MagicMock()

    with patch.object(mealie_app, "_move_ingredients_from_shopping_list_to_bring") as mock_move:
        mealie_app._run_debounced_move_ingredients_from_shopping_list()

    assert mealie_app.move_debounce_timer is None
    mock_move.assert_called_once()


def test_handle_stop_signal_stops_loop_and_logs_out(mealie_app, monkeypatch):
    with patch("source.mealie_bring_api.sys.exit") as mock_exit:
        mealie_app._handle_stop_signal(signal_number=2, _frame=None)

        mealie_app.bring_handler.logout.assert_called_once()
        mealie_app.loop.stop.assert_called_once()
        mock_exit.assert_called_once_with(0)


def test_handle_stop_signal_flushes_pending_debounced_move(mealie_app):
    pending_timer = MagicMock()
    mealie_app.move_debounce_timer = pending_timer

    with (
        patch("source.mealie_bring_api.sys.exit"),
        patch.object(mealie_app, "_move_ingredients_from_shopping_list_to_bring") as mock_move,
    ):
        mealie_app._handle_stop_signal(signal_number=2, _frame=None)

    pending_timer.cancel.assert_called_once()
    mock_move.assert_called_once()
    assert mealie_app.move_debounce_timer is None
