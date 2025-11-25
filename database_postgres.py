from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL connection
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Minorebarber2025!')
DATABASE_URL = f"postgresql+psycopg://postgres:{DB_PASSWORD}@db.jljpkwssshgpwqhahtyj.supabase.co:5432/postgres"

print(f"Connecting to: postgresql+psycopg://postgres:***@db.jljpkwssshgpwqhahtyj.supabase.co:5432/postgres")

engine = create_engine(
    DATABASE_URL,
    echo=True,  # Debug SQL
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()