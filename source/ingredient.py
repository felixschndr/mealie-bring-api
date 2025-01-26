from __future__ import annotations

import dataclasses
import uuid


@dataclasses.dataclass
class Ingredient:
    name: str
    specification: str = None

    @staticmethod
    def from_raw_data(raw_data: dict) -> Ingredient:
        return Ingredient(name=Ingredient._get_name(raw_data), specification=Ingredient._get_specification(raw_data))

    @staticmethod
    def _get_name(raw_data: dict) -> str:
        return raw_data["food"]["name"]

    @staticmethod
    def _get_specification(raw_data: dict) -> str:
        specification = f"{Ingredient._get_quantity(raw_data)}{Ingredient._get_unit(raw_data)}"
        note = Ingredient._get_note(raw_data)
        specification += note if specification == "" else f" {note}"
        return specification

    @staticmethod
    def _get_quantity(raw_data: dict) -> str:
        quantity_raw = raw_data["quantity"]
        if quantity_raw is None:
            return ""
        quantity = int(quantity_raw) if quantity_raw.is_integer() else quantity_raw
        return str(quantity)

    @staticmethod
    def _get_unit(raw_data: dict) -> str:
        unit_raw = raw_data["unit"]
        if unit_raw is None:
            return ""
        quantity_is_not_one = raw_data["quantity"] != 1
        if quantity_is_not_one:
            if unit_raw["plural_name"]:
                return f" {unit_raw["plural_name"]}"
            if unit_raw["plural_abbreviation"]:
                return unit_raw["plural_abbreviation"]

        if unit_raw["name"]:
            return f" {unit_raw["name"]}"
        if unit_raw["abbreviation"]:
            return unit_raw["abbreviation"]

        return ""

    @staticmethod
    def _get_note(raw_data: dict) -> str:
        if not raw_data["note"]:
            return ""

        return f"({raw_data['note']})"

    @staticmethod
    def is_ignored(name_of_ingredient: str, ignored_ingredients: list[Ingredient]) -> bool:
        return name_of_ingredient.lower() in [ingredient.name for ingredient in ignored_ingredients]

    def to_dict(self) -> dict:
        return {"itemId": self.name, "spec": self.specification, "uuid": str(uuid.uuid4())}


@dataclasses.dataclass
class IngredientWithAmountsDisabled(Ingredient):
    @staticmethod
    def from_raw_data(raw_data: dict) -> Ingredient:
        return IngredientWithAmountsDisabled(name=raw_data["display"])
