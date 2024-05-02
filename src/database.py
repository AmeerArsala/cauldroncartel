import os
import dotenv
import sqlalchemy
from sqlalchemy import create_engine
from src.schemas.inventory import Inventory


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")


engine = create_engine(database_connection_url(), pool_pre_ping=True)


def retrieve_inventory() -> Inventory:
    global engine

    with engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM Inventory"))

    row: Inventory = Inventory.wrap_result(result.first())

    return row
