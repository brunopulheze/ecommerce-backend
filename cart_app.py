from fastapi import FastAPI, Depends, HTTPException, APIRouter
from pymongo import MongoClient
from bson import ObjectId
from typing import List, Dict, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# Import the real get_current_user dependency and UserOut model from auth_app.py
from auth_app import get_current_user, UserOut

# MongoDB setup (adjust connection string as needed)
import os
from dotenv import load_dotenv
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

router = APIRouter()

@router.get("/products")
def get_products():
    products = list(db.products.find())
    for p in products:
        p["id"] = str(p["_id"])
        del p["_id"]
    return products

@router.get("/products/{product_id}")
def get_product(product_id: str):
    product = db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(404, detail="Product not found")
    product["id"] = str(product["_id"])
    del product["_id"]
    return product

@router.get("/cart")
def get_cart(current_user: UserOut = Depends(get_current_user)):
    cart = db.carts.find_one({"user_id": current_user.id}) or {"items": []}
    # Remove or convert all ObjectId fields before returning
    if "_id" in cart:
        cart["id"] = str(cart["_id"])
        del cart["_id"]
    # If any item has an ObjectId field, convert those too
    for item in cart.get("items", []):
        if "product_id" in item and isinstance(item["product_id"], ObjectId):
            item["product_id"] = str(item["product_id"])
    return cart

@router.post("/cart")
def update_cart(
    items: List[Dict[str, Any]],
    current_user: UserOut = Depends(get_current_user)
):
    db.carts.update_one(
        {"user_id": current_user.id},
        {"$set": {"items": items}},
        upsert=True
    )
    return {"status": "ok"}

@router.post("/checkout")
def checkout(current_user: UserOut = Depends(get_current_user)):
    cart = db.carts.find_one({"user_id": current_user.id})
    if not cart or not cart.get("items"):
        raise HTTPException(400, detail="Cart is empty")
    total = 0
    items = []
    for item in cart["items"]:
        prod = db.products.find_one({"_id": ObjectId(item["product_id"])})
        if not prod or prod["stock"] < item["quantity"]:
            raise HTTPException(400, detail=f"Not enough stock for {prod['name'] if prod else 'Unknown'}")
        db.products.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$inc": {"stock": -item["quantity"]}}
        )
        total += prod["price"] * item["quantity"]
        items.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "price": prod["price"]
        })
    db.purchases.insert_one({
        "user_id": current_user.id,
        "items": items,
        "total": total,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "completed"
    })
    db.carts.delete_one({"user_id": current_user.id})
    return {"status": "ok", "total": total}