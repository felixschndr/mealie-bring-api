from __future__ import annotations

import dataclasses
import uuid
from typing import Optional


@dataclasses.dataclass
class Quantity:
    value: Optional[float]
    scale: float = 1.0

    @property
    def scaled_value(self) -> Optional[float]:
        if self.value is None:
            return None
        return self.value * self.scale

    @property
    def is_one(self) -> bool:
        return self.scaled_value == 1

    @property
    def formatted(self) -> str:
        if self.scaled_value is None:
            return ""
        # Convert to integer if it's a whole number
        value = (
            int(self.scaled_value)
            if self.scaled_value.is_integer()
            else self.scaled_value
        )
        return str(value)


@dataclasses.dataclass
class Ingredient:
    name: str
    specification: str | None = None

    @staticmethod
    def from_raw_data(raw_data: dict, recipe_scale: float = 1.0) -> Ingredient:
        quantity = Quantity(raw_data["quantity"], recipe_scale)

        return Ingredient(
            name=Ingredient._get_name(raw_data, quantity),
            specification=Ingredient._get_specification(raw_data, quantity),
        )

    @staticmethod
    def _get_name(raw_data: dict, quantity: Quantity) -> str:
        food = raw_data["food"]
        if not quantity.is_one and food.get("plural_name"):
            return food["plural_name"].capitalize()
        return food["name"].capitalize()

    @staticmethod
    def _get_specification(raw_data: dict, quantity: Quantity) -> str:
        specification = (
            f"{quantity.formatted}{Ingredient._get_unit_formatted(raw_data, quantity)}"
        )
        note = Ingredient._get_note(raw_data)

        if specification == "" and note == "":
            return ""
        if specification == "":
            return note
        if note == "":
            return specification
        return f"{specification} {note}"

    @staticmethod
    def _get_unit_formatted(raw_data: dict, quantity: Quantity) -> str:
        unit_raw = raw_data["unit"]
        if unit_raw is None:
            return ""

        if not quantity.is_one:
            if unit_raw["plural_name"]:
                # For None quantity case, don't add a leading space if formatted is empty
                prefix = " " if quantity.formatted else ""
                return f"{prefix}{unit_raw['plural_name']}"
            if unit_raw["plural_abbreviation"]:
                return unit_raw["plural_abbreviation"]

        if unit_raw["name"]:
            return f" {unit_raw['name']}"
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
    """Ingredient class for items where amounts are disabled."""

    @staticmethod
    def from_raw_data(raw_data: dict, _recipe_scale: float = 1.0) -> Ingredient:
        """Create an ingredient with amounts disabled from raw data."""
        return IngredientWithAmountsDisabled(name=raw_data["display"])
