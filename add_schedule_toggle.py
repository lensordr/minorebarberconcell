#!/usr/bin/env python3

from database_postgres import get_db
import models

def add_schedule_toggle():
    """Add is_open column to schedule table"""
    db = next(get_db())
    
    try:
        from sqlalchemy import text
        # Try to add the column
        db.execute(text("ALTER TABLE schedule ADD COLUMN is_open INTEGER DEFAULT 1"))
        db.commit()
        print("✅ Added is_open column to schedule table")
    except Exception as e:
        if "already exists" in str(e) or "duplicate column" in str(e).lower():
            print("✅ is_open column already exists")
        else:
            print(f"❌ Error adding column: {e}")
            db.rollback()
    
    db.close()

if __name__ == "__main__":
    add_schedule_toggle()