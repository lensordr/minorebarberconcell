#!/usr/bin/env python3
"""
Database migration to add email and cancel_token columns
"""

import sqlite3
import os

def migrate_database():
    db_path = "barbershop.db"
    
    if not os.path.exists(db_path):
        print("Database not found. Run setup.py first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if email column exists
        cursor.execute("PRAGMA table_info(appointments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email' not in columns:
            print("Adding email column...")
            cursor.execute("ALTER TABLE appointments ADD COLUMN email TEXT DEFAULT ''")
        
        if 'cancel_token' not in columns:
            print("Adding cancel_token column...")
            cursor.execute("ALTER TABLE appointments ADD COLUMN cancel_token TEXT DEFAULT ''")
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()