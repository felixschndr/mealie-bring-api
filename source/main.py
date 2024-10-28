import logging
import os

from bring_handler import BringHandler
from dotenv import load_dotenv
from errors import IgnoredIngredient
from flask import Flask, request
from ingredient import Ingredient
from logger_mixin import LoggerMixin

load_dotenv()

app = Flask(__name__)


@app.route("/", methods=["POST"])
def webhook_handler() -> str:
    data = request.get_json(force=True)

    mealie_version_after_2 = True
    if "name" in data.keys():
        mealie_version_after_2 = False

    if mealie_version_after_2:
        logger.log.info(f'Received recipe "{data["content"]["name"]}" from "{request.remote_addr}"')
    else:
        logger.log.info(f'Received recipe "{data["name"]}" from "{request.remote_addr}"')

    if mealie_version_after_2:
        enable_amount = not data["content"]["settings"]["disable_amount"]
    else:
        enable_amount = not data["settings"]["disableAmount"]
    if enable_amount:
        logger.log.debug("This recipe has its ingredient amount enabled")
    else:
        logger.log.warning(
            "This recipe has its ingredient amount this disabled --> Its ingredients will not be checked whether they are supposed to be ignored"
        )

    if mealie_version_after_2:
        ingredients = data["content"]["recipe_ingredient"]
    else:
        ingredients = data["recipeIngredient"]
    for ingredient in ingredients:
        try:
            parsed_ingredient = Ingredient(
                ingredient,
                bring_handler.ignored_ingredients,
                enable_amount,
                mealie_version_after_2,
            )
        except ValueError as e:
            logger.log.warning(e)
            continue
        except IgnoredIngredient as e:
            logger.log.debug(e)
            continue

        bring_handler.add_item_to_list(parsed_ingredient)

    logger.log.info("Added all ingredients to Bring")
    bring_handler.notify_users_about_changes_in_list()

    return "OK"


@app.route("/status", methods=["GET"])
def status_handler() -> str:
    logger.log.debug("Got a status request")
    return "OK"


if __name__ == "__main__":
    logger = LoggerMixin()
    logger.log = logging.getLogger("Main")
    bring_handler = BringHandler()

    host = os.getenv("HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_PORT", 8742))
    logger.log.info(f"Listening on {host}:{port}")
    app.run(
        host=host,
        port=port,
    )
