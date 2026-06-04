import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sudharshan@6302',
    'database': 'student_club_db'
}

def alter_database():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Migrating connection_requests to connections...")
        
        # Check if connection_requests exists
        cursor.execute("SHOW TABLES LIKE 'connection_requests'")
        if cursor.fetchone():
            print("Table connection_requests found. Renaming and altering columns...")
            
            # Since foreign keys exist, renaming columns might fail if we don't drop FK first or use CHANGE
            # But the easiest way in MySQL is to rename the table, then change columns
            cursor.execute("RENAME TABLE connection_requests TO connections")
            
            # Drop foreign keys first. We need to find their names.
            cursor.execute("""
                SELECT CONSTRAINT_NAME 
                FROM information_schema.KEY_COLUMN_USAGE 
                WHERE TABLE_NAME = 'connections' 
                AND TABLE_SCHEMA = 'student_club_db' 
                AND REFERENCED_TABLE_NAME IS NOT NULL
            """)
            fks = cursor.fetchall()
            for fk in fks:
                cursor.execute(f"ALTER TABLE connections DROP FOREIGN KEY {fk[0]}")
            
            # Now change columns
            cursor.execute("ALTER TABLE connections CHANGE student_id sender_id INT NOT NULL")
            cursor.execute("ALTER TABLE connections CHANGE teacher_id receiver_id INT NOT NULL")
            
            # Re-add foreign keys
            cursor.execute("ALTER TABLE connections ADD FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE")
            cursor.execute("ALTER TABLE connections ADD FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE")
            
            print("Migration completed successfully!")
        else:
            print("No connection_requests table found. Assuming migration already applied or fresh DB.")
            
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == '__main__':
    alter_database()
