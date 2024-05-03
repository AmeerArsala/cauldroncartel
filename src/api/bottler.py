from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts

from src.schemas.barrels import Barrels, BarrelSchema
from src.schemas.potions import Potion, PotionInventory

from src.lib.potion_generation import generate_potions, make_potions_from_mls
from src.lib import potion_selling, barreling

import numpy as np


router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    with db.engine.begin() as conn:
        # Generate Potions
        potions: list[Potion] = generate_potions(potions_delivered)

        # Aggregate information
        orders_tuple_query: str = ""
        potions_tuple_query: str = ""
        num_added_potions: int = 0
        for potion in potions:
            orders_tuple_query += f"({order_id}, '{potion.sku}'), "
            potions_tuple_query += f"('{potion.sku}', {potion.red_percent}, {potion.blue_percent}, {potion.green_percent}, {potion.dark_percent}, {potion.quantity}, {consts.INVENTORY_ID}), "

            num_added_potions += potion.quantity

        # remove the ", "
        potions_tuple_query = potions_tuple_query[:-2]
        orders_tuple_query = orders_tuple_query[:-2]

        # Algorithm to decide which potions get sold as part of the catalog
        selling_potions: list[Potion] = potion_selling.put_subset_for_sale(potions)

        selling_potions_tuple_query: str = ""
        for potion in selling_potions:
            selling_potions_tuple_query += f"('{potion.sku}', '{potion_selling.name_potion(potion)}', {potion.quantity}, {potion_selling.price_potion(potion)}), "

        # remove the ", "
        selling_potions_tuple_query = selling_potions_tuple_query[:-2]

        # Add an order
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO orders(order_id, order_name) VALUES {orders_tuple_query}"
            )
        )

        # Check if any already exist
        # result = conn.execute(sqlalchemy.text("SELECT * FROM potions WHERE "))

        # Add potions to Potions
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO potions(sku, red_percent, blue_percent, green_percent, dark_percent, quantity, inventory_id) VALUES {potions_tuple_query}"
            )
        )

        # Add corresponding CatalogPotionItems
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO catalogpotionitems(sku, name, quantity, price) VALUES {selling_potions_tuple_query}"
            )
        )

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

    with db.engine.begin() as conn:
        # FIRST: get total resources of red, blue, green, dark
        mult: str = "(ml_per_barrel * quantity / 100.0)"
        total_query = f"""
            SELECT sku, red_percent * {mult}, blue_percent * {mult}, green_percent * {mult}, dark_percent * {mult}
            FROM barrels
        """

        results = conn.execute(sqlalchemy.text(total_query)).fetchall()
        barrels_list: list[Barrels] = [
            Barrels.wrap_result(result) for result in results
        ]

        # barrel mls in groups organized by row
        barrels_mls: np.ndarray = np.array(
            [barrel_group.extract_ml() for barrel_group in barrels_list]
        )

        # [total_red, total_blue, total_green, total_dark]
        total_mls: np.ndarray = barrels_mls.sum(axis=0)

        # SECOND: Algorithm to decide which Potions are made from this
        (made_potions, used_up_mls) = make_potions_from_mls(total_mls)

        # THIRD: subtract ml from Inventory/Barrels, insert corresponding Potions & CatalogPotionItems
        new_total_mls = total_mls - used_up_mls

        # Barrels
        # Algorithm to calculate the new barrel set
        new_barrel_set: list[BarrelSchema] = barreling.stabilize_barrels(new_total_mls)

        # Aggregate the results into a str
        new_barrels_tuple_query: str = ""
        for new_barrel in new_barrel_set:
            new_barrels_tuple_query += f"('{new_barrel.sku}', {new_barrel.red_percent}, {new_barrel.blue_percent}, {new_barrel.green_percent}, {new_barrel.dark_percent}, {new_barrel.ml_per_barrel}, {new_barrel.quantity}, {new_barrel.inventory_id}), "

        # remove the last ", "
        new_barrels_tuple_query = new_barrels_tuple_query[:-2]

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

        # Potions
        potions_tuple_query: str = ""
        num_added_potions: int = 0
        for potion in made_potions:
            potions_tuple_query += f"('{potion.sku}', {potion.red_percent}, {potion.blue_percent}, {potion.green_percent}, {potion.dark_percent}, {potion.quantity}, {consts.INVENTORY_ID}), "

            num_added_potions += potion.quantity

        # remove the ", "
        potions_tuple_query = potions_tuple_query[:-2]

        # Algorithm to decide which potions get sold as part of the catalog
        selling_potions: list[Potion] = potion_selling.put_subset_for_sale(made_potions)

        selling_potions_tuple_query: str = ""
        for potion in selling_potions:
            selling_potions_tuple_query += f"('{potion.sku}', '{potion_selling.name_potion(potion)}', {potion.quantity}, {potion_selling.price_potion(potion)}), "

        # remove the ", "
        selling_potions_tuple_query = selling_potions_tuple_query[:-2]

        # Add Potions
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO potions(sku, red_percent, blue_percent, green_percent, dark_percent, quantity, inventory_id) VALUES {potions_tuple_query}"
            )
        )

        # Add corresponding CatalogPotionItems
        conn.execute(
            sqlalchemy.text(
                f"INSERT INTO catalogpotionitems(sku, name, quantity, price) VALUES {selling_potions_tuple_query}"
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

    # return [
    #     {
    #         "potion_type": [0, 0, 100, 0],
    #         "quantity": current_green_potions,
    #     },
    #     {
    #         "potion_type": [100, 0, 0, 0],
    #         "quantity": current_red_potions,
    #     },
    #     {
    #         "potion_type": [0, 100, 0, 0],
    #         "quantity": current_blue_potions,
    #     },
    # ]
