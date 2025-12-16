import sqlite3
import os

def fix_database():
    db_path = 'anomaly_detector.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} tidak ditemukan!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"Kolom yang ada: {columns}")
        
        # Add selected_stock if not exists
        if 'selected_stock' not in columns:
            print("Menambahkan kolom selected_stock...")
            cursor.execute("ALTER TABLE user ADD COLUMN selected_stock TEXT")
            print("✓ Kolom selected_stock ditambahkan")
        else:
            print("✓ Kolom selected_stock sudah ada")
        
        # Add analysis_period if not exists
        if 'analysis_period' not in columns:
            print("Menambahkan kolom analysis_period...")
            cursor.execute("ALTER TABLE user ADD COLUMN analysis_period TEXT")
            print("✓ Kolom analysis_period ditambahkan")
        else:
            print("✓ Kolom analysis_period sudah ada")
        
        conn.commit()
        print("\n✓ Database berhasil diupdate!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database()
