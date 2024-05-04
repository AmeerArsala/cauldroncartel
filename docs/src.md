- **admin.py** @ router("/admin")
  
  - ?`reset()` @POST("/reset")

- **auth.py**
  
  - @`get_api_key(request: Request, api_key_header: str = Security(api_key_header))`

- **barrels.py** @ router("/barrels")
  
  - ~~`purchase_barrels(barrels_delivered: list[Barrel])`~~
  
  - @`post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int)` @POST("/deliver/{order_id}")
  
  - @`get_wholesale_purchase_plan(wholesale_catalog: list[Barrel])` **@POST("/plan")**
  
  - <u>NOTE: Barrel Conveyor Belt</u>

- **bottler.py** @ router("/bottler")
  
  - @`post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int)` @POST("/deliver/{order_id})
  
  - @`get_bottle_plan()` **@POST("/plan")**
  
  - <u>NOTE: Bottle Conveyor Belt</u>

- **carts.py** @ router("/carts")
  
  - `search_orders(customer_name, potion_sku, search_page, sort_col, sort_order)` @GET("/search/")
  
  - @`post_visits(visit_id: int, customers: list[Customer])` @POST("/visits/{visit_id}")
  
  - @`create_cart(new_cart: Customer)` @POST("/")
  
  - @`set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem)` @POST("/{cart_id}/items/{item_sku}")
  
  - @`checkout(cart_id: int, cart_checkout: CartCheckout)` @POST("/{cart_id}/checkout")
  
  - <u>NOTE: customer checkout</u>

- **catalog.py**
  
  - @`get_catalog()` @GET("/catalog/")
  - <u>NOTE: available items to sell</u>

- **info.py**
  
  - `post_time(timestamp: Timestamp)` @POST("/current_time")

- **inventory.py** @ router("/inventory")
  
  - @`get_inventory()` @GET("/audit")
  
  - @`get_capacity_plan()` **@POST("/plan")**
  
  - @`deliver_capacity_plan(capacity_purchase: CapacityPurchase, order_id: int)` @POST("/deliver/{order_id}")
  
  - <u>NOTE: Capacity/Inventory Upgrades Conveyor Belt</u>

# TODO

1. On Insert Potion, check to see if it already exists. If so, just add another one. In general, deal with quantities (including carts)

2. Limits on Potions and mL as capacity

3. Ledgers

4. Search Bar

5. `post_time`

6. `reset` for the new era (not global_inventory)

7. `schema.sql`

8. Optimize algorithms to be simple yet time series forecast

9. Update this doc


