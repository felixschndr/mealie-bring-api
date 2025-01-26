from __future__ import annotations

import dataclasses
import uuid


@dataclasses.dataclass
class Ingredient:
    name: str
    specification: str = None
    uuid: str = None

    @staticmethod
    def from_raw_data(raw_data: dict) -> Ingredient:
        return Ingredient(
            name=Ingredient._get_name(raw_data),
            specification=Ingredient._get_specification(raw_data),
            uuid=str(uuid.uuid4()),
        )

    @staticmethod
    def _get_name(raw_data: dict) -> str:
        return raw_data["food"]["name"]

    @staticmethod
    def _get_specification(raw_data: dict) -> str:
        return f"{Ingredient._get_quantity(raw_data)}{Ingredient._get_unit(raw_data)}{Ingredient._get_note(raw_data)}"

    @staticmethod
    def _get_quantity(raw_data: dict) -> str:
        quantity_raw = raw_data["quantity"]
        quantity = int(quantity_raw) if quantity_raw.is_integer() else quantity_raw
        return str(quantity)

    @staticmethod
    def _get_unit(raw_data: dict) -> str:
        unit_raw = raw_data["unit"]
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

        return f" ({raw_data['note']})"

    @staticmethod
    def is_ignored(raw_data: dict, ignored_ingredients: list[Ingredient]) -> bool:
        return raw_data["food"]["name"] in Ingredient.to_string_list(ignored_ingredients)

    @staticmethod
    def to_string_list(ingredients: list[Ingredient]) -> list[str]:
        return [ingredient.name for ingredient in ingredients]

    def to_dict(self) -> dict:
        return {"itemId": self.name, "spec": self.specification, "uuid": self.uuid}
