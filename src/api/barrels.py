from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts


router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


global_wholesale_catalog: list[Barrel] = []


def purchase_barrels(barrels_delivered: list[Barrel]):
    # Deliver the barrels
    total_green_ml = 0
    total_red_ml = 0
    total_blue_ml = 0

    total_price = 0

    # Calculate totals
    def calculate_barrel_totals(barrel: Barrel, potion_type: int):
        proportion = barrel.potion_type[potion_type] / 100.0
        ml = proportion * barrel.ml_per_barrel * barrel.quantity

        return ml

    for barrel in barrels_delivered:
        total_green_ml += calculate_barrel_totals(barrel, consts.GREEN)
        total_red_ml += calculate_barrel_totals(barrel, consts.RED)
        total_blue_ml += calculate_barrel_totals(barrel, consts.BLUE)

        total_price += barrel.price * barrel.quantity

    # Update the DB by diminishing gold and increasing ml (barrels)
    with db.engine.begin() as conn:
        select_result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = select_result[0]

        current_green_ml = row["num_green_ml"] + total_green_ml
        current_red_ml = row["num_red_ml"] + total_red_ml
        current_blue_ml = row["num_blue_ml"] + total_blue_ml

        current_gold = row["gold"] - total_price

        # Update statement
        conn.execute(
            sqlalchemy.text(
                f"UPDATE global_inventory SET gold = {current_gold}, num_green_ml = {current_green_ml}, num_red_ml = {current_red_ml}, num_blue_ml = {current_blue_ml}"
            )
        )


@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """

    purchase_barrels(barrels_delivered)

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    As a very basic initial logic, purchase a new small green potion barrel only if the number of potions in inventory is less than 10.
    Always mix all available green ml if any exists.
    Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
    """
    global global_wholesale_catalog

    global_wholesale_catalog = wholesale_catalog
    print(wholesale_catalog)

    with db.engine.begin() as conn:
        result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

    row = result[0]  # Only one row rn

    if row["num_green_potions"] < 10:
        # Purchase a new small green potion barrel

        def find_barrel(barrel_name: str) -> Barrel:
            for barrel in wholesale_catalog:
                if barrel.sku == barrel_name:
                    return barrel

        # Find the small potion barrels
        small_green_potion_barrel: Barrel = find_barrel("SMALL_GREEN_BARREL")
        small_red_potion_barrel: Barrel = find_barrel("SMALL_RED_BARREL")
        small_blue_potion_barrel: Barrel = find_barrel("SMALL_BLUE_BARREL")

        barrels: list[Barrel] = [
            small_green_potion_barrel,
            small_red_potion_barrel,
            small_blue_potion_barrel,
        ]

        # Purchase the barrel
        purchase_barrels(barrels)

    # Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
    # Done in `catalog.py`

    return [
        {
            "sku": small_green_potion_barrel.sku,
            "quantity": small_green_potion_barrel.sku,
        },
        {
            "sku": small_red_potion_barrel.sku,
            "quantity": small_red_potion_barrel.sku,
        },
        {
            "sku": small_blue_potion_barrel.sku,
            "quantity": small_blue_potion_barrel.sku,
        },
    ]
