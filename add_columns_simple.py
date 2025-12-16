import sqlite3
import os

# Find database file
db_paths = ['instance/anopus.db', 'anopus.db', 'instance/app.db', 'app.db']
db_path = None

for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("Error: Database file not found!")
    print("Please create the database first by running the Flask app.")
    exit(1)

print(f"Found database at: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(user)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Current columns: {columns}")

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

# Commit and close
conn.commit()

# Verify changes
cursor.execute("PRAGMA table_info(user)")
new_columns = [col[1] for col in cursor.fetchall()]
print(f"\nUpdated columns: {new_columns}")

conn.close()
print("\n✓ Database update completed! Please restart your Flask app.")
