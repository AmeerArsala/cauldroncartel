from fastapi import APIRouter, HTTPException

import sqlalchemy
from src import database as db
from src.schemas.catalogitems import CatalogItem


router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    catalog: list[dict] = []

    try:
        with db.engine.begin() as conn:
            result = conn.execute(
                sqlalchemy.text(
                    """
                    SELECT (CatalogPotionItems.sku, name, CatalogPotionItems.quantity, price, red_percent, blue_percent, green_percent, dark_percent)
                    FROM CatalogPotionItems INNER JOIN Potions ON CatalogPotionItems.sku = Potions.sku
                    """
                )
            )

        rows = result.fetchall()

        def to_catalog_potion_dict(item: CatalogItem) -> dict:
            return {
                "sku": item.sku,
                "name": item.name,
                "quantity": item.quantity,
                "price": item.price,
                "potion_type": [
                    item.red_percent,
                    item.blue_percent,
                    item.green_percent,
                    item.dark_percent,
                ],
            }

        catalog = [to_catalog_potion_dict(CatalogItem.wrap_result(row)) for row in rows]
    except sqlalchemy.exc.SQLAlchemyError as err:
        print(err)
        raise HTTPException(status_code=500, detail="Internal server error")

    return catalog
