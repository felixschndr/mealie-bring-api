import asyncio
import logging

from bring_handler import BringHandler
from environment_variable_getter import EnvironmentVariableGetter
from flask import Blueprint, Flask, request
from ingredient import Ingredient, IngredientWithAmountsDisabled
from logger_mixin import LoggerMixin

app = Flask(__name__)

basepath = EnvironmentVariableGetter.get("HTTP_BASE_PATH", "")
base_bp = Blueprint("base_bp", __name__, url_prefix=f"{basepath}")


@base_bp.route("/", methods=["POST"])
def webhook_handler() -> str:
    data = request.get_json(force=True)

    logger.log.info(f'Received recipe "{data["content"]["name"]}" from "{request.remote_addr}"')

    enable_amount = not data["content"]["settings"]["disable_amount"]
    if enable_amount:
        logger.log.debug("This recipe has its ingredient amount enabled")
    else:
        logger.log.warning(
            "This recipe has its ingredient amount this disabled --> Its ingredients will not be checked whether they are supposed to be ignored"
        )

    ingredients_to_add = []
    ingredients_raw_data = data["content"]["recipe_ingredient"]
    for ingredient_raw_data in ingredients_raw_data:
        logger.log.debug(f"Parsing ingredient {ingredient_raw_data}")
        if not enable_amount or ingredient_raw_data["food"] is None:
            # The second case happens if the data is only in the note and the food is not properly set
            # This often is the case when a recipe is imported from some source and not properly formatted yet
            ingredients_to_add.append(IngredientWithAmountsDisabled.from_raw_data(ingredient_raw_data))
        else:
            name_of_ingredient = ingredient_raw_data["food"]["name"]
            if Ingredient.is_ignored(name_of_ingredient, ignored_ingredients):
                logger.log.debug(f"Ignoring ingredient {name_of_ingredient}")
                continue
            ingredients_to_add.append(Ingredient.from_raw_data(ingredient_raw_data))

    logger.log.info(f"Adding ingredients to Bring: {ingredients_to_add}")
    loop.run_until_complete(bring_handler.add_items(ingredients_to_add))
    loop.run_until_complete(bring_handler.notify_users_about_changes_in_list())

    return "OK"


@base_bp.route("/status", methods=["GET"])
def status_handler() -> str:
    logger.log.debug("Got a status request")
    return "OK"


def parse_ignored_ingredients() -> list[Ingredient]:
    try:
        ignored_ingredients_input = EnvironmentVariableGetter.get("IGNORED_INGREDIENTS")
    except RuntimeError:
        logger.log.info(
            "The variable IGNORED_INGREDIENTS is not set. All ingredients will be added. "
            'Consider setting the variable to something like "Salt,Pepper"'
        )
        return []

    ignored_ingredients_raw = ignored_ingredients_input.replace(", ", ",").split(",")
    logger.log.info(f"Ignoring ingredients {ignored_ingredients_raw}")
    return [Ingredient(name.lower()) for name in ignored_ingredients_raw]


if __name__ == "__main__":
    logger = LoggerMixin()
    logger.log = logging.getLogger("Main")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bring_handler = BringHandler(loop)
    ignored_ingredients = parse_ignored_ingredients()

    host = EnvironmentVariableGetter.get("HTTP_HOST", "0.0.0.0")
    port = int(EnvironmentVariableGetter.get("HTTP_PORT", 8742))
    logger.log.info(f"Listening on {host}:{port}{basepath}")
    app.register_blueprint(base_bp)
    app.run(host=host, port=port)
