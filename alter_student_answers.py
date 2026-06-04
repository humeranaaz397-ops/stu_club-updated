import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE student_answers ADD COLUMN rejection_reason TEXT NULL")
    conn.commit()
    print("rejection_reason column added successfully!")
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
