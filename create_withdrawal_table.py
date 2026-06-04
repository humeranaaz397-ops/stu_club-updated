import mysql.connector
from app import DB_CONFIG

def create_table():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating withdrawal_requests table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS withdrawal_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                bank_name VARCHAR(100) NOT NULL,
                account_number VARCHAR(100) NOT NULL,
                ifsc_code VARCHAR(50) NOT NULL,
                status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()
        
        print("Database schema updated successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error executing migration: {e}")

if __name__ == '__main__':
    create_table()
