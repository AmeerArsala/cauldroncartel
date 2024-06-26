from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from src.api import auth, catalog
from enum import Enum

import sqlalchemy
from src import database as db
from src.schemas.carts import Cart  # CartItem
from src.schemas.searchresults import SearchResult

import numpy as np


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
    # sku: str = Field(default="")
    quantity: int


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int


class CartCheckout(BaseModel):
    payment: str


# line_temp_id: int = 0
#
#
# def gen_id():
#     global line_temp_id
#
#     line_temp_id += 1
#
#     return line_temp_id


@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: int = 1,
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

    PREV_PAGE_TOKEN = search_page - 1
    NEXT_PAGE_TOKEN = search_page + 1

    ITEMS_PER_PAGE = 5  # change later
    # offset: int = (search_page - 1) * ITEMS_PER_PAGE

    first_idx: int = (search_page - 1) * ITEMS_PER_PAGE
    last_idx: int = (search_page * ITEMS_PER_PAGE) - 1

    # Normalize options
    order_by: str = str(sort_order).upper()
    sort_by_col: str = ""
    if sort_col == search_sort_options.item_sku:
        sort_by_col = "cartitems.sku"
    elif sort_col == search_sort_options.customer_name:
        sort_by_col = "customers.name"
    elif sort_col == search_sort_options.line_item_total:
        sort_by_col = "line_item_total"
    elif sort_col == search_sort_options.timestamp:
        sort_by_col = "cartitems.timestamp"

    with db.engine.begin() as conn:
        query: str = """
                SELECT ROW_NUMBER() OVER () AS line_item_id, cartitems.sku, customers.name, (cartitems.quantity * catalogpotionitems.price) AS line_item_total, cartitems.timestamp
                FROM cartitems
                INNER JOIN carts ON cartitems.cart_id = carts.id
                INNER JOIN customers ON carts.customer_id = customers.id
                INNER JOIN catalogpotionitems ON cartitems.sku = catalogpotionitems.sku
                WHERE customers.name = :name AND cartitems.sku = :sku"""

        if len(sort_by_col) > 0:
            query += f"""
                ORDER BY {sort_by_col} {order_by}
            """

        # NOTE: I removed this to deal with a degenerate case
        # query += """
        #     LIMIT :results_per_page OFFSET :offset
        # """

        results = conn.execute(
            sqlalchemy.text(
                query,
                [
                    {"name": customer_name, "sku": potion_sku}
                ],  # "results_per_page": ITEMS_PER_PAGE, "offset": offset
            )
        )

        full_search_results: list[SearchResult] = [
            SearchResult.wrap_result(result) for result in results
        ]

        # Time to include the paging in the postprocessing as to not screw with the degenerate case
        # Who cares about overfetching!!! Who cares about the environment!!!
        # I'd be using GraphQL if I did!!!
        has_prev_page: bool = search_page > 1
        has_next_page: bool = last_idx < len(full_search_results)

        search_results: list[SearchResult] = full_search_results[
            first_idx : (last_idx + 1)
        ]

    return {
        "previous": PREV_PAGE_TOKEN if has_prev_page else None,
        "next": NEXT_PAGE_TOKEN if has_next_page else None,
        "results": search_results,
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
            INSERT INTO customers(name, character_class, level)
            SELECT name, character_class, level
            FROM (VALUES {values_str}) AS T(name, character_class, level)
            WHERE NOT EXISTS (
                SELECT 1
                FROM customers
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
            f"SELECT id FROM customers WHERE name = '{new_cart.customer_name}' AND character_class = '{new_cart.character_class}' AND level = {new_cart.level}"
        )

        customer_id = conn.execute(sqlalchemy.text(id_query)).first()

        if customer_id is None or len(customer_id) == 0:  # it doesn't exist
            # print(err)

            # Make a new customer
            conn.execute(
                sqlalchemy.text(
                    f"INSERT INTO customers(name, character_class, level) VALUES ('{new_cart.customer_name}', '{new_cart.character_class}', {new_cart.level})"
                )
            )

            # redo the customer_id
            customer_id = conn.execute(sqlalchemy.text(id_query)).first()

        customer_id = np.array(customer_id).ravel().tolist()[0]

        conn.execute(
            sqlalchemy.text(f"INSERT INTO carts(customer_id) VALUES ({customer_id})")
        )

    return "OK"


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    should_delete_item: bool = cart_item.quantity == 0

    with db.engine.begin() as conn:
        if should_delete_item:
            conn.execute(
                sqlalchemy.text(
                    f"DELETE FROM cartitems WHERE cart_id = {cart_id} AND sku = '{item_sku}'"
                )
            )
            return "OK"

        find_query: str = (
            f"SELECT * FROM cartitems WHERE cart_id = {cart_id} AND sku = '{item_sku}'"
        )
        find_result = conn.execute(sqlalchemy.text(find_query)).first()

        if find_result is None or len(find_result) == 0:  # empty
            # Add a new one
            conn.execute(
                sqlalchemy.text(
                    f"INSERT INTO cartitems(sku, cart_id, quantity) VALUES ('{item_sku}', {cart_id}, {cart_item.quantity})"
                )
            )
        else:
            # Update the old one's quantity
            conn.execute(
                sqlalchemy.text(
                    f"UPDATE cartitems SET quantity = {cart_item.quantity} WHERE cart_id = {cart_id} AND sku = '{item_sku}'"
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
            SELECT SUM(cartitems.quantity), SUM(cartitems.quantity * catalogpotionitems.price)
            FROM cartitems INNER JOIN catalogpotionitems ON cartitems.sku = catalogpotionitems.sku
            WHERE cartitems.cart_id = {cart_id}
            """
            )
        )

        (total_potions_bought, total_gold_paid) = select_result.first()

        # Apply difference in potion items from cart
        # Update inventory gold
        update_query = f"""
            WITH update_catalogpotionitems AS (
                UPDATE catalogpotionitems
                SET quantity = catalogpotionitems.quantity - cartitems.quantity
                FROM cartitems
                WHERE cartitems.sku = catalogpotionitems.sku
            ),
            update_potions AS (
                UPDATE potions
                SET quantity = potions.quantity - cartitems.quantity
                FROM cartitems
                WHERE potions.sku = cartitems.sku
            ),
            UPDATE inventory
            SET gold = gold + {total_gold_paid}, num_potions = num_potions + {total_gold_paid}
        """

        conn.execute(sqlalchemy.text(update_query))

        # cleanup
        conn.execute(
            sqlalchemy.text("DELETE FROM catalogpotionitems WHERE quantity <= 0")
        )
        conn.execute(sqlalchemy.text("DELETE FROM potions WHERE quantity <= 0"))

        # Empty cart items
        conn.execute(
            sqlalchemy.text(f"DELETE FROM cartitems WHERE cart_id = {cart_id}")
        )

        # Delete cart
        conn.execute(sqlalchemy.text(f"DELETE FROM carts WHERE id = {cart_id}"))

    return {
        "total_potions_bought": total_potions_bought,
        "total_gold_paid": total_gold_paid,
    }
