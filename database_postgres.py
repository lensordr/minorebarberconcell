from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use Render PostgreSQL or fallback to Supabase
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Minorebarber2025!')
    DATABASE_URL = f"postgresql+psycopg://postgres.jljpkwssshgpwqhahtyj:{DB_PASSWORD}@aws-1-eu-central-1.pooler.supabase.com:5432/postgres"

print(f"Connecting to PostgreSQL...")

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_timeout=20,
        max_overflow=0,
        connect_args={
            "connect_timeout": 5,
            "application_name": "minore_barbershop"
        }
    )
    # Test connection
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    print("✅ PostgreSQL connected")
except Exception as e:
    print(f"❌ PostgreSQL failed: {e}")
    print("🔄 Using SQLite fallback")
    engine = create_engine(
        "sqlite:///./barbershop.db",
        connect_args={"check_same_thread": False}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()