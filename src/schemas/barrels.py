from src.schemas import Schema, wrap_result_with_schema
from pydantic import Field
from src import constants as consts
import numpy as np


class Barrels(Schema):
    sku: str

    red_ml: int
    blue_ml: int
    green_ml: int
    dark_ml: int

    def extract_ml(self) -> list[int]:
        return [self.red_ml, self.blue_ml, self.green_ml, self.dark_ml]

    def to_barrel_schema(self, quantity: int = 1):
        mls = np.array(self.extract_ml())
        whole_sum = np.sum(mls)

        red_percent: int = int(self.red_ml / whole_sum)
        blue_percent: int = int(self.blue_ml / whole_sum)
        green_percent: int = int(self.green_ml / whole_sum)
        dark_percent: int = int(self.dark_ml / whole_sum)

        percents: list[int] = [red_percent, blue_percent, green_percent, dark_percent]

        idx = np.argmax(mls)

        ml_per_barrel: int = int(100 * (mls[idx] / (percents[idx] * quantity)))

        return BarrelSchema(
            sku=self.sku,
            red_percent=red_percent,
            blue_percent=blue_percent,
            green_percent=green_percent,
            dark_percent=dark_percent,
            ml_per_barrel=ml_per_barrel,
            quantity=quantity,
        )

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, Barrels)


class BarrelSchema(Schema):
    sku: str

    red_percent: int
    blue_percent: int
    green_percent: int
    dark_percent: int

    ml_per_barrel: int
    quantity: int
    inventory_id: int = Field(default=consts.INVENTORY_ID)

    def calculate_total_mls(self) -> np.ndarray:
        potion_proportions = (
            np.array(
                [
                    self.red_percent,
                    self.blue_percent,
                    self.green_percent,
                    self.dark_percent,
                ]
            )
            / 100.0
        )

        return potion_proportions * self.ml_per_barrel * self.quantity

    def to_barrels(self) -> Barrels:
        total_mls: np.ndarray = self.calculate_total_mls()
        return Barrels(
            sku=self.sku,
            red_ml=total_mls[0],
            blue_ml=total_mls[1],
            green_ml=total_mls[2],
            dark_ml=total_mls[3],
        )

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, BarrelSchema)
