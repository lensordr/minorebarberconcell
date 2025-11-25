from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use Render PostgreSQL or fallback to Supabase
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Minorebarber2025!')
    DATABASE_URL = f"postgresql+psycopg://postgres.jljpkwssshgpwqhahtyj:{DB_PASSWORD}@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"

print(f"Connecting to PostgreSQL...")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 10,
        "application_name": "minore_barbershop",
        "options": "-c default_transaction_isolation=read_committed"
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()