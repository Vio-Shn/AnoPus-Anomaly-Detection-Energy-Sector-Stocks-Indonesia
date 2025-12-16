import sqlite3
import os

# Path to database
db_path = 'anomaly_detector.db'

if not os.path.exists(db_path):
    print(f"Database {db_path} tidak ditemukan!")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Memeriksa dan menambahkan kolom yang hilang...")

try:
    # Check if selected_stock column exists
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add selected_stock if not exists
    if 'selected_stock' not in columns:
        cursor.execute("ALTER TABLE user ADD COLUMN selected_stock VARCHAR(20) DEFAULT 'BBRI.JK'")
        print("✓ Kolom selected_stock ditambahkan")
    else:
        print("✓ Kolom selected_stock sudah ada")
    
    # Add analysis_period if not exists
    if 'analysis_period' not in columns:
        cursor.execute("ALTER TABLE user ADD COLUMN analysis_period VARCHAR(10) DEFAULT '1mo'")
        print("✓ Kolom analysis_period ditambahkan")
    else:
        print("✓ Kolom analysis_period sudah ada")
    
    conn.commit()
    print("\n✅ Database berhasil diupdate!")
    print("Silakan restart aplikasi Flask Anda.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
finally:
    conn.close()
