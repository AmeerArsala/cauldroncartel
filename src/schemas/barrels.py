from src.schemas import Schema, wrap_result_with_schema


class Barrels(Schema):
    sku: str

    red_ml: int
    blue_ml: int
    green_ml: int
    dark_ml: int

    # mls_per_barrel: int
    # quantity: int
    # inventory_id: int

    def extract_ml(self) -> list:
        return [self.red_ml, self.blue_ml, self.green_ml, self.dark_ml]

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, Barrels)
