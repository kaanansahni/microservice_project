# shared/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Shared SQLite database location
DATABASE_URL = "sqlite:////Users/kaanansahni/microservices_project/users.db"  # Adjust if needed (e.g., absolute path in deployment)

# Create the engine with appropriate SQLite settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite + multithreaded FastAPI
)

# Create a session factory bound to the engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a DB session (used in FastAPI routes)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
