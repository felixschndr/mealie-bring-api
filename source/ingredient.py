from __future__ import annotations

import dataclasses
import uuid


@dataclasses.dataclass
class Ingredient:
    name: str
    specification: str = None

    @staticmethod
    def from_raw_data(raw_data: dict, recipe_scale: float) -> Ingredient:
        return Ingredient(
            name=Ingredient._get_name(raw_data),
            specification=Ingredient._get_specification(raw_data, recipe_scale),
        )

    @staticmethod
    def _get_name(raw_data: dict) -> str:
        return raw_data["food"]["name"].capitalize()

    @staticmethod
    def _get_specification(raw_data: dict, recipe_scale: float) -> str:
        specification = f"{Ingredient._get_quantity_formatted(raw_data, recipe_scale)}{Ingredient._get_unit_formatted(raw_data, recipe_scale)}"
        note = Ingredient._get_note(raw_data)
        if specification == "" and note == "":
            return ""
        if specification == "":
            return note
        if note == "":
            return specification
        return f"{specification} {note}"

    @staticmethod
    def _get_quantity_scaled(raw_data: dict, recipe_scale: float) -> float | None:
        quantity_raw = raw_data["quantity"]
        if quantity_raw is None:
            return quantity_raw

        return quantity_raw * recipe_scale

    @staticmethod
    def _get_quantity_formatted(raw_data: dict, recipe_scale: float) -> str:
        quantity = Ingredient._get_quantity_scaled(raw_data, recipe_scale)
        if quantity is None:
            return ""
        quantity = int(quantity) if quantity.is_integer() else quantity
        return str(quantity)

    @staticmethod
    def _get_unit_formatted(raw_data: dict, recipe_scale: float) -> str:
        unit_raw = raw_data["unit"]
        if unit_raw is None:
            return ""
        quantity_is_not_one = (
            Ingredient._get_quantity_scaled(raw_data, recipe_scale) != 1
        )
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
    def in_household(raw_data: dict) -> bool:
        return len(raw_data["food"].get("households_with_ingredient_food", [])) > 0

    def to_dict(self) -> dict:
        return {
            "itemId": self.name,
            "spec": self.specification,
            "uuid": str(uuid.uuid4()),
        }


@dataclasses.dataclass
class IngredientWithAmountsDisabled(Ingredient):
    @staticmethod
    def from_raw_data(raw_data: dict) -> Ingredient:
        return IngredientWithAmountsDisabled(name=raw_data["display"])
