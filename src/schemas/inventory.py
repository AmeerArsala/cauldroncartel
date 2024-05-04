from uuid import UUID
from pydantic import BaseModel
from src.schemas import Schema, wrap_result_with_schema
from src import constants as consts


class Inventory(Schema):
    id_: int
    num_potions: int
    red_ml: int
    blue_ml: int
    green_ml: int
    dark_ml: int
    potion_capacity: int
    ml_capacity: int
    gold: int

    def calculate_total_mls(self):
        return self.red_ml + self.blue_ml + self.green_ml + self.dark_ml

    def num_potions_capacity(self):
        return self.potion_capacity * consts.POTIONS_PER_CAPACITY_POINT

    def num_ml_capacity(self):
        return self.ml_capacity * consts.ML_PER_CAPACITY_POINT

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, Inventory)


class GlobalInventory(Schema):
    id_: UUID
    gold: int

    num_green_potions: int
    num_green_ml: int

    num_red_potions: int
    num_red_ml: int

    num_blue_potions: int
    num_blue_ml: int

    def wrap_result(row: tuple[UUID, int, int, int, int, int, int, int]):
        return GlobalInventory(
            id_=row[0],
            gold=row[3],
            num_green_potions=row[1],
            num_green_ml=row[2],
            num_red_potions=row[4],
            num_red_ml=row[5],
            num_blue_potions=row[6],
            num_blue_ml=row[7],
        )
