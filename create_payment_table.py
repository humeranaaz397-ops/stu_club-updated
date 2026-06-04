import mysql.connector
from app import DB_CONFIG

def create_table_and_alter():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating course_payments table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                screenshot_path VARCHAR(255) NOT NULL,
                status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        
        # Alter videos table if needed
        cursor.execute("SHOW COLUMNS FROM videos LIKE 'course_id'")
        if not cursor.fetchone():
            print("Adding course_id to videos table...")
            cursor.execute("ALTER TABLE videos ADD COLUMN course_id INT NULL")
            cursor.execute("ALTER TABLE videos ADD FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE")
            conn.commit()
            
        # Alter materials table if needed
        cursor.execute("SHOW COLUMNS FROM materials LIKE 'course_id'")
        if not cursor.fetchone():
            print("Adding course_id to materials table...")
            cursor.execute("ALTER TABLE materials ADD COLUMN course_id INT NULL")
            cursor.execute("ALTER TABLE materials ADD FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE")
            conn.commit()
            
        print("Database schema updated successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error executing migration: {e}")

if __name__ == '__main__':
    create_table_and_alter()
