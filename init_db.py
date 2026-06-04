import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sudha@8897'
}

def init_database():
    try:
        # Connect to MySQL Server (without specifying db first to drop/recreate)
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Resetting database student_club_db...")
        cursor.execute("DROP DATABASE IF EXISTS student_club_db")
        cursor.execute("CREATE DATABASE student_club_db")
        cursor.execute("USE student_club_db")
        
        # Read and parse db.sql
        with open('db.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        # Split statements by semicolon (simple parser)
        statements = sql_script.split(';')
        for statement in statements:
            stmt = statement.strip()
            if not stmt:
                continue
            # Skip USE or CREATE DATABASE statements since we handled them
            if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                continue
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"Error executing statement: {stmt[:50]}...")
                print(f"Details: {e}")
                raise e
                
        conn.commit()
        print("Database schema and seed data loaded successfully!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database initialization failed: {e}")

if __name__ == '__main__':
    init_database()
