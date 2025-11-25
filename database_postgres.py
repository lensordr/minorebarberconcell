from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Supabase PostgreSQL connection
SUPABASE_URL = "https://jljpkwssshgpwqhahtyj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsanBrd3Nzc2hncHdxaGFodHlqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQwNzQ4MTEsImV4cCI6MjA3OTY1MDgxMX0.QFXjK9DNLgJ0AqRmFtNW8RK2n-iJhKcNScuCOoszP7I"

# PostgreSQL connection string for Supabase
DATABASE_URL = os.environ.get(
    'DATABASE_URL', 
    'postgresql://postgres:Minorebarber2025!@db.jljpkwssshgpwqhahtyj.supabase.co:5432/postgres'
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()