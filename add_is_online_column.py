#!/usr/bin/env python3
"""
Migration script to add is_online column to appointments table
"""

from database_postgres import SessionLocal, engine
from sqlalchemy import text

def add_is_online_column():
    """Add is_online column to appointments table"""
    
    with engine.connect() as connection:
        try:
            # Add the column
            connection.execute(text("ALTER TABLE appointments ADD COLUMN is_online INTEGER DEFAULT 0"))
            connection.commit()
            print("✅ Added is_online column to appointments table")
            
        except Exception as e:
            if "already exists" in str(e) or "duplicate column" in str(e):
                print("✅ is_online column already exists")
            else:
                print(f"❌ Error adding column: {e}")
                raise

if __name__ == "__main__":
    print("Adding is_online column to appointments table...")
    add_is_online_column()
    print("Migration completed!")