"""
Database migration script to add new columns to existing database
"""
import sqlite3
import os

DB_PATH = 'instance/quiz.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database doesn't exist yet. No migration needed.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(participant)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add current_question column if it doesn't exist
        if 'current_question' not in columns:
            print("Adding current_question column to participant table...")
            cursor.execute("ALTER TABLE participant ADD COLUMN current_question INTEGER DEFAULT 0")
            print("✓ Added current_question column")
        else:
            print("✓ current_question column already exists")
        
        # Add finished column if it doesn't exist
        if 'finished' not in columns:
            print("Adding finished column to participant table...")
            cursor.execute("ALTER TABLE participant ADD COLUMN finished BOOLEAN DEFAULT 0")
            print("✓ Added finished column")
        else:
            print("✓ finished column already exists")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    migrate()
