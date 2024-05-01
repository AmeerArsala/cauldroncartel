- **admin.py** @ router("/admin")
  
  - `reset()` @router.post("/reset")

- **auth.py**
  
  - `get_api_key(request: Request, api_key_header: str = Security(api_key_header))`

- **barrels.py** @ router("/barrels")
  
  - `purchase_barrels(barrels_delivered: list[Barrel])`
  
  - `post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int)` @router.post("/deliver/{order_id}")
  
  - `get_wholesale_purchase_plan(wholesale_catalog: list[Barrel])` @router.post("/plan")

- **bottler.py** @ router("/bottler")
  
  - `post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int)` @router.post("/deliver/{order_id})
  
  - `get_bottle_plan()` @router.post("/plan")

- **carts.py** @ router("/carts")
  
  - `search_orders(customer_name, potion_sku, search_page, sort_col, sort_order)` @router.get("/search/")
  
  - `post_visits(visit_id: int, customers: list[Customer])` @router.post("/visits/{visit_id}")
  
  - `create_cart(new_cart: Customer)` @router.post("/")
  
  - `set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem)` @router.post("/{cart_id}/items/{item_sku}")
  
  - `checkout(cart_id: int, cart_checkout: CartCheckout)` @router.post("/{cart_id}/checkout")

- **catalog.py**
  
  - `get_catalog()` @router.get("/catalog/")

- **info.py**
  
  - `post_time(timestamp: Timestamp)` @router.post("/current_time")

- **inventory.py** @ router("/inventory")
  
  - `get_inventory()` @router.get("/audit")
  
  - `get_capacity_plan()` @router.post("/plan")
  
  - `deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int)` @router.post("/deliver/{order_id}")



# Action Steps

1. From Jupyter Notebook, check row[0], 1, ..., etc. for the correct column values

2. Translate that into code

3. Scan this doc for what is needed for arbitrary number of potions 

4. Turn that into a DB and update the codebase accordingly
