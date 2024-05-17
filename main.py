import os
import sys

from dotenv import load_dotenv
from flask import Flask, request
from python_bring_api.bring import Bring
from python_bring_api.types import BringNotificationType

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
            if food.lower() in ignored_ingredients:
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
            bring.saveItem(bring_list_uuid, food, specification)
        else:
            logging.debug(f"Adding ingredient to Bring: {food}")
            bring.saveItem(bring_list_uuid, food)

    logging.info("Added all ingredients to Bring")
    bring.notify(bring_list_uuid, BringNotificationType.CHANGED_LIST)

    return "OK"


def determine_list_uuid() -> str:
    bring_list_uuid = None
    bring_list_name_lower = bring_list_name.lower()
    for bring_list in bring.loadLists()["lists"]:
        if bring_list["name"].lower() == bring_list_name_lower:
            bring_list_uuid = bring_list["listUuid"]
            break

    if not bring_list_uuid:
        logging.critical(f"Could not find a bring list with the name {bring_list_name}")
        sys.exit(1)

    logging.info(
        f"Found the bring list with the name {bring_list_name} (UUID: {bring_list_uuid})"
    )

    return bring_list_uuid


def parse_ignored_ingredients() -> list[str]:
    ignored_ingredients = []

    if not ignored_ingredients_input:
        return ignored_ingredients

    for ingredient in ignored_ingredients_input.replace(", ", ",").split(","):
        ignored_ingredients.append(ingredient.lower())
    if ignored_ingredients:
        logging.info(f"Ignoring ingredients {ignored_ingredients}")
    return ignored_ingredients


if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=log_level,
    )
    logging.getLogger("asyncio").setLevel(logging.INFO)
    # Disable Flask log messages
    logging.getLogger("werkzeug").setLevel(logging.INFO)

    bring_username = os.getenv("BRING_USERNAME")
    bring_password = os.getenv("BRING_PASSWORD")
    bring_list_name = os.getenv("BRING_LIST_NAME")
    ignored_ingredients_input = os.getenv("IGNORED_INGREDIENTS")

    if not bring_username or not bring_password or not bring_list_name:
        logging.critical(
            "Ensure that the environment variables BRING_USERNAME, BRING_PASSWORD and BRING_LIST_NAME are set"
        )
        sys.exit(1)
    logging.debug("Bring credentials and list name are set")
    if not ignored_ingredients_input:
        logging.info(
            'The variable IGNORED_INGREDIENTS is not set. All ingredients will be added. Consider adding something like "Salt,Pepper"'
        )

    bring = Bring(bring_username, bring_password)
    logging.info("Attempting to login into Bring to determine list ID")
    bring.login()
    logging.info("\tSuccess: Logged in")

    bring_list_uuid = determine_list_uuid()
    ignored_ingredients = parse_ignored_ingredients()

    app.run(
        host=(os.getenv("HTTP_HOST", "0.0.0.0")),
        port=(int(os.getenv("HTTP_PORT", 8080))),
    )
