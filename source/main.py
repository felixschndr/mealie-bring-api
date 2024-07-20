import logging
import os

from dotenv import load_dotenv
from flask import Flask, request

from bring_handler import BringHandler
from errors import IgnoredIngredient
from ingredient import Ingredient
from logger_mixin import LoggerMixin

load_dotenv()


app = Flask(__name__)


@app.route("/", methods=["POST"])
def webhook_handler():
    data = request.get_json(force=True)

    logger.log.info(f'Received recipe "{data["name"]}" from "{request.origin}"')

    enable_amount = not data["settings"]["disableAmount"]
    if enable_amount:
        logger.log.debug("This recipe has its ingredient amount enabled")
    else:
        logger.log.warning(
            "This recipe has its ingredient amount this disabled --> Its ingredients will not be checked whether they are supposed to be ignored"
        )

    for ingredient in data["recipeIngredient"]:
        try:
            parsed_ingredient = Ingredient(
                ingredient, bring_handler.ignored_ingredients, enable_amount
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
def status_handler():
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
