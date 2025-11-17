import asyncio
import copy
import logging
from typing import Union

from flask import Blueprint, Flask, request
from source.bring_handler import BringHandler
from source.environment_variable_getter import EnvironmentVariableGetter
from source.ingredient import Ingredient, IngredientWithAmountsDisabled
from source.logger_mixin import LoggerMixin
from source.mealie_handler import MealieHandler


class MealieBringAPI:
    def __init__(self):
        self.host = EnvironmentVariableGetter.get("HTTP_HOST", "0.0.0.0")  # nosec: B104
        self.port = int(EnvironmentVariableGetter.get("HTTP_PORT", 8742))
        self.basepath = EnvironmentVariableGetter.get("HTTP_BASE_PATH", "")

        self.logger = self._create_logger()
        self.loop = self._create_event_loop()
        self.bring_handler = self._create_bring_handler(self.loop)
        self.mealie_handler = MealieHandler()
        self.app = self._create_app()

    @staticmethod
    def _create_logger() -> LoggerMixin:
        logger = LoggerMixin()
        logger.log = logging.getLogger("Main")
        return logger

    @staticmethod
    def _create_event_loop() -> asyncio.AbstractEventLoop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

    @staticmethod
    def _create_bring_handler(loop: asyncio.AbstractEventLoop) -> BringHandler:
        return BringHandler(loop)

    def _create_app(self) -> Flask:
        base_bp = Blueprint("base_bp", __name__, url_prefix=self.basepath)

        @base_bp.route("/", methods=["POST"])
        def copy_ingredients_from_recipe_to_bring() -> str:
            data = request.get_json(force=True)
            self.logger.log.info(f'Received recipe "{data["content"]["name"]}" from "{request.remote_addr}"')

            self._add_ingredients_to_bring(self.process_recipe_data(data))

            return "OK"

        @base_bp.route("/move-ingredients-from-shopping-list", methods=["POST"])
        def move_ingredients_from_shopping_list_to_bring() -> str | tuple[str, int]:
            if not self.mealie_handler.mealie_is_setup:
                self.logger.log.warning("Mealie is not setup! See the logs above for more information.")
                return "", 400

            self.logger.log.info("Moving ingredients from shopping list to Bring")

            items_on_shopping_list = self.mealie_handler.get_items_on_shopping_list()
            self._add_ingredients_to_bring([Ingredient.from_raw_data(item) for item in items_on_shopping_list])
            self.mealie_handler.delete_items_from_shopping_list(items_on_shopping_list)

            return "OK"

        @base_bp.route("/status", methods=["GET"])
        def status_handler() -> str:
            self.logger.log.debug("Got a status request")
            return "OK"

        app.register_blueprint(base_bp)
        return app

    def process_recipe_data(self, data: dict) -> list[Union[Ingredient, IngredientWithAmountsDisabled]]:
        # was deprecated in https://github.com/mealie-recipes/mealie/pull/5684
        enable_amount = not data["content"]["settings"].get("disable_amount", False)
        if enable_amount:
            self.logger.log.debug("This recipe has its ingredient amount enabled")
        else:
            self.logger.log.warning(
                "This recipe has its ingredient amount this disabled --> Its ingredients will not be checked whether they are supposed to be ignored"
            )

        recipe_scale = data.get("recipe_scale", 1)
        self.logger.log.debug(f"Recipe scale is {recipe_scale}")

        unparsed_ingredients = self._extract_ingredients_data_from_recipe_data(data["content"]["recipe_ingredient"])

        parsed_ingredients_to_add = []
        for ingredient_raw_data in unparsed_ingredients:
            self.logger.log.debug(f"Parsing ingredient {ingredient_raw_data}")
            if not enable_amount or ingredient_raw_data["food"] is None:
                # The second case happens if the data is only in the note and the food is not properly set,
                # This often is the case when a recipe is imported from some source and not properly formatted yet
                parsed_ingredients_to_add.append(IngredientWithAmountsDisabled.from_raw_data(ingredient_raw_data))
            else:
                if Ingredient.in_household(ingredient_raw_data):
                    self.logger.log.info(f"Ignoring ingredient {ingredient_raw_data['food']['name']}")
                    continue
                parsed_ingredients_to_add.append(Ingredient.from_raw_data(ingredient_raw_data, recipe_scale))

        return parsed_ingredients_to_add

    def _extract_ingredients_data_from_recipe_data(self, recipe_ingredients: list[dict]) -> list[dict]:
        unparsed_ingredients = []
        for ingredient_of_recipe in recipe_ingredients:
            if referenced_recipe := ingredient_of_recipe.get("referenced_recipe", None):
                self.logger.log.debug(f"Ingredient is a recipe: {referenced_recipe['name']}")
                parent_quantity = ingredient_of_recipe.get("quantity", 1.0)
                for ingredient_of_referenced_recipe in referenced_recipe["recipe_ingredient"]:
                    ingredient_copy = copy.deepcopy(ingredient_of_referenced_recipe)
                    if isinstance(ingredient_copy.get("quantity"), (int, float)):
                        ingredient_copy["quantity"] = ingredient_copy["quantity"] * parent_quantity
                    unparsed_ingredients.append(ingredient_copy)
            else:
                unparsed_ingredients.append(ingredient_of_recipe)
        return unparsed_ingredients

    def _add_ingredients_to_bring(self, ingredients_to_add: list[Ingredient]) -> None:
        if not ingredients_to_add:
            self.logger.log.warning("There are no ingredients to add")
            return

        self.logger.log.info(f"Adding ingredients to Bring: {ingredients_to_add}")
        self.loop.run_until_complete(self.bring_handler.add_items(ingredients_to_add))

        self.loop.run_until_complete(self.bring_handler.notify_users_about_changes_in_list())

    def run(self) -> None:
        self.logger.log.info(f"Listening on {self.host}:{self.port}{self.basepath}")
        self.app.run(host=self.host, port=self.port)


app = Flask(__name__)

if __name__ == "__main__":
    mealie_app = MealieBringAPI()
    app = mealie_app.app
    mealie_app.run()
