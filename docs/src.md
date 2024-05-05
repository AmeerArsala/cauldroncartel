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

# Key Algorithms

TODO: put tick/day frequency for each one of these

- **lib/potion_selling.py**
  
  - `put_subset_for_sale(potions: list[Potion]) -> list[Potion]`
  
  - `price_potion(potion: Potion) -> int`

- **lib/potion_generation.py**
  
  - `make_potions_from_mls(total_mls: np.ndarray) -> tuple[list[Potion], np.ndarray]`

- **lib/barreling.py**
  
  - `stabilize_barrels(new_total_ml: np.ndarray) -> list[BarrelSchema]`

- **api/barrels.py** @ router("/barrels")
  
  - `get_wholesale_purchase_plan(wholesale_catalog: list[Barrel])` @POST("/plan")

- **api/inventory.py** @ router("/inventory")
  
  - `get_capacity_plan()` @POST("/plan")



# TODO

1. ~~On Insert Potion, check to see if it already exists. If so, just add another one. In general, deal with quantities (including carts)~~

2. ~~Limits on Potions and mL as capacity~~

3. `put_subset_for_sale`
   
   - ~~Only 6 potions can be sold at a time in the catalog. Take care of this~~
   
   - ~~Have it take into account the existing potions in addition to the ones being added~~
   
   - Have it take into account what was previously sold (historical data)

4. ~~Delete 0 quantity items~~
   
   - ~~CartItems (when set to 0)~~
   
   - ~~Potions (when checkout)~~
   
   - ~~Barrels (when going from barrel to bottle)~~

5. Ledgers

6. ~~Have checkout delete the cart~~

7. ~~Have all potions/catalogpotionitems that go to 0 be deleted~~

8. ~~Search Bar~~

9. ~~`post_time`~~

10. ~~`reset` for the new era (not global_inventory)~~

11. `schema.sql`

12. Optimize algorithms to be simple yet time series forecast

13. Update this doc



New info:

- You can only sell 6 potions at a time
