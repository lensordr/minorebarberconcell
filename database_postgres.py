from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use Render PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    # Render PostgreSQL URL
    DATABASE_URL = "postgresql://minore_barbershop_production_user:wpxw9iKAdGi4BFyXabqHYl9hSxkdwEYB@dpg-d4jijreuk2gs73bm33vg-a.frankfurt-postgres.render.com/minore_barbershop_production"

print(f"Connecting to PostgreSQL...")

# Use psycopg (not psycopg2) for Python 3.13 compatibility
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,  # Reduced from 1800
    pool_timeout=10,   # Reduced from 20
    pool_size=10,      # Increased pool size
    max_overflow=5,    # Increased from 0
    connect_args={
        "connect_timeout": 5,  # Reduced from 10
        "application_name": "minore_barbershop"
    }
)
print("✅ Using PostgreSQL database only")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()