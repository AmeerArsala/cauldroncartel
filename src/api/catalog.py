from fastapi import APIRouter

import sqlalchemy
from src import database as db


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as conn:
        result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))

    row = result[0]

    return [
        {
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": row["num_green_potions"],
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        }
    ]
    # return [
    #         {
    #             "sku": "RED_POTION_0",
    #             "name": "red potion",
    #             "quantity": 1,
    #             "price": 50,
    #             "potion_type": [100, 0, 0, 0],
    #         }
    #     ]
