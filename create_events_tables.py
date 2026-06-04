import mysql.connector
from datetime import datetime, timedelta
from app import DB_CONFIG

def setup_database():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    print("Creating tables...")
    
    # 1. Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        event_type ENUM('Hackathon', 'Workshop', 'Seminar', 'Live Class') NOT NULL,
        event_date DATETIME NOT NULL,
        location VARCHAR(255) NOT NULL,
        prize VARCHAR(255) NULL,
        apply_link VARCHAR(255) NULL,
        image_url VARCHAR(255) NULL,
        price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
        created_by INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 2. Event Registrations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_registrations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        student_id INT NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL,
        college VARCHAR(255) NOT NULL,
        year_of_study VARCHAR(50) NOT NULL,
        department VARCHAR(100) NOT NULL,
        team_name VARCHAR(100) NULL,
        why_join TEXT NOT NULL,
        payment_method VARCHAR(50) NOT NULL,
        payment_status VARCHAR(50) NOT NULL DEFAULT 'free',
        paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY (event_id, student_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 3. Event Likes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_likes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        student_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY (event_id, student_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 4. Event Saves Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_saves (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        student_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY (event_id, student_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 5. Event Comments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        event_id INT NOT NULL,
        student_id INT NOT NULL,
        comment_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    # 6. Reported Content Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reported_content (
        id INT AUTO_INCREMENT PRIMARY KEY,
        content_type ENUM('Course', 'Video', 'Material') NOT NULL,
        content_id INT NOT NULL,
        reporter_id INT NOT NULL,
        reason VARCHAR(255) NOT NULL,
        priority ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'low',
        status ENUM('pending', 'approved', 'removed', 'dismissed') NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    
    conn.commit()
    print("Tables created successfully. Seeding initial data...")
    
    # Get seed users
    cursor.execute("SELECT id, role, name FROM users")
    users = cursor.fetchall()
    
    admin_id = None
    teacher_id = None
    student_id = None
    
    for u in users:
        if u['role'] == 'admin':
            admin_id = u['id']
        elif u['role'] == 'teacher' and not teacher_id:
            teacher_id = u['id']
        elif u['role'] == 'student' and not student_id:
            student_id = u['id']
            
    if not admin_id or not teacher_id or not student_id:
        print("Missing base seeded users! Make sure index/db.sql was run.")
        cursor.close()
        conn.close()
        return

    # Clear old seeded events to avoid duplicate entries
    cursor.execute("DELETE FROM events")
    cursor.execute("DELETE FROM reported_content")
    conn.commit()
    
    # Seed Events
    # Event 1 (Approved, Free)
    cursor.execute("""
    INSERT INTO events (title, description, event_type, event_date, location, prize, apply_link, image_url, price, status, created_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        "AI Innovation Hackathon 2026",
        "Build smart AI solutions with your team and present your idea to mentors and judges.",
        "Hackathon",
        datetime.now() + timedelta(days=5),
        "Hyderabad",
        "Prize 1,00,000",
        "/student/event/apply/1", # placeholder
        "https://images.unsplash.com/photo-1552664730-d307ca884978?q=80&w=900&auto=format&fit=crop",
        0.00,
        "approved",
        admin_id
    ))
    event1_id = cursor.lastrowid
    
    # Event 2 (Approved, Free)
    cursor.execute("""
    INSERT INTO events (title, description, event_type, event_date, location, prize, apply_link, image_url, price, status, created_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        "Full Stack Web Development Bootcamp",
        "Learn HTML, CSS, JavaScript, Bootstrap, React, and build real-world projects.",
        "Workshop",
        datetime.now() + timedelta(days=14),
        "Online",
        "Free Certificate",
        "/student/event/apply/2", # placeholder
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=900&auto=format&fit=crop",
        0.00,
        "approved",
        admin_id
    ))
    event2_id = cursor.lastrowid

    # Event 3 (Approved, Paid)
    cursor.execute("""
    INSERT INTO events (title, description, event_type, event_date, location, prize, apply_link, image_url, price, status, created_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        "Advanced Cybersecurity Summit",
        "Deep dive into penetration testing, network monitoring, and security compliance.",
        "Seminar",
        datetime.now() + timedelta(days=20),
        "Bangalore",
        "Industry Badge",
        "/student/event/apply/3",
        "https://images.unsplash.com/photo-1563986768609-322da13575f3?q=80&w=900&auto=format&fit=crop",
        299.00,
        "approved",
        teacher_id
    ))
    event3_id = cursor.lastrowid
    
    # Event 4 (Pending, Teacher Created)
    cursor.execute("""
    INSERT INTO events (title, description, event_type, event_date, location, prize, apply_link, image_url, price, status, created_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        "UX/UI Design Workshop",
        "Master Figma and learn user-centric design paradigms from industry experts.",
        "Workshop",
        datetime.now() + timedelta(days=10),
        "Online",
        "Design Certificate",
        "/student/event/apply/4",
        "https://images.unsplash.com/photo-1581291518633-83b4ebd1d83e?q=80&w=900&auto=format&fit=crop",
        0.00,
        "pending",
        teacher_id
    ))
    
    # Update apply_links now that we have IDs
    cursor.execute("UPDATE events SET apply_link = CONCAT('/student/event/apply/', id)")
    
    # Seed registrations
    cursor.execute("""
    INSERT INTO event_registrations (event_id, student_id, first_name, last_name, email, phone, college, year_of_study, department, why_join, payment_method, payment_status, paid_amount)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        event1_id,
        student_id,
        "Sudharshan",
        "Jaggula",
        "sudharshanjaggula605@gmail.com",
        "9999999999",
        "VNR VJIET",
        "3rd Year",
        "Computer Science",
        "I want to build smart AI applications and participate with other tech enthusiasts.",
        "UPI",
        "free",
        0.00
    ))
    
    cursor.execute("""
    INSERT INTO event_registrations (event_id, student_id, first_name, last_name, email, phone, college, year_of_study, department, why_join, payment_method, payment_status, paid_amount)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        event3_id,
        student_id,
        "Sudharshan",
        "Jaggula",
        "sudharshanjaggula605@gmail.com",
        "9999999999",
        "VNR VJIET",
        "3rd Year",
        "Computer Science",
        "Cybersecurity is my primary interest domain.",
        "Credit / Debit Card",
        "paid",
        299.00
    ))
    
    # Seed Likes & Saves
    cursor.execute("INSERT INTO event_likes (event_id, student_id) VALUES (%s, %s)", (event1_id, student_id))
    cursor.execute("INSERT INTO event_likes (event_id, student_id) VALUES (%s, %s)", (event2_id, student_id))
    cursor.execute("INSERT INTO event_saves (event_id, student_id) VALUES (%s, %s)", (event2_id, student_id))
    cursor.execute("INSERT INTO event_saves (event_id, student_id) VALUES (%s, %s)", (event3_id, student_id))
    
    # Seed Comments
    cursor.execute("INSERT INTO event_comments (event_id, student_id, comment_text) VALUES (%s, %s, %s)", (
        event1_id,
        student_id,
        "This hackathon looks amazing!"
    ))
    cursor.execute("INSERT INTO event_comments (event_id, student_id, comment_text) VALUES (%s, %s, %s)", (
        event2_id,
        student_id,
        "Excited to participate in full stack bootcamp!"
    ))
    
    # Seed Content Moderation (Reported Content)
    # Check if courses, videos, and materials exist to link them
    cursor.execute("SELECT id FROM courses LIMIT 1")
    c_row = cursor.fetchone()
    if c_row:
        cursor.execute("""
        INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status)
        VALUES ('Course', %s, %s, 'Flagged for plagiarism and inappropriate cover image.', 'high', 'pending')
        """, (c_row['id'], student_id))
        
    cursor.execute("SELECT id FROM videos LIMIT 1")
    v_row = cursor.fetchone()
    if v_row:
        cursor.execute("""
        INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status)
        VALUES ('Video', %s, %s, 'Inappropriate background noise and copyright music.', 'medium', 'pending')
        """, (v_row['id'], student_id))
        
    cursor.execute("SELECT id FROM materials LIMIT 1")
    m_row = cursor.fetchone()
    if m_row:
        cursor.execute("""
        INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status)
        VALUES ('Material', %s, %s, 'Outdated syllabus contents.', 'low', 'pending')
        """, (m_row['id'], student_id))
        
    conn.commit()
    cursor.close()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    setup_database()
