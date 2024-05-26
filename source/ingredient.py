from errors import IgnoredIngredient
from logger_mixin import LoggerMixin


class Ingredient (LoggerMixin):
    def __init__(self, ingredient_input: dict, ignored_ingredients: list[str]):
        super().__init__()

        self.ingredient_input = ingredient_input
        self.ignored_ingredients = ignored_ingredients

        self.food = None
        self.specification = ""

        self.parse_input()

    def __repr__(self):
        if self.specification:
            return f"{self.food} ({self.specification})"
        return self.food

    def parse_input(self) -> None:
        try:
            _ = self.ingredient_input["food"]
        except KeyError:
            # Happens if there is an empty ingredient (i.e. added one ingredient but did not fill it out)
            raise ValueError("There is an ingredient with no name, it will be ignored!")
        if self.ingredient_input["disableAmount"]:
            self._parse_input_with_no_ingredient_amounts()
        else:
            self._parse_input_with_ingredient_amounts()

    def _parse_input_with_no_ingredient_amounts(self) -> None:
        self.log.debug("Parsing input with no ingredient amount")
        self.food = self.ingredient_input["display"]

    def _parse_input_with_ingredient_amounts(self) -> None:
        self.log.debug("Parsing input with ingredient amount")
        self.log.debug(f"Complete ingredient: {self.ingredient_input}")

        food_name = self.ingredient_input["food"]["name"]
        if food_name.lower() in self.ignored_ingredients:
            raise IgnoredIngredient(f"Found ignored ingredient {food_name}")
        self.food = food_name


        quantity = self.ingredient_input.get("quantity", None)
        if quantity:
            self.specification += f"{str(quantity)} "

        unit = self.ingredient_input.get("unit", None)
        self.log.debug(f"Unit: {unit}")
        if unit:
            abbreviation = unit["abbreviation"]
            name = unit["name"]
            if abbreviation:
                self.specification += abbreviation
            elif name:
                self.specification += name

        self.log.debug(f"Specification afterwards: {self.specification}")

        note = self.ingredient_input.get("note", None)
        if note:
            self.specification += f" ({note})"
