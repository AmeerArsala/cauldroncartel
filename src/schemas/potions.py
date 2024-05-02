from src.schemas import Schema, wrap_result_with_schema
from pydantic import BaseModel


class Potion(Schema):
    sku: str
    red_percent: int
    blue_percent: int
    green_percent: int
    dark_percent: int
    quantity: int
    inventory_id: int

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, Potion)
