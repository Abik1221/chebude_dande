import sqlite3
import os

db_path = "estatevision_ai.db"
if os.path.exists(db_path):
    print(f"File exists: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables: {tables}")
        
        cursor.execute("SELECT id, username, email, hashed_password FROM users;")
        users = cursor.fetchall()
        for user in users:
            print(f"User: {user}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"File not found: {db_path}")
