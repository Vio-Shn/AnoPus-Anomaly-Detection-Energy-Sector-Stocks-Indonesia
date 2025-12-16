import sqlite3
import os

# Find database file
db_paths = [
    'anopus.db',
    'instance/anopus.db',
    'database.db',
    'instance/database.db'
]

db_path = None
for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("ERROR: Database file not found!")
    print("Please check where your database file is located.")
    exit(1)

print(f"Found database at: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current columns
cursor.execute("PRAGMA table_info(user)")
columns = [column[1] for column in cursor.fetchall()]
print(f"Current columns in user table: {columns}")

# Add phone column if not exists
if 'phone' not in columns:
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(20)")
        print("✓ Added 'phone' column")
    except Exception as e:
        print(f"Error adding phone column: {e}")

# Add profile_photo column if not exists  
if 'profile_photo' not in columns:
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN profile_photo VARCHAR(255)")
        print("✓ Added 'profile_photo' column")
    except Exception as e:
        print(f"Error adding profile_photo column: {e}")

# Commit changes
conn.commit()

# Verify changes
cursor.execute("PRAGMA table_info(user)")
columns = [column[1] for column in cursor.fetchall()]
print(f"\nUpdated columns in user table: {columns}")

conn.close()
print("\n✓ Database update completed successfully!")
print("Please restart your Flask application.")
