from errors import IgnoredIngredient
from logger_mixin import LoggerMixin


class Ingredient(LoggerMixin):
    def __init__(
        self,
        ingredient_input: dict,
        ignored_ingredients: list[str],
        enable_amount: bool,
    ):
        super().__init__()

        self.ingredient_input = ingredient_input
        self.ignored_ingredients = ignored_ingredients

        self.enable_amount = enable_amount

        self.food = None
        self.specification = ""

        self.parse_input()

    def __repr__(self):
        if self.specification:
            return f"{self.food} ({self.specification})"
        return self.food

    def parse_input(self) -> None:
        self.log.debug(f"Parsing {self.ingredient_input}")
        try:
            if self.enable_amount:
                self._parse_input_with_ingredient_amounts()
            else:
                self._parse_input_with_no_ingredient_amounts()
        except ValueError:
            # Happens if there is an empty ingredient (i.e. added one ingredient but did not fill it out)
            raise ValueError("There is an ingredient with no name, it will be ignored!")

        self.log.debug(f"Parsed ingredient: {self}")

    def _parse_input_with_no_ingredient_amounts(self) -> None:
        note = self.ingredient_input["note"]
        if not note:
            raise ValueError()
        self.food = note

    def _parse_input_with_ingredient_amounts(self) -> None:
        if not self.ingredient_input["food"]:
            raise ValueError()

        food_name = self.ingredient_input["food"]["name"]
        food_plural_name = self.ingredient_input["food"]["pluralName"]
        quantity = int(self.ingredient_input["quantity"] or 0)
        unit = self.ingredient_input["unit"]
        note = self.ingredient_input["note"]

        # Ignored check #
        if food_name.lower() in self.ignored_ingredients:
            raise IgnoredIngredient(f"Found ignored ingredient {food_name}")

        # Food #
        if quantity and quantity > 1 and food_plural_name:
            self.food = food_plural_name
        else:
            self.food = food_name

        # Quantity #
        if quantity:
            self.specification += str(quantity)

        # Seperator between Quantity and Unit #
        if quantity and unit:
            self.specification += " "

        # Unit #
        if unit:
            unit_name = unit["name"]
            unit_abbreviation = unit["abbreviation"]
            unit_plural_name = unit["pluralName"]
            if unit_abbreviation:
                self.specification += unit_abbreviation
            elif unit_plural_name and quantity and quantity > 1:
                self.specification += unit_plural_name
            elif unit_name:
                self.specification += unit_name

        # Note #
        if note:
            self.specification += f" ({note})"
