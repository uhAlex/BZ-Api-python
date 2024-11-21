import requests
import re
from fastapi import FastAPI, Query
from typing import List, Optional
items = requests.get("https://api.hypixel.net/v2/resources/skyblock/items").json().get("items")
usersItems = []



def getName(id):
    """Get the name of the item with the given ID"""
    for item in items:
        if item["id"] == id:
            name = item["name"]
            name = re.sub(r'%%.*?%%', '', name[2:] if name and name.startswith("§") else name) if name else name
            return name

def updateData():
    """Updated items from the Hypixel API to the global variable "items"."""
    global items
    items = requests.get("https://api.hypixel.net/v2/resources/skyblock/items").json().get("items")
    # Update the items list in the global scope

def getProducts():
    """
    Returns the Hypixel Skyblock Bazaar.
    """
    products = requests.get("https://api.hypixel.net/v2/skyblock/bazaar").json().get("products", {}).values()
    return list(products)

def getInfo(mpi = 50, mpp = 8, mfp = 3000000, mbi = 30000, BFp = 0, sellHours = 2, purse = 100000000, maxSpent = 0.5, avoid = ["LOG:1"]):
    """
    ---------------------------------------------------*****Parameters*****---------------------------------------------------
    | mpi (int): minimum amount of profit per item                                                                           |
    | mpp (int): maximum amount of profit percent                                                                            |
    | mfp (int): minimum amount of total profit per order                                                                    |
    | mbi (int): minimum amount of items to buy (useful to avoid low supply items)                                           |
    | BFp (int): bazaar flipper perk, found in the community shop. (Used for tax calculations.)                              |
    | sellHours (int): approximate amount of hours needed to sell each item. (Used to decide actual flips that will sell)    |
    | purse (int): amount of money player is currently holding (used to limit the amount spent per order)                    |
    | maxSpent (float): biggest percentage of purse used to buy each order.                                                  |
    | avoid (list): list of item IDs to avoid (e.g., ["item_id_1", "item_id_2"])                                             |
    | Returns a 2D list: [[name, id, buyAmount, cost, totalProfit], [name, id, buyAmount, cost, totalProfit]]                |
    --------------------------------------------------------------------------------------------------------------------------
    """
    
    updateData() #UPDATE DATA
    products = getProducts() #Get BZ Products
    UsableData = []
    for product in products: #loops through each product in the bazaar
        item = product.get("quick_status") #gets generalized data of the product, I prefer to call this the item('s data) as opposed to the product('s data) as it is generalized

        name = getName(item.get("productId")) 
        if name is None: continue 
        #Searchable name with /bz name, if it does not exist then the item cannot be flipped

        id = item.get("productId")
        if id in avoid: continue
        #ID of the product for blacklisting

        buyOrder = product.get("sell_summary")[0].get("pricePerUnit") if product.get("sell_summary") else 0
        if buyOrder == 0: continue 
        sellOrder = product.get("buy_summary")[0].get("pricePerUnit") if product.get("buy_summary") else 0
        if sellOrder == 0: continue
        #avoidence of no sell or buy price and instructions for order.

        gap = sellOrder - buyOrder
        taxCoefficient = 0.0125 - (0.00125*BFp)
        profit = gap - sellOrder*(taxCoefficient)
        if profit <= 0: continue
        profitPercent = (profit / buyOrder * 100) if buyOrder != 0 else 0
        if profitPercent <= 0: continue
        #filtering stuff for profit and profit percent

        sellWeek = item.get("buyMovingWeek") 
        if sellWeek is None: continue
        sellDay = sellWeek/7
        sellHour = sellDay/24
        #items instant bought/recieved from a sell order in the past 7 days translated to items per hour.

        buyAmount = int(sellHour * sellHours)
        if buyAmount == 0: continue
        if buyAmount > 71800: buyAmount = 71800
        #calculations to find how many you can buy and clear in the target time.

        fullProfit = profit*buyAmount
        cost = buyAmount*buyOrder

        if (profit < mpi): continue
        if (profitPercent < mpp): continue
        if (fullProfit < mfp): continue
        if (buyAmount < mbi): continue
        if (cost > purse*maxSpent): continue

        UsableData.append([name, id, buyAmount, cost, fullProfit])

        output = (f"""
        ===========================================================================================
        | Name: {name}                                                                            |
        | ID: "{id}"                                                                              |
        | Profit: {int(fullProfit)} coins                                                         |
        | Profit Percentage: {int(profitPercent)}%                                                |
        | Purchase: {buyAmount} items                                                             |
        | Spent: {cost} coins limited by {purse} in purse with max spending being {maxSpent*100}% |
        ===========================================================================================
        """)
    return UsableData

def setup_routes(app: FastAPI):
    # Define the GET endpoint
    @app.get("/flips/")
    async def flips(
        mpi: int = Query(50),
        mpp: int = Query(8),
        mfp: int = Query(3000000),
        mbi: int = Query(30000),
        BFp: int = Query(0),
        sellHours: int = Query(2),
        purse: int = Query(100000000),
        maxSpent: float = Query(0.5),
        avoid: Optional[List[str]] = Query(["LOG:1"])
    ):
        """
        Endpoint to call getInfo with given parameters.
        ---------------------------------------------------*****Parameters*****---------------------------------------------------
        | mpi (int): minimum amount of profit per item                                                                           |
        | mpp (int): maximum amount of profit percent                                                                            |
        | mfp (int): minimum amount of total profit per order                                                                    |
        | mbi (int): minimum amount of items to buy (useful to avoid low supply items)                                           |
        | BFp (int): bazaar flipper perk, found in the community shop. (Used for tax calculations.)                              |
        | sellHours (int): approximate amount of hours needed to sell each item. (Used to decide actual flips that will sell)    |
        | purse (int): amount of money player is currently holding (used to limit the amount spent per order)                    |
        | maxSpent (float): biggest percentage of purse used to buy each order.                                                  |
        | avoid (list): list of item IDs to avoid (e.g., ["item_id_1", "item_id_2"])                                             |
        | Returns a 2D list: [[name, id, buyAmount, cost, totalProfit], [name, id, buyAmount, cost, totalProfit]]                |
        --------------------------------------------------------------------------------------------------------------------------
        """
        return getInfo(mpi, mpp, mfp, mbi, BFp, sellHours, purse, maxSpent, avoid)

def create_app():
    """Create a FastAPI app with routes from setup routes."""
    app = FastAPI()
    # Register the routes
    setup_routes(app)
    return app

app = create_app() # Create a FastAPI app with routes from setup routes