import sqlite3
import os

# Try to find the database in multiple locations
possible_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'anopus.db'),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'anopus.db'),
]

db_path = None
for path in possible_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("❌ Database file not found in expected locations:")
    for path in possible_paths:
        print(f"   - {path}")
    exit(1)

print(f"✓ Found database at: {db_path}")
print("Updating database schema...")

try:
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    print(f"\nCurrent columns in 'user' table: {', '.join(columns)}")
    
    # Add phone column if it doesn't exist
    if 'phone' not in columns:
        print("\nAdding 'phone' column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(20)")
        print("✓ Added 'phone' column")
    else:
        print("\n✓ 'phone' column already exists")
    
    # Add profile_photo column if it doesn't exist
    if 'profile_photo' not in columns:
        print("Adding 'profile_photo' column to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN profile_photo VARCHAR(255)")
        print("✓ Added 'profile_photo' column")
    else:
        print("✓ 'profile_photo' column already exists")
    
    # Commit changes
    conn.commit()
    
    # Verify the changes
    cursor.execute("PRAGMA table_info(user)")
    new_columns = [column[1] for column in cursor.fetchall()]
    print(f"\nUpdated columns in 'user' table: {', '.join(new_columns)}")
    
    print("\n✅ Database migration completed successfully!")
    print("\nPlease restart your Flask application to apply the changes.")
    
except sqlite3.Error as e:
    print(f"\n❌ Error during migration: {e}")
    if conn:
        conn.rollback()
    
finally:
    if conn:
        conn.close()
        print("\nDatabase connection closed.")
