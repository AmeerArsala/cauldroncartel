from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
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
        "ml_in_barrels": row.red_ml + row.blue_ml + row.green_ml + row.dark_ml,
        "gold": row.gold,
    }


# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """

    row: Inventory = db.retrieve_inventory()

    return {"potion_capacity": row.potion_capacity, "ml_capacity": row.ml_capacity}


class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int


# Gets called once a day
# The daily action plan!!!
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int):
    """
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional
    capacity unit costs 1000 gold.
    """

    return "OK"
