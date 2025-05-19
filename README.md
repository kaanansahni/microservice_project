# Microservices Project

This is a simple microservices-based application built with FastAPI. It includes a login/authentication service, a shop/order service, and a shared SQLite database.

---

## 🛠 Project Structure

main
|
requirements.txt - old - much more added
|
login
|  |_ main.py
|  |_ logs for login
|
shop
|  |_ shop_service.py
|  |_ logs for login
|
shared_db
|  |_ db.py - creation of db
|  |_ models.py - creation of tables
|
UI
|  |_ index.html - login html
|  |_ store.html
|
log_config.py - log configerations
|
users.db - db for project (SQLite)



start main (login)
uvicorn login.main:app --reload --port 8000


start shop
uvicorn shop.main:app --reload --port 8001
