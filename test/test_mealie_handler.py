import logging
from unittest.mock import MagicMock, patch

import pytest
import requests

from source.environment_variable_getter import EnvironmentVariableGetter
from source.ingredient import Ingredient
from source.mealie_handler import MealieHandler


def setup_handler_with_credentials(handler, mock_logger):
    handler.log = mock_logger.log
    handler.mealie_base_url = "https://mealie.example.com"
    handler.mealie_api_key = "test_api_key"
    return handler


@pytest.fixture
def mock_env_vars():
    return {
        "MEALIE_BASE_URL": "https://mealie.example.com",
        "MEALIE_API_KEY": "test_api_key",
        "MEALIE_SHOPPING_LIST_UUID": "test_uuid",
    }


@pytest.fixture
def mock_env_getter(mock_env_vars):
    def mock_get(var_name, default=None):
        if var_name in mock_env_vars:
            return mock_env_vars[var_name]
        if default is not None:
            return default
        raise RuntimeError(f'The environment variable "{var_name}" is not set!')

    with patch.object(EnvironmentVariableGetter, "get", side_effect=mock_get):
        yield


@pytest.fixture
def mock_response():
    response = MagicMock(spec=requests.Response)
    response.raise_for_status = MagicMock()
    response.json.return_value = {"items": []}
    return response


@pytest.fixture
def mock_requests(mock_response):
    with patch("requests.get", return_value=mock_response) as mock_get:
        with patch("requests.delete", return_value=mock_response) as mock_delete:
            yield mock_get, mock_delete


@pytest.fixture
def mealie_handler(monkeypatch, mock_logger, mock_env_getter, mock_requests):
    monkeypatch.setattr(MealieHandler, "_try_api_key", MagicMock())
    with patch.object(MealieHandler, "__init__", lambda self: None):
        handler = MealieHandler()
        setup_handler_with_credentials(handler, mock_logger)
        handler.shopping_list_uuid = "test_uuid"
        handler.mealie_is_setup = True
        return handler


def test_init_with_complete_config(mock_env_getter, mock_requests, mock_env_vars, mock_logger, monkeypatch):
    def mock_get_logger(name=None):
        return mock_logger.log

    monkeypatch.setattr(logging, "getLogger", mock_get_logger)

    with patch.object(
        EnvironmentVariableGetter, "get", side_effect=lambda var_name, default="": mock_env_vars.get(var_name, default)
    ):
        with patch.object(MealieHandler, "_try_api_key"):
            handler = MealieHandler()

        assert handler.mealie_base_url == "https://mealie.example.com"
        assert handler.mealie_api_key == "test_api_key"
        assert handler.shopping_list_uuid == "test_uuid"
        assert handler.mealie_is_setup is True
        mock_logger.log.info.assert_any_call(
            f"Will filter items for shopping list with UUID {handler.shopping_list_uuid}"
        )


def test_init_with_incomplete_config(monkeypatch, mock_env_getter, mock_logger):
    def mock_get_logger(name=None):
        return mock_logger.log

    monkeypatch.setattr(logging, "getLogger", mock_get_logger)

    with patch.object(EnvironmentVariableGetter, "get", side_effect=lambda var_name, default="": ""):
        with patch.object(MealieHandler, "_try_api_key") as mock_try_api_key:
            handler = MealieHandler()

            assert handler.mealie_base_url == ""
            assert handler.mealie_api_key == ""
            assert handler.mealie_is_setup is False
            mock_try_api_key.assert_not_called()
            mock_logger.log.info.assert_any_call(
                "The configuration for Mealie is incomplete. "
                "If you want to add the items from the shopping list to Bring you have to set the environment "
                'variables "MEALIE_BASE_URL" and "MEALIE_API_KEY" (check out the README for more information). '
                "If you don't need this feature you can safely ignore this message."
            )


def test_init_with_mealie_set_up_but_no_shopping_list_uuid(
    mock_env_getter, mock_env_vars, mock_requests, mock_logger, monkeypatch
):
    # Create a modified env vars dictionary without the UUID
    env_vars_without_uuid = mock_env_vars.copy()
    del env_vars_without_uuid["MEALIE_SHOPPING_LIST_UUID"]

    # Mock the logging.getLogger function to return our mock logger
    def mock_get_logger(name=None):
        return mock_logger.log

    monkeypatch.setattr(logging, "getLogger", mock_get_logger)

    with patch.object(
        EnvironmentVariableGetter,
        "get",
        side_effect=lambda var_name, default="": env_vars_without_uuid.get(var_name, default),
    ):
        with patch.object(MealieHandler, "_try_api_key") as mock_try_api_key:
            handler = MealieHandler()

            assert handler.mealie_base_url == "https://mealie.example.com"
            assert handler.mealie_api_key == "test_api_key"
            assert handler.shopping_list_uuid == ""
            assert handler.mealie_is_setup is True
            mock_try_api_key.assert_called_once()
            mock_logger.log.info.assert_any_call(
                "No shopping list UUID specified --> Will add the ingredients of all shopping lists"
            )


def test_try_api_key_success(mock_env_getter, mock_response, mock_logger):
    with patch("requests.get", return_value=mock_response):
        with patch.object(MealieHandler, "_try_api_key"):
            handler = MealieHandler()

        setup_handler_with_credentials(handler, mock_logger)

        MealieHandler._try_api_key(handler)

        mock_response.raise_for_status.assert_called_once()


def test_try_api_key_failure(mock_env_getter, mock_response, mock_logger):
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API key invalid")

    with patch("requests.get", return_value=mock_response):
        with patch("sys.exit") as mock_exit:
            with patch.object(MealieHandler, "_try_api_key"):
                handler = MealieHandler()

            setup_handler_with_credentials(handler, mock_logger)

            MealieHandler._try_api_key(handler)

            mock_exit.assert_called_once_with(1)


def test_get_ingredients_from_shopping_list_with_uuid(mealie_handler, mock_requests):
    mock_get, _ = mock_requests
    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        "items": [
            {"id": "item1", "shoppingListId": "test_uuid", "display": "1 gram Berry"},
            {"id": "item2", "shoppingListId": "other_uuid", "display": "2 Apples"},
        ]
    }

    with patch.object(mealie_handler, "_delete_items_from_shopping_list") as mock_delete:
        with patch.object(Ingredient, "from_raw_data", return_value=MagicMock(spec=Ingredient)) as mock_from_raw_data:
            result = mealie_handler.get_ingredients_from_shopping_list()

            mock_get.assert_called_once_with(
                f"{mealie_handler.mealie_base_url}/api/households/shopping/items?perPage=-1",
                headers={"Authorization": f"Bearer {mealie_handler.mealie_api_key}"},
                timeout=20,
            )
            mock_delete.assert_called_once_with(["item1"])
            assert mock_from_raw_data.call_count == 1
            assert len(result) == 1


def test_get_ingredients_from_shopping_list_without_uuid(mealie_handler, mock_requests):
    mealie_handler.shopping_list_uuid = ""
    mock_get, _ = mock_requests
    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        "items": [
            {"id": "item1", "shoppingListId": "uuid1", "display": "1 gram Berry"},
            {"id": "item2", "shoppingListId": "uuid2", "display": "2 grams Apple"},
        ]
    }

    with patch.object(mealie_handler, "_delete_items_from_shopping_list") as mock_delete:
        with patch.object(Ingredient, "from_raw_data", return_value=MagicMock(spec=Ingredient)) as mock_from_raw_data:
            result = mealie_handler.get_ingredients_from_shopping_list()

            mock_get.assert_called_once_with(
                f"{mealie_handler.mealie_base_url}/api/households/shopping/items?perPage=-1",
                headers={"Authorization": f"Bearer {mealie_handler.mealie_api_key}"},
                timeout=20,
            )
            mock_delete.assert_called_once_with(["item1", "item2"])
            assert mock_from_raw_data.call_count == 2
            assert len(result) == 2


def test_delete_items_from_shopping_list(mealie_handler, mock_requests):
    _, mock_delete = mock_requests
    item_ids = ["item1", "item2", "item3"]

    mealie_handler._delete_items_from_shopping_list(item_ids)

    assert mock_delete.call_count == 3
    for i, item_id in enumerate(item_ids):
        assert (
            mock_delete.call_args_list[i][1]["url"]
            == f"{mealie_handler.mealie_base_url}/api/households/shopping/items?ids={item_id}"
        )
        assert mock_delete.call_args_list[i][1]["headers"] == {
            "Authorization": f"Bearer {mealie_handler.mealie_api_key}"
        }
        assert mock_delete.call_args_list[i][1]["timeout"] == 20
