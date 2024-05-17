import os
import sys

from dotenv import load_dotenv
from python_bring_api.bring import Bring
from python_bring_api.types import BringNotificationType

from ingredient import Ingredient
from logger_mixin import LoggerMixin


class BringHandler(LoggerMixin):
    def __init__(self):
        super().__init__()

        load_dotenv()
        self.username = os.getenv("BRING_USERNAME")
        self.password = os.getenv("BRING_PASSWORD")
        self.list_name = os.getenv("BRING_LIST_NAME")
        self.ignored_ingredients_input = os.getenv("IGNORED_INGREDIENTS")
        self.def_check_if_environment_variables_are_set()

        self.bring = self.login_into_bring()

        self.list_uuid = self.determine_list_uuid()
        self.ignored_ingredients = self.parse_ignored_ingredients()

    def def_check_if_environment_variables_are_set(self) -> None:
        if not self.username or not self.password or not self.list_name:
            self.log.critical(
                "Ensure that the environment variables BRING_USERNAME, BRING_PASSWORD and BRING_LIST_NAME are set"
            )
            sys.exit(1)
        self.log.debug("Bring credentials and list name are set")

        if not self.ignored_ingredients_input:
            self.log.info(
                'The variable IGNORED_INGREDIENTS is not set. All ingredients will be added. Consider adding something like "Salt,Pepper"'
            )

    def login_into_bring(self) -> Bring:
        bring = Bring(self.username, self.password)
        self.log.info("Attempting the login into Bring")
        bring.login()
        self.log.info("Login successful")

        return bring

    def determine_list_uuid(self) -> str:
        bring_list_uuid = None
        bring_list_name_lower = self.list_name.lower()
        for bring_list in self.bring.loadLists()["lists"]:
            if bring_list["name"].lower() == bring_list_name_lower:
                bring_list_uuid = bring_list["listUuid"]
                break

        if not bring_list_uuid:
            self.log.critical(
                f"Could not find a bring list with the name {self.list_name}"
            )
            sys.exit(1)

        self.log.info(
            f"Found the bring list {self.list_name} (UUID: {bring_list_uuid})"
        )

        return bring_list_uuid

    def parse_ignored_ingredients(self) -> list[str]:
        ignored_ingredients = []

        if not self.ignored_ingredients_input:
            return ignored_ingredients

        for ingredient in self.ignored_ingredients_input.replace(", ", ",").split(","):
            ignored_ingredients.append(ingredient.lower())

        if ignored_ingredients:
            self.log.info(f"Ignoring ingredients {ignored_ingredients}")

        return ignored_ingredients

    def add_item_to_list(self, ingredient: Ingredient) -> None:
        self.log.debug(f"Adding ingredient to Bring: {ingredient}")

        if ingredient.specification:
            self.bring.saveItem(self.list_uuid, ingredient.food, ingredient.specification)
        else:
            self.bring.saveItem(self.list_uuid, ingredient.food)

    def notify_users_about_changes_in_list(self) -> None:
        self.log.debug("Notifying users about changes in shopping list")
        self.bring.notify(self.list_uuid, BringNotificationType.CHANGED_LIST)
