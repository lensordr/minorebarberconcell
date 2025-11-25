from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL connection using environment variables
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    f"postgresql+psycopg://postgres:{os.environ.get('DB_PASSWORD', 'Minorebarber2025!')}@db.jljpkwssshgpwqhahtyj.supabase.co:5432/postgres"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()