from src.schemas import Schema, wrap_result_with_schema
from pydantic import BaseModel, Field
import src.constants as consts


class Potion(Schema):
    sku: str
    red_percent: int
    blue_percent: int
    green_percent: int
    dark_percent: int
    quantity: int
    inventory_id: int = Field(default=consts.INVENTORY_ID)

    def as_potion_inventory(self):
        potion_type: list[int] = [
            self.red_percent,
            self.blue_percent,
            self.green_percent,
            self.dark_percent,
        ]
        quantity: int = self.quantity

        return PotionInventory(potion_type=potion_type, quantity=quantity)

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, Potion)


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int
