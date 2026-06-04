import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_id INT NOT NULL,
            student_id INT NOT NULL,
            answer_text TEXT NOT NULL,
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    print("student_answers table created successfully!")
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
