import asyncio
import logging
import os

from bring_handler import BringHandler
from dotenv import load_dotenv
from flask import Flask, request
from ingredient import Ingredient
from logger_mixin import LoggerMixin

from source.environment_variable_getter import EnvironmentVariableGetter

load_dotenv()

app = Flask(__name__)


@app.route("/", methods=["POST"])
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
        if Ingredient.is_ignored(ingredient_raw_data, ignored_ingredients):
            logger.log.debug(f"Ignoring ingredient {ingredient_raw_data}")

        try:
            ingredients_to_add.append(Ingredient.from_raw_data(ingredient_raw_data))
        except ValueError:
            logger.log.warning(exc_info=True)
            continue

    logger.log.info(f"Adding ingredients to Bring: {ingredients_to_add}")
    loop.run_until_complete(bring_handler.add_items(ingredients_to_add))
    loop.run_until_complete(bring_handler.notify_users_about_changes_in_list())

    return "OK"


@app.route("/status", methods=["GET"])
def status_handler() -> str:
    logger.log.debug("Got a status request")
    return "OK"


def parse_ignored_ingredients() -> list[Ingredient]:
    try:
        ignored_ingredients_input = EnvironmentVariableGetter.get("IGNORED_INGREDIENTS")
    except KeyError:
        logger.log.info(
            'The variable IGNORED_INGREDIENTS is not set. All ingredients will be added. Consider adding something like "Salt,Pepper"'
        )
        return []

    ignored_ingredients = [
        Ingredient(name) for name in ignored_ingredients_input.lower().replace(", ", ",").split(",")
    ]
    logger.log.info(f"Ignoring ingredients {Ingredient.to_string_list(ignored_ingredients)}")

    return ignored_ingredients


if __name__ == "__main__":
    logger = LoggerMixin()
    logger.log = logging.getLogger("Main")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    bring_handler = BringHandler(loop)
    ignored_ingredients = parse_ignored_ingredients()

    host = os.getenv("HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", 8742))
    logger.log.info(f"Listening on {host}:{port}")
    app.run(host=host, port=port)
