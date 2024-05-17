import logging
import os

from dotenv import load_dotenv
from flask import Flask, request

from source.bring_handler import BringHandler
from source.errors import IgnoredIngredient
from source.ingredient import Ingredient
from source.logger_mixin import LoggerMixin

load_dotenv()


app = Flask(__name__)


@app.route("/", methods=["POST"])
def webhook_handler():
    data = request.get_json(force=True)

    recipe_name = data["name"]
    logger.log.info(f"Received recipe {recipe_name} from {request.origin}")

    for ingredient in data["recipeIngredient"]:
        try:
            ingredient = Ingredient(ingredient, bring_handler.ignored_ingredients)
        except ValueError as e:
            logging.error(e)
            continue
        except IgnoredIngredient as e:
            logging.debug(e)
            continue

        bring_handler.add_item_to_list(ingredient)

    logger.log.info("Added all ingredients to Bring")
    bring_handler.notify_users_about_changes_in_list()

    return "OK"


if __name__ == "__main__":
    logger = LoggerMixin()
    bring_handler = BringHandler()

    app.run(
        host=os.getenv("HTTP_HOST", "0.0.0.0"),
        port=int(os.getenv("HTTP_PORT", 8080)),
    )
