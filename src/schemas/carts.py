from src.schemas import Schema, wrap_result_with_schema


class Cart(Schema):
    id: int
    customer_id: int

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, Cart)


class CartItem(Schema):
    sku: str
    cart_id: int
    quantity: int

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, CartItem)
