from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts
from src.schemas.inventory import Inventory


router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.get("/audit")
def get_inventory():
    """ """
    row: Inventory = db.retrieve_inventory()

    return {
        "number_of_potions": row.num_potions,
        "ml_in_barrels": row.calculate_total_mls(),
        "gold": row.gold,
    }


class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int


def purchase_capacity(capacity_purchase: CapacityPurchase):
    # Add capacity points, modify Inventory to subtract gold
    # Assumes neither of the fields are 0. Otherwise it would be a waste of time
    with db.engine.begin() as conn:
        gold_spent: int = (
            capacity_purchase.potion_capacity * consts.POTIONS_PER_CAPACITY_POINT
        ) + (capacity_purchase.ml_capacity * consts.ML_PER_CAPACITY_POINT)

        conn.execute(
            sqlalchemy.text(
                f"""
                UPDATE inventory
                SET potion_capacity = potion_capacity + {capacity_purchase.potion_capacity}, ml_capacity = ml_capacity + {capacity_purchase.ml_capacity}, gold = gold - {gold_spent}
                WHERE id = {consts.INVENTORY_ID}
                """
            )
        )

        # conn.execute(sqlalchemy.text(f"INSERT INTO capacitypurchases(id) VALUES ('{str()}')"))


# Gets called once a day
# NOTE: SUPER KEY ALGORITHM
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """

    inventory_row: Inventory = db.retrieve_inventory()

    capacity_purchase = CapacityPurchase(potion_capacity=0, ml_capacity=0)

    if inventory_row.num_potions >= (
        inventory_row.potion_capacity * consts.POTIONS_PER_CAPACITY_POINT
    ):
        # Purchase another point if possible
        if inventory_row.gold >= consts.POTIONS_PER_CAPACITY_POINT:
            capacity_purchase.potion_capacity = 1

    if inventory_row.calculate_total_mls() >= (
        inventory_row.ml_capacity * consts.ML_PER_CAPACITY_POINT
    ):
        # Purchase another point if possible
        if capacity_purchase.potion_capacity == 0:
            if inventory_row.gold >= consts.ML_PER_CAPACITY_POINT:
                capacity_purchase.ml_capacity = 1
        else:
            if inventory_row.gold >= (
                consts.ML_PER_CAPACITY_POINT
                + (
                    capacity_purchase.potion_capacity
                    * consts.POTIONS_PER_CAPACITY_POINT
                )
            ):
                capacity_purchase.ml_capacity = 1

    if capacity_purchase.potion_capacity > 0 or capacity_purchase.ml_capacity > 0:
        purchase_capacity(capacity_purchase)

    return {
        "potion_capacity": inventory_row.potion_capacity
        + capacity_purchase.potion_capacity,
        "ml_capacity": inventory_row.ml_capacity + capacity_purchase.ml_capacity,
    }


# Gets called once a day
# The daily action plan!!!
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """

    # all that needs to happen atp is to log the order
    with db.engine.begin() as conn:
        # Log the Order
        price = (
            capacity_purchase.potion_capacity * consts.POTIONS_PER_CAPACITY_POINT
        ) + (capacity_purchase.ml_capacity * consts.ML_PER_CAPACITY_POINT)
        order_name: str = str(capacity_purchase)

        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO orders(order_id, order_name, price) VALUES ({order_id}, '{order_name}', {price})"
            )
        )

    return "OK"
