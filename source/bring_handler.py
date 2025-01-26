import asyncio
import sys

import aiohttp
from bring_api import Bring, BringItemOperation, BringNotificationType
from environment_variable_getter import EnvironmentVariableGetter
from ingredient import Ingredient
from logger_mixin import LoggerMixin


class BringHandler(LoggerMixin):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()

        self.bring = loop.run_until_complete(self.initialize())
        self.list_uuid = loop.run_until_complete(self.determine_list_uuid())

    async def initialize(self) -> Bring:
        username = EnvironmentVariableGetter.get("BRING_USERNAME")
        password = EnvironmentVariableGetter.get("BRING_PASSWORD")

        session = aiohttp.ClientSession()
        bring = Bring(session, username, password)
        self.log.info("Attempting the login into Bring")
        await bring.login()
        self.log.info("Login successful")

        return bring

    async def determine_list_uuid(self) -> str:
        list_name = EnvironmentVariableGetter.get("BRING_LIST_NAME")

        list_name_lower = list_name.lower()
        for bring_list in (await self.bring.load_lists())["lists"]:
            if bring_list["name"].lower() == list_name_lower:
                bring_list_uuid = bring_list["listUuid"]
                self.log.info(f'Found the list with the name "{list_name}" (UUID: {bring_list_uuid})')
                return bring_list_uuid

        self.log.critical(f'Can not find a list with the name "{list_name}"')
        sys.exit(1)

    async def add_items(self, ingredients: list[Ingredient]) -> None:
        items = [ingredient.to_dict() for ingredient in ingredients]
        await self.bring.batch_update_list(self.list_uuid, items, BringItemOperation.ADD)

    async def notify_users_about_changes_in_list(self) -> None:
        self.log.debug("Notifying users about changes in shopping list")
        await self.bring.notify(self.list_uuid, BringNotificationType.CHANGED_LIST)
