import os
import dotenv
from sqlalchemy import create_engine

from uuid import UUID
from pydantic import BaseModel


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")


class GlobalInventory(BaseModel):
    id_: UUID
    gold: int

    num_green_potions: int
    num_green_ml: int

    num_red_potions: int
    num_red_ml: int

    num_blue_potions: int
    num_blue_ml: int


def wrap_result_as_global_inventory(
    row: tuple[UUID, int, int, int, int, int, int, int]
) -> GlobalInventory:
    return GlobalInventory(
        id_=row[0],
        gold=row[3],
        num_green_potions=row[1],
        num_green_ml=row[2],
        num_red_potions=row[4],
        num_red_ml=row[5],
        num_blue_potions=row[6],
        num_blue_ml=row[7],
    )


engine = create_engine(database_connection_url(), pool_pre_ping=True)
