from src.schemas import Schema, wrap_result_with_schema


class CatalogItem(Schema):
    sku: str
    name: str
    quantity: int
    price: int

    red_percent: int
    blue_percent: int
    green_percent: int
    dark_percent: int

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, CatalogItem)
