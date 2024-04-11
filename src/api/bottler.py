from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db


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

    # TODO: it only does green potions rn, change to all types later
    GREEN_POTION = [0, 0, 100, 0]

    for potion in potions_delivered:
        if potion.potion_type == GREEN_POTION:
            with db.engine.begin() as conn:
                select_result = conn.execute(
                    sqlalchemy.text("SELECT * FROM global_inventory")
                )
                row = select_result[0]

                current_green_potions = row["num_green_potions"] + potion.quantity

                # Update the DB
                conn.execute(
                    sqlalchemy.text(
                        f"UPDATE global_inventory SET num_green_potions = {current_green_potions}"
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
    # Now: it is green

    return [
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": 5,
        }
    ]


if __name__ == "__main__":
    print(get_bottle_plan())
