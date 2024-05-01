from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    with db.engine.begin() as conn:
        select_result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = dict(db.wrap_result_as_global_inventory(select_result.first()))

        current_red_potions = row["num_red_potions"]
        current_blue_potions = row["num_blue_potions"]
        current_green_potions = row["num_green_potions"]
        for potion in potions_delivered:
            if potion.potion_type == consts.PURE_RED_POTION:
                current_red_potions += potion.quantity
            elif potion.potion_type == consts.PURE_BLUE_POTION:
                current_blue_potions += potion.quantity
            elif potion.potion_type == consts.PURE_GREEN_POTION:
                current_green_potions += potion.quantity

        # Update the DB
        conn.execute(
            sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_potions = {current_green_potions}, num_red_potions = {current_red_potions}, num_blue_potions = {current_blue_potions}"
            )
        )

    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    return "OK"


@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    # Latest logic: bottle all barrels into their respective red, blue, and green potions

    with db.engine.begin() as conn:
        select_result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = dict(db.wrap_result_as_global_inventory(select_result.first()))

        def convert_barrel_to_potions(
            num_current_ml: int, num_current_potions: int
        ) -> tuple[int, int]:
            num_current_ml_: int = num_current_ml
            num_added_potions: int = int(num_current_ml_ / consts.ML_PER_BOTTLE)

            num_current_ml_ -= num_added_potions * consts.ML_PER_BOTTLE
            total_potions: int = num_current_potions + num_added_potions

            return (num_current_ml_, total_potions)

        (current_green_ml, current_green_potions) = convert_barrel_to_potions(
            num_current_ml=row["num_green_ml"],
            num_current_potions=row["num_green_potions"],
        )

        (current_blue_ml, current_blue_potions) = convert_barrel_to_potions(
            num_current_ml=row["num_blue_ml"],
            num_current_potions=row["num_blue_potions"],
        )

        (current_red_ml, current_red_potions) = convert_barrel_to_potions(
            num_current_ml=row["num_red_ml"],
            num_current_potions=row["num_red_potions"],
        )

        # Update the DB
        conn.execute(
            sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_potions = {current_green_potions}, num_green_ml = {current_green_ml}, num_blue_potions = {current_blue_potions}, num_blue_ml = {current_blue_ml}, num_red_potions = {current_red_potions}, num_red_ml = {current_red_ml}"
            )
        )

    return [
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": current_green_potions,
        },
        {
            "potion_type": [100, 0, 0, 0],
            "quantity": current_red_potions,
        },
        {
            "potion_type": [0, 100, 0, 0],
            "quantity": current_blue_potions,
        },
    ]


if __name__ == "__main__":
    print(get_bottle_plan())
