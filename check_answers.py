import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    cursor.execute("DESCRIBE answers")
    for row in cursor.fetchall():
        print(row)
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
