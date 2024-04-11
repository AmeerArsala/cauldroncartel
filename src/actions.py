import sqlalchemy
from src import database as db
from src.api.barrels import Barrel


def initial_purchase(wholesale_catalog: list[Barrel]):
    """
    As a very basic initial logic, purchase a new small green potion barrel only if the number of potions in inventory is less than 10.
    Always mix all available green ml if any exists.
    Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
    """

    # with db.engine.begin() as conn:
    #     result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
    #
    # row = result[0]  # Only one row rn
    #
    # if row["num_green_potions"] < 10:
    #     # Purchase a new small green potion barrel
    #     barrels: list[Barrel] = [
    #             Barrel(sku="SMALL_GREEN_BARREL", ml_per_barrel=, potion_type=[0, 0, 100, 0], price=, quantity=1)
    #     ]

    # Offer up for sale in the catalog only the amount of green potions that actually exist currently in inventory.
    # Done in `catalog.py`
