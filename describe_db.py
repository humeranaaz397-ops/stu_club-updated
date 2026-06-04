import mysql.connector
from app import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

for table in ['videos', 'materials']:
    cursor.execute(f"DESCRIBE {table}")
    print(f"\nTable: {table}")
    for row in cursor.fetchall():
        print(row)
        
cursor.close()
conn.close()
