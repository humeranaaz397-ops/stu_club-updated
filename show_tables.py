import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    for row in cursor.fetchall():
        print(row[0])
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
