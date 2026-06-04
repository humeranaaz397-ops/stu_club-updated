import mysql.connector
import sys

print("Attempting to connect...")
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Sudha@8897',
        connect_timeout=3
    )
    print("Connection SUCCESSFUL!")
    conn.close()
except Exception as e:
    print(f"Connection FAILED: {e}")
    sys.exit(1)
print("Done.")
