import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE quizzes ADD COLUMN teacher_id INT NULL")
    conn.commit()
    print("Schema updated successfully: teacher_id added.")
    
    # Optional: Update existing quizzes with teacher_id from courses
    cursor.execute("""
        UPDATE quizzes q
        JOIN courses c ON q.course_id = c.id
        SET q.teacher_id = c.created_by
        WHERE q.teacher_id IS NULL
    """)
    conn.commit()
    print("Existing quizzes updated with teacher_id.")
    
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
