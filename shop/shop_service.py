import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from log_config import setup_logger

import json
from typing import Dict

from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from shared_db.db import engine, get_db
from shared_db.models import Order, User  # Make sure User is also imported


# FastAPI setup
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "../UI")

templates = Jinja2Templates(directory=TEMPLATES_DIR)



# Logging setup
logger = setup_logger("shop", "shop/logs/shop.log")


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Order table if not already in users.db
try:
    Order.__table__.create(bind=engine, checkfirst=True)
    logger.info("Orders table created or already exists in shared DB.")
except SQLAlchemyError as e:
    logger.critical(f"Error creating orders table: {e}")

# Product list endpoint
@app.get("/api/products")
def get_products():
    try:
        products = [
            {"name": "Apple", "price": 1.00},
            {"name": "Banana", "price": 0.75},
            {"name": "Orange", "price": 1.25},
        ]
        logger.info("Fetched product list.")
        return JSONResponse(content=products)
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return JSONResponse(content={"message": "Failed to fetch products."}, status_code=500)

# Checkout request schema
class CheckoutRequest(BaseModel):
    username: str
    cart: Dict[str, int]

@app.post("/checkout")
def checkout(payload: CheckoutRequest, db=Depends(get_db)):
    logger.info(f"Received checkout for user: {payload.username}")
    try:
        # Look up user to get user_id
        user = db.query(User).filter(User.username == payload.username).first()
        if not user:
            logger.warning(f"Checkout failed: user {payload.username} not found.")
            return JSONResponse(content={"message": "User not found."}, status_code=404)

        order = Order(
            user_id=user.id,
            cart=json.dumps(payload.cart)
        )
        db.add(order)
        db.commit()
        logger.info(f"Order saved for user: {payload.username}")
        return JSONResponse(content={"message": "Order submitted!"}, status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Error saving order for user {payload.username}: {e}")
        return JSONResponse(content={"message": "Failed to save order."}, status_code=500)

# Optional UI route for testing
@app.get("/shop", response_class=HTMLResponse)
def shop(request: Request):
    try:
        products = [
            {"name": "Apple", "price": 1.00},
            {"name": "Banana", "price": 0.75},
            {"name": "Orange", "price": 1.25},
        ]
        logger.info("Rendering shop UI.")
        return templates.TemplateResponse("shop.html", {"request": request, "products": products})
    except Exception as e:
        logger.error(f"Error rendering shop UI: {e}")
        return HTMLResponse("<h1>Failed to load shop page.</h1>", status_code=500)
