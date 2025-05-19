import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import httpx

from log_config import setup_logger

from fastapi import Body, FastAPI, Form, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from shared_db.db import get_db, engine
from shared_db.models import User, Base  # User is now imported from shared

# FastAPI setup
app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "../UI")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


#logging setup
logger = setup_logger("login", "login/logs/app.log")

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    try:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "register_message": "An unexpected error occurred. Please try again later."
        }, status_code=500)
    except Exception as render_error:
        logger.critical(f"Failed to render fallback page: {render_error}")
        return HTMLResponse("<h1>Something went wrong</h1><p>Please try again later.</p>", status_code=500)

# Create user table (if not exists)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
except SQLAlchemyError as e:
    logger.critical(f"Database connection/setup failed: {e}")
    raise SystemExit("Could not connect to the database.")
except Exception as e:
    logger.critical(f"Unexpected error during DB setup: {e}")
    raise SystemExit("Unexpected error during DB setup.")

# Routes
@app.get("/", response_class=HTMLResponse)
def show_login_page(request: Request):
    logger.info("Rendering login/register page.")
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        return HTMLResponse("<h1>We're having trouble loading the page.</h1>", status_code=500)

@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request):
    return templates.TemplateResponse("store.html", {"request": request})

@app.post("/register")
def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    address: str = Form(...),
    db=Depends(get_db)
):
    logger.info(f"Attempting to register user: {username}")
    try:
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.warning(f"Registration failed: User {username} already exists.")
            return templates.TemplateResponse("index.html", {"request": request, "register_message": "User already exists."}, status_code=400)

        new_user = User(
            username=username,
            password=password,
            email=email,
            full_name=full_name,
            address=address
        )
        db.add(new_user)
        db.commit()
        logger.info(f"User {username} registered successfully")
        return templates.TemplateResponse("index.html", {"request": request, "register_message": "User registered successfully!"})
    except SQLAlchemyError as e:
        logger.error(f"Database error during registration: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "register_message": "Registration failed: please try again."}, status_code=500)
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "register_message": "Registration failed due to an internal error."}, status_code=500)

@app.post("/submit-login")
def handle_login(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(get_db)):
    logger.info(f"User {username} attempting to log in.")
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and user.password == password:
            logger.info(f"User {username} logged in successfully.")

            # Fetch products from shop microservice
            try:
                response = httpx.get("http://localhost:8001/api/products")
                products = response.json()
            except Exception as e:
                logger.error(f"Failed to fetch products: {e}")
                products = []

            return templates.TemplateResponse("store.html", {
                "request": request,
                "products": products,
                "username": username
            })

        logger.warning(f"Invalid login attempt for user: {username}")
        return templates.TemplateResponse("index.html", {"request": request, "login_message": "Login failed: invalid username or password."}, status_code=401)
    except SQLAlchemyError as e:
        logger.error(f"Database error during login: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "login_message": "Login failed due to a database error."}, status_code=500)
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "login_message": "Login failed due to an internal error."}, status_code=500)

@app.post("/submit-order")
def submit_order(request: Request, payload: dict = Body(...)):
    try:
        response = httpx.post("http://localhost:8001/checkout", json=payload)
        response.raise_for_status()
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.RequestError as e:
        logger.error(f"Shop service unreachable: {e}")
        return JSONResponse(content={"message": "Failed to submit order. Shop service is unavailable."}, status_code=503)
    except Exception as e:
        logger.error(f"Unexpected error while submitting order: {e}")
        return JSONResponse(content={"message": "Unexpected error during checkout."}, status_code=500)
