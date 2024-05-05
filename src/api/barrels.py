from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db
from src import constants as consts

from src.schemas.barrels import BarrelSchema
from src.schemas.inventory import Inventory
from src.lib import barreling

import numpy as np


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

    def calculate_total_mls(self) -> np.ndarray:
        potion_proportions = np.array(self.potion_type)  # .astype(float) / 100.0

        return potion_proportions * self.ml_per_barrel * self.quantity  # .astype(int)

    def calculate_total_mls_value(self) -> int:
        return self.ml_per_barrel * self.quantity

    def calculate_total_price(self) -> int:
        return self.price * self.quantity

    def to_barrel_schema(self) -> BarrelSchema:
        return BarrelSchema(
            sku=self.sku,
            red_percent=self.potion_type[consts.RED],
            blue_percent=self.potion_type[consts.BLUE],
            green_percent=self.potion_type[consts.GREEN],
            dark_percent=self.potion_type[consts.DARK],
            ml_per_barrel=self.ml_per_barrel,
            quantity=self.quantity,
        )

    def with_quantity(self, quantity: int):
        return Barrel(
            sku=self.sku,
            ml_per_barrel=self.ml_per_barrel,
            potion_type=self.potion_type,
            price=self.price,
            quantity=quantity,
        )

    def dummy():
        return Barrel(
            sku="NOTHING", ml_per_barrel=0, potion_type=[], price=0, quantity=0
        )


def deliver_barrels(
    barrels_delivered: list[Barrel], is_purchase: bool = False, order_id=None
):
    # barrel_schemas_delivered: list[BarrelSchema] = [
    #     barrel.to_barrel_schema() for barrel in barrels_delivered
    # ]

    inventory_row: Inventory = db.retrieve_inventory()
    max_added_mls: int = (
        inventory_row.num_ml_capacity() - inventory_row.calculate_total_mls()
    )

    # Purchase will add an order + subtract gold from inventory

    # Otherwise, to deliver, here are the steps:
    # Insert the barrels into Barrels
    # Update Inventory's stats

    with db.engine.begin() as conn:
        # Insert the barrels into Barrels

        # Put a ceil on the number of ml that could be added
        idx = 0
        total_ml_added_scalar: int = 0
        for barrel in barrels_delivered:
            should_break: bool = False

            if (
                total_ml_added_scalar + barrel.calculate_total_mls_value()
                >= max_added_mls
            ):
                # Attempt to fit a quantity
                local_ml_capacity: int = max_added_mls - total_ml_added_scalar
                quantity: int = np.min(
                    [
                        int(float(local_ml_capacity) / barrel.ml_per_barrel),
                        barrel.quantity,
                    ]
                )

                if quantity > 0:
                    barrel.quantity = quantity
                else:
                    # Otherwise, don't add it at all and just break
                    break

                should_break = True

            total_ml_added_scalar += barrel.calculate_total_mls_value()
            idx += 1
            if should_break:
                break

        barrels_delivered = barrels_delivered[:idx]

        barrel_values_tuples: str = ",".join(
            [
                barrel.to_barrel_schema().as_tuple_value_str()
                for barrel in barrels_delivered
            ]
        )

        # print(barrel_values_tuples)

        # Now actually add the barrels in
        conn.execute(
            sqlalchemy.text(
                f"""
                INSERT INTO barrels(sku, red_percent, blue_percent, green_percent, dark_percent, ml_per_barrel, quantity, inventory_id) VALUES {barrel_values_tuples}
                ON CONFLICT (sku) DO UPDATE
                SET quantity = barrels.quantity + EXCLUDED.quantity
                """
            )
        )

        # Get the stats of what just happened
        # Row-wise total mls
        total_mls_added_by_row = np.array(
            [barrel.calculate_total_mls() for barrel in barrels_delivered]
        )
        total_mls_added: np.ndarray = total_mls_added_by_row.sum(axis=0)

        print(total_ml_added_scalar)
        print(total_mls_added)

        # Update Inventory's stats
        update_query: str = f"""
            UPDATE inventory 
            SET red_ml = red_ml + {total_mls_added[consts.RED]}, blue_ml = blue_ml + {total_mls_added[consts.BLUE]}, green_ml = green_ml + {total_mls_added[consts.GREEN]}, dark_ml = dark_ml + {total_mls_added[consts.DARK]} 
        """

        total_prices = [0] * len(barrels_delivered)
        total_price: int = 0
        if is_purchase:
            # If purchase, add gold removing to the query
            total_prices = np.array(
                [barrel.calculate_total_price() for barrel in barrels_delivered]
            )
            total_price = total_prices.sum()

            update_query += f", gold = gold - {total_price}"

        conn.execute(
            sqlalchemy.text(
                f"""
            {update_query}
            WHERE id = {consts.INVENTORY_ID}
            """
            )
        )

        # Now, add an order (if one is supplied)
        if order_id is not None:
            order_tuple_values: str = ""
            for i in range(len(barrels_delivered)):
                order_name: str = barrels_delivered[i].sku
                price: int = total_prices[i]

                order_tuple_values += f"({order_id}, {price}, '{order_name}'), "

            # remove the last ", "
            order_tuple_values = order_tuple_values[:-2]

            conn.execute(
                sqlalchemy.text(
                    f"INSERT INTO orders(order_id, price, order_name) VALUES {order_tuple_values}"
                )
            )


# Given a list of barrels and an `order_id`, this function will actually deliver the barrels (update the db with the delivered barrels)
# Assumes they have already been purchased
@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    # Since they've already been purchased, set their price to 0
    deliver_barrels(barrels_delivered, is_purchase=False, order_id=order_id)

    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called once a day
# Given a `wholesale_catalog` of barrels, the shop will purchase using this function once per day
# NOTE: SUPER KEY ALGORITHM
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    As a very basic initial logic, purchase a new small green potion barrel only if the number of potions in inventory is less than 10.
    Always mix all available green ml if any exists.
    Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
    """

    barrels: list[Barrel] = []

    catalog_len: int = len(wholesale_catalog)

    # Only one row for inventory
    inventory_row: Inventory = db.retrieve_inventory()

    # Hold out some funds for Inventory upgrades
    hold_out_percent: float = 0.2
    budget: int = inventory_row.gold * (1.0 - hold_out_percent)

    def can_purchase(barrels: list[Barrel], budget: int) -> bool:
        for barrel in barrels:
            if budget >= barrel.price:
                return True

        return False

    # Decide strategy
    # policy returns a quantity to purchase at each index
    policy = lambda: ([1] * catalog_len)
    if inventory_row.num_potions < 10:
        # Purchase as many barrels as it can afford
        def restock(barrels: list[Barrel], budget: int = budget) -> list[int]:
            # Choose the barrels that maximize the # of purchases
            # Do it by finding the lowest prices and going from there but also having a diversity score

            purchases: list[int] = [0] * catalog_len
            max_browse = len(barrels)

            random_idx_chance: float = 0.25
            standard_chance: float = 1.0 - random_idx_chance

            prices = np.array([[barrel.price, i] for (i, barrel) in enumerate(barrels)])

            MAX_PRICE = 9999999999
            browse: int = 0

            while can_purchase(barrels, budget):
                # Roll random chance
                randomize_idx: bool = np.random.choice(
                    [True, False], p=[random_idx_chance, standard_chance]
                )

                chosen_idx: int = 0

                if randomize_idx:
                    idx = int(np.random.rand() * catalog_len)
                    barrel: Barrel = barrels[idx]
                    if budget >= barrel.price:
                        # Purchase just 1 (for diversification' sake)
                        purchases[idx] += 1
                        budget -= barrel.price

                        chosen_idx = idx
                    else:
                        continue
                else:
                    # The standard stuff: choose the barrel with the lowest price
                    lowest = prices.argmin(axis=0)[0]
                    lowest_pair = prices[lowest]
                    (price, idx) = (lowest_pair[0], lowest_pair[1])

                    num_purchases = np.min(
                        [int(float(budget) / price), barrels[lowest].quantity]
                    )

                    # Now purchase as many as possible
                    purchases[idx] += num_purchases
                    budget -= num_purchases * price

                # Instead of popping it out, just set to a max value
                prices[chosen_idx, 0] = MAX_PRICE

                browse += 1
                if browse >= max_browse:
                    break

            return purchases

        policy = restock
    else:
        # Purchase the most expensive one that can be afforded
        def aristocratic(barrels: list[Barrel], budget: int = budget) -> list[int]:
            purchases: list[int] = [0] * catalog_len

            random_idx_chance: float = 0.25
            standard_chance: float = 1.0 - random_idx_chance

            prices = np.array([[barrel.price, i] for (i, barrel) in enumerate(barrels)])
            max_browse = len(barrels)

            MIN_PRICE = 0
            browse: int = 0

            while can_purchase(barrels, budget):
                # Roll random chance
                randomize_idx: bool = np.random.choice(
                    [True, False], p=[random_idx_chance, standard_chance]
                )

                chosen_idx: int = 0

                if randomize_idx:
                    idx = int(np.random.rand() * catalog_len)
                    barrel: Barrel = barrels[idx]
                    if budget >= barrel.price:
                        # Purchase just 1 (for diversification' sake)
                        purchases[idx] += 1
                        budget -= barrel.price

                        chosen_idx = idx
                    else:
                        continue
                else:
                    # The standard stuff: choose the barrel with the highest price
                    highest = prices.argmax(axis=0)[0]
                    highest_pair = prices[highest]
                    (price, idx) = (highest_pair[0], highest_pair[1])

                    num_purchases = np.min(
                        [int(float(budget) / price), barrels[highest].quantity]
                    )

                    # Now purchase as many as possible
                    purchases[idx] += num_purchases
                    budget -= num_purchases * price

                    chosen_idx = highest

                # Instead of popping it out, just set to a min value
                prices[chosen_idx, 0] = MIN_PRICE

                browse += 1
                if browse >= max_browse:
                    break

            return purchases

        policy = aristocratic

    # Purchasing SPREE
    purchases: list[bool] = policy(wholesale_catalog)
    for barrel, quantity_to_purchase in zip(wholesale_catalog, purchases):
        if quantity_to_purchase > 0:
            barrels.append(barrel.with_quantity(quantity_to_purchase))

    if len(barrels) > 0:
        deliver_barrels(barrels, is_purchase=True)

    return [{"sku": barrel.sku, "quantity": barrel.quantity} for barrel in barrels]
