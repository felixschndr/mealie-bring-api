import os
import sys

from dotenv import load_dotenv
from flask import Flask, request
from python_bring_api.bring import Bring
from python_bring_api.types import BringNotificationType

from source.bring_handler import BringHandler

load_dotenv()

app = Flask(__name__)


import logging


@app.route("/", methods=["POST"])
def webhook_handler():
    data = request.get_json(force=True)

    recipe_name = data["name"]
    logging.info(f"Received recipe {recipe_name}")

    for ingredient in data["recipeIngredient"]:
        try:
            food = ingredient["food"]["name"]
            if food.lower() in bring_handler.ignored_ingredients:
                logging.debug(f"Ignoring ingredient {food}")
                continue

        except TypeError:
            logging.error(
                "This recipe has a ingredient with no name, it will be ignored!"
            )
            continue

        specification = ""
        quantity = ingredient.get("quantity", None)
        if quantity:
            specification += str(quantity)
        unit = ingredient.get("unit", None)
        if unit:
            specification += unit.get("abbreviation", unit["name"])
        note = ingredient.get("note", None)
        if note:
            specification += f" ({note})"

        if specification:
            logging.debug(f"Adding ingredient to Bring: {food} ({specification})")
            bring_handler.bring.saveItem(bring_handler.list_uuid, food, specification)
        else:
            logging.debug(f"Adding ingredient to Bring: {food}")
            bring_handler.bring.saveItem(bring_handler.list_uuid, food)

    logging.info("Added all ingredients to Bring")
    bring_handler.bring.notify(bring_handler.list_uuid, BringNotificationType.CHANGED_LIST)

    return "OK"





if __name__ == "__main__":
    bring_handler = BringHandler()

    app.run(
        host=(os.getenv("HTTP_HOST", "0.0.0.0")),
        port=(int(os.getenv("HTTP_PORT", 8080))),
    )
