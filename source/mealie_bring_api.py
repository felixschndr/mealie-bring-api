import asyncio
import logging
from typing import Union

from flask import Blueprint, Flask, Request, request

from source.bring_handler import BringHandler
from source.environment_variable_getter import EnvironmentVariableGetter
from source.ingredient import Ingredient, IngredientWithAmountsDisabled
from source.logger_mixin import LoggerMixin


class MealieBringAPI:
    def __init__(self):
        self.host = EnvironmentVariableGetter.get("HTTP_HOST", "0.0.0.0")  # nosec: B104
        self.port = int(EnvironmentVariableGetter.get("HTTP_PORT", 8742))
        self.basepath = EnvironmentVariableGetter.get("HTTP_BASE_PATH", "")

        self.logger = self._create_logger()
        self.loop = self._create_event_loop()
        self.bring_handler = self._create_bring_handler(self.loop)
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
        def webhook_handler() -> str:
            return self.process_webhook(request)

        @base_bp.route("/status", methods=["GET"])
        def status_handler() -> str:
            self.logger.log.debug("Got a status request")
            return "OK"

        app.register_blueprint(base_bp)
        return app

    def process_webhook(self, request_obj: Request) -> str:
        data = request_obj.get_json(force=True)
        self.logger.log.info(f'Received recipe "{data["content"]["name"]}" from "{request_obj.remote_addr}"')

        ingredients_to_add = self.process_recipe_data(data)

        self.logger.log.info(f"Adding ingredients to Bring: {ingredients_to_add}")
        self.loop.run_until_complete(self.bring_handler.add_items(ingredients_to_add))
        self.loop.run_until_complete(self.bring_handler.notify_users_about_changes_in_list())

        return "OK"

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

        ingredients_to_add = []
        for ingredient_raw_data in data["content"]["recipe_ingredient"]:
            self.logger.log.debug(f"Parsing ingredient {ingredient_raw_data}")
            if not enable_amount or ingredient_raw_data["food"] is None:
                # The second case happens if the data is only in the note and the food is not properly set
                # This often is the case when a recipe is imported from some source and not properly formatted yet
                ingredients_to_add.append(IngredientWithAmountsDisabled.from_raw_data(ingredient_raw_data))
            else:
                if Ingredient.in_household(ingredient_raw_data):
                    self.logger.log.info(f"Ignoring ingredient {ingredient_raw_data['food']['name']}")
                    continue
                ingredients_to_add.append(Ingredient.from_raw_data(ingredient_raw_data, recipe_scale))

        return ingredients_to_add

    def run(self) -> None:
        self.logger.log.info(f"Listening on {self.host}:{self.port}{self.basepath}")
        self.app.run(host=self.host, port=self.port)


app = Flask(__name__)

if __name__ == "__main__":
    mealie_app = MealieBringAPI()
    app = mealie_app.app
    mealie_app.run()
