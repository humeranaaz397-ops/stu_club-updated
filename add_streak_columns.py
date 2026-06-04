import mysql.connector
import os

def alter_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="baki",
        database="student_club_db"
    )
    cursor = conn.cursor()
    
    queries = [
        "ALTER TABLE student_profiles ADD COLUMN current_streak INT DEFAULT 0;",
        "ALTER TABLE student_profiles ADD COLUMN longest_streak INT DEFAULT 0;",
        "ALTER TABLE student_profiles ADD COLUMN last_activity_date DATE NULL;",
        "ALTER TABLE student_profiles ADD COLUMN last_reward_streak INT DEFAULT 0;"
    ]
    
    for query in queries:
        try:
            cursor.execute(query)
            print(f"Executed: {query}")
        except mysql.connector.Error as err:
            if err.errno == 1060: # Duplicate column name
                print(f"Column already exists: {query}")
            else:
                print(f"Error executing {query}: {err}")
            
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    alter_db()
