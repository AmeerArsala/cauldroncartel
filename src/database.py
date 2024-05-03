import os
import dotenv
import sqlalchemy
from sqlalchemy import create_engine
from src.schemas.inventory import Inventory
import src.constants as consts


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")


engine = create_engine(database_connection_url(), pool_pre_ping=True)


def retrieve_inventory() -> Inventory:
    global engine

    with engine.begin() as connection:
        result = connection.execute(sqlalchemy.text("SELECT * FROM inventory"))

    row: Inventory = Inventory.wrap_result(result.first())

    consts.INVENTORY_ID = row.id_

    return row


# with engine.begin() as connection:
#     results = connection.execute(
#         sqlalchemy.text(
#             "SELECT * FROM inventory"
#             # "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
#         )
#     )
#     print("printing result...")
#     print(results.fetchall())
