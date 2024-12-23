from typing import Optional

from errors import IgnoredIngredient
from logger_mixin import LoggerMixin

NO_INGREDIENT_NAME_ERROR = "There is an ingredient with no name, it will be ignored!"


class Ingredient(LoggerMixin):
    def __init__(
        self,
        ingredient_input: dict,
        ignored_ingredients: list[str],
        enable_amount: bool,
        mealie_version_after_2: bool,
    ):
        super().__init__()

        self.ingredient_input = ingredient_input
        self.ignored_ingredients = ignored_ingredients

        self.enable_amount = enable_amount

        self.food = None
        self.specification = ""

        self.parse_input(mealie_version_after_2)

    def __repr__(self):
        if self.specification:
            return f"{self.food} ({self.specification})"
        return self.food

    def parse_input(self, mealie_version_after_2: bool) -> None:
        self.log.debug(f"Parsing {self.ingredient_input}")

        if self.enable_amount:
            self._parse_input_with_ingredient_amounts(mealie_version_after_2)
        else:
            self._parse_input_with_no_ingredient_amounts()

        self.log.debug(f"Parsed ingredient: {self}")

    def _parse_input_with_no_ingredient_amounts(self) -> None:
        note = self.ingredient_input["note"]
        if not note:
            raise ValueError(NO_INGREDIENT_NAME_ERROR)
        self.food = note

    def _parse_input_with_ingredient_amounts(self, mealie_version_after_2: bool) -> None:
        if not self.ingredient_input["food"]:
            # Happens if there is an empty ingredient (i.e., added one ingredient but did not fill it out)
            raise ValueError(NO_INGREDIENT_NAME_ERROR)

        food_name = self.ingredient_input["food"]["name"]
        if mealie_version_after_2:
            food_plural_name = self.ingredient_input["food"]["plural_name"]
        else:
            food_plural_name = self.ingredient_input["food"]["pluralName"]
        quantity_raw = self.ingredient_input["quantity"] or 0
        if int(quantity_raw) == quantity_raw:
            quantity = int(quantity_raw)
        else:
            quantity = quantity_raw
        unit = self.ingredient_input["unit"]
        note = self.ingredient_input["note"]

        # Ignored check #
        if food_name.lower() in self.ignored_ingredients:
            raise IgnoredIngredient(f"Found ignored ingredient {food_name}")

        self._set_food(food_name, food_plural_name, quantity)
        self._set_quantity(quantity)
        self._set_seperator(quantity, unit)
        self._set_unit(quantity, unit, mealie_version_after_2)
        self._set_note(note)

    def _set_food(self, food_name: str, food_plural_name: str, quantity: int) -> None:
        if quantity and quantity > 1 and food_plural_name:
            self.food = food_plural_name
            return

        self.food = food_name

    def _set_quantity(self, quantity: int) -> None:
        if quantity:
            self.specification += str(quantity)

    def _set_seperator(self, quantity: int, unit: Optional[dict]) -> None:
        if quantity and unit:
            self.specification += " "

    def _set_unit(self, quantity: int, unit: Optional[dict], mealie_version_after_2: bool) -> None:
        if not unit:
            return

        unit_name = unit["name"]
        unit_abbreviation = unit["abbreviation"]
        if mealie_version_after_2:
            unit_plural_name = unit["plural_name"]
        else:
            unit_plural_name = unit["pluralName"]
        if unit_abbreviation:
            self.specification += unit_abbreviation
        elif unit_plural_name and quantity and quantity > 1:
            self.specification += unit_plural_name
        elif unit_name:
            self.specification += unit_name

    def _set_note(self, note: str) -> None:
        if note:
            self.specification += f" ({note})"
