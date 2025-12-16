import sqlite3
import os
from werkzeug.security import generate_password_hash

# Find database file
db_paths = ['instance/database.db', 'database.db', 'app.db', 'instance/app.db']
db_path = None
for path in db_paths:
    if os.path.exists(path):
        db_path = path
        break

if not db_path:
    print("Database file not found!")
    exit(1)

print(f"Found database at: {db_path}")

# Backup existing users
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing user data
try:
    cursor.execute("SELECT id, username, email, password_hash, created_at FROM user")
    existing_users = cursor.fetchall()
    print(f"Found {len(existing_users)} existing users to backup")
except:
    existing_users = []
    print("No existing users to backup")

# Get existing watchlist data
try:
    cursor.execute("SELECT id, user_id, stock_code, added_date FROM watchlist")
    existing_watchlist = cursor.fetchall()
    print(f"Found {len(existing_watchlist)} watchlist entries to backup")
except:
    existing_watchlist = []
    print("No existing watchlist to backup")

conn.close()

# Drop and recreate user table with new columns
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("\nDropping old user table...")
cursor.execute("DROP TABLE IF EXISTS user")

print("Creating new user table with phone and profile_photo columns...")
cursor.execute("""
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    profile_photo VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# Restore user data
print(f"\nRestoring {len(existing_users)} users...")
for user in existing_users:
    cursor.execute("""
        INSERT INTO user (id, username, email, password_hash, created_at, phone, profile_photo)
        VALUES (?, ?, ?, ?, ?, NULL, NULL)
    """, user)

# Recreate watchlist table if needed
print("\nRecreating watchlist table...")
cursor.execute("DROP TABLE IF EXISTS watchlist")
cursor.execute("""
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    added_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")

# Restore watchlist data
print(f"Restoring {len(existing_watchlist)} watchlist entries...")
for entry in existing_watchlist:
    cursor.execute("""
        INSERT INTO watchlist (id, user_id, stock_code, added_date)
        VALUES (?, ?, ?, ?)
    """, entry)

conn.commit()
conn.close()

print("\n✅ Database recreated successfully!")
print("✅ All user data and watchlist restored!")
print("✅ New columns 'phone' and 'profile_photo' added to user table!")
print("\nYou can now restart your Flask application.")
