import sys

import requests

from source.environment_variable_getter import EnvironmentVariableGetter
from source.logger_mixin import LoggerMixin


class MealieHandler(LoggerMixin):
    def __init__(self):
        super().__init__()

        self.mealie_base_url = EnvironmentVariableGetter.get("MEALIE_BASE_URL", "")
        self.mealie_api_key = EnvironmentVariableGetter.get("MEALIE_API_KEY", "")

        self.mealie_is_setup = True
        if not self.mealie_base_url or not self.mealie_api_key:
            self.mealie_is_setup = False
            self.log.info(
                "The configuration for Mealie is incomplete. "
                "If you want to add the items from the shopping list to Bring you have to set the environment "
                'variables "MEALIE_BASE_URL" and "MEALIE_API_KEY" (check out the README for more information). '
                "If you don't need this feature you can safely ignore this message."
            )
            return

        self.shopping_list_uuid = EnvironmentVariableGetter.get("MEALIE_SHOPPING_LIST_UUID", "")
        if self.shopping_list_uuid:
            self.log.info(f"Will filter items for shopping list with UUID {self.shopping_list_uuid}")
        else:
            self.log.info("No shopping list UUID specified --> Will add the ingredients of all shopping lists")

        self._try_api_key()

    def _try_api_key(self) -> None:
        response = requests.get(
            f"{self.mealie_base_url}/api/households/shopping/items?perPage=1",
            headers={"Authorization": f"Bearer {self.mealie_api_key}"},
            timeout=5,
        )
        try:
            response.raise_for_status()
            self.log.info("Connection to Mealie successful")
        except requests.exceptions.HTTPError:
            self.log.critical("Invalid Mealie URL or API key!")
            sys.exit(1)

    def get_items_on_shopping_list(self) -> list[dict]:
        self.log.debug("Getting items from shopping list")
        response = requests.get(
            f"{self.mealie_base_url}/api/households/shopping/items?perPage=-1",
            headers={"Authorization": f"Bearer {self.mealie_api_key}"},
            timeout=20,
        )
        response.raise_for_status()

        items_on_shopping_list = response.json()["items"]

        if self.shopping_list_uuid:
            items_on_shopping_list = [
                item for item in items_on_shopping_list if item["shoppingListId"] == self.shopping_list_uuid
            ]

        return items_on_shopping_list

    def delete_items_from_shopping_list(self, items_on_shopping_list: list[dict]) -> None:
        item_ids = [item["id"] for item in items_on_shopping_list]
        self.log.debug(f"Deleting {len(item_ids)} items from shopping list")
        for item_id in item_ids:
            response = requests.delete(
                url=f"{self.mealie_base_url}/api/households/shopping/items?ids={item_id}",
                headers={"Authorization": f"Bearer {self.mealie_api_key}"},
                timeout=20,
            )
            response.raise_for_status()
