from source.errors import IgnoredIngredient


class Ingredient:
    def __init__(self, ingredient_input: dict, ignored_ingredients: list[str]):
        self.food = None
        self.specification = ""

        self.parse_input(ingredient_input, ignored_ingredients)

    def __repr__(self):
        if self.specification:
            return f"{self.food} ({self.specification})"
        return self.food

    def parse_input(self,ingredient_input: dict,  ignored_ingredients: list[str]) -> None:
        food = ingredient_input.get("food", None)
        if not food:
            raise ValueError("This recipe has a ingredient with no name, it will be ignored!")

        food_name = food["name"]
        if food_name.lower() in ignored_ingredients:
            raise IgnoredIngredient(f"Found ignored ingredient {food_name}")
        self.food = food_name

        quantity = ingredient_input.get("quantity", None)
        if quantity:
            self.specification += str(quantity)

        unit = ingredient_input.get("unit", None)
        if unit:
            self.specification += unit.get("abbreviation", unit["name"])

        note = ingredient_input.get("note", None)
        if note:
            self.specification += f" ({note})"
