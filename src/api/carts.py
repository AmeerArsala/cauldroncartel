from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from src.api import auth, catalog
from enum import Enum

import sqlalchemy
from src import database as db
from src.schemas.carts import Cart, CartItem


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

# MAX_CARTS = 100_000_000_000_000


class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"


class CartItem(BaseModel):
    sku: str = Field(default="")
    quantity: int


# class Cart(BaseModel):
#     cart_id: int = Field(default_factory=lambda: np.random.randint(MAX_CARTS))
#     cart_items: dict[str, CartItem] = Field(default={})
#
#     # If `name_starts_with` is left blank, it will just count all items
#     def total_num_items(self, name_starts_with: str = "") -> int:
#         num_items: int = 0
#         for cart_item in self.cart_items.values():
#             if name_starts_with == "" or cart_item.sku.startswith(name_starts_with):
#                 num_items += cart_item.quantity
#
#         return num_items
#
#     def total_price(self) -> int:
#         price: int = 0
#         full_catalog: list[dict[str, str]] = catalog.get_catalog()
#
#         def find_catalog_item(sku: str):
#             for item in full_catalog:
#                 if item["sku"] == sku:
#                     return item
#
#             return {"price": 0}  # default value
#
#         for cart_item in self.cart_items.values():
#             price += find_catalog_item(cart_item.sku)["price"] * cart_item.quantity
#
#         return price
#
#     def as_str(self) -> str:
#         return {"cart_id": f"{self.cart_id:.0f}", "cart_items": self.cart_items}


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int


class CartCheckout(BaseModel):
    payment: str


# carts: dict[int, Cart] = {}


@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku,
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    with db.engine.begin() as conn:
        values_str: str = ""
        for customer in customers:
            values_str += f"('{customer.customer_name}', '{customer.character_class}', {customer.level}), "

        values_str = values_str[:-2]  # remove the last `, `

        conn.execute(
            sqlalchemy.text(
                f"""
            INSERT INTO Customers(name, character_class, level)
            SELECT name, character_class, level
            FROM (VALUES {values_str}) AS T(name, character_class, level)
            WHERE NOT EXISTS (
                SELECT 1
                FROM Customers
                WHERE name = T.name
            )
        """
            )
        )

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    with db.engine.begin() as conn:
        id_query: str = (
            f"SELECT id FROM Customers WHERE name = {new_cart.customer_name} AND character_class = {new_cart.character_class} AND level = {new_cart.level}"
        )

        customer_id = conn.execute(sqlalchemy.text(id_query)).first()

        if len(customer_id) == 0:
            # Make a new customer
            conn.execute(
                sqlalchemy.text(
                    f"INSERT INTO Customers(name, character_class, level) VALUES ({new_cart.customer_name}, {new_cart.character_class}, {new_cart.level})"
                )
            )

        conn.execute(
            sqlalchemy.text(f"INSERT INTO Carts(customer_id) VALUES ({id_query})")
        )

    return "OK"


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as conn:
        find_query: str = (
            f"SELECT * FROM CartItems WHERE cart_id = {cart_id} AND sku = {item_sku}"
        )
        find_result = conn.execute(sqlalchemy.text(find_query)).first()

        if len(find_result) == 0:  # empty
            # Add a new one
            conn.execute(
                sqlalchemy.text(
                    f"INSERT INTO CartItems(sku, cart_id, quantity) VALUES ({item_sku}, {cart_id}, {cart_item.quantity})"
                )
            )
        else:
            # Update the old one's quantity
            conn.execute(
                sqlalchemy.text(
                    f"UPDATE CartItems SET quantity = {cart_item.quantity} WHERE cart_id = {cart_id} AND sku = {item_sku}"
                )
            )

    return "OK"


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    with db.engine.begin() as conn:
        select_result = conn.execute(
            sqlalchemy.text(
                f"""
            SELECT SUM(CartItems.quantity), SUM(CartItems.quantity * CatalogPotionItems.price)
            FROM CartItems INNER JOIN CatalogPotionItems ON CartItems.sku = CatalogPotionItems.sku
            WHERE CartItems.cart_id = {cart_id}
            """
            )
        )

        (total_potions_bought, total_gold_paid) = select_result.first()

        # Apply difference in potion items from cart
        # Update inventory gold
        update_query = f"""
            UPDATE (CartItems INNER JOIN CatalogPotionItems ON CartItems.sku = CatalogPotionItems.sku)
            INNER JOIN Potions ON CatalogPotionItems.sku = Potions.sku
            INNER JOIN Inventory ON Potions.inventory_id = Inventory.id
            SET CatalogPotionItems.quantity = CatalogPotionItems.quantity - CartItems.quantity, Potions.quantity = Potions.quantity - CartItems.quantity, Inventory.gold = Inventory.gold + {total_gold_paid}, Inventory.num_potions = Inventory.num_potions + {total_gold_paid}
            WHERE CartItems.cart_id = {cart_id}
        """
        conn.execute(sqlalchemy.text(update_query))

        # Empty cart items
        conn.execute(
            sqlalchemy.text(f"DELETE FROM CartItems WHERE cart_id = {cart_id}")
        )

    return {
        "total_potions_bought": total_potions_bought,
        "total_gold_paid": total_gold_paid,
    }
