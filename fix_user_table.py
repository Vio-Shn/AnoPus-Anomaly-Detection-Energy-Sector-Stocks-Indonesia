import sqlite3
import os

# Find database file
db_paths = ['instance/anopus.db', 'anopus.db']
db_path = None

for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("ERROR: Database file not found!")
    print("Please check if anopus.db exists in your project folder")
    exit(1)

print(f"Found database at: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check current columns
    cursor.execute("PRAGMA table_info(user)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in user table: {columns}")
    
    # Add phone column if not exists
    if 'phone' not in columns:
        print("Adding phone column...")
        cursor.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(20)")
        print("✓ Phone column added successfully")
    else:
        print("✓ Phone column already exists")
    
    # Add profile_photo column if not exists
    if 'profile_photo' not in columns:
        print("Adding profile_photo column...")
        cursor.execute("ALTER TABLE user ADD COLUMN profile_photo VARCHAR(200)")
        print("✓ Profile_photo column added successfully")
    else:
        print("✓ Profile_photo column already exists")
    
    conn.commit()
    print("\n✓ Database migration completed successfully!")
    print("Please restart your Flask application now.")
    
except Exception as e:
    print(f"\n✗ Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
