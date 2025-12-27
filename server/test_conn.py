import sqlite3
try:
    conn = sqlite3.connect("connectivity_test.db")
    conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
    conn.execute("INSERT INTO test (id) VALUES (1)")
    conn.commit()
    conn.close()
    with open("connectivity_success.txt", "w") as f:
        f.write("SQLITE_SUCCESS")
except Exception as e:
    with open("connectivity_error.txt", "w") as f:
        f.write(str(e))
