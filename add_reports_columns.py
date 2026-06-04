import mysql.connector
from app import DB_CONFIG

def migrate():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if status column exists in contact_messages
        cursor.execute("SHOW COLUMNS FROM contact_messages LIKE 'status'")
        if not cursor.fetchone():
            print("Adding status column to contact_messages...")
            cursor.execute("ALTER TABLE contact_messages ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open'")
            conn.commit()
            
        # Check if priority column exists in contact_messages
        cursor.execute("SHOW COLUMNS FROM contact_messages LIKE 'priority'")
        if not cursor.fetchone():
            print("Adding priority column to contact_messages...")
            cursor.execute("ALTER TABLE contact_messages ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'medium'")
            conn.commit()
            
        print("Database schema for contact_messages updated successfully!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == '__main__':
    migrate()
