import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE quizzes MODIFY course_id INT NULL")
    conn.commit()
    print("Schema updated successfully: course_id is now NULLable.")
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
