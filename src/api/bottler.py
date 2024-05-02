from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts
from src.schemas.barrels import Barrels

import numpy as np


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
        # FIRST: get total resources of red, blue, green, dark
        mult: str = "(ml_per_barrel * quantity)"
        total_query = f"""
            SELECT sku, red_percent * {mult}, blue_percent * {mult}, green_percent * {mult}, dark_percent * {mult}
            FROM Barrels
        """

        results = conn.execute(sqlalchemy.text(total_query)).fetchall()
        barrels_list: list[Barrels] = [
            Barrels.wrap_result(result) for result in results
        ]

        barrels_mls: np.ndarray = np.array(
            [barrel_group.extract_ml() for barrel_group in barrels_list]
        )
        total_mls: np.ndarray = barrels_mls.sum(axis=0)

        # TODO: SECOND: Algorithm to decide which Potions are made from this

        # TODO: THIRD: subtract ml from Inventory/Barrels, insert corresponding Potions

        # TODO: FOURTH: Algorithm to decide which of these potions gets to go on the catalog

        # TODO: FIFTH: insert corresponding CatalogPotionItems

        # Update the DB
        # conn.execute(
        #     sqlalchemy.text(
        #         f"UPDATE global_inventory SET num_green_potions = {current_green_potions}, num_green_ml = {current_green_ml}, num_blue_potions = {current_blue_potions}, num_blue_ml = {current_blue_ml}, num_red_potions = {current_red_potions}, num_red_ml = {current_red_ml}"
        #     )
        # )

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
