from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts

from src.schemas.barrels import Barrels, BarrelSchema
from src.schemas.inventory import Inventory
from src.schemas.potions import Potion, PotionInventory
from src.schemas.catalogitems import CatalogPotionItem

from src.lib.potion_generation import generate_potions, make_potions_from_mls
from src.lib import potion_selling, barreling

import numpy as np


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


def put_potions_for_sale(conn):
    # Now, get the existing potions
    existing_potions_rows = conn.execute(
        sqlalchemy.text(
            f"SELECT * FROM potions WHERE inventory_id = {consts.INVENTORY_ID}"
        )
    ).fetchall()
    all_potions: list[Potion] = [
        Potion.wrap_result(existing_potion_row)
        for existing_potion_row in existing_potions_rows
    ]

    # Algorithm to decide which six potions get sold as part of the catalog
    # TODO: collect statistics on historical data and pass into `put_subset_for_sale`
    selling_potions: list[Potion] = potion_selling.put_subset_for_sale(all_potions)

    selling_potions_tuple_query: str = ", ".join(
        [
            CatalogPotionItem(
                sku=potion.sku,
                name=potion_selling.name_potion(potion),
                quantity=potion.quantity,
                price=potion_selling.price_potion(potion),
            ).as_tuple_value_str()
            for potion in selling_potions
        ]
    )

    # Delete all CatalogPotionItems and replace with the ones that are being sold
    conn.execute(sqlalchemy.text("DELETE FROM catalogpotionitems"))

    # Add corresponding CatalogPotionItems
    conn.execute(
        sqlalchemy.text(
            f"""
            INSERT INTO catalogpotionitems(sku, name, quantity, price) VALUES {selling_potions_tuple_query}
            """
        )
    )


@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """

    inventory_row: Inventory = db.retrieve_inventory()
    max_num_added_potions: int = (
        inventory_row.num_potions_capacity() - inventory_row.num_potions
    )

    with db.engine.begin() as conn:
        # Generate Potions
        potions: list[Potion] = generate_potions(potions_delivered)

        # Aggregate information
        # Build queries for potions being added along with orders
        orders_tuple_query: str = ""
        potions_tuple_query: str = ""
        num_added_potions: int = 0
        idx = 0
        for potion in potions:
            should_break: bool = False
            if num_added_potions + potion.quantity >= max_num_added_potions:
                potion.quantity = max_num_added_potions - num_added_potions
                should_break = True

            orders_tuple_query += f"({order_id}, '{potion.sku}'), "
            potions_tuple_query += f"('{potion.sku}', {potion.red_percent}, {potion.blue_percent}, {potion.green_percent}, {potion.dark_percent}, {potion.quantity}, {consts.INVENTORY_ID}), "

            num_added_potions += potion.quantity
            idx += 1

            if should_break:
                break

        # Only use the ones you are storing (cuz they fit)
        potions = potions[:idx]

        # remove last ", "
        potions_tuple_query = potions_tuple_query[:-2]
        orders_tuple_query = orders_tuple_query[:-2]

        # Add an order
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO orders(order_id, order_name) VALUES {orders_tuple_query}"
            )
        )

        # Add potions to Potions
        conn.execute(
            sqlalchemy.text(
                f"""
                INSERT INTO potions(sku, red_percent, blue_percent, green_percent, dark_percent, quantity, inventory_id) VALUES {potions_tuple_query}
                ON CONFLICT (sku) DO UPDATE
                SET quantity = potions.quantity + EXCLUDED.quantity
                """
            )
        )

        # Put potions in DB for sale
        put_potions_for_sale(conn)

        # Add Potions to Inventory
        conn.execute(
            sqlalchemy.text(
                f"UPDATE inventory SET num_potions = num_potions + {num_added_potions} WHERE id = {consts.INVENTORY_ID}"
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

    inventory_row: Inventory = db.retrieve_inventory()
    max_num_added_potions: int = (
        inventory_row.num_potions_capacity() - inventory_row.num_potions
    )

    # HERE!
    # [total_red, total_blue, total_green, total_dark]
    # total_mls: np.ndarray = barrels_mls.sum(axis=0)
    total_mls: np.ndarray = np.array(inventory_row.get_mls())

    # print(total_mls)

    # SECOND: Algorithm to decide which Potions are made from this
    made_potions: list[Potion] = make_potions_from_mls(total_mls)

    if len(made_potions) == 0:
        return []

    with db.engine.begin() as conn:
        # Hey! This is kinda like a Ledger!!!
        def get_total_mls_used(potions: list[Potion]):
            mls_history = np.array([potion.extract_mls() for potion in potions])

            return mls_history.sum(axis=0)

        # Build query for which Potions to put in the DB now that they've been calculated
        potions_tuple_query: str = ""
        num_added_potions: int = 0
        idx = 0
        for potion in made_potions:
            should_break: bool = False
            if num_added_potions + potion.quantity >= max_num_added_potions:
                potion.quantity = max_num_added_potions - num_added_potions
                should_break = True

            potions_tuple_query += f"('{potion.sku}', {potion.red_percent}, {potion.blue_percent}, {potion.green_percent}, {potion.dark_percent}, {potion.quantity}, {consts.INVENTORY_ID}), "

            num_added_potions += potion.quantity
            idx += 1
            if should_break:
                break

        # Don't include the potions that you aren't storing since you don't have the capacity
        made_potions = made_potions[:idx]
        potions_tuple_query = potions_tuple_query[:-2]  # remove last ", "

        # print(len(potions_tuple_query))

        # Add Potions
        conn.execute(
            sqlalchemy.text(
                f"""
                INSERT INTO potions(sku, red_percent, blue_percent, green_percent, dark_percent, quantity, inventory_id) VALUES {potions_tuple_query}
                ON CONFLICT (sku) DO UPDATE
                SET quantity = potions.quantity + EXCLUDED.quantity
                """
            )
        )

        # Now put 'em on sale
        put_potions_for_sale(conn)

        # THIRD: Time to update the barrels that have been being turned into bottles to match this
        # subtract ml from Inventory/Barrels, insert corresponding Potions & CatalogPotionItems
        new_total_mls = total_mls - get_total_mls_used(made_potions)

        # Barrels
        # Algorithm to calculate the new barrel set
        new_barrel_set: list[BarrelSchema] = barreling.stabilize_barrels(new_total_mls)

        # Aggregate the results into a str
        new_barrels_tuple_query: str = ", ".join(
            [new_barrel.as_tuple_value_str() for new_barrel in new_barrel_set]
        )

        # Delete all barrels and insert these instead
        conn.execute(
            sqlalchemy.text(
                f"DELETE FROM barrels WHERE inventory_id = {consts.INVENTORY_ID}"
            )
        )
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO barrels(sku, red_percent, blue_percent, green_percent, dark_percent, ml_per_barrel, quantity, inventory_id) VALUES {new_barrels_tuple_query}"
            )
        )

        # Inventory
        conn.execute(
            sqlalchemy.text(
                f"""
                    UPDATE inventory
                    SET num_potions = num_potions + {num_added_potions}, red_ml = {new_total_mls[consts.RED]}, blue_ml = {new_total_mls[consts.BLUE]}, green_ml = {new_total_mls[consts.GREEN]}, dark_ml = {new_total_mls[consts.DARK]} 
                    WHERE id = {consts.INVENTORY_ID}
                """
            )
        )

    return [made_potion.as_potion_inventory() for made_potion in made_potions]
