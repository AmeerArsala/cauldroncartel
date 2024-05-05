from src.schemas import Schema, wrap_result_with_schema

# from pydantic import Field


class SearchResult(Schema):
    line_item_id: int
    item_sku: str
    customer_name: str
    line_item_total: int  # total price
    timestamp: str

    def wrap_result(row: tuple):
        return wrap_result_with_schema(row, SearchResult)
