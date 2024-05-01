from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from src.api import auth, catalog
from enum import Enum
import numpy as np

import sqlalchemy
from src import database as db


router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

MAX_CARTS = 100_000_000_000_000


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


class Cart(BaseModel):
    cart_id: int = Field(default_factory=lambda: np.random.randint(MAX_CARTS))
    cart_items: dict[str, CartItem] = Field(default={})

    # If `name_starts_with` is left blank, it will just count all items
    def total_num_items(self, name_starts_with: str = "") -> int:
        num_items: int = 0
        for cart_item in self.cart_items.values():
            if name_starts_with == "" or cart_item.sku.startswith(name_starts_with):
                num_items += cart_item.quantity

        return num_items

    def total_price(self) -> int:
        price: int = 0
        full_catalog: list[dict[str, str]] = catalog.get_catalog()

        def find_catalog_item(sku: str):
            for item in full_catalog:
                if item["sku"] == sku:
                    return item

            return {"price": 0}  # default value

        for cart_item in self.cart_items.values():
            price += find_catalog_item(cart_item.sku)["price"] * cart_item.quantity

        return price

    def as_str(self) -> str:
        return {"cart_id": f"{self.cart_id:.0f}", "cart_items": self.cart_items}


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int


class CartCheckout(BaseModel):
    payment: str


carts: dict[int, Cart] = {}


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

    return "OK"


@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    global carts

    cart: Cart = Cart()
    carts[cart.cart_id] = cart

    return cart.dict()  # cart.as_str()


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    global carts

    print(carts)
    cart: Cart = carts[cart_id]

    # cart_item.sku = item_sku

    cart.cart_items[item_sku] = CartItem(sku=item_sku, quantity=cart_item.quantity)

    return "OK"


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    global carts

    cart: Cart = carts[cart_id]

    # Calculate result
    total_potions_bought = cart.total_num_items()

    total_green_potions_bought: int = cart.total_num_items(name_starts_with="GREEN")
    total_red_potions_bought: int = cart.total_num_items(name_starts_with="RED")
    total_blue_potions_bought: int = cart.total_num_items(name_starts_with="BLUE")

    total_gold_paid: int = cart.total_price()

    with db.engine.begin() as conn:
        select_result = conn.execute(sqlalchemy.text("SELECT * FROM global_inventory"))
        row = dict(db.wrap_result_as_global_inventory(select_result.first()))

        # Calculate update
        current_green_potions: int = (
            row["num_green_potions"] - total_green_potions_bought
        )
        current_red_potions: int = row["num_red_potions"] - total_red_potions_bought
        current_blue_potions: int = row["num_blue_potions"] - total_blue_potions_bought
        current_gold: int = row["gold"] + total_gold_paid

        # Apply update
        conn.execute(
            sqlalchemy.text(
                f"UPDATE global_inventory SET gold = {current_gold}, num_green_potions = {current_green_potions}, num_red_potions = {current_red_potions}, num_blue_potions = {current_blue_potions}"
            )
        )

    return {
        "total_potions_bought": total_potions_bought,
        "total_gold_paid": total_gold_paid,
    }
