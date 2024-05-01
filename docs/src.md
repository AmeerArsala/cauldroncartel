- **admin.py** @ router("/admin")
  
  - `reset()` @POST("/reset")

- **auth.py**
  
  - `get_api_key(request: Request, api_key_header: str = Security(api_key_header))`

- **barrels.py** @ router("/barrels")
  
  - `purchase_barrels(barrels_delivered: list[Barrel])`
  
  - `post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int)` @POST("/deliver/{order_id}")
  
  - `get_wholesale_purchase_plan(wholesale_catalog: list[Barrel])` @POST("/plan")
  
  - NOTE: Barrel Conveyor Belt

- **bottler.py** @ router("/bottler")
  
  - `post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int)` @POST("/deliver/{order_id})
  
  - `get_bottle_plan()` @POST("/plan")
  
  - NOTE: Bottle Conveyor Belt

- **carts.py** @ router("/carts")
  
  - `search_orders(customer_name, potion_sku, search_page, sort_col, sort_order)` @GET("/search/")
  
  - `post_visits(visit_id: int, customers: list[Customer])` @POST("/visits/{visit_id}")
  
  - `create_cart(new_cart: Customer)` @POST("/")
  
  - `set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem)` @POST("/{cart_id}/items/{item_sku}")
  
  - `checkout(cart_id: int, cart_checkout: CartCheckout)` @POST("/{cart_id}/checkout")
  
  - NOTE: customer checkout

- **catalog.py**
  
  - `get_catalog()` @GET("/catalog/")
  - NOTE: available items to sell 

- **info.py**
  
  - `post_time(timestamp: Timestamp)` @POST("/current_time")

- **inventory.py** @ router("/inventory")
  
  - `get_inventory()` @GET("/audit")
  
  - `get_capacity_plan()` @POST("/plan")
  
  - `deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int)` @POST("/deliver/{order_id}")
  
  - NOTE: Capacity/Inventory Upgrades Conveyor Belt

# Action Steps

1. ~~From Jupyter Notebook, check row[0], 1, ..., etc. for the correct column values~~

2. ~~Translate that into code~~

3. Scan this doc for what is needed for arbitrary number of potions 

4. Turn that into a DB and update the codebase accordingly
