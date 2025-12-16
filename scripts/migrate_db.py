#!/usr/bin/env python3
"""
Database migration script untuk menambahkan missing columns ke user table
"""
import sqlite3
import sys

def migrate_database():
    """Tambahkan kolom selected_stock dan analysis_period ke user table"""
    try:
        # Koneksi ke database
        conn = sqlite3.connect('instance/anopus.db')
        cursor = conn.cursor()
        
        # Check jika kolom sudah ada
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"[Migration] Current columns in user table: {columns}")
        
        # Tambahkan selected_stock kolom jika belum ada
        if 'selected_stock' not in columns:
            print("[Migration] Adding selected_stock column...")
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN selected_stock VARCHAR(20) DEFAULT 'ADRO.JK'
            """)
            print("[Migration] ✓ selected_stock column added")
        else:
            print("[Migration] selected_stock column already exists")
        
        # Tambahkan analysis_period kolom jika belum ada
        if 'analysis_period' not in columns:
            print("[Migration] Adding analysis_period column...")
            cursor.execute("""
                ALTER TABLE user 
                ADD COLUMN analysis_period VARCHAR(10) DEFAULT '1mo'
            """)
            print("[Migration] ✓ analysis_period column added")
        else:
            print("[Migration] analysis_period column already exists")
        
        # Commit changes
        conn.commit()
        print("[Migration] ✓ Database migration completed successfully!")
        
        # Verify columns
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"[Migration] Updated columns in user table: {columns}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[Migration] ✗ Error during migration: {e}")
        return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
