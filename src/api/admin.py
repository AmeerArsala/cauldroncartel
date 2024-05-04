from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                "UPDATE inventory SET gold = 100, num_potions = 0, red_ml = 0, blue_ml = 0, green_ml = 0, dark_ml = 0, potion_capacity = 1, ml_capacity = 1"
            )
        )

        # Start deleting!!!
        connection.execute(sqlalchemy.text("DELETE * FROM barrels"))
        connection.execute(sqlalchemy.text("DELETE * FROM cartitems"))
        connection.execute(sqlalchemy.text("DELETE * FROM orders"))
        connection.execute(sqlalchemy.text("DELETE * FROM catalogpotionitems"))
        connection.execute(sqlalchemy.text("DELETE * FROM potions"))
        connection.execute(sqlalchemy.text("DELETE * FROM carts"))

    return "OK"
