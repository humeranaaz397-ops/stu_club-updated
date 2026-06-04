import os
import time
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super_secret_student_club_key_12345'

# # Database configuration
# DB_CONFIG = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'humera0825',
#     'database': 'student_club_db'
# }

DB_CONFIG = {
    'host': 'acela.proxy.rlwy.net',
    'user': 'root',
    'password': 'eRMmuqWlpZmdLTjsBCGeyXkFOCvrrgEo',
    'database': 'railway',
    'port': 20065
}

# Upload directories
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper function to get database connection
def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# Helper to check if a user is logged in
def is_logged_in():
    return 'user_id' in session

# Decorator-like checking for role authorization
def check_role(allowed_roles):
    if not is_logged_in():
        return False
    return session.get('role') in allowed_roles

def add_notification_to_all_students(message):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE role = 'student'")
        students = cursor.fetchall()
        for student in students:
            cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (student['id'], message))
        conn.commit()
    except Exception as e:
        print("Error adding notification to all students:", e)
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

def update_student_streak(student_id):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT current_streak, longest_streak, last_activity_date, last_reward_streak FROM student_profiles WHERE user_id = %s", (student_id,))
        profile = cursor.fetchone()
        
        if not profile:
            return

        from datetime import datetime
        today = datetime.now().date()
        last_activity = profile['last_activity_date']
        current_streak = profile['current_streak']
        longest_streak = profile['longest_streak']
        last_reward_streak = profile['last_reward_streak']

        if last_activity == today:
            return # Already updated today

        if last_activity:
            delta = (today - last_activity).days
            if delta == 1:
                current_streak += 1
            else:
                current_streak = 1
        else:
            current_streak = 1

        if current_streak > longest_streak:
            longest_streak = current_streak

        cursor.execute("""
            UPDATE student_profiles 
            SET current_streak = %s, longest_streak = %s, last_activity_date = %s
            WHERE user_id = %s
        """, (current_streak, longest_streak, today, student_id))

        if current_streak >= 7 and current_streak - last_reward_streak >= 7:
            cursor.execute("SELECT id FROM courses WHERE price_type = 'paid' AND id NOT IN (SELECT course_id FROM enrollments WHERE student_id = %s)", (student_id,))
            paid_courses = cursor.fetchall()
            if paid_courses:
                import random
                selected_course = random.choice(paid_courses)['id']
                cursor.execute("INSERT INTO enrollments (student_id, course_id, progress) VALUES (%s, %s, 0)", (student_id, selected_course))
                cursor.execute("UPDATE student_profiles SET last_reward_streak = %s WHERE user_id = %s", (current_streak, student_id))
                msg = f"🎉 Congratulations on your {current_streak}-day learning streak! You have unlocked a premium course for free!"
                cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (student_id, msg))
                
        conn.commit()
    except Exception as e:
        print("Error updating student streak:", e)
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@app.before_request
def check_student_streak():
    from flask import request, session
    if request.endpoint and request.endpoint.startswith('student_'):
        if 'user_id' in session and session.get('role') == 'student':
            update_student_streak(session['user_id'])

# Create default upload directories inside static
os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'resumes'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'materials'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'videos'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'courses'), exist_ok=True)

# 0. Check if 'users' table exists. If not, initialize database from db.sql!
try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("SHOW TABLES LIKE 'users'")
    if not _cursor.fetchone():
        db_sql_path = os.path.join(app.root_path, 'db.sql')
        if os.path.exists(db_sql_path):
            with open(db_sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            statements = sql_script.split(';')
            for statement in statements:
                stmt = statement.strip()
                if not stmt:
                    continue
                if stmt.upper().startswith("CREATE DATABASE") or stmt.upper().startswith("USE "):
                    continue
                try:
                    _cursor.execute(stmt)
                except Exception:
                    pass
            _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("ALTER TABLE quiz_questions ADD COLUMN explanation TEXT NULL")
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("ALTER TABLE watched_videos ADD COLUMN progress_percentage INT DEFAULT 0")
    _cursor.execute("ALTER TABLE watched_videos ADD COLUMN last_position INT DEFAULT 0")
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("ALTER TABLE student_profiles ADD COLUMN id_card_url VARCHAR(255) NULL")
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("ALTER TABLE live_classes ADD COLUMN course_id INT NULL")
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id INT NOT NULL,
            student_id INT NOT NULL,
            rating TINYINT NOT NULL DEFAULT 5,
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_review (teacher_id, student_id),
            FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("ALTER TABLE event_registrations ADD COLUMN id_card_url VARCHAR(255) NULL")
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()
    _cursor.execute("ALTER TABLE student_profiles ADD COLUMN competitive_exam VARCHAR(100) NULL")
    _conn.commit()
    _cursor.close()
    _conn.close()
except Exception:
    pass

try:
    _conn = get_db()
    _cursor = _conn.cursor()

    # 1. Alter courses (status column)
    try:
        _cursor.execute("ALTER TABLE courses ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'approved'")
        _conn.commit()
    except Exception:
        pass
        
    # 2. course_payments table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 3. Alter videos (add course_id)
    try:
        _cursor.execute("ALTER TABLE videos ADD COLUMN course_id INT NULL")
        _cursor.execute("ALTER TABLE videos ADD FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE")
        _conn.commit()
    except Exception:
        pass

    # 4. Alter materials (add course_id)
    try:
        _cursor.execute("ALTER TABLE materials ADD COLUMN course_id INT NULL")
        _cursor.execute("ALTER TABLE materials ADD FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE")
        _conn.commit()
    except Exception:
        pass

    # 5. withdrawal_requests table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 6. student_answers table
    try:
        _cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_answers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NOT NULL,
                student_id INT NOT NULL,
                answer_text TEXT NOT NULL,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        _conn.commit()
    except Exception:
        pass

    # 7. events table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 8. event_registrations table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 9. event_likes table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 10. event_saves table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 11. event_comments table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 12. reported_content table
    try:
        _cursor.execute("""
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
        _conn.commit()
    except Exception:
        pass

    # 13. Alter contact_messages (add status and priority)
    try:
        _cursor.execute("ALTER TABLE contact_messages ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open'")
        _conn.commit()
    except Exception:
        pass
    try:
        _cursor.execute("ALTER TABLE contact_messages ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'medium'")
        _conn.commit()
    except Exception:
        pass

    # 14. Alter student_profiles (add streak columns)
    try:
        _cursor.execute("ALTER TABLE student_profiles ADD COLUMN current_streak INT DEFAULT 0")
        _conn.commit()
    except Exception:
        pass
    try:
        _cursor.execute("ALTER TABLE student_profiles ADD COLUMN longest_streak INT DEFAULT 0")
        _conn.commit()
    except Exception:
        pass
    try:
        _cursor.execute("ALTER TABLE student_profiles ADD COLUMN last_activity_date DATE NULL")
        _conn.commit()
    except Exception:
        pass
    try:
        _cursor.execute("ALTER TABLE student_profiles ADD COLUMN last_reward_streak INT DEFAULT 0")
        _conn.commit()
    except Exception:
        pass

    # 15. Alter quizzes (add teacher_id and make course_id nullable)
    try:
        _cursor.execute("ALTER TABLE quizzes ADD COLUMN teacher_id INT NULL")
        _conn.commit()
    except Exception:
        pass
    try:
        _cursor.execute("ALTER TABLE quizzes MODIFY course_id INT NULL")
        _conn.commit()
    except Exception:
        pass

    # 16. Alter student_answers (add rejection_reason)
    try:
        _cursor.execute("ALTER TABLE student_answers ADD COLUMN rejection_reason TEXT NULL")
        _conn.commit()
    except Exception:
        pass

    # 17. Sync quizzes teacher_id
    try:
        _cursor.execute("""
            UPDATE quizzes q
            JOIN courses c ON q.course_id = c.id
            SET q.teacher_id = c.created_by
            WHERE q.teacher_id IS NULL
        """)
        _conn.commit()
    except Exception:
        pass

    # 18. Alter event_registrations (add payment_screenshot)
    try:
        _cursor.execute("ALTER TABLE event_registrations ADD COLUMN payment_screenshot VARCHAR(255) NULL")
        _conn.commit()
    except Exception:
        pass

    # 19. Create teacher_earnings table
    try:
        _cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_earnings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                teacher_id INT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                reason VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        _conn.commit()
    except Exception:
        pass

    # 20. Alter questions (add subject)
    try:
        _cursor.execute("ALTER TABLE questions ADD COLUMN subject VARCHAR(255) NULL")
        _conn.commit()
    except Exception:
        pass

    # 21. Alter questions (make teacher_id NULLable)
    try:
        _cursor.execute("ALTER TABLE questions MODIFY COLUMN teacher_id INT NULL")
        _conn.commit()
    except Exception:
        pass

    # 22. Alter chats (add deleted_by_sender and deleted_by_receiver)
    try:
        _cursor.execute("ALTER TABLE chats ADD COLUMN deleted_by_sender BOOLEAN NOT NULL DEFAULT FALSE")
        _conn.commit()
    except Exception:
        pass
    try:
        _cursor.execute("ALTER TABLE chats ADD COLUMN deleted_by_receiver BOOLEAN NOT NULL DEFAULT FALSE")
        _conn.commit()
    except Exception:
        pass

    # 23. Alter live_classes (add status)
    try:
        _cursor.execute("ALTER TABLE live_classes ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'upcoming'")
        _conn.commit()
    except Exception:
        pass

    _cursor.close()
    _conn.close()
except Exception:
    pass



@app.context_processor
def inject_notification_counts():
    counts = {'pending_requests': 0, 'unread_messages': 0, 'total_alerts': 0}
    if is_logged_in():
        user_id = session.get('user_id')
        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            
            # Pending connection requests
            cursor.execute("SELECT COUNT(*) as count FROM connections WHERE receiver_id = %s AND status = 'pending'", (user_id,))
            counts['pending_requests'] = cursor.fetchone()['count']
            
            # Unread chat messages
            cursor.execute("SELECT COUNT(*) as count FROM chats WHERE receiver_id = %s AND is_read = FALSE AND deleted_by_receiver = FALSE", (user_id,))
            counts['unread_messages'] = cursor.fetchone()['count']
            
            counts['total_alerts'] = counts['pending_requests'] + counts['unread_messages']
        except Exception as e:
            print("Error in context processor:", e)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    return counts

@app.context_processor
def inject_current_user():
    class CurrentUser:
        def __init__(self, name, email, role):
            self.name = name
            self.email = email
            self.role = role
    if is_logged_in() and 'name' in session:
        return {'current_user': CurrentUser(session.get('name'), session.get('email'), session.get('role'))}
    return {'current_user': None}

# ----------------- PUBLIC ROUTES -----------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/explore')
def explore():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.*, u.name as teacher_name 
        FROM courses c 
        JOIN users u ON c.created_by = u.id
    """)
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('explore.html', courses=courses)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        conn = get_db()
        cursor = conn.cursor()
        # Store message
        cursor.execute(
            "INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)",
            (name, email, message)
        )
        conn.commit()
        
        # Trigger Admin Notification
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        for admin in admins:
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (admin[0], f"New contact message received from {name} ({email}).")
            )
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        # Redirect if already logged in
        if session['role'] == 'student':
            return redirect(url_for('student_dashboard'))
        elif session['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        elif session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            if user['role'] == 'teacher' and user['status'] == 'pending':
                flash("Your teacher account is pending admin approval.", "warning")
                return redirect(url_for('login'))
            elif user['role'] == 'teacher' and user['status'] == 'rejected':
                flash("Your registration was rejected by the administrator.", "danger")
                return redirect(url_for('login'))
                
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            
            if user['role'] == 'student':
                return redirect(url_for('student_dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    role = request.form.get('role2')
    name = request.form.get('name')
    age = request.form.get('age')
    gender = request.form.get('gender')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Check duplicate email
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        flash("Email is already registered!", "warning")
        return redirect(url_for('login'))
        
    # Default status: pending for teacher, approved for student/admin
    status = 'pending' if role == 'teacher' else 'approved'
    
    # Insert user
    cursor.execute(
        "INSERT INTO users (name, email, phone, password, age, gender, role, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (name, email, phone, password, age, gender, role, status)
    )
    user_id = cursor.lastrowid
    
    if role == 'student':
        class_level = request.form.get('class_level')
        stream = request.form.get('stream')
        competitive_exam = request.form.get('competitive_exam')
        
        id_card_url = None
        id_card = request.files.get('id_card')
        if id_card and id_card.filename:
            filename = secure_filename(id_card.filename)
            id_card_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            id_card.save(id_card_path)
            id_card_url = filename
            
        cursor.execute(
            "INSERT INTO student_profiles (user_id, class_level, stream, id_card_url, competitive_exam) VALUES (%s, %s, %s, %s, %s)",
            (user_id, class_level, stream, id_card_url, competitive_exam)
        )
    elif role == 'teacher':
        subject = request.form.get('subject')
        teacher_id_code = request.form.get('teacher_id')
        experience = request.form.get('experience')
        
        # File upload
        resume_file = request.files.get('resume')
        resume_url = ''
        if resume_file and resume_file.filename != '':
            filename = f"resume_{user_id}_{int(time.time())}_{resume_file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', filename)
            resume_file.save(save_path)
            resume_url = f"/static/uploads/resumes/{filename}"
            
        cursor.execute(
            "INSERT INTO teacher_profiles (user_id, subject, teacher_id_code, experience, resume_url) VALUES (%s, %s, %s, %s, %s)",
            (user_id, subject, teacher_id_code, experience, resume_url)
        )
        
        # Notify admins about a pending teacher approval request
        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        for admin in admins:
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (admin[0], f"New teacher registration pending approval: {name}.")
            )
            
    conn.commit()
    cursor.close()
    conn.close()
    
    if role == 'teacher':
        flash("Registration submitted! Pending Admin approval before login.", "info")
    else:
        flash("Registration successful! You can now log in.", "success")
        
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))


# ----------------- STUDENT DASHBOARD & PAGES -----------------

@app.route('/student/dashboard')
def student_dashboard():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Streak info
    cursor.execute("SELECT current_streak, competitive_exam FROM student_profiles WHERE user_id = %s", (student_id,))
    profile = cursor.fetchone()
    student_streak = profile['current_streak'] if profile else 0
    competitive_exam = profile.get('competitive_exam') if profile else None
    
    # 1. Enrolled courses count
    cursor.execute("SELECT COUNT(*) as count FROM enrollments WHERE student_id = %s", (student_id,))
    enrolled_count = cursor.fetchone()['count']
    
    # 2. Completed courses count
    cursor.execute("SELECT COUNT(*) as count FROM enrollments WHERE student_id = %s AND completed = TRUE", (student_id,))
    completed_count = cursor.fetchone()['count']
    
    # 3. Watched videos count
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM watched_videos wv
        JOIN videos v ON wv.video_id = v.id
        WHERE wv.student_id = %s AND v.course_id IS NULL
    """, (student_id,))
    watched_videos_count = cursor.fetchone()['count']
    
    # 4. Certificates earned
    cursor.execute("SELECT COUNT(*) as count FROM certificates WHERE student_id = %s", (student_id,))
    certificates_count = cursor.fetchone()['count']
    
    # 5. Average quiz score
    cursor.execute("SELECT AVG(score) as avg_score FROM quiz_results WHERE student_id = %s", (student_id,))
    avg_score_row = cursor.fetchone()
    avg_score = round(float(avg_score_row['avg_score']), 2) if avg_score_row['avg_score'] is not None else 0.0
    
    # 6. Connected teachers count
    cursor.execute("SELECT COUNT(*) as count FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (student_id, student_id))
    connections_count = cursor.fetchone()['count']
    
    # Upcoming live classes from connected teachers
    cursor.execute("""
        SELECT lc.*, u.name as teacher_name 
        FROM live_classes lc 
        JOIN users u ON lc.teacher_id = u.id 
        WHERE lc.teacher_id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        ) AND lc.class_date >= CURDATE()
        ORDER BY lc.class_date ASC, lc.class_time ASC
    """, (student_id, student_id))
    upcoming_classes = cursor.fetchall()
    
    # Enrolled courses list with detailed progress
    cursor.execute("""
        SELECT c.id, c.title, c.cover_image_url, c.category, c.price_type,
               e.progress, e.completed, u.name as teacher_name,
               (SELECT COUNT(*) FROM videos WHERE course_id = c.id) as total_videos,
               (SELECT COUNT(*) FROM watched_videos wv 
                JOIN videos v ON wv.video_id = v.id 
                WHERE wv.student_id = %s AND v.course_id = c.id) as watched_videos,
               (SELECT certificate_code FROM certificates 
                WHERE student_id = %s AND course_id = c.id LIMIT 1) as cert_code
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN users u ON c.created_by = u.id
        WHERE e.student_id = %s
        ORDER BY e.progress DESC
    """, (student_id, student_id, student_id))
    enrolled_courses = cursor.fetchall()

    import json
    
    # 1. Enrolled courses list for JavaScript table view
    cursor.execute("""
        SELECT c.id as course_id, c.title, DATE_FORMAT(e.enrolled_at, '%Y-%m-%d') as enrolled_date, e.progress, e.completed
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE e.student_id = %s
        ORDER BY e.enrolled_at DESC
    """, (student_id,))
    enrolled_courses_raw = cursor.fetchall()
    
    enrolled_courses_list = []
    for ec in enrolled_courses_raw:
        status_span = "<span class='status done'>Completed</span>" if ec['completed'] else "<span class='status pending'>In Progress</span>"
        course_link = f"<a href='/course/{ec['course_id']}' style='color:#2c2a99; font-weight:700; text-decoration:none;'>{ec['title']} 📖</a>"
        enrolled_courses_list.append([
            course_link,
            str(ec['enrolled_date'] or ''),
            f"{ec['progress']}%",
            status_span
        ])

    # 2. Watched videos list
    cursor.execute("""
        SELECT DATE_FORMAT(wv.watched_at, '%Y-%m-%d') as watched_date, v.title as video_title, c.title as course_title, v.video_url, wv.progress_percentage
        FROM watched_videos wv
        JOIN videos v ON wv.video_id = v.id
        LEFT JOIN courses c ON v.course_id = c.id
        WHERE wv.student_id = %s AND v.course_id IS NULL
        ORDER BY wv.watched_at DESC
    """, (student_id,))
    watched_videos_raw = cursor.fetchall()
    
    watched_videos_list = []
    for wv in watched_videos_raw:
        video_link = f"<a href='{wv['video_url']}' target='_blank' style='color:#2c2a99; font-weight:700; text-decoration:none;'>{wv['video_title']} 🎥</a>"
        progress = wv.get('progress_percentage', 0)
        
        if progress >= 100:
            status_span = "<span class='status done'>Watched</span>"
        else:
            status_span = f"<span class='status pending'>In Progress ({progress}%)</span>"
            
        watched_videos_list.append([
            str(wv['watched_date'] or ''),
            video_link,
            wv['course_title'] or 'No Course',
            status_span
        ])

    # 3. Certificates list
    cursor.execute("""
        SELECT DATE_FORMAT(cert.issued_at, '%Y-%m-%d') as issue_date, cert.certificate_code, c.title as course_title, c.id as course_id
        FROM certificates cert
        JOIN courses c ON cert.course_id = c.id
        WHERE cert.student_id = %s
        ORDER BY cert.issued_at DESC
    """, (student_id,))
    certificates_raw = cursor.fetchall()
    
    certificates_list = []
    for cert in certificates_raw:
        action_btn = f"<a href='/student/certificate/{cert['course_id']}' target='_blank' class='status done' style='display:inline-block; text-decoration:none;'>Download 🏆</a>"
        certificates_list.append([
            str(cert['issue_date'] or ''),
            cert['course_title'],
            cert['certificate_code'],
            action_btn
        ])

    # 4. Quiz results list
    cursor.execute("""
        SELECT q.title as quiz_title, qr.score, DATE_FORMAT(qr.created_at, '%Y-%m-%d') as completed_date
        FROM quiz_results qr
        JOIN quizzes q ON qr.quiz_id = q.id
        WHERE qr.student_id = %s
        ORDER BY qr.created_at DESC
    """, (student_id,))
    quiz_results_raw = cursor.fetchall()
    
    quiz_results_list = []
    for qr in quiz_results_raw:
        quiz_results_list.append([
            qr['quiz_title'],
            f"{float(qr['score']):.2f}%",
            str(qr['completed_date'] or '')
        ])

    cursor.close()
    conn.close()

    return render_template(
        'student/studentdashboard.html',
        competitive_exam=competitive_exam,
        student_streak=student_streak,
        enrolled_count=enrolled_count,
        completed_count=completed_count,
        watched_videos_count=watched_videos_count,
        certificates_count=certificates_count,
        avg_score=avg_score,
        connections_count=connections_count,
        upcoming_classes=upcoming_classes,
        enrolled_courses=enrolled_courses,
        enrolled_courses_json=json.dumps(enrolled_courses_list),
        watched_videos_json=json.dumps(watched_videos_list),
        certificates_json=json.dumps(certificates_list),
        quiz_results_json=json.dumps(quiz_results_list)
    )

@app.route('/student/certificate/<int:course_id>')
def student_certificate(course_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Verify student has indeed earned a certificate for this course
    cursor.execute("""
        SELECT cert.certificate_code, cert.issued_at, c.title as course_title, u.name as student_name
        FROM certificates cert
        JOIN courses c ON cert.course_id = c.id
        JOIN users u ON cert.student_id = u.id
        WHERE cert.student_id = %s AND cert.course_id = %s
    """, (student_id, course_id))
    cert = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not cert:
        flash("You have not earned a certificate for this course yet.", "warning")
        return redirect(url_for('student_dashboard'))
        
    return render_template('student/certificate.html', cert=cert)

@app.route('/student/courses', methods=['GET', 'POST'])
def student_courses():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Enroll in a course
        course_id = request.form.get('course_id')
        cursor.execute("SELECT id FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
            conn.commit()
            flash("Enrolled successfully in the course!", "success")
        else:
            flash("You are already enrolled in this course.", "info")
        return redirect(url_for('student_courses'))
        
    # Get all courses
    cursor.execute("""
        SELECT c.*, u.name as teacher_name, 
               (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id) as student_count,
               (SELECT COUNT(*) FROM videos WHERE course_id = c.id) as video_count,
               (SELECT COUNT(*) FROM materials WHERE course_id = c.id) as material_count,
               (SELECT progress FROM enrollments WHERE student_id = %s AND course_id = c.id) as student_progress,
               (SELECT id FROM enrollments WHERE student_id = %s AND course_id = c.id) as enrolled_id
        FROM courses c 
        JOIN users u ON c.created_by = u.id
        WHERE c.status = 'approved'
    """, (student_id, student_id))
    db_courses = cursor.fetchall()
    
    courses_list = []
    for dc in db_courses:
        is_enrolled = dc['enrolled_id'] is not None
        lessons_count = dc['video_count'] + dc['material_count']
        if lessons_count == 0:
            lessons_count = 5  # default fallback
            
        courses_list.append({
            'id': dc['id'],
            'img': dc['cover_image_url'],
            'title': dc['title'],
            'desc': dc['description'],
            'category': dc['category'],
            'lessons': lessons_count,
            'duration': f"{lessons_count * 45} mins" if lessons_count > 0 else "4 hours",
            'students': dc['student_count'] if dc['student_count'] > 0 else 0,
            'rating': 4.8,
            'start': dc['created_at'].strftime('%Y-%m-%d') if isinstance(dc['created_at'], datetime) else str(dc['created_at']),
            'end': 'Self-paced',
            'type': dc['price_type'],
            'price': float(dc['price']) if dc['price'] is not None else 0.0,
            'oldPrice': float(dc['price']) * 2.5 if dc['price'] and dc['price'] > 0 else 0.0,
            'enrolled': is_enrolled,
            'progress': dc['student_progress'] if dc['student_progress'] is not None else 0,
            'tag': 'trending' if dc['student_count'] > 2 else None,
            'ribbon': dc['price_type'],
            'mode': 'live' if dc['id'] % 3 == 0 else ('recorded' if dc['id'] % 3 == 1 else 'live+recorded')
        })
        
    import json
    courses_json = json.dumps(courses_list)
    
    cursor.close()
    conn.close()
    
    return render_template('student/course.html', courses=db_courses, courses_json=courses_json)

@app.route('/student/course/complete/<int:course_id>', methods=['POST'])
def student_complete_course(course_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    # Check enrollment
    cursor.execute("SELECT id, completed FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    enrollment = cursor.fetchone()
    if enrollment:
        # Mark as 100% completed
        cursor.execute(
            "UPDATE enrollments SET progress = 100, completed = TRUE WHERE student_id = %s AND course_id = %s",
            (student_id, course_id)
        )
        # Check if certificate code already exists
        cursor.execute("SELECT id FROM certificates WHERE student_id = %s AND course_id = %s", (student_id, course_id))
        if not cursor.fetchone():
            cert_code = f"CERT-{student_id}-{course_id}-{str(uuid.uuid4())[:8].upper()}"
            cursor.execute(
                "INSERT INTO certificates (student_id, course_id, certificate_code) VALUES (%s, %s, %s)",
                (student_id, course_id, cert_code)
            )
            # Notify student
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (student_id, f"Congratulations! You earned a certificate for course ID {course_id}. Code: {cert_code}")
            )
        conn.commit()
        flash("Course completed and Certificate generated successfully!", "success")
    
    cursor.close()
    conn.close()
    return redirect(url_for('student_dashboard'))

@app.route('/student/materials')
def student_materials():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch materials uploaded by connected teachers
    cursor.execute("""
        SELECT m.*, u.name as teacher_name, c.title as course_title
        FROM materials m 
        JOIN users u ON m.uploaded_by = u.id 
        LEFT JOIN courses c ON m.course_id = c.id
        ORDER BY m.created_at DESC
    """, ())
    materials = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('student/studymaterial(s).html', materials=materials)

@app.route('/student/review_material', methods=['POST'])
def student_review_material():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    teacher_id = request.form.get('teacher_id')
    rating = request.form.get('rating', 5)
    review_text = request.form.get('review_text', '')
    redirect_url = request.form.get('redirect_url')
    
    if teacher_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teacher_reviews (teacher_id, student_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE rating=VALUES(rating), review_text=VALUES(review_text)
        """, (teacher_id, student_id, rating, review_text))
        conn.commit()
        cursor.close()
        conn.close()
        
    return redirect(redirect_url if redirect_url else url_for('student_materials'))

@app.route('/student/videos', methods=['GET', 'POST'])
def student_videos():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Mark video as watched and save review
        video_id = request.form.get('video_id')
        rating = request.form.get('rating', 5)
        review_text = request.form.get('review_text', '')
        
        cursor.execute("SELECT uploaded_by FROM videos WHERE id = %s", (video_id,))
        video = cursor.fetchone()
        
        if video:
            teacher_id = video['uploaded_by']
            cursor.execute("""
                INSERT INTO teacher_reviews (teacher_id, student_id, rating, review_text)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE rating=VALUES(rating), review_text=VALUES(review_text)
            """, (teacher_id, student_id, rating, review_text))

        cursor.execute("""
            INSERT INTO watched_videos (student_id, video_id, progress_percentage) 
            VALUES (%s, %s, 100)
            ON DUPLICATE KEY UPDATE progress_percentage = 100, watched_at = CURRENT_TIMESTAMP
        """, (student_id, video_id))
        
        conn.commit()
        flash("Video marked as watched and review submitted!", "success")
        return redirect(url_for('student_videos'))
        
    # Fetch videos from connected teachers only
    cursor.execute("""
        SELECT v.*, u.name as teacher_name,
               IFNULL(wv.progress_percentage, 0) as progress_percentage,
               IFNULL(wv.last_position, 0) as last_position,
               CASE WHEN wv.id IS NOT NULL THEN 1 ELSE 0 END as watched
        FROM videos v 
        JOIN users u ON v.uploaded_by = u.id 
        LEFT JOIN watched_videos wv ON wv.video_id = v.id AND wv.student_id = %s
        WHERE v.course_id IS NULL
        ORDER BY v.created_at DESC
    """, (student_id,))
    videos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('student/video(s).html', videos=videos)

@app.route('/student/update_video_progress', methods=['POST'])
def student_update_video_progress():
    if not check_role(['student']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    student_id = session['user_id']
    data = request.json
    video_id = data.get('video_id')
    progress_percentage = data.get('progress_percentage', 0)
    last_position = data.get('last_position', 0)
    
    if not video_id:
        return jsonify({'success': False, 'message': 'Missing video_id'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO watched_videos (student_id, video_id, progress_percentage, last_position)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                progress_percentage = GREATEST(progress_percentage, VALUES(progress_percentage)),
                last_position = VALUES(last_position),
                watched_at = CURRENT_TIMESTAMP
        """, (student_id, video_id, progress_percentage, last_position))
        conn.commit()
    except Exception as e:
        print("Error updating video progress:", e)
    finally:
        cursor.close()
        conn.close()
        
    return jsonify({'success': True})

@app.route('/student/live-classes')
def student_live_classes():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Upcoming and past live classes from connected teachers
    cursor.execute("""
        SELECT lc.*, u.name as teacher_name, c.title as course_title
        FROM live_classes lc 
        JOIN users u ON lc.teacher_id = u.id 
        LEFT JOIN courses c ON lc.course_id = c.id
        WHERE lc.teacher_id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
        ORDER BY lc.class_date DESC, lc.class_time DESC
    """, (student_id, student_id))
    live_classes = cursor.fetchall()
    cursor.close()
    conn.close()
    
    from datetime import datetime
    now = datetime.now()
    
    upcoming_classes = []
    past_classes = []
    active_class = None
    
    for lc in live_classes:
        dt_str = f"{lc['class_date']} {lc['class_time']}"
        try:
            lc['scheduled_at'] = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            lc['scheduled_at'] = now # fallback if format is weird
        
        lc['title'] = lc['topic']
        
        # Optionally format course title into topic if it exists
        if lc.get('course_title'):
            lc['title'] = f"[{lc['course_title']}] {lc['title']}"
            
        if lc['scheduled_at'] > now:
            upcoming_classes.append(lc)
        else:
            past_classes.append(lc)
            
    # For now, active_class logic is simple (could check if current time is within duration)
    # Let's just leave it None unless you want to implement it like teacher side
    
    return render_template('student/liveclasses(s).html', 
                           upcoming_classes=upcoming_classes, 
                           past_classes=past_classes, 
                           active_class=active_class)

@app.route('/student/connections', methods=['GET', 'POST'])
def student_connections():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_request':
            # Send connection request
            teacher_id = request.form.get('teacher_id')
            cursor.execute("SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))", (student_id, teacher_id, teacher_id, student_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO connections (sender_id, receiver_id, status) VALUES (%s, %s, 'pending')", (student_id, teacher_id))
                conn.commit()
                
                # Notify receiver
                cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", 
                               (teacher_id, f"You have a new connection request from Student: {session['name']}."))
                conn.commit()
                flash("Connection request sent successfully!", "success")
            else:
                flash("Request already sent or connection exists.", "warning")
        else:
            # Accepting or rejecting a request
            request_id = request.form.get('request_id')
            new_status = request.form.get('status') # 'accepted' or 'rejected'
            
            # Verify request exists
            cursor.execute("SELECT sender_id as sender FROM connections WHERE id = %s AND receiver_id = %s", (request_id, student_id))
            req = cursor.fetchone()
            if req:
                cursor.execute("UPDATE connections SET status = %s WHERE id = %s", (new_status, request_id))
                conn.commit()
                
                # Notify sender
                cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", 
                               (req['sender'], f"Your connection request to student {session['name']} has been {new_status}."))
                conn.commit()
                flash(f"Connection request {new_status} successfully!", "success")
            else:
                flash("Connection request not found.", "danger")
        
        return redirect(url_for('student_connections'))
        
    # Get all approved teachers
    cursor.execute("""
        SELECT DISTINCT u.id as teacher_id, u.name, u.email, tp.subject, tp.experience,
               cr.status as connection_status
        FROM users u 
        LEFT JOIN teacher_profiles tp ON u.id = tp.user_id 
        LEFT JOIN connections cr ON (cr.receiver_id = u.id AND cr.sender_id = %s) OR (cr.sender_id = u.id AND cr.receiver_id = %s)
        WHERE u.role = 'teacher' AND u.status = 'approved' AND u.id != %s
    """, (student_id, student_id, student_id))
    teachers = cursor.fetchall()
    
    # Get all approved students
    cursor.execute("""
        SELECT DISTINCT u.id as student_id, u.name, u.email, sp.class_level, sp.stream,
               conn.status as connection_status
        FROM users u
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        LEFT JOIN connections conn ON (conn.receiver_id = u.id AND conn.sender_id = %s) OR (conn.sender_id = u.id AND conn.receiver_id = %s)
        WHERE u.role = 'student' AND u.status = 'approved' AND u.id != %s
    """, (student_id, student_id, student_id))
    students = cursor.fetchall()
    
    # Get connection requests
    cursor.execute("""
        SELECT cr.id as request_id, cr.status, cr.created_at, u.id as sender_id, u.name, u.email, u.role
        FROM connections cr 
        JOIN users u ON cr.sender_id = u.id 
        WHERE cr.receiver_id = %s AND cr.status = 'pending'
        ORDER BY cr.created_at DESC
    """, (student_id,))
    requests_list = cursor.fetchall()
    
    # Get total connections count
    cursor.execute("SELECT COUNT(*) as count FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (student_id, student_id))
    connections_count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    return render_template('student/findpeople(s).html', teachers=teachers, students=students, requests=requests_list, connections_count=connections_count)

@app.route('/chat/delete/<int:other_id>', methods=['POST'])
def delete_chat(other_id):
    if not is_logged_in():
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE chats SET deleted_by_sender = TRUE 
        WHERE sender_id = %s AND receiver_id = %s
    """, (user_id, other_id))
    
    cursor.execute("""
        UPDATE chats SET deleted_by_receiver = TRUE 
        WHERE receiver_id = %s AND sender_id = %s
    """, (user_id, other_id))
    
    # Optional cleanup for messages deleted by both
    cursor.execute("""
        DELETE FROM chats WHERE deleted_by_sender = TRUE AND deleted_by_receiver = TRUE
    """)

    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Chat deleted successfully.", "success")
    
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher_chat'))
    else:
        return redirect(url_for('student_chat'))

@app.route('/chat/delete_message/<int:message_id>', methods=['POST'])
def delete_single_message(message_id):
    if not is_logged_in():
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    active_chat = request.form.get('active_chat')
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM chats 
        WHERE id = %s AND (sender_id = %s OR receiver_id = %s)
    """, (message_id, user_id, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    if session.get('role') == 'teacher':
        return redirect(url_for('teacher_chat', active_chat=active_chat))
    else:
        return redirect(url_for('student_chat', active_chat=active_chat))

@app.route('/student/chat', methods=['GET', 'POST'])
def student_chat():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        message = request.form.get('message')
        
        if not receiver_id or not receiver_id.isdigit():
            flash("Invalid user selected.", "danger")
            return redirect(url_for('student_chat'))
            
        # Verify connection
        cursor.execute("SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)) AND status = 'accepted'", (student_id, receiver_id, receiver_id, student_id))
        if cursor.fetchone():
            cursor.execute("INSERT INTO chats (sender_id, receiver_id, message) VALUES (%s, %s, %s)", (student_id, receiver_id, message))
            conn.commit()
            return redirect(url_for('student_chat', active_chat=receiver_id))
        else:
            flash("You can only chat with connected members.", "danger")
            return redirect(url_for('student_chat'))
            
    # Load all connected users with unread message counts
    cursor.execute("""
        SELECT u.id as user_id, u.name, u.role,
               (SELECT COUNT(*) FROM chats WHERE sender_id = u.id AND receiver_id = %s AND is_read = FALSE AND deleted_by_receiver = FALSE) as unread_count
        FROM users u 
        WHERE u.id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
    """, (student_id, student_id, student_id))
    connected_users = cursor.fetchall()
    
    # Load chat history if active_chat is specified
    active_chat_id = request.args.get('active_chat')
    if active_chat_id and not active_chat_id.isdigit():
        active_chat_id = None
        
    messages = []
    active_user = None
    if active_chat_id:
        cursor.execute("SELECT name, role FROM users WHERE id = %s", (active_chat_id,))
        active_user = cursor.fetchone()
        if active_user:
            # Mark messages as read
            cursor.execute("UPDATE chats SET is_read = TRUE WHERE sender_id = %s AND receiver_id = %s", (active_chat_id, student_id))
            conn.commit()
            
            cursor.execute("""
                SELECT * FROM chats 
                WHERE ((sender_id = %s AND receiver_id = %s AND deleted_by_sender = FALSE) 
                   OR (sender_id = %s AND receiver_id = %s AND deleted_by_receiver = FALSE))
                ORDER BY created_at ASC
            """, (student_id, active_chat_id, active_chat_id, student_id))
            messages = cursor.fetchall()
            
    cursor.close()
    conn.close()
    return render_template('student/chat(s).html', connected_users=connected_users, messages=messages, active_user=active_user, active_chat_id=active_chat_id)

@app.route('/student/qa', methods=['GET', 'POST'])
def student_qa():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action', 'ask_question')
        
        if action == 'ask_question':
            subject = request.form.get('subject', '').strip()
            question_text = request.form.get('question_text')
            
            if subject and question_text:
                cursor.execute("INSERT INTO questions (student_id, subject, question_text) VALUES (%s, %s, %s)", (student_id, subject, question_text))
                conn.commit()
                flash("Question submitted successfully!", "success")
            else:
                flash("Subject and question text are required.", "danger")
            return redirect(url_for('student_qa'))
            
        elif action == 'answer_question':
            question_id = request.form.get('question_id')
            answer_text = request.form.get('answer_text')
            cursor.execute("INSERT INTO student_answers (question_id, student_id, answer_text, status) VALUES (%s, %s, %s, 'pending')", (question_id, student_id, answer_text))
            conn.commit()
            flash("Answer submitted for teacher approval!", "success")
            return redirect(url_for('student_qa'))
            
        elif action == 'delete_question':
            question_id = request.form.get('question_id')
            cursor.execute("SELECT id FROM questions WHERE id = %s AND student_id = %s", (question_id, student_id))
            if cursor.fetchone():
                cursor.execute("DELETE FROM answers WHERE question_id = %s", (question_id,))
                cursor.execute("DELETE FROM student_answers WHERE question_id = %s", (question_id,))
                cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
                conn.commit()
                flash("Question deleted successfully!", "success")
            else:
                flash("Unauthorized to delete this question.", "danger")
            return redirect(url_for('student_qa'))
        
    # Get all questions (community)
    cursor.execute("""
        SELECT q.id as question_id, q.question_text, q.subject, q.created_at, q.student_id, u.name as teacher_name,
               a.answer_text, a.created_at as answered_at, su.name as student_name
        FROM questions q
        LEFT JOIN users u ON q.teacher_id = u.id
        JOIN users su ON q.student_id = su.id
        LEFT JOIN answers a ON a.question_id = q.id
        ORDER BY q.created_at DESC
    """)
    questions = cursor.fetchall()
    
    # Get approved student answers and student's own answers
    cursor.execute("""
        SELECT sa.question_id, sa.answer_text, sa.created_at, su.name as student_name, sa.status, sa.rejection_reason, sa.student_id
        FROM student_answers sa
        JOIN users su ON sa.student_id = su.id
        WHERE sa.status = 'approved' OR sa.student_id = %s
    """, (student_id,))
    student_answers_db = cursor.fetchall()
    
    # Group them by question_id
    student_answers_dict = {}
    for sa in student_answers_db:
        qid = sa['question_id']
        if qid not in student_answers_dict:
            student_answers_dict[qid] = []
        student_answers_dict[qid].append(sa)
        
    for q in questions:
        q['student_answers'] = student_answers_dict.get(q['question_id'], [])
    
    # Get connected teachers list for dropdown
    cursor.execute("""
        SELECT u.id as teacher_id, u.name 
        FROM users u 
        WHERE u.id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        ) AND u.role = 'teacher'
    """, (student_id, student_id))
    connected_teachers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('student/q&a(s).html', questions=questions, teachers=connected_teachers)

@app.route('/student/quizzes', methods=['GET', 'POST'])
def student_quizzes():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Submit Quiz
        quiz_id = request.form.get('quiz_id')
        cursor.execute("SELECT * FROM quiz_questions WHERE quiz_id = %s", (quiz_id,))
        questions = cursor.fetchall()
        
        correct_count = 0
        total_count = len(questions)
        
        results_details = []
        
        for q in questions:
            submitted_ans = request.form.get(f"question_{q['id']}")
            is_correct = (submitted_ans == q['correct_option'])
            if is_correct:
                correct_count += 1
                
            results_details.append({
                'question_text': q['question_text'],
                'option_a': q['option_a'],
                'option_b': q['option_b'],
                'option_c': q['option_c'],
                'option_d': q['option_d'],
                'submitted': submitted_ans,
                'correct': q['correct_option'],
                'explanation': q['explanation'],
                'is_correct': is_correct
            })
                
        score = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # Save results
        cursor.execute("INSERT INTO quiz_results (quiz_id, student_id, score) VALUES (%s, %s, %s)", (quiz_id, student_id, score))
        conn.commit()
        cursor.close()
        conn.close()
        
        return render_template('student/quiz_result.html', score=score, total_count=total_count, correct_count=correct_count, results=results_details)
        
    # Get quizzes:
    # 1. From enrolled courses
    # 2. From courses matching student's stream/category
    # 3. From ANY connected teacher (so quizzes show up even without course enrollment)
    # 4. Standalone quizzes (no course) by connected teachers
    cursor.execute("""
        SELECT DISTINCT qz.id, qz.title, qz.created_at,
               COALESCE(c.title, 'General Quiz') as course_title,
               u.name as teacher_name,
               (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = qz.id) as question_count,
               (SELECT score FROM quiz_results WHERE quiz_id = qz.id AND student_id = %s ORDER BY id DESC LIMIT 1) as last_score
        FROM quizzes qz
        LEFT JOIN courses c ON qz.course_id = c.id
        JOIN users u ON qz.teacher_id = u.id
        WHERE (
            -- Enrolled in course
            (qz.course_id IS NOT NULL AND qz.course_id IN (SELECT course_id FROM enrollments WHERE student_id = %s))
            -- Course matches stream
            OR (qz.course_id IS NOT NULL AND c.category = (SELECT stream FROM student_profiles WHERE user_id = %s))
            -- Connected teacher's quizzes (any quiz)
            OR qz.teacher_id IN (
                SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
                UNION
                SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
            )
        )
        HAVING question_count > 0
        ORDER BY qz.created_at DESC
    """, (student_id, student_id, student_id, student_id, student_id))
    quizzes = cursor.fetchall()
    
    active_quiz_id = request.args.get('quiz_id')
    quiz_questions = []
    active_quiz = None
    if active_quiz_id:
        cursor.execute("SELECT * FROM quizzes WHERE id = %s", (active_quiz_id,))
        active_quiz = cursor.fetchone()
        cursor.execute("SELECT * FROM quiz_questions WHERE quiz_id = %s", (active_quiz_id,))
        quiz_questions = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return render_template('student/quizzes(s).html', quizzes=quizzes, questions=quiz_questions, active_quiz=active_quiz, active_quiz_id=active_quiz_id)
@app.route('/student/notifications')
def student_notifications():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Mark all as read
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (student_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (student_id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('student/notification(s).html', notifications=notifications)

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        class_level = request.form.get('class_level')
        stream = request.form.get('stream')
        competitive_exam = request.form.get('competitive_exam')
        
        cursor.execute("""
            UPDATE users SET name = %s, phone = %s, age = %s, gender = %s 
            WHERE id = %s
        """, (name, phone, age, gender, student_id))
        cursor.execute("""
            UPDATE student_profiles SET class_level = %s, stream = %s, competitive_exam = %s 
            WHERE user_id = %s
        """, (class_level, stream, competitive_exam, student_id))
        conn.commit()
        session['name'] = name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('student_profile'))
        
    cursor.execute("""
        SELECT u.*, sp.class_level, sp.stream, sp.competitive_exam 
        FROM users u 
        JOIN student_profiles sp ON u.id = sp.user_id 
        WHERE u.id = %s
    """, (student_id,))
    user = cursor.fetchone()
    
    # 1. Enrolled courses
    cursor.execute("""
        SELECT c.title, e.progress 
        FROM enrollments e 
        JOIN courses c ON e.course_id = c.id 
        WHERE e.student_id = %s
        ORDER BY e.enrolled_at DESC
    """, (student_id,))
    enrolled_courses = cursor.fetchall()
    
    # 2. Certificates
    cursor.execute("""
        SELECT cert.certificate_code, cert.issued_at, c.title as course_title 
        FROM certificates cert 
        JOIN courses c ON cert.course_id = c.id 
        WHERE cert.student_id = %s
        ORDER BY cert.issued_at DESC
    """, (student_id,))
    certificates = cursor.fetchall()
    
    # 3. Connections count
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM connections 
        WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'
    """, (student_id, student_id))
    connections_count = cursor.fetchone()['count']
    
    # 4. Recent activity: Quizzes completed
    cursor.execute("""
        SELECT q.title, qr.score, qr.created_at 
        FROM quiz_results qr 
        JOIN quizzes q ON qr.quiz_id = q.id 
        WHERE qr.student_id = %s 
        ORDER BY qr.created_at DESC LIMIT 2
    """, (student_id,))
    recent_quizzes = cursor.fetchall()
    
    # 5. Recent activity: Videos watched
    cursor.execute("""
        SELECT v.title, wv.watched_at 
        FROM watched_videos wv 
        JOIN videos v ON wv.video_id = v.id 
        WHERE wv.student_id = %s 
        ORDER BY wv.watched_at DESC LIMIT 2
    """, (student_id,))
    recent_videos = cursor.fetchall()
    
    # 6. Recent activity: Questions asked
    cursor.execute("""
        SELECT question_text, created_at 
        FROM questions 
        WHERE student_id = %s 
        ORDER BY created_at DESC LIMIT 2
    """, (student_id,))
    recent_questions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template(
        'student/studentprofile.html', 
        user=user, 
        enrolled_courses=enrolled_courses,
        certificates=certificates,
        connections_count=connections_count,
        recent_quizzes=recent_quizzes,
        recent_videos=recent_videos,
        recent_questions=recent_questions
    )


@app.route('/student/events')
def student_event():
    if not check_role(['student']):
        return redirect(url_for('login'))
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all approved events
    cursor.execute("SELECT * FROM events WHERE status = 'approved' ORDER BY event_date ASC")
    db_events = cursor.fetchall()
    
    events = []
    for e in db_events:
        event_id = e['id']
        
        # Likes count
        cursor.execute("SELECT COUNT(*) as count FROM event_likes WHERE event_id = %s", (event_id,))
        likes_count = cursor.fetchone()['count']
        
        # Whether liked by current student
        cursor.execute("SELECT 1 FROM event_likes WHERE event_id = %s AND student_id = %s", (event_id, student_id))
        is_liked = cursor.fetchone() is not None
        
        # Whether saved by current student
        cursor.execute("SELECT 1 FROM event_saves WHERE event_id = %s AND student_id = %s", (event_id, student_id))
        is_saved = cursor.fetchone() is not None
        
        # Whether applied by current student
        cursor.execute("SELECT 1 FROM event_registrations WHERE event_id = %s AND student_id = %s", (event_id, student_id))
        is_applied = cursor.fetchone() is not None
        
        # Comments
        cursor.execute("""
            SELECT ec.*, u.name as student_name 
            FROM event_comments ec 
            JOIN users u ON ec.student_id = u.id 
            WHERE ec.event_id = %s 
            ORDER BY ec.created_at ASC
        """, (event_id,))
        comments = cursor.fetchall()
        
        events.append({
            'id': event_id,
            'title': e['title'],
            'description': e['description'],
            'event_type': e['event_type'],
            'event_date': e['event_date'],
            'location': e['location'],
            'prize': e['prize'],
            'apply_link': e['apply_link'],
            'image_url': e['image_url'],
            'price': float(e['price']),
            'likes_count': likes_count,
            'is_liked': is_liked,
            'is_saved': is_saved,
            'is_applied': is_applied,
            'comments': comments
        })
        
    # Get overall stats for student
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE status = 'approved'")
    total_events = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM event_registrations WHERE student_id = %s", (student_id,))
    applied_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM event_saves WHERE student_id = %s", (student_id,))
    saved_count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    stats = {
        'total': total_events,
        'applied': applied_count,
        'saved': saved_count
    }
    
    return render_template('student/event.html', events=events, stats=stats)

@app.route('/student/event/action/<int:event_id>/<string:action_type>', methods=['POST'])
def student_event_action(event_id, action_type):
    if not check_role(['student']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    student_id = session['user_id']
    if action_type not in ('like', 'save'):
        return jsonify({'success': False, 'message': 'Invalid action type'}), 400
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    table = 'event_likes' if action_type == 'like' else 'event_saves'
    
    # Check if already exists
    cursor.execute(f"SELECT id FROM {table} WHERE event_id = %s AND student_id = %s", (event_id, student_id))
    row = cursor.fetchone()
    
    if row:
        # Delete if exists (toggle off)
        cursor.execute(f"DELETE FROM {table} WHERE id = %s", (row['id'],))
        action = 'removed'
    else:
        # Insert if not exists (toggle on)
        cursor.execute(f"INSERT INTO {table} (event_id, student_id) VALUES (%s, %s)", (event_id, student_id))
        action = 'added'
        
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'action': action})

@app.route('/student/event/comment/<int:event_id>', methods=['POST'])
def student_event_comment(event_id):
    if not check_role(['student']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    student_id = session['user_id']
    comment_text = request.form.get('comment_text', '').strip()
    
    if not comment_text:
        return jsonify({'success': False, 'message': 'Comment text is empty'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO event_comments (event_id, student_id, comment_text) VALUES (%s, %s, %s)", (event_id, student_id, comment_text))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/student/event/apply/<int:event_id>', methods=['GET', 'POST'])
def student_event_apply(event_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch event details
    cursor.execute("SELECT * FROM events WHERE id = %s AND status = 'approved'", (event_id,))
    event = cursor.fetchone()
    if not event:
        cursor.close()
        conn.close()
        flash("Event not found or not approved yet.", "danger")
        return redirect(url_for('student_event'))
        
    if request.method == 'POST':
        # Handles JSON or Form payload
        data = request.form
        first_name = data.get('first_name') or data.get('firstName')
        last_name = data.get('last_name') or data.get('lastName')
        email = data.get('email')
        phone = data.get('phone')
        college = data.get('college')
        year_of_study = data.get('year_of_study') or data.get('year')
        department = data.get('department') or data.get('dept')
        team_name = data.get('team_name') or data.get('team')
        why_join = data.get('why_join') or data.get('reason')
        payment_method = data.get('payment_method') or data.get('payment')
        
        # Parse id_card if present
        id_card_url = None
        id_card = request.files.get('id_card')
        if id_card and id_card.filename:
            filename = secure_filename(id_card.filename)
            # Prepend uuid to avoid collisions
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            id_card_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            id_card.save(id_card_path)
            id_card_url = unique_filename
            
        # Parse payment screenshot if paid
        payment_screenshot_url = None
        if float(event['price']) > 0:
            payment_screenshot = request.files.get('payment_screenshot')
            if payment_screenshot and payment_screenshot.filename:
                ps_filename = secure_filename(payment_screenshot.filename)
                unique_ps_filename = f"ps_{uuid.uuid4().hex}_{ps_filename}"
                ps_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_ps_filename)
                payment_screenshot.save(ps_path)
                payment_screenshot_url = f"/static/{unique_ps_filename}"
            else:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Payment screenshot is required for paid events'}), 400
        
        # Validate required fields
        if not all([first_name, last_name, email, phone, college, year_of_study, department, why_join, payment_method]):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        payment_status = 'free' if float(event['price']) == 0.0 else 'pending'
        paid_amount = float(event['price'])
        
        try:
            cursor.execute("""
                INSERT INTO event_registrations (event_id, student_id, first_name, last_name, email, phone, college, year_of_study, department, team_name, why_join, payment_method, payment_status, paid_amount, id_card_url, payment_screenshot)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (event_id, student_id, first_name, last_name, email, phone, college, year_of_study, department, team_name, why_join, payment_method, payment_status, paid_amount, id_card_url, payment_screenshot_url))
            conn.commit()
            
            # Send dynamic notifications
            cursor.execute("""
                INSERT INTO notifications (user_id, message) 
                VALUES (%s, %s)
            """, (student_id, f"You registered successfully for event: {event['title']}!"))
            conn.commit()
            
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Registered successfully'})
        except Exception as ex:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': str(ex)}), 500
            
    cursor.close()
    conn.close()
    return render_template('student/apply_form.html', event=event)


@app.route('/student/progress')
def student_progress():
    if not check_role(['student']):
        return redirect(url_for('login'))
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Quiz Analytics - All historical scores
    cursor.execute("""
        SELECT score, created_at 
        FROM quiz_results 
        WHERE student_id = %s 
        ORDER BY created_at DESC 
    """, (student_id,))
    all_scores = cursor.fetchall()
    
    latest_score = 0
    previous_score = 0
    trend = 0
    trend_direction = 'none'
    avg_score = 0
    
    if len(all_scores) > 0:
        latest_score = all_scores[0]['score']
        total_score = sum(s['score'] for s in all_scores)
        avg_score = round(total_score / len(all_scores), 1)
        
    if len(all_scores) > 1:
        previous_score = all_scores[1]['score']
        trend = latest_score - previous_score
        if trend > 0:
            trend_direction = 'increased'
        elif trend < 0:
            trend_direction = 'decreased'
        else:
            trend_direction = 'same'
    
    # Recent Quiz Performance
    cursor.execute("""
        SELECT qr.score, DATE_FORMAT(qr.created_at, '%b %d, %Y') as date, q.title as quiz_title, c.title as course_title
        FROM quiz_results qr
        JOIN quizzes q ON qr.quiz_id = q.id
        JOIN courses c ON q.course_id = c.id
        WHERE qr.student_id = %s
        ORDER BY qr.created_at DESC
        LIMIT 4
    """, (student_id,))
    recent_quizzes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    stats = {
        'avg_score': avg_score,
        'latest_score': latest_score,
        'previous_score': previous_score,
        'trend': round(trend, 1),
        'trend_direction': trend_direction
    }
    
    return render_template('student/learningprogress(s).html', recent_quizzes=recent_quizzes, stats=stats)

# ---- Student: Review a Teacher ----
@app.route('/student/review/<int:teacher_id>', methods=['GET', 'POST'])
def student_review_teacher(teacher_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Must be connected to the teacher
    cursor.execute("""
        SELECT id FROM connections
        WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))
        AND status = 'accepted'
    """, (student_id, teacher_id, teacher_id, student_id))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        flash("You can only review teachers you are connected with.", "danger")
        return redirect(url_for('student_connections'))

    # Fetch teacher info
    cursor.execute("""
        SELECT u.name, u.email, tp.subject, tp.experience
        FROM users u
        JOIN teacher_profiles tp ON u.id = tp.user_id
        WHERE u.id = %s
    """, (teacher_id,))
    teacher = cursor.fetchone()
    if not teacher:
        cursor.close(); conn.close()
        flash("Teacher not found.", "danger")
        return redirect(url_for('student_connections'))

    # Existing review (if any)
    cursor.execute("SELECT * FROM teacher_reviews WHERE teacher_id = %s AND student_id = %s", (teacher_id, student_id))
    existing_review = cursor.fetchone()

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        review_text = request.form.get('review_text', '').strip()
        if not review_text:
            flash("Review text cannot be empty.", "danger")
            cursor.close(); conn.close()
            return redirect(url_for('student_review_teacher', teacher_id=teacher_id))
        if rating < 1 or rating > 5:
            rating = 5
        try:
            cursor.execute("""
                INSERT INTO teacher_reviews (teacher_id, student_id, rating, review_text)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE rating = VALUES(rating), review_text = VALUES(review_text), created_at = CURRENT_TIMESTAMP
            """, (teacher_id, student_id, rating, review_text))
            conn.commit()
            # Notify the teacher
            cursor.execute("""
                INSERT INTO notifications (user_id, message) VALUES (%s, %s)
            """, (teacher_id, f"{session['name']} left you a {rating}-star review!"))
            conn.commit()
            flash("Review submitted successfully! ⭐", "success")
        except Exception as ex:
            flash(f"Error submitting review: {ex}", "danger")
        cursor.close(); conn.close()
        return redirect(url_for('student_connections'))

    cursor.close(); conn.close()
    return render_template('student/review_teacher.html', teacher=teacher, teacher_id=teacher_id, existing_review=existing_review)

@app.route('/teacher/events', methods=['GET', 'POST'])
def teacher_event():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        title = data.get('title')
        event_type = data.get('event_type') or data.get('type')
        event_date = data.get('event_date') or data.get('date')
        location = data.get('location')
        prize = data.get('prize')
        apply_link = data.get('apply_link') or data.get('applyLink')
        description = data.get('description')
        image_url = data.get('image_url') or data.get('image')
        price = data.get('price') or 0.0
        mode = data.get('mode') or 'Online'
        
        if not all([title, event_type, event_date, location, description]):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
            
        try:
            price_val = float(price)
        except ValueError:
            price_val = 0.0
            
        if not image_url:
            image_url = "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=900&auto=format&fit=crop"
            
        try:
            cursor.execute("""
                INSERT INTO events (title, description, event_type, event_date, location, prize, apply_link, image_url, price, status, created_by, mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            """, (title, description, event_type, event_date, location, prize, apply_link, image_url, price_val, teacher_id, mode))
            conn.commit()
            event_id = cursor.lastrowid
            cursor.execute("INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status) VALUES ('Event', %s, %s, 'New submission for review', 'low', 'pending')", (event_id, teacher_id))
            conn.commit()
            add_notification_to_all_students(f"New event created: {title}")
            
            if not apply_link:
                cursor.execute("UPDATE events SET apply_link = %s WHERE id = %s", (f"/student/event/apply/{event_id}", event_id))
                conn.commit()
                
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'Event created successfully and is pending admin approval'})
        except Exception as ex:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': str(ex)}), 500
            
    # Fetch events created by this teacher
    cursor.execute("SELECT * FROM events WHERE created_by = %s ORDER BY created_at DESC", (teacher_id,))
    db_events = cursor.fetchall()
    
    teacher_events = []
    for e in db_events:
        event_id = e['id']
        
        # Likes count
        cursor.execute("SELECT COUNT(*) as count FROM event_likes WHERE event_id = %s", (event_id,))
        likes_count = cursor.fetchone()['count']
        
        # Comments
        cursor.execute("""
            SELECT ec.*, u.name as student_name 
            FROM event_comments ec 
            JOIN users u ON ec.student_id = u.id 
            WHERE ec.event_id = %s 
            ORDER BY ec.created_at ASC
        """, (event_id,))
        comments = cursor.fetchall()
        
        teacher_events.append({
            'id': event_id,
            'title': e['title'],
            'description': e['description'],
            'event_type': e['event_type'],
            'event_date': e['event_date'],
            'location': e['location'],
            'prize': e['prize'],
            'apply_link': e['apply_link'],
            'image_url': e['image_url'],
            'price': float(e['price']),
            'status': e['status'],
            'likes_count': likes_count,
            'comments': comments
        })
        
    # Get stats for teacher dashboard
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE created_by = %s", (teacher_id,))
    total_events = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE created_by = %s AND status = 'approved'", (teacher_id,))
    approved_events = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM events WHERE created_by = %s AND status = 'pending'", (teacher_id,))
    pending_events = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    teacher_stats = {
        'total': total_events,
        'approved': approved_events,
        'pending': pending_events
    }
    
    return render_template('teacher/event_teacher.html', teacher_events=teacher_events, teacher_stats=teacher_stats)

@app.route('/teacher/event/delete/<int:event_id>', methods=['POST'])
def teacher_event_delete(event_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    teacher_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Check if the event belongs to this teacher
    cursor.execute("SELECT id FROM events WHERE id = %s AND created_by = %s", (event_id, teacher_id))
    event = cursor.fetchone()
    if not event:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Event not found or unauthorized'}), 404
        
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Event deleted successfully.'})

@app.route('/course/<int:course_id>')
def view_course_detail(course_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch course details
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    if not course:
        cursor.close()
        conn.close()
        flash("Course not found.", "danger")
        return redirect(url_for('student_courses'))
        
    # 2. Check if student is enrolled in this course
    cursor.execute("SELECT id FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    enrollment = cursor.fetchone()
    if not enrollment:
        cursor.close()
        conn.close()
        flash("You need to enroll in this course first.", "warning")
        return redirect(url_for('student_courses'))
        
    # 3. Fetch course videos
    cursor.execute("SELECT id, title, video_url, id as order_num FROM videos WHERE course_id = %s ORDER BY id ASC", (course_id,))
    videos = cursor.fetchall()
    
    # 4. Fetch completed video IDs for this student
    cursor.execute("""
        SELECT video_id FROM watched_videos 
        WHERE student_id = %s AND video_id IN (
            SELECT id FROM videos WHERE course_id = %s
        )
    """, (student_id, course_id))
    completed_video_rows = cursor.fetchall()
    completed_video_ids = [r['video_id'] for r in completed_video_rows]
    
    completed_count = len(completed_video_ids)
    
    # 5. Check if certificate is unlocked
    cert_unlocked = len(videos) > 0 and completed_count == len(videos)
    
    # 6. Fetch student details
    cursor.execute("SELECT * FROM users WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template(
        'student/start.html',
        course=course,
        videos=videos,
        completed_video_ids=completed_video_ids,
        completed_count=completed_count,
        cert_unlocked=cert_unlocked,
        student=student
    )

@app.route('/progress', methods=['POST'])
def update_course_progress():
    if not check_role(['student']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    student_id = session['user_id']
    data = request.get_json()
    video_id = data.get('video_id')
    
    if not video_id:
        return jsonify({'success': False, 'message': 'Missing video_id'}), 400
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Insert into watched_videos if not already watched
    cursor.execute("SELECT id FROM watched_videos WHERE student_id = %s AND video_id = %s", (student_id, video_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO watched_videos (student_id, video_id) VALUES (%s, %s)", (student_id, video_id))
        conn.commit()
        
    # 2. Get the course_id for this video to calculate enrollment progress
    cursor.execute("SELECT course_id FROM videos WHERE id = %s", (video_id,))
    v_row = cursor.fetchone()
    if v_row and v_row['course_id']:
        course_id = v_row['course_id']
        
        # Calculate total videos in course
        cursor.execute("SELECT COUNT(*) as count FROM videos WHERE course_id = %s", (course_id,))
        total_v = cursor.fetchone()['count']
        
        # Calculate watched videos in course
        cursor.execute("""
            SELECT COUNT(*) as count FROM watched_videos 
            WHERE student_id = %s AND video_id IN (
                SELECT id FROM videos WHERE course_id = %s
            )
        """, (student_id, course_id))
        watched_v = cursor.fetchone()['count']
        
        progress = int((watched_v / total_v) * 100) if total_v > 0 else 0
        completed = 1 if progress == 100 else 0
        
        cursor.execute("UPDATE enrollments SET progress = %s, completed = %s WHERE student_id = %s AND course_id = %s", (progress, completed, student_id, course_id))
        conn.commit()
        
        # If 100% completed, check/generate certificate
        if completed:
            cursor.execute("SELECT id FROM certificates WHERE student_id = %s AND course_id = %s", (student_id, course_id))
            if not cursor.fetchone():
                cert_code = f"CERT-{student_id}-{course_id}-{str(uuid.uuid4())[:8].upper()}"
                cursor.execute(
                    "INSERT INTO certificates (student_id, course_id, certificate_code) VALUES (%s, %s, %s)",
                    (student_id, course_id, cert_code)
                )
                # Notify student
                cursor.execute(
                    "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                    (student_id, f"Congratulations! You completed the course and earned a certificate. Code: {cert_code}")
                )
                conn.commit()
                
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})


# ----------------- TEACHER PORTAL ROUTES -----------------

@app.route('/teacher/earnings')
def teacher_earnings():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch total earnings
    cursor.execute("SELECT SUM(amount) as total FROM teacher_earnings WHERE teacher_id = %s", (teacher_id,))
    res = cursor.fetchone()
    total_earnings = float(res['total']) if res and res['total'] else 0.0
    
    # Fetch transaction history
    cursor.execute("SELECT * FROM teacher_earnings WHERE teacher_id = %s ORDER BY created_at DESC", (teacher_id,))
    history = cursor.fetchall()

    # Fetch withdrawal requests
    cursor.execute("SELECT * FROM withdrawal_requests WHERE teacher_id = %s ORDER BY created_at DESC", (teacher_id,))
    withdrawals = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('teacher/earnings.html', total_earnings=total_earnings, history=history, withdrawals=withdrawals)

@app.route('/teacher/withdraw', methods=['POST'])
def teacher_withdraw():
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    teacher_id = session['user_id']
    amount = request.form.get('amount')
    bank_name = request.form.get('bank_name')
    account_number = request.form.get('account_number')
    ifsc_code = request.form.get('ifsc_code')
    
    if not all([amount, bank_name, account_number, ifsc_code]):
        flash("All fields are required.", "danger")
        return redirect(url_for('teacher_earnings'))
        
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        flash("Invalid amount.", "danger")
        return redirect(url_for('teacher_earnings'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Verify balance
    cursor.execute("SELECT SUM(amount) as total FROM teacher_earnings WHERE teacher_id = %s", (teacher_id,))
    res = cursor.fetchone()
    total_earnings = float(res['total']) if res and res['total'] else 0.0
    
    # Calculate pending withdrawals to prevent over-withdrawing
    cursor.execute("SELECT SUM(amount) as pending_total FROM withdrawal_requests WHERE teacher_id = %s AND status = 'pending'", (teacher_id,))
    res_pending = cursor.fetchone()
    pending_total = float(res_pending['pending_total']) if res_pending and res_pending['pending_total'] else 0.0
    
    available_balance = total_earnings - pending_total
    
    if amount > available_balance:
        flash(f"Insufficient available balance. You have ₹{available_balance:.2f} available for withdrawal.", "danger")
    else:
        cursor.execute("""
            INSERT INTO withdrawal_requests (teacher_id, amount, bank_name, account_number, ifsc_code) 
            VALUES (%s, %s, %s, %s, %s)
        """, (teacher_id, amount, bank_name, account_number, ifsc_code))
        
        # Notify admins (optional, using id 1 as proxy for admin if we want, or general logic. Skipping specific admin notification for now or we can broadcast)
        
        conn.commit()
        flash("Withdrawal request submitted successfully! It is pending admin approval.", "success")
        
    cursor.close()
    conn.close()
    return redirect(url_for('teacher_earnings'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Connected students count
    cursor.execute("SELECT COUNT(*) as count FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (teacher_id, teacher_id))
    connected_students_count = cursor.fetchone()['count']
    
    # 2. Courses created
    cursor.execute("SELECT COUNT(*) as count FROM courses WHERE created_by = %s", (teacher_id,))
    courses_created_count = cursor.fetchone()['count']
    
    # 3. Materials uploaded
    cursor.execute("SELECT COUNT(*) as count FROM materials WHERE uploaded_by = %s", (teacher_id,))
    materials_uploaded_count = cursor.fetchone()['count']
    
    # 4. Videos uploaded
    cursor.execute("SELECT COUNT(*) as count FROM videos WHERE uploaded_by = %s", (teacher_id,))
    videos_uploaded_count = cursor.fetchone()['count']
    
    # 5. Live classes conducted
    cursor.execute("SELECT COUNT(*) as count FROM live_classes WHERE teacher_id = %s", (teacher_id,))
    live_classes_count = cursor.fetchone()['count']
    
    # 6. Pending questions count
    cursor.execute("""
        SELECT COUNT(*) as count FROM questions q
        WHERE q.teacher_id = %s AND q.id NOT IN (SELECT question_id FROM answers)
    """, (teacher_id,))
    pending_questions_count = cursor.fetchone()['count']
    
    # Pending questions list
    cursor.execute("""
        SELECT q.*, u.name as student_name 
        FROM questions q
        JOIN users u ON q.student_id = u.id
        WHERE q.teacher_id = %s AND q.id NOT IN (SELECT question_id FROM answers)
        ORDER BY q.created_at ASC
    """, (teacher_id,))
    pending_questions = cursor.fetchall()
    
    # Upcoming live classes
    cursor.execute("""
        SELECT * FROM live_classes 
        WHERE teacher_id = %s AND class_date >= CURDATE()
        ORDER BY class_date ASC, class_time ASC
    """, (teacher_id,))
    upcoming_classes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template(
        'teacher/teacherdashboard.html',
        connected_students_count=connected_students_count,
        courses_created_count=courses_created_count,
        materials_uploaded_count=materials_uploaded_count,
        videos_uploaded_count=videos_uploaded_count,
        live_classes_count=live_classes_count,
        pending_questions_count=pending_questions_count,
        pending_questions=pending_questions,
        upcoming_classes=upcoming_classes
    )

@app.route('/teacher/upload-material', methods=['GET', 'POST'])
def teacher_upload_material():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        subject = request.form.get('subject')
        course_id = request.form.get('course_id') or None  # optional course link
        
        file = request.files.get('material_file')
        file_url = ''
        if file and file.filename != '':
            filename = f"mat_{teacher_id}_{int(time.time())}_{file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'materials', filename)
            file.save(save_path)
            file_url = f"/static/uploads/materials/{filename}"
            
        cursor.execute(
            "INSERT INTO materials (title, description, file_url, subject, course_id, uploaded_by) VALUES (%s, %s, %s, %s, %s, %s)",
            (title, description, file_url, subject, course_id, teacher_id)
        )
        conn.commit()
        
        # Notify connected students
        cursor.execute("SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as student_id FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (teacher_id, teacher_id, teacher_id))
        students = cursor.fetchall()
        for stud in students:
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (stud['student_id'], f"Your connected teacher {session['name']} uploaded a new material: {title}.")
            )
        conn.commit()
        
        flash("Study material uploaded successfully!", "success")
        return redirect(url_for('teacher_upload_material'))
        
    # Get own uploaded materials with course name
    cursor.execute("""
        SELECT m.*, c.title as course_title 
        FROM materials m
        LEFT JOIN courses c ON m.course_id = c.id
        WHERE m.uploaded_by = %s ORDER BY m.created_at DESC
    """, (teacher_id,))
    my_materials = cursor.fetchall()
    
    # Get teacher's courses for the dropdown
    cursor.execute("SELECT id, title FROM courses WHERE created_by = %s ORDER BY title ASC", (teacher_id,))
    teacher_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('teacher/uploadpdf.html', materials=my_materials, teacher_courses=teacher_courses)

@app.route('/teacher/delete-material/<int:material_id>', methods=['POST'])
def teacher_delete_material(material_id):
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify ownership before deleting
    cursor.execute("SELECT file_url FROM materials WHERE id = %s AND uploaded_by = %s", (material_id, teacher_id))
    material = cursor.fetchone()
    if material:
        file_url = material[0]
        # Delete file from system
        if file_url:
            file_path = os.path.join(app.root_path, file_url.strip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        cursor.execute("DELETE FROM materials WHERE id = %s", (material_id,))
        conn.commit()
        flash("Study material deleted successfully.", "success")
    else:
        flash("Unauthorized deletion attempt.", "danger")
        
    cursor.close()
    conn.close()
    return redirect(url_for('teacher_upload_material'))

@app.route('/teacher/upload-video', methods=['GET', 'POST'])
def teacher_upload_video():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        video_source = request.form.get('video_source')  # 'file' or 'link'
        course_id = request.form.get('course_id') or None  # optional course link
        
        video_url = ''
        if video_source == 'file':
            file = request.files.get('video_file')
            if file and file.filename != '':
                filename = f"vid_{teacher_id}_{int(time.time())}_{file.filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
                file.save(save_path)
                video_url = f"/static/uploads/videos/{filename}"
        else:
            video_url = request.form.get('video_link')
            
        if not video_url:
            flash("Please upload a file or paste a video link first!", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('teacher_upload_video'))
            
        cursor.execute(
            "INSERT INTO videos (title, description, video_url, course_id, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
            (title, description, video_url, course_id, teacher_id)
        )
        conn.commit()
        
        # Notify connected students
        cursor.execute("SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as student_id FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (teacher_id, teacher_id, teacher_id))
        students = cursor.fetchall()
        for stud in students:
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (stud['student_id'], f"New video uploaded by connected teacher {session['name']}: {title}.")
            )
        conn.commit()
        
        flash("Video uploaded successfully!", "success")
        return redirect(url_for('teacher_upload_video'))
        
    # Get own uploaded videos (standalone only)
    cursor.execute("""
        SELECT v.*, c.title as course_title 
        FROM videos v
        LEFT JOIN courses c ON v.course_id = c.id
        WHERE v.uploaded_by = %s AND v.course_id IS NULL ORDER BY v.created_at DESC
    """, (teacher_id,))
    my_videos = cursor.fetchall()
    
    # Get teacher's courses for the dropdown
    cursor.execute("SELECT id, title FROM courses WHERE created_by = %s ORDER BY title ASC", (teacher_id,))
    teacher_courses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('teacher/uploadvideo.html', videos=my_videos, teacher_courses=teacher_courses)

@app.route('/teacher/delete-video/<int:video_id>', methods=['POST'])
def teacher_delete_video(video_id):
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify ownership before deleting
    cursor.execute("SELECT video_url FROM videos WHERE id = %s AND uploaded_by = %s", (video_id, teacher_id))
    video = cursor.fetchone()
    if video:
        video_url = video[0]
        # Delete file from system
        if video_url and video_url.startswith('/static/'):
            file_path = os.path.join(app.root_path, video_url.strip('/'))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
        conn.commit()
        flash("Video deleted successfully.", "success")
    else:
        flash("Unauthorized deletion attempt.", "danger")
        
    cursor.close()
    conn.close()
    return redirect(url_for('teacher_upload_video'))

@app.route('/teacher/delete-videos-bulk', methods=['POST'])
def teacher_delete_videos_bulk():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    video_ids = request.form.getlist('video_ids')
    
    if not video_ids:
        flash("No videos selected for deletion.", "warning")
        return redirect(url_for('teacher_upload_video'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch and delete each video file that belongs to this teacher
    format_strings = ','.join(['%s'] * len(video_ids))
    query = f"SELECT id, video_url FROM videos WHERE id IN ({format_strings}) AND uploaded_by = %s"
    
    cursor.execute(query, tuple(video_ids) + (teacher_id,))
    videos_to_delete = cursor.fetchall()
    
    deleted_count = 0
    if videos_to_delete:
        for vid in videos_to_delete:
            video_url = vid['video_url']
            if video_url and video_url.startswith('/static/'):
                file_path = os.path.join(app.root_path, video_url.strip('/'))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception:
                        pass
            cursor.execute("DELETE FROM videos WHERE id = %s", (vid['id'],))
            deleted_count += 1
            
        conn.commit()
        flash(f"Successfully deleted {deleted_count} video(s).", "success")
    else:
        flash("No valid videos found to delete or unauthorized attempt.", "danger")
        
    cursor.close()
    conn.close()
    return redirect(url_for('teacher_upload_video'))

@app.route('/teacher/live-classes', methods=['GET', 'POST'])
def teacher_live_classes():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'schedule':
            topic = request.form.get('topic')
            class_date = request.form.get('class_date')
            class_time = request.form.get('class_time')
            duration = request.form.get('duration')
            meeting_link = request.form.get('meeting_link')
            
            cursor.execute("""
                INSERT INTO live_classes (topic, class_date, class_time, duration, meeting_link, teacher_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (topic, class_date, class_time, duration, meeting_link, teacher_id))
            conn.commit()
            class_id = cursor.lastrowid
            cursor.execute("INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status) VALUES ('Class', %s, %s, 'New submission for review', 'low', 'pending')", (class_id, teacher_id))
            conn.commit()
            
            # Notify connected students
            cursor.execute("SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as student_id FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (teacher_id, teacher_id, teacher_id))
            students = cursor.fetchall()
            for stud in students:
                cursor.execute(
                    "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                    (stud['student_id'], f"New live class scheduled by {session['name']}: {topic} on {class_date} at {class_time}.")
                )
            conn.commit()
            flash("Live class scheduled successfully!", "success")
            
        elif action == 'add_recording':
            class_id = request.form.get('class_id')
            recording_link = request.form.get('recording_link')
            
            # Verify owner
            cursor.execute("SELECT id FROM live_classes WHERE id = %s AND teacher_id = %s", (class_id, teacher_id))
            if cursor.fetchone():
                cursor.execute("UPDATE live_classes SET recording_link = %s WHERE id = %s", (recording_link, class_id))
                conn.commit()
                flash("Recording link added successfully!", "success")
            else:
                flash("Unauthorized request.", "danger")
                
        return redirect(url_for('teacher_live_classes'))
        
    # Get scheduled live classes
    cursor.execute("SELECT * FROM live_classes WHERE teacher_id = %s ORDER BY class_date DESC, class_time DESC", (teacher_id,))
    live_classes = cursor.fetchall()
    
    # Get courses for dropdown
    cursor.execute("SELECT id, title FROM courses WHERE created_by = %s", (teacher_id,))
    teacher_courses = cursor.fetchall()
    
    from datetime import datetime
    now = datetime.now()
    
    upcoming_classes = []
    past_classes = []
    active_class = None
    
    for lc in live_classes:
        # Convert class_date and class_time to scheduled_at datetime for the template
        dt_str = f"{lc['class_date']} {lc['class_time']}"
        lc['scheduled_at'] = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        lc['title'] = lc['topic'] # Template uses 'title'
        
        # Determine if upcoming, past, or active
        if lc['scheduled_at'] > now:
            upcoming_classes.append(lc)
        else:
            past_classes.append(lc)
            
    cursor.close()
    conn.close()
    return render_template('teacher/teacher live classes.html', upcoming_classes=upcoming_classes, past_classes=past_classes, active_class=active_class, teacher_courses=teacher_courses)

@app.route('/teacher/live-classes/create', methods=['POST'])
def teacher_create_live_class():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    title = request.form.get('title')
    scheduled_at = request.form.get('scheduled_at') # YYYY-MM-DDTHH:MM
    duration = request.form.get('duration')
    description = request.form.get('description')
    course_id = request.form.get('course_id')
    if course_id == "":
        course_id = None
    
    if scheduled_at:
        date_part, time_part = scheduled_at.split('T')
    else:
        from datetime import datetime
        date_part = datetime.now().strftime('%Y-%m-%d')
        time_part = datetime.now().strftime('%H:%M:%S')
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO live_classes (topic, class_date, class_time, duration, meeting_link, teacher_id, course_id) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (title, date_part, time_part, duration, "Pending", teacher_id, course_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Live class scheduled successfully!", "success")
    return redirect(url_for('teacher_live_classes'))

@app.route('/teacher/live-classes/start-instant', methods=['POST'])
def teacher_start_instant_class():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    from datetime import datetime
    date_part = datetime.now().strftime('%Y-%m-%d')
    time_part = datetime.now().strftime('%H:%M:%S')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO live_classes (topic, class_date, class_time, duration, meeting_link, teacher_id) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, ("Instant Live Class", date_part, time_part, 60, "Pending", teacher_id))
    conn.commit()
    class_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return redirect(url_for('teacher_live_class', id=class_id))



@app.route('/teacher/quiz', methods=['GET', 'POST'])
def teacher_quiz():
    if not check_role(['teacher', 'admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_quiz':
            course_id = request.form.get('course_id')
            if not course_id:
                course_id = None
            title = request.form.get('title')
            
            cursor.execute("INSERT INTO quizzes (course_id, title, teacher_id) VALUES (%s, %s, %s)", (course_id, title, session['user_id']))
            conn.commit()
            flash("Quiz wrapper created! Now add questions.", "success")
            return redirect(url_for('teacher_quiz', active_quiz=cursor.lastrowid))
            
        elif action == 'add_question':
            quiz_id = request.form.get('quiz_id')
            question_text = request.form.get('question_text')
            option_a = request.form.get('option_a')
            option_b = request.form.get('option_b')
            option_c = request.form.get('option_c')
            option_d = request.form.get('option_d')
            correct_option = request.form.get('correct_option')
            explanation = request.form.get('explanation')
            
            cursor.execute("""
                INSERT INTO quiz_questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_option, explanation))
            conn.commit()
            flash("Question added to Quiz!", "success")
            return redirect(url_for('teacher_quiz', active_quiz=quiz_id))
            
    # Get courses
    cursor.execute("SELECT id, title FROM courses WHERE created_by = %s", (session['user_id'],))
    courses = cursor.fetchall()
    
    # Get all quizzes for this teacher
    cursor.execute("""
        SELECT qz.*, c.title as course_title, 
               (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = qz.id) as question_count
        FROM quizzes qz
        LEFT JOIN courses c ON qz.course_id = c.id
        WHERE qz.teacher_id = %s OR c.created_by = %s
        ORDER BY qz.created_at DESC
    """, (session['user_id'], session['user_id']))
    quizzes = cursor.fetchall()
    
    active_quiz_id = request.args.get('active_quiz')
    quiz_questions = []
    active_quiz = None
    if active_quiz_id:
        cursor.execute("SELECT * FROM quizzes WHERE id = %s", (active_quiz_id,))
        active_quiz = cursor.fetchone()
        cursor.execute("SELECT * FROM quiz_questions WHERE quiz_id = %s", (active_quiz_id,))
        quiz_questions = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return render_template('teacher/quiz.html', courses=courses, quizzes=quizzes, active_quiz_id=active_quiz_id, active_quiz=active_quiz, questions=quiz_questions)

@app.route('/teacher/qa', methods=['GET', 'POST'])
def teacher_qa():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        question_id = request.form.get('question_id')
        answer_text = request.form.get('answer_text')
        
        # Verify the question exists
        cursor.execute("SELECT student_id, question_text FROM questions WHERE id = %s", (question_id,))
        q = cursor.fetchone()
        if q:
            # Check duplicate answer by THIS teacher
            cursor.execute("SELECT id FROM answers WHERE question_id = %s AND teacher_id = %s", (question_id, teacher_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO answers (question_id, teacher_id, answer_text) VALUES (%s, %s, %s)", (question_id, teacher_id, answer_text))
            else:
                cursor.execute("UPDATE answers SET answer_text = %s WHERE question_id = %s AND teacher_id = %s", (answer_text, question_id, teacher_id))
            conn.commit()
            
            # Notify student
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (q['student_id'], f"Your connected teacher answered your question: '{q['question_text'][:30]}...'")
            )
            conn.commit()
            flash("Answer submitted successfully!", "success")
        else:
            flash("Unauthorized attempt to answer.", "danger")
        return redirect(url_for('teacher_qa'))
        
    # Get the teacher's subject
    cursor.execute("SELECT subject FROM teacher_profiles WHERE user_id = %s", (teacher_id,))
    t_prof = cursor.fetchone()
    teacher_subject = t_prof['subject'] if t_prof and t_prof['subject'] else ''
    
    questions = []
    pending_student_answers = []
    reviewed_student_answers = []
    
    if teacher_subject:
        # Get questions matching the teacher's subject
        cursor.execute("""
            SELECT q.id as question_id, q.question_text, q.subject, q.created_at, u.name as student_name,
                   a.answer_text, a.created_at as answered_at
            FROM questions q
            JOIN users u ON q.student_id = u.id
            LEFT JOIN answers a ON a.question_id = q.id AND a.teacher_id = %s
            WHERE q.subject = %s
            ORDER BY q.created_at DESC
        """, (teacher_id, teacher_subject))
        questions = cursor.fetchall()
        
        # Get pending student answers for this subject
        cursor.execute("""
            SELECT sa.id as student_answer_id, sa.answer_text, sa.created_at, su.name as student_name,
                   q.question_text, q.id as question_id, asking_student.name as asking_student_name
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            JOIN users su ON sa.student_id = su.id
            JOIN users asking_student ON q.student_id = asking_student.id
            WHERE q.subject = %s AND sa.status = 'pending'
            ORDER BY sa.created_at DESC
        """, (teacher_subject,))
        pending_student_answers = cursor.fetchall()
        
        # Get reviewed student answers for this subject
        cursor.execute("""
            SELECT sa.id as student_answer_id, sa.answer_text, sa.created_at, su.name as student_name,
                   q.question_text, q.id as question_id, asking_student.name as asking_student_name,
                   sa.status, sa.rejection_reason
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            JOIN users su ON sa.student_id = su.id
            JOIN users asking_student ON q.student_id = asking_student.id
            WHERE q.subject = %s AND sa.status != 'pending'
            ORDER BY sa.created_at DESC
        """, (teacher_subject,))
        reviewed_student_answers = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return render_template('teacher/answer_q&a.html', questions=questions, pending_student_answers=pending_student_answers, reviewed_student_answers=reviewed_student_answers, teacher_subject=teacher_subject)

@app.route('/teacher/qa/approve/<int:answer_id>', methods=['POST'])
def teacher_qa_approve(answer_id):
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE student_answers SET status = 'approved' WHERE id = %s", (answer_id,))
    conn.commit()
    
    cursor.execute("SELECT student_id FROM student_answers WHERE id = %s", (answer_id,))
    sa = cursor.fetchone()
    if sa:
        cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (sa[0], "Your answer was approved by the teacher!"))
        conn.commit()
        
    cursor.close()
    conn.close()
    flash("Student answer approved.", "success")
    return redirect(url_for('teacher_qa'))

@app.route('/teacher/qa/reject', methods=['POST'])
def teacher_qa_reject():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    answer_id = request.form.get('answer_id')
    reason = request.form.get('reason', '').strip()
    
    # Rejection reason is mandatory
    if not reason:
        flash("Rejection reason is required. Please explain why you are rejecting this answer.", "warning")
        return redirect(url_for('teacher_qa'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE student_answers SET status = 'rejected', rejection_reason = %s WHERE id = %s", (reason, answer_id))
    conn.commit()
    
    cursor.execute("SELECT student_id FROM student_answers WHERE id = %s", (answer_id,))
    sa = cursor.fetchone()
    if sa:
        cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (sa[0], f"Your answer was rejected by the teacher. Reason: {reason}"))
        conn.commit()
        
    cursor.close()
    conn.close()
    flash("Student answer rejected. The student has been notified with your reason.", "danger")
    return redirect(url_for('teacher_qa'))

@app.route('/teacher/qa/undo-reject', methods=['POST'])
def teacher_qa_undo_reject():
    """Allow teacher to undo an accidental rejection and move answer back to pending."""
    if not check_role(['teacher']):
        return redirect(url_for('login'))
    
    answer_id = request.form.get('answer_id')
    teacher_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Verify the answer belongs to a question of this teacher
    cursor.execute("""
        SELECT sa.id, sa.student_id, q.question_text
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.id
        WHERE sa.id = %s AND q.teacher_id = %s AND sa.status = 'rejected'
    """, (answer_id, teacher_id))
    sa = cursor.fetchone()
    
    if sa:
        cursor.execute(
            "UPDATE student_answers SET status = 'pending', rejection_reason = NULL WHERE id = %s",
            (answer_id,)
        )
        conn.commit()
        # Notify the student that their answer is back under review
        cursor.execute(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (sa['student_id'], f"Good news! The teacher has reconsidered your answer to: '{sa['question_text'][:40]}...' — it is now back under review.")
        )
        conn.commit()
        flash("Rejection undone. The student's answer is back to Pending review.", "success")
    else:
        flash("Could not undo rejection. The answer may not be yours or is not in a rejected state.", "danger")
    
    cursor.close()
    conn.close()
    return redirect(url_for('teacher_qa'))

@app.route('/teacher/connections', methods=['GET', 'POST'])
def teacher_connections():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_request':
            # Teacher sending request to another user
            receiver_id = request.form.get('teacher_id') # Form uses teacher_id for the target user
            cursor.execute("SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))", (teacher_id, receiver_id, receiver_id, teacher_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO connections (sender_id, receiver_id, status) VALUES (%s, %s, 'pending')", (teacher_id, receiver_id))
                conn.commit()
                # Notify receiver
                cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", 
                               (receiver_id, f"You have a new connection request from Teacher: {session['name']}."))
                conn.commit()
                flash("Connection request sent successfully!", "success")
            else:
                flash("Request already sent or connection exists.", "warning")
        else:
            # Accepting or rejecting a request
            request_id = request.form.get('request_id')
            new_status = request.form.get('status') # 'accepted' or 'rejected'
            
            # Verify request exists
            cursor.execute("SELECT sender_id as student_id FROM connections WHERE id = %s AND receiver_id = %s", (request_id, teacher_id))
            req = cursor.fetchone()
            if req:
                cursor.execute("UPDATE connections SET status = %s WHERE id = %s", (new_status, request_id))
                conn.commit()
                
                # Notify sender
                cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", 
                               (req['student_id'], f"Your connection request to teacher {session['name']} has been {new_status}."))
                conn.commit()
                flash(f"Connection request {new_status} successfully!", "success")
            else:
                flash("Connection request not found.", "danger")
        
        return redirect(url_for('teacher_connections'))
        
    # Get connection requests (both pending and accepted)
    cursor.execute("""
        SELECT cr.id as request_id, cr.status, cr.created_at, u.id as sender_id, u.name, u.email, u.role
        FROM connections cr 
        JOIN users u ON cr.sender_id = u.id 
        LEFT JOIN student_profiles sp ON u.id = sp.user_id 
        WHERE cr.receiver_id = %s AND cr.status = 'pending'
        ORDER BY cr.created_at DESC
    """, (teacher_id,))
    requests_list = cursor.fetchall()
    
    # Get all other teachers
    cursor.execute("""
        SELECT DISTINCT u.id as teacher_id, u.name, u.email, tp.subject, tp.experience,
               c.status as connection_status
        FROM users u 
        LEFT JOIN teacher_profiles tp ON u.id = tp.user_id 
        LEFT JOIN connections c ON (c.receiver_id = u.id AND c.sender_id = %s) OR (c.sender_id = u.id AND c.receiver_id = %s)
        WHERE u.id != %s AND u.role = 'teacher' AND u.status = 'approved'
    """, (teacher_id, teacher_id, teacher_id))
    teachers = cursor.fetchall()

    # Get all approved students
    cursor.execute("""
        SELECT DISTINCT u.id as student_id, u.name, u.email, sp.class_level, sp.stream,
               c.status as connection_status
        FROM users u
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        LEFT JOIN connections c ON (c.receiver_id = u.id AND c.sender_id = %s) OR (c.sender_id = u.id AND c.receiver_id = %s)
        WHERE u.role = 'student' AND u.status = 'approved' AND u.id != %s
    """, (teacher_id, teacher_id, teacher_id))
    students = cursor.fetchall()
    
    # Get total connections count
    cursor.execute("SELECT COUNT(*) as count FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (teacher_id, teacher_id))
    connections_count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    return render_template('teacher/findpeople(T).html', requests=requests_list, teachers=teachers, students=students, connections_count=connections_count)

@app.route('/teacher/chat', methods=['GET', 'POST'])
def teacher_chat():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        receiver_id = request.form.get('receiver_id')
        message = request.form.get('message')
        
        if not receiver_id or not receiver_id.isdigit():
            flash("Invalid user selected.", "danger")
            return redirect(url_for('teacher_chat'))
            
        # Verify connection
        cursor.execute("SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)) AND status = 'accepted'", (teacher_id, receiver_id, receiver_id, teacher_id))
        if cursor.fetchone():
            cursor.execute("INSERT INTO chats (sender_id, receiver_id, message) VALUES (%s, %s, %s)", (teacher_id, receiver_id, message))
            conn.commit()
            return redirect(url_for('teacher_chat', active_chat=receiver_id))
        else:
            flash("You can only chat with connected members.", "danger")
            return redirect(url_for('teacher_chat'))
            
    # Load all connected users with unread message counts
    cursor.execute("""
        SELECT u.id as user_id, u.name, u.role,
               (SELECT COUNT(*) FROM chats WHERE sender_id = u.id AND receiver_id = %s AND is_read = FALSE AND deleted_by_receiver = FALSE) as unread_count
        FROM users u 
        WHERE u.id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
    """, (teacher_id, teacher_id, teacher_id))
    connected_users = cursor.fetchall()
    
    # Load chat history if active_chat is specified
    active_chat_id = request.args.get('active_chat')
    if active_chat_id and not active_chat_id.isdigit():
        active_chat_id = None
        
    messages = []
    active_user = None
    if active_chat_id:
        cursor.execute("SELECT name, role FROM users WHERE id = %s", (active_chat_id,))
        active_user = cursor.fetchone()
        if active_user:
            # Mark messages as read
            cursor.execute("UPDATE chats SET is_read = TRUE WHERE sender_id = %s AND receiver_id = %s", (active_chat_id, teacher_id))
            conn.commit()
            
            cursor.execute("""
                SELECT * FROM chats 
                WHERE (sender_id = %s AND receiver_id = %s AND deleted_by_sender = FALSE) 
                   OR (sender_id = %s AND receiver_id = %s AND deleted_by_receiver = FALSE)
                ORDER BY created_at ASC
            """, (teacher_id, active_chat_id, active_chat_id, teacher_id))
            messages = cursor.fetchall()
            
    cursor.close()
    conn.close()
    return render_template('teacher/chat(T).html', connected_users=connected_users, messages=messages, active_user=active_user, active_chat_id=active_chat_id)

@app.route('/teacher/post-notification', methods=['GET', 'POST'])
def teacher_post_notification():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    
    if request.method == 'POST':
        message = request.form.get('message')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Get all connected students
        cursor.execute("SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as student_id FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'", (teacher_id, teacher_id, teacher_id))
        students = cursor.fetchall()
        for stud in students:
            cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", 
                           (stud['student_id'], f"Announcement from {session['name']}: {message}"))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Notification posted to all connected students!", "success")
        return redirect(url_for('teacher_post_notification'))
        
    return render_template('teacher/post_notification.html')

@app.route('/teacher/notifications')
def teacher_notifications():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Mark all as read
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (teacher_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (teacher_id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher/notification(t).html', notifications=notifications)

@app.route('/teacher/profile', methods=['GET', 'POST'])
def teacher_profile():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        subject = request.form.get('subject')
        experience = request.form.get('experience')
        
        cursor.execute("""
            UPDATE users SET name = %s, phone = %s, age = %s, gender = %s 
            WHERE id = %s
        """, (name, phone, age, gender, teacher_id))
        cursor.execute("""
            UPDATE teacher_profiles SET subject = %s, experience = %s 
            WHERE user_id = %s
        """, (subject, experience, teacher_id))
        conn.commit()
        session['name'] = name
        flash("Profile updated successfully!", "success")
        return redirect(url_for('teacher_profile'))
        
    cursor.execute("""
        SELECT u.*, tp.subject, tp.experience, tp.teacher_id_code, tp.resume_url 
        FROM users u 
        JOIN teacher_profiles tp ON u.id = tp.user_id 
        WHERE u.id = %s
    """, (teacher_id,))
    user = cursor.fetchone()
    
    # Stats
    cursor.execute("""
        SELECT COUNT(DISTINCT e.student_id) as total_students
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        WHERE c.created_by = %s
    """, (teacher_id,))
    r = cursor.fetchone()
    total_students = r['total_students'] if r else 0
    
    cursor.execute("SELECT COUNT(*) as cnt FROM courses WHERE created_by = %s", (teacher_id,))
    total_courses = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM videos WHERE uploaded_by = %s", (teacher_id,))
    total_videos = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM materials WHERE uploaded_by = %s", (teacher_id,))
    total_materials = cursor.fetchone()['cnt']
    
    stats = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_videos': total_videos,
        'total_materials': total_materials
    }
    
    # Courses with student count
    cursor.execute("""
        SELECT c.title, COUNT(e.id) as student_count
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        WHERE c.created_by = %s
        GROUP BY c.id, c.title
        ORDER BY student_count DESC
    """, (teacher_id,))
    courses = cursor.fetchall()
    
    # 1. Students list (unique students enrolled in teacher's courses)
    cursor.execute("""
        SELECT DISTINCT u.name
        FROM enrollments e
        JOIN courses c ON e.course_id = c.id
        JOIN users u ON e.student_id = u.id
        WHERE c.created_by = %s
    """, (teacher_id,))
    students_list = [row['name'] for row in cursor.fetchall()]

    # 2. Courses list
    cursor.execute("""
        SELECT title
        FROM courses
        WHERE created_by = %s
    """, (teacher_id,))
    courses_list = [row['title'] for row in cursor.fetchall()]

    # 3. Videos list
    cursor.execute("""
        SELECT title
        FROM videos
        WHERE uploaded_by = %s
    """, (teacher_id,))
    videos_list = [row['title'] for row in cursor.fetchall()]
    
    # 4. Reviews for this teacher
    cursor.execute("""
        SELECT tr.rating, tr.review_text, tr.created_at, u.name as student_name
        FROM teacher_reviews tr
        JOIN users u ON tr.student_id = u.id
        WHERE tr.teacher_id = %s
        ORDER BY tr.created_at DESC
    """, (teacher_id,))
    reviews = cursor.fetchall()
    avg_rating = round(sum(r['rating'] for r in reviews) / len(reviews), 1) if reviews else 0.0

    cursor.close()
    conn.close()
    
    import json
    return render_template('teacher/teacherprofile.html', 
                           user=user, 
                           stats=stats, 
                           courses=courses,
                           students_json=json.dumps(students_list),
                           courses_json=json.dumps(courses_list),
                           videos_json=json.dumps(videos_list),
                           reviews=reviews,
                           avg_rating=avg_rating)


# ----------------- ADMIN PORTAL ROUTES -----------------

@app.route('/admin/dashboard')
def admin_dashboard():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Total users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    # 2. Total students
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()['count']
    
    # 3. Total teachers
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'")
    total_teachers = cursor.fetchone()['count']
    
    # 4. Pending teacher approvals
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher' AND status = 'pending'")
    pending_approvals_count = cursor.fetchone()['count']
    
    # 5. Total courses
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    total_courses = cursor.fetchone()['count']
    
    # 6. Total materials
    cursor.execute("SELECT COUNT(*) as count FROM materials")
    total_materials = cursor.fetchone()['count']
    
    # 7. Total videos
    cursor.execute("SELECT COUNT(*) as count FROM videos")
    total_videos = cursor.fetchone()['count']
    
    # 8. Contact messages count
    cursor.execute("SELECT COUNT(*) as count FROM contact_messages")
    total_contact_messages = cursor.fetchone()['count']
    
    # 9. Live Classes today
    from datetime import datetime, timedelta
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT lc.id, lc.topic, lc.class_time, lc.duration, lc.status as db_status, u.name as teacher_name
        FROM live_classes lc
        JOIN users u ON lc.teacher_id = u.id
        WHERE lc.class_date = %s
    """, (today_str,))
    live_classes_today = cursor.fetchall()
    
    for lc in live_classes_today:
        if lc.get('db_status') == 'ended':
            lc['status'] = 'Ended'
        else:
            class_time_delta = lc.get('class_time')
            if class_time_delta:
                try:
                    # mysql.connector usually returns timedelta for TIME columns
                    total_seconds = class_time_delta.total_seconds()
                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    start_dt = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
                    end_dt = start_dt + timedelta(minutes=int(lc['duration']))
                    
                    if start_dt <= now <= end_dt:
                        lc['status'] = 'LIVE'
                    elif now < start_dt:
                        lc['status'] = 'Upcoming'
                    else:
                        lc['status'] = 'Ended'
                except Exception:
                    lc['status'] = 'Unknown'
            else:
                lc['status'] = 'Unknown'
                
        lc['class_time'] = str(lc['class_time'])
        
    active_live_classes_count = sum(1 for lc in live_classes_today if lc.get('status') == 'LIVE')
    
    import json
    live_classes_json = json.dumps(live_classes_today)
    
    # Pending teachers list
    cursor.execute("""
        SELECT u.*, tp.subject, tp.experience, tp.teacher_id_code, tp.resume_url 
        FROM users u 
        JOIN teacher_profiles tp ON u.id = tp.user_id 
        WHERE u.role = 'teacher' AND u.status = 'pending'
    """)
    pending_teachers = cursor.fetchall()
    
    # Pending courses list
    cursor.execute("""
        SELECT c.id, c.title, u.name as teacher_name, c.created_at
        FROM courses c
        JOIN users u ON c.created_by = u.id
        WHERE c.status = 'pending'
        ORDER BY c.created_at DESC
    """)
    pending_courses = cursor.fetchall()
    
    # Course payments
    cursor.execute("""
        SELECT cp.id, cp.amount, cp.screenshot_path, cp.status, cp.submitted_at,
               u.name as student_name, c.title as course_title
        FROM course_payments cp
        JOIN users u ON cp.student_id = u.id
        JOIN courses c ON cp.course_id = c.id
        WHERE cp.status = 'pending'
        ORDER BY cp.submitted_at DESC
    """)
    db_pending_payments = cursor.fetchall()
    pending_payments = []
    for p in db_pending_payments:
        pending_payments.append({
            'id': p['id'],
            'amount': float(p['amount']),
            'screenshot_path': os.path.basename(p['screenshot_path']),
            'status': p['status'],
            'submitted_at': str(p['submitted_at']),
            'student': {'name': p['student_name']},
            'course': {'title': p['course_title']}
        })
        
    # Pending event payments
    cursor.execute("""
        SELECT er.id, er.paid_amount, er.payment_status, er.registered_at,
               er.first_name, er.last_name, e.title as event_title, er.payment_screenshot
        FROM event_registrations er
        JOIN events e ON er.event_id = e.id
        WHERE er.payment_status = 'pending'
    """)
    db_pending_events = cursor.fetchall()
    for p in db_pending_events:
        pending_payments.append({
            'id': f"evt_{p['id']}",
            'amount': float(p['paid_amount']),
            'screenshot_path': os.path.basename(p['payment_screenshot']) if p['payment_screenshot'] else '',
            'status': p['payment_status'],
            'submitted_at': str(p['registered_at']),
            'student': {'name': f"{p['first_name']} {p['last_name']}"},
            'course': {'title': f"Event: {p['event_title']}"}
        })
        
    pending_payments.sort(key=lambda x: x['submitted_at'], reverse=True)
        
    cursor.execute("""
        SELECT cp.id, cp.amount, cp.screenshot_path, cp.status, cp.submitted_at,
               u.name as student_name, c.title as course_title
        FROM course_payments cp
        JOIN users u ON cp.student_id = u.id
        JOIN courses c ON cp.course_id = c.id
        ORDER BY cp.submitted_at DESC
    """)
    db_all_payments = cursor.fetchall()
    all_payments = []
    for p in db_all_payments:
        all_payments.append({
            'id': p['id'],
            'amount': float(p['amount']),
            'screenshot_path': os.path.basename(p['screenshot_path']) if p['screenshot_path'] else '',
            'status': p['status'],
            'submitted_at': str(p['submitted_at']),
            'student': {'name': p['student_name']},
            'course': {'title': p['course_title']}
        })
        
    cursor.execute("""
        SELECT er.id, er.paid_amount, er.payment_status, er.registered_at,
               er.first_name, er.last_name, e.title as event_title, er.payment_screenshot
        FROM event_registrations er
        JOIN events e ON er.event_id = e.id
        WHERE er.paid_amount > 0
    """)
    db_event_payments = cursor.fetchall()
    for p in db_event_payments:
        all_payments.append({
            'id': f"evt_{p['id']}",
            'amount': float(p['paid_amount']),
            'screenshot_path': os.path.basename(p['payment_screenshot']) if p['payment_screenshot'] else '',
            'status': 'approved' if p['payment_status'] == 'paid' else p['payment_status'],
            'submitted_at': str(p['registered_at']),
            'student': {'name': f"{p['first_name']} {p['last_name']}"},
            'course': {'title': f"Event: {p['event_title']}"}
        })

        
    all_payments.sort(key=lambda x: x['submitted_at'], reverse=True)
        
    total_payments = len(all_payments)
    
    # JSON serializations
    import json
    
    cursor.execute("""
        SELECT c.id, c.title, u.name as teacher_name,
               (SELECT COUNT(*) FROM videos WHERE course_id = c.id) as video_count
        FROM courses c
        JOIN users u ON c.created_by = u.id
    """)
    courses_db = cursor.fetchall()
    courses_list = []
    for c in courses_db:
        courses_list.append({
            'id': c['id'],
            'title': c['title'],
            'teacher_name': c['teacher_name'],
            'video_count': c['video_count']
        })
    courses_json = json.dumps(courses_list)
    
    cursor.execute("""
        SELECT v.id, v.title, v.video_url, c.title as course_title, u.name as teacher_name
        FROM videos v
        LEFT JOIN courses c ON v.course_id = c.id
        JOIN users u ON v.uploaded_by = u.id
        WHERE v.course_id IS NULL
    """)
    videos_db = cursor.fetchall()
    videos_list = []
    for v in videos_db:
        videos_list.append({
            'id': v['id'],
            'title': v['title'],
            'video_url': v['video_url'],
            'course_title': v['course_title'] if v['course_title'] else 'N/A',
            'teacher_name': v['teacher_name']
        })
    videos_json = json.dumps(videos_list)
    
    cursor.execute("""
        SELECT m.id, m.title, m.file_url, c.title as course_title, u.name as teacher_name
        FROM materials m
        LEFT JOIN courses c ON m.course_id = c.id
        JOIN users u ON m.uploaded_by = u.id
    """)
    materials_db = cursor.fetchall()
    materials_list = []
    for m in materials_db:
        file_path = m['file_url']
        if file_path.startswith('/static/'):
            file_path = file_path[8:]
        materials_list.append({
            'id': m['id'],
            'title': m['title'],
            'file_path': file_path,
            'course_title': m['course_title'] if m['course_title'] else 'N/A',
            'teacher_name': m['teacher_name']
        })
    materials_json = json.dumps(materials_list)
    
    payments_list = []
    for p in all_payments:
        scr_path = p['screenshot_path']
        if scr_path.startswith('/static/'):
            scr_path = scr_path[8:]
        payments_list.append({
            'id': p['id'],
            'student_name': p['student']['name'],
            'course_title': p['course']['title'],
            'amount': float(p['amount']),
            'status': p['status'],
            'submitted_at': p['submitted_at'],
            'screenshot_path': scr_path
        })
    payments_json = json.dumps(payments_list)
    
    cursor.close()
    conn.close()
    
    return render_template(
        'admin/admindashboard.html',
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        pending_approvals_count=pending_approvals_count,
        total_courses=total_courses,
        total_materials=total_materials,
        total_videos=total_videos,
        total_contact_messages=total_contact_messages,
        pending_teachers=pending_teachers,
        pending_payments=pending_payments,
        pending_courses=pending_courses,
        all_payments=all_payments,
        total_payments=total_payments,
        courses_json=courses_json,
        videos_json=videos_json,
        materials_json=materials_json,
        payments_json=payments_json,
        live_classes_today=live_classes_today,
        live_classes_json=live_classes_json,
        active_live_classes_count=active_live_classes_count
    )

@app.route('/admin/live-classes/end/<int:class_id>', methods=['POST'])
def admin_end_live_class(class_id):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE live_classes SET status = 'ended' WHERE id = %s", (class_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Class ended successfully'})

@app.route('/admin/controlpanel')
def admin_controlpanel():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    return render_template('admin/controlpanel.html')

# ----------------- ADMIN TEACHER PERFORMANCE -----------------
@app.route('/admin/teacher-performance')
def admin_teacher_performance():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get all approved teachers
    cursor.execute("""
        SELECT u.id, u.name, u.email, tp.subject, tp.experience 
        FROM users u 
        JOIN teacher_profiles tp ON u.id = tp.user_id 
        WHERE u.role = 'teacher' AND u.status = 'approved'
    """)
    teachers = cursor.fetchall()
    
    for t in teachers:
        # 1. Total Courses
        cursor.execute("SELECT COUNT(*) as count FROM courses WHERE created_by = %s", (t['id'],))
        t['total_courses'] = cursor.fetchone()['count']
        
        # 2. Total Students enrolled in their courses
        cursor.execute("""
            SELECT COUNT(e.id) as count 
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id
            WHERE c.created_by = %s
        """, (t['id'],))
        t['total_students'] = cursor.fetchone()['count']
        
        # 3. Total Earnings
        cursor.execute("SELECT SUM(amount) as total FROM teacher_earnings WHERE teacher_id = %s", (t['id'],))
        res = cursor.fetchone()
        t['total_earnings'] = float(res['total']) if res and res['total'] else 0.0
        
    cursor.close()
    conn.close()
    return render_template('admin/teacher_performance.html', teachers=teachers)

@app.route('/admin/assign-earning', methods=['POST'])
def admin_assign_earning():
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    teacher_id = request.form.get('teacher_id')
    amount = request.form.get('amount')
    reason = request.form.get('reason', 'Performance Bonus')
    
    if not teacher_id or not amount:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    try:
        amount_val = float(amount)
        if amount_val <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount format'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO teacher_earnings (teacher_id, amount, reason)
        VALUES (%s, %s, %s)
    """, (teacher_id, amount_val, reason))
    conn.commit()
    
    # Notify teacher
    cursor.execute(
        "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
        (teacher_id, f"You have received a payout of ₹{amount_val:.2f} for {reason}.")
    )
    conn.commit()
    
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': f'Successfully assigned ₹{amount_val:.2f} to teacher.'})

@app.route('/admin/withdrawals')
def admin_withdrawals():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT w.*, u.name as teacher_name, u.email as teacher_email 
        FROM withdrawal_requests w
        JOIN users u ON w.teacher_id = u.id
        ORDER BY w.created_at DESC
    """)
    withdrawals = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/withdrawals.html', withdrawals=withdrawals)

@app.route('/admin/withdraw/<string:action>/<int:req_id>', methods=['POST'])
def admin_withdraw_action(action, req_id):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    if action not in ['approve', 'reject']:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get request
    cursor.execute("SELECT * FROM withdrawal_requests WHERE id = %s", (req_id,))
    req = cursor.fetchone()
    
    if not req:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Request not found'}), 404
        
    if req['status'] != 'pending':
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Request already processed'}), 400
        
    new_status = 'approved' if action == 'approve' else 'rejected'
    
    cursor.execute("UPDATE withdrawal_requests SET status = %s WHERE id = %s", (new_status, req_id))
    
    if new_status == 'approved':
        # Deduct from earnings balance by adding a negative earning transaction
        cursor.execute("""
            INSERT INTO teacher_earnings (teacher_id, amount, reason) 
            VALUES (%s, %s, %s)
        """, (req['teacher_id'], -float(req['amount']), f"Withdrawal Approved (Req #{req_id})"))
        
        # Notify teacher
        msg = f"Your withdrawal request for ₹{req['amount']:.2f} has been approved and processed."
    else:
        msg = f"Your withdrawal request for ₹{req['amount']:.2f} has been rejected."
        
    cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (req['teacher_id'], msg))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': f'Withdrawal request {new_status} successfully.'})

@app.route('/admin/analytics')
def admin_analytics():
    if not check_role(['admin']):
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM enrollments")
    total_enrollments = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM enrollments WHERE completed = 1")
    completed_enrollments = cursor.fetchone()['count']
    completion_rate = round((completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0, 1)
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM enrollments 
        WHERE MONTH(enrolled_at) = MONTH(CURDATE()) AND YEAR(enrolled_at) = YEAR(CURDATE())
    """)
    new_enrollments = cursor.fetchone()['count']
    
    # Top performing courses (most enrolled)
    cursor.execute("""
        SELECT c.title, COUNT(e.id) as student_count
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        GROUP BY c.id, c.title
        ORDER BY student_count DESC
        LIMIT 5
    """)
    db_top_courses = cursor.fetchall()
    top_courses = []
    for c in db_top_courses:
        top_courses.append({
            'title': c['title'],
            'student_count': c['student_count'],
            'completion_rate': 78,
            'rating': 4.8
        })
        
    # Top performing teachers (most connected students)
    cursor.execute("""
        SELECT u.name, COUNT(DISTINCT c.id) as course_count,
               COUNT(DISTINCT e.student_id) as student_count
        FROM users u
        LEFT JOIN courses c ON c.created_by = u.id
        LEFT JOIN enrollments e ON e.course_id = c.id
        WHERE u.role = 'teacher' AND u.status = 'approved'
        GROUP BY u.id, u.name
        ORDER BY student_count DESC
        LIMIT 5
    """)
    db_top_teachers = cursor.fetchall()
    top_teachers = []
    for t in db_top_teachers:
        top_teachers.append({
            'name': t['name'],
            'course_count': t['course_count'],
            'student_count': t['student_count'],
            'rating': 4.9
        })
        
    cursor.close()
    conn.close()
    
    # Process for template variable names
    daily_active_users = int(total_users * 0.45) if total_users > 0 else 12
    course_completion_rate = f"{completion_rate}%"
    avg_watch_time = "4.2 hrs"
    
    import random
    user_activity_heights = [random.randint(20, 95) for _ in range(30)]
    
    return render_template('admin/analytics.html',
        daily_active_users=daily_active_users,
        course_completion_rate=course_completion_rate,
        avg_watch_time=avg_watch_time,
        new_enrollments=new_enrollments,
        user_activity_heights=user_activity_heights,
        top_courses=top_courses,
        top_teachers=top_teachers
    )

@app.route('/admin/events')
def admin_event():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Fetch active (approved) events with registrant count & revenue stats
    cursor.execute("""
        SELECT e.*, u.name as teacher_name 
        FROM events e 
        LEFT JOIN users u ON e.created_by = u.id
        WHERE e.status = 'approved' ORDER BY e.event_date ASC
    """)
    db_active = cursor.fetchall()
    
    events_with_stats = []
    for e in db_active:
        event_id = e['id']
        
        # Registrations count
        cursor.execute("SELECT COUNT(*) as count FROM event_registrations WHERE event_id = %s", (event_id,))
        reg_count = cursor.fetchone()['count']
        
        # Total Revenue (sum of paid_amount)
        cursor.execute("SELECT SUM(paid_amount) as rev FROM event_registrations WHERE event_id = %s", (event_id,))
        rev_row = cursor.fetchone()
        total_revenue = float(rev_row['rev'] or 0.0)
        
        events_with_stats.append({
            'event': e,
            'reg_count': reg_count,
            'total_revenue': total_revenue
        })
        
    # 2. Fetch pending events with teacher name
    cursor.execute("""
        SELECT e.*, u.name as teacher_name 
        FROM events e 
        LEFT JOIN users u ON e.created_by = u.id
        WHERE e.status = 'pending' ORDER BY e.created_at DESC
    """)
    pending_events = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/events.html', 
        events_with_stats=events_with_stats,
        pending_events=pending_events
    )

@app.route('/admin/event/approve/<int:event_id>', methods=['POST'])
def admin_approve_event(event_id):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    
    data = request.get_json() if request.is_json else request.form
    new_price = data.get('new_price')
    
    if new_price is not None:
        try:
            price_val = float(new_price)
            cursor.execute("UPDATE events SET status = 'approved', price = %s WHERE id = %s", (price_val, event_id))
        except ValueError:
            cursor.execute("UPDATE events SET status = 'approved' WHERE id = %s", (event_id,))
    else:
        cursor.execute("UPDATE events SET status = 'approved' WHERE id = %s", (event_id,))
        
    conn.commit()
    
    # Fetch creator ID to send a notification
    cursor.execute("SELECT created_by, title FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    if event:
        cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (event[0], f"Your event '{event[1]}' has been approved by admin!"))
        conn.commit()
        
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Event approved successfully.'})

@app.route('/admin/event/reject/<int:event_id>', methods=['POST'])
def admin_reject_event(event_id):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch creator ID to send a notification (before deleting)
    cursor.execute("SELECT created_by, title FROM events WHERE id = %s", (event_id,))
    event = cursor.fetchone()
    
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()
    
    if event:
        cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (event[0], f"Your event request '{event[1]}' was rejected/deleted by admin."))
        conn.commit()
        
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': 'Event rejected and deleted successfully.'})

@app.route('/admin/event/registrations/<int:event_id>', methods=['GET'])
def admin_event_registrations(event_id):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT first_name, last_name, email, phone, college, department, year_of_study, team_name, why_join, payment_method, payment_status, paid_amount, registered_at
        FROM event_registrations
        WHERE event_id = %s
        ORDER BY registered_at DESC
    """, (event_id,))
    registrations = cursor.fetchall()
    
    # Format registered_at date string
    for r in registrations:
        r['registered_at'] = r['registered_at'].strftime('%Y-%m-%d %H:%M') if isinstance(r['registered_at'], datetime) else str(r['registered_at'])
        r['paid_amount'] = float(r['paid_amount'])
        
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'registrations': registrations})

@app.route('/admin/upload-material', methods=['GET', 'POST'])
def admin_upload_material():
    if not check_role(['admin']):
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        course_id = request.form.get('course_id')
        file = request.files.get('file')
        file_url = ''
        if file and file.filename != '':
            filename = f"material_{int(time.time())}_{file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'materials', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            file_url = f"/static/uploads/materials/{filename}"
        cursor.execute(
            "INSERT INTO materials (title, description, course_id, file_url, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
            (title, description, course_id, file_url, session['user_id'])
        )
        conn.commit()
        flash("Material uploaded successfully!", "success")
        return redirect(url_for('admin_upload_material'))
    cursor.execute("SELECT * FROM materials ORDER BY created_at DESC")
    materials = cursor.fetchall()
    cursor.execute("SELECT id, title FROM courses ORDER BY title")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/addmeterial.html', materials=materials, courses=courses)

@app.route('/admin/upload-video', methods=['GET', 'POST'])
def admin_upload_video():
    if not check_role(['admin']):
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        course_id = request.form.get('course_id')
        video_url = request.form.get('video_url', '')
        file = request.files.get('video_file')
        if file and file.filename != '':
            filename = f"video_{int(time.time())}_{file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            file.save(save_path)
            video_url = f"/static/uploads/videos/{filename}"
        cursor.execute(
            "INSERT INTO videos (title, description, course_id, video_url, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
            (title, description, course_id, video_url, session['user_id'])
        )
        conn.commit()
        flash("Video uploaded successfully!", "success")
        return redirect(url_for('admin_upload_video'))
    cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
    videos = cursor.fetchall()
    cursor.execute("SELECT id, title FROM courses ORDER BY title")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/addviedo.html', videos=videos, courses=courses)

@app.route('/admin/post-notification', methods=['GET', 'POST'])
def admin_post_notification():
    if not check_role(['admin']):
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        message = request.form.get('message')
        target = request.form.get('target', 'all')  # 'all', 'student', 'teacher'
        if target == 'all':
            cursor.execute("SELECT id FROM users WHERE role IN ('student','teacher')")
        else:
            cursor.execute("SELECT id FROM users WHERE role = %s", (target,))
        users = cursor.fetchall()
        for u in users:
            cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (u['id'], message))
        conn.commit()
        flash(f"Notification sent to {len(users)} user(s)!", "success")
        return redirect(url_for('admin_post_notification'))
    cursor.close()
    conn.close()
    return render_template('admin/post.html')

@app.route('/admin/approve-teacher/<int:teacher_id>', methods=['POST'])
def admin_approve_teacher(teacher_id):
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    action = request.form.get('action') # 'approve' or 'reject'
    status = 'approved' if action == 'approve' else 'rejected'
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = %s WHERE id = %s AND role = 'teacher'", (status, teacher_id))
    conn.commit()
    
    # Notify teacher of the status update
    cursor.execute(
        "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
        (teacher_id, f"Your registration status has been updated to: {status}.")
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    flash(f"Teacher registration has been {status}!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/courses', methods=['GET', 'POST'])
def admin_courses():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Create course
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        price_type = request.form.get('price_type')
        price = request.form.get('price') if price_type == 'paid' else 0.00
        
        file = request.files.get('cover_image')
        cover_image_url = '/static/images/course_default.jpg'
        if file and file.filename != '':
            filename = f"course_{int(time.time())}_{file.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'courses', filename)
            file.save(save_path)
            cover_image_url = f"/static/uploads/courses/{filename}"
            
        cursor.execute("""
            INSERT INTO courses (title, description, category, cover_image_url, price_type, price, created_by, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'approved')
        """, (title, description, category, cover_image_url, price_type, price, session['user_id']))
        conn.commit()
        flash("Course created successfully!", "success")
        return redirect(url_for('admin_courses'))
        
    cursor.execute("""
        SELECT c.*, u.name as creator_name 
        FROM courses c 
        JOIN users u ON c.created_by = u.id
    """)
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/addcourse.html', courses=courses)

@app.route('/admin/review-course/<int:course_id>', methods=['POST'])
def admin_review_course(course_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
        
    action = request.form.get('action') # 'approve', 'reject', 'update'
    
    conn = get_db()
    cursor = conn.cursor()
    
    if action == 'reject':
        cursor.execute("UPDATE courses SET status = 'rejected' WHERE id = %s", (course_id,))
        conn.commit()
        flash("Course rejected.", "warning")
    else:
        # For 'approve' or 'update'
        price_type = request.form.get('price_type', 'free')
        price = request.form.get('price', 0.0)
        cursor.execute("""
            UPDATE courses 
            SET status = 'approved', price_type = %s, price = %s
            WHERE id = %s
        """, (price_type, price, course_id))
        conn.commit()
        
        if action == 'approve':
            flash("Course approved and payment details set successfully!", "success")
        else:
            flash("Course payment details updated.", "success")
            
    cursor.close()
    conn.close()
    return redirect(url_for('admin_courses'))

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Add User directly
        role = request.form.get('role')
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Check duplicate
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email is already registered!", "warning")
        else:
            cursor.execute(
                "INSERT INTO users (name, email, phone, password, age, gender, role, status) VALUES (%s, %s, %s, %s, %s, %s, %s, 'approved')",
                (name, email, phone, password, age, gender, role)
            )
            user_id = cursor.lastrowid
            
            if role == 'student':
                cursor.execute(
                    "INSERT INTO student_profiles (user_id, class_level, stream) VALUES (%s, 'N/A', 'N/A')",
                    (user_id,)
                )
            elif role == 'teacher':
                cursor.execute(
                    "INSERT INTO teacher_profiles (user_id, subject, teacher_id_code, experience, resume_url) VALUES (%s, 'N/A', 'N/A', 0, 'N/A')",
                    (user_id,)
                )
            conn.commit()
            flash("User created successfully!", "success")
        return redirect(url_for('admin_users'))
        
    # Get all users
    cursor.execute("SELECT * FROM users WHERE id != %s ORDER BY role, name", (session['user_id'],))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/adduser.html', users=users)

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("User deleted successfully.", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/messages')
def admin_messages():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM contact_messages ORDER BY created_at DESC")
    messages = cursor.fetchall()
    
    reports_list = []
    for msg in messages:
        date_str = msg['created_at'].strftime('%Y-%m-%d') if isinstance(msg['created_at'], datetime) else str(msg['created_at'])
        time_str = msg['created_at'].strftime('%Y-%m-%d %H:%M') if isinstance(msg['created_at'], datetime) else str(msg['created_at'])
        
        timeline = [{'time': time_str, 'text': 'Feedback message received by system'}]
        if msg.get('status') == 'investigating':
            timeline.append({'time': time_str, 'text': 'Investigation started by Admin'})
        elif msg.get('status') == 'resolved':
            timeline.append({'time': time_str, 'text': 'Marked as Resolved by Admin'})
        elif msg.get('status') == 'dismissed':
            timeline.append({'time': time_str, 'text': 'Report dismissed by Admin'})
            
        reports_list.append({
            'id': msg['id'],
            'title': f"Feedback message from {msg['name']}",
            'priority': msg.get('priority', 'medium'),
            'status': msg.get('status', 'open'),
            'category': 'General Inquiry',
            'reporter': msg['name'],
            'item': msg['email'],
            'date': date_str,
            'description': msg['message'],
            'timeline': timeline
        })
        
    import json
    reports_json = json.dumps(reports_list)
    
    cursor.close()
    conn.close()
    return render_template('admin/reports.html', messages=messages, reports_json=reports_json)

@app.route('/admin/reports/action/<int:report_id>/<string:action>', methods=['POST'])
def admin_report_action(report_id, action):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    status_map = {
        'investigate': 'investigating',
        'resolve': 'resolved',
        'dismiss': 'dismissed',
        'reopen': 'open'
    }
    status = status_map.get(action)
    if not status:
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE contact_messages SET status = %s WHERE id = %s", (status, report_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/profile')
def admin_profile():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
    user = cursor.fetchone()
    
    # Calculate stats for the admin profile
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    total_courses = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM contact_messages")
    total_reports = cursor.fetchone()['count']
    
    # Since there is no explicit rating table, we will use a static high rating for the admin platform
    stats = {
        'total_users': total_users,
        'total_courses': total_courses,
        'total_reports': total_reports,
        'rating': 4.9
    }
    
    cursor.close()
    conn.close()
    return render_template('admin/adminprofile.html', user=user, stats=stats)

@app.route('/admin/notifications')
def admin_notifications():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    admin_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Mark all as read
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (admin_id,))
    conn.commit()
    
    cursor.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (admin_id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/notification.html', notifications=notifications)

@app.route('/admin/settings')
def admin_settings():
    if not check_role(['admin']):
        return redirect(url_for('login'))
    return render_template('admin/settings.html')


# ----------------- ADDED BACKEND ROUTES -----------------
@app.route('/admin/update_profile', methods=['POST'])
def admin_update_profile():
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    name = request.form.get('name')
    email = request.form.get('email')
    
    if not name or not email:
        return jsonify({'success': False, 'message': 'Missing name or email'}), 400
        
    admin_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = %s, email = %s WHERE id = %s", (name, email, admin_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    # Update session name
    session['name'] = name
    
    return jsonify({'success': True, 'message': 'Profile updated successfully'})


@app.route('/admin/manage')
def admin_manage():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # 1. Total users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    # 2. Total students
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()['count']
    
    # 3. Total teachers
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher'")
    total_teachers = cursor.fetchone()['count']
    
    # 4. Pending teacher approvals
    cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'teacher' AND status = 'pending'")
    pending_approval = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT u.id, u.name, u.email, u.role, u.status, 
               DATE_FORMAT(u.created_at, '%Y-%m-%d') as joined,
               sp.stream as student_stream, sp.class_level,
               tp.subject as teacher_subject, tp.resume_url as teacher_resume,
               (SELECT COUNT(*) FROM enrollments WHERE student_id = u.id) as student_courses_count,
               (SELECT COUNT(*) FROM courses WHERE created_by = u.id) as teacher_courses_count
        FROM users u
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
        LEFT JOIN teacher_profiles tp ON u.id = tp.user_id
        WHERE u.id != %s
        ORDER BY u.role, u.name
    """, (session['user_id'],))
    db_users = cursor.fetchall()
    
    users_list = []
    for du in db_users:
        enrolled_titles = []
        if du['role'] == 'student':
            cursor.execute("SELECT c.id, c.title FROM enrollments e JOIN courses c ON e.course_id = c.id WHERE e.student_id = %s", (du['id'],))
            enrolled_titles = [{'id': row['id'], 'title': row['title']} for row in cursor.fetchall()]
        
        cv_filename = ''
        if du['teacher_resume']:
            cv_filename = os.path.basename(du['teacher_resume'])
            
        users_list.append({
            'id': du['id'],
            'name': du['name'],
            'email': du['email'],
            'role': du['role'],
            'status': du['status'],
            'joined': du['joined'],
            'courses': du['student_courses_count'] if du['role'] == 'student' else du['teacher_courses_count'],
            'stream': du['student_stream'] if du['role'] == 'student' else '',
            'subject': du['teacher_subject'] if du['role'] == 'teacher' else '',
            'cv': cv_filename,
            'enrolled': enrolled_titles
        })
        
    import json
    users_json = json.dumps(users_list)
    
    cursor.close()
    conn.close()
    
    return render_template(
        'admin/manage.html',
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        pending_approval=pending_approval,
        users_json=users_json
    )

@app.route('/approve-teacher/<int:teacher_id>', methods=['POST'])
def approve_teacher(teacher_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'approved' WHERE id = %s AND role = 'teacher'", (teacher_id,))
    conn.commit()
    cursor.execute(
        "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
        (teacher_id, "Your registration status has been updated to: approved.")
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Teacher approved successfully.'})

@app.route('/reject-teacher/<int:teacher_id>', methods=['POST'])
def reject_teacher(teacher_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'rejected' WHERE id = %s AND role = 'teacher'", (teacher_id,))
    conn.commit()
    cursor.execute(
        "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
        (teacher_id, "Your registration status has been updated to: rejected.")
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Teacher rejected successfully.'})

@app.route('/admin/suspend-user/<int:user_id>', methods=['POST'])
def suspend_user(user_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = 'rejected' WHERE id = %s", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'User suspended successfully.'})

@app.route('/admin/remove-course-access/<int:student_id>/<int:course_id>', methods=['POST'])
def admin_remove_course_access(student_id, course_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Course access removed successfully.'})

@app.route('/enroll-course/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
    student_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
        conn.commit()
        flash("Enrolled successfully in the course!", "success")
    else:
        flash("You are already enrolled in this course.", "info")
    cursor.close()
    conn.close()
    return redirect(url_for('student_courses'))

@app.route('/purchase/<int:course_id>', methods=['GET'])
def purchase_course(course_id):
    if not check_role(['student']):
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE id = %s", (course_id,))
    course = cursor.fetchone()
    cursor.close()
    conn.close()
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('student_courses'))
    thumbnail_path = course['cover_image_url'].lstrip('/')
    course['thumbnail_path'] = thumbnail_path
    
    return render_template('student/purchase.html', course=course)

@app.route('/upload-payment', methods=['POST'])
def upload_payment():
    if not check_role(['student']):
        return redirect(url_for('login'))
    student_id = session['user_id']
    course_id = request.form.get('course_id')
    screenshot = request.files.get('screenshot')
    
    if not course_id or not screenshot or screenshot.filename == '':
        flash("Invalid upload details.", "danger")
        return redirect(url_for('student_courses'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id FROM enrollments WHERE student_id = %s AND course_id = %s", (student_id, course_id))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        flash("You are already enrolled in this course.", "info")
        return redirect(url_for('student_courses'))
        
    cursor.execute("SELECT price FROM courses WHERE id = %s", (course_id,))
    c_row = cursor.fetchone()
    if not c_row:
        cursor.close()
        conn.close()
        flash("Course not found.", "danger")
        return redirect(url_for('student_courses'))
        
    amount = c_row['price']
    
    filename = f"pay_{student_id}_{course_id}_{int(time.time())}_{screenshot.filename}"
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'payments', filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    screenshot.save(save_path)
    screenshot_url = f"/static/uploads/payments/{filename}"
    
    cursor.execute("""
        INSERT INTO course_payments (student_id, course_id, amount, screenshot_path, status)
        VALUES (%s, %s, %s, %s, 'approved')
    """, (student_id, course_id, amount, screenshot_url))
    
    # Automatically enroll the student
    cursor.execute("""
        INSERT INTO enrollments (student_id, course_id, progress, completed)
        VALUES (%s, %s, 0, FALSE)
    """, (student_id, course_id))
    
    conn.commit()
    
    cursor.execute("SELECT id FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    for admin in admins:
        cursor.execute(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (admin['id'], f"Student ID {student_id} automatically enrolled in Course ID {course_id} after payment submission.")
        )
    conn.commit()
    
    cursor.close()
    conn.close()
    flash("Payment successful! You are now enrolled in the course.", "success")
    return redirect(url_for('student_courses'))

@app.route('/approve-payment/<string:payment_id>', methods=['POST'])
def approve_payment(payment_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if payment_id.startswith('evt_'):
        real_id = int(payment_id[4:])
        cursor.execute("SELECT er.*, e.title as event_title FROM event_registrations er JOIN events e ON er.event_id = e.id WHERE er.id = %s", (real_id,))
        pay = cursor.fetchone()
        if pay:
            cursor.execute("UPDATE event_registrations SET payment_status = 'paid' WHERE id = %s", (real_id,))
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (pay['student_id'], f"Your payment for event '{pay['event_title']}' has been approved!")
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Event payment approved successfully.'})
    else:
        real_id = int(payment_id)
        cursor.execute("SELECT * FROM course_payments WHERE id = %s", (real_id,))
        pay = cursor.fetchone()
        if pay:
            cursor.execute("UPDATE course_payments SET status = 'approved' WHERE id = %s", (real_id,))
            cursor.execute("INSERT IGNORE INTO enrollments (student_id, course_id) VALUES (%s, %s)", (pay['student_id'], pay['course_id']))
            cursor.execute("SELECT title FROM courses WHERE id = %s", (pay['course_id'],))
            course_title = cursor.fetchone()['title']
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (pay['student_id'], f"Your payment for course '{course_title}' has been approved! You are now enrolled.")
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Payment approved successfully.'})
            
    cursor.close()
    conn.close()
    return jsonify({'message': 'Payment request not found.'}), 404

@app.route('/reject-payment/<string:payment_id>', methods=['POST'])
def reject_payment(payment_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if payment_id.startswith('evt_'):
        real_id = int(payment_id[4:])
        cursor.execute("SELECT er.*, e.title as event_title FROM event_registrations er JOIN events e ON er.event_id = e.id WHERE er.id = %s", (real_id,))
        pay = cursor.fetchone()
        if pay:
            cursor.execute("UPDATE event_registrations SET payment_status = 'rejected' WHERE id = %s", (real_id,))
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (pay['student_id'], f"Your payment request for event '{pay['event_title']}' was rejected. Please verify screenshot.")
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Event payment request rejected.'})
    else:
        real_id = int(payment_id)
        cursor.execute("SELECT * FROM course_payments WHERE id = %s", (real_id,))
        pay = cursor.fetchone()
        if pay:
            cursor.execute("UPDATE course_payments SET status = 'rejected' WHERE id = %s", (real_id,))
            cursor.execute("SELECT title FROM courses WHERE id = %s", (pay['course_id'],))
            course_title = cursor.fetchone()['title']
            cursor.execute(
                "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
                (pay['student_id'], f"Your payment request for course '{course_title}' was rejected. Please verify screenshot.")
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Payment request rejected.'})
            
    cursor.close()
    conn.close()
    return jsonify({'message': 'Payment request not found.'}), 404

@app.route('/admin/delete-course/<int:course_id>', methods=['POST'])
def admin_delete_course(course_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Course deleted successfully.'})

@app.route('/admin/delete-video/<int:video_id>', methods=['POST'])
def admin_delete_video(video_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Video deleted successfully.'})

@app.route('/admin/delete-assignment/<int:material_id>', methods=['POST'])
def admin_delete_assignment(material_id):
    if not check_role(['admin']):
        return jsonify({'message': 'Unauthorized'}), 403
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials WHERE id = %s", (material_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Material deleted successfully.'})

@app.route('/teacher/upload-course', methods=['GET', 'POST'])
def teacher_upload_course():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        stream = request.form.get('stream')
        subject = request.form.get('subject')
        
        thumbnail = request.files.get('thumbnail')
        cover_image_url = '/static/images/course_default.jpg'
        if thumbnail and thumbnail.filename != '':
            filename = f"course_{teacher_id}_{int(time.time())}_{thumbnail.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'courses', filename)
            thumbnail.save(save_path)
            cover_image_url = f"/static/uploads/courses/{filename}"
            
        intro_video = request.files.get('intro_video')
        if intro_video and intro_video.filename != '':
            filename = f"intro_{teacher_id}_{int(time.time())}_{intro_video.filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
            intro_video.save(save_path)
            
        cursor.execute("""
            INSERT INTO courses (title, description, category, cover_image_url, price_type, price, created_by, status)
            VALUES (%s, %s, %s, %s, 'free', 0.00, %s, 'pending')
        """, (title, description, category, cover_image_url, teacher_id))
        conn.commit()
        course_id = cursor.lastrowid
        cursor.execute("INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status) VALUES ('Course', %s, %s, 'New submission for review', 'low', 'pending')", (course_id, teacher_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'title': title,
            'description': description
        })
        
    cursor.execute("SELECT * FROM courses WHERE created_by = %s ORDER BY created_at DESC", (teacher_id,))
    teacher_courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('teacher/uploadcourse.html', teacher_courses=teacher_courses)


# ── Upload video to a specific course ─────────────────────────────────────────
@app.route('/teacher/course/<int:course_id>/upload-video', methods=['POST'])
def teacher_course_upload_video(course_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Verify the course belongs to this teacher
    cursor.execute("SELECT id FROM courses WHERE id = %s AND created_by = %s", (course_id, teacher_id))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Course not found or unauthorized'}), 404

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    video_source = request.form.get('video_source', 'link')

    if video_source == 'file':
        files = request.files.getlist('video_file')
        if not files or all(f.filename == '' for f in files):
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': 'No video files provided'}), 400
            
        uploaded_count = 0
        import time, os
        for idx, file in enumerate(files):
            if file and file.filename != '':
                filename = f"vid_{teacher_id}_{course_id}_{int(time.time())}_{idx}_{os.path.basename(file.filename)}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                file.save(save_path)
                video_url = f"/static/uploads/videos/{filename}"
                
                vid_title = title if len(files) == 1 else f"{title} - {os.path.splitext(os.path.basename(file.filename))[0]}"
                
                cursor.execute(
                    "INSERT INTO videos (title, description, video_url, course_id, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
                    (vid_title, description, video_url, course_id, teacher_id)
                )
                uploaded_count += 1
                video_id = cursor.lastrowid
                cursor.execute("INSERT INTO reported_content (content_type, content_id, reporter_id, reason, priority, status) VALUES ('Video', %s, %s, 'New submission for review', 'low', 'pending')", (video_id, teacher_id))
                
        conn.commit()
        add_notification_to_all_students(f"New video(s) uploaded for course: {title}")
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': f'{uploaded_count} Video(s) uploaded successfully!'})
    else:
        video_url = request.form.get('video_link', '').strip()
        if not title or not video_url:
            cursor.close(); conn.close()
            return jsonify({'success': False, 'message': 'Title and video are required'}), 400

        cursor.execute(
            "INSERT INTO videos (title, description, video_url, course_id, uploaded_by) VALUES (%s, %s, %s, %s, %s)",
            (title, description, video_url, course_id, teacher_id)
        )
        conn.commit()
        add_notification_to_all_students(f"New video uploaded for course: {title}")
        cursor.close(); conn.close()
        return jsonify({'success': True, 'message': 'Video uploaded successfully!'})


# ── Upload material to a specific course ──────────────────────────────────────
@app.route('/teacher/course/<int:course_id>/upload-material', methods=['POST'])
def teacher_course_upload_material(course_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM courses WHERE id = %s AND created_by = %s", (course_id, teacher_id))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Course not found or unauthorized'}), 404

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    subject = request.form.get('subject', 'General').strip()

    file = request.files.get('material_file')
    file_url = ''
    if file and file.filename != '':
        filename = f"mat_{teacher_id}_{course_id}_{int(time.time())}_{file.filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'materials', filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        file_url = f"/static/uploads/materials/{filename}"

    if not title or not file_url:
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Title and file are required'}), 400

    cursor.execute(
        "INSERT INTO materials (title, description, file_url, subject, course_id, uploaded_by) VALUES (%s, %s, %s, %s, %s, %s)",
        (title, description, file_url, subject, course_id, teacher_id)
    )
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'success': True, 'message': 'Study material uploaded successfully!'})


# ── Get course videos & materials (for modal) ─────────────────────────────────
@app.route('/teacher/course/<int:course_id>/content', methods=['GET'])
def teacher_course_content(course_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM courses WHERE id = %s AND created_by = %s", (course_id, teacher_id))
    course = cursor.fetchone()
    if not course:
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Not found'}), 404

    cursor.execute("SELECT id, title, description, video_url, created_at FROM videos WHERE course_id = %s ORDER BY created_at DESC", (course_id,))
    videos = cursor.fetchall()
    for v in videos:
        v['created_at'] = v['created_at'].strftime('%d %b %Y') if v['created_at'] else ''

    cursor.execute("SELECT id, title, description, file_url, subject, created_at FROM materials WHERE course_id = %s ORDER BY created_at DESC", (course_id,))
    materials = cursor.fetchall()
    for m in materials:
        m['created_at'] = m['created_at'].strftime('%d %b %Y') if m['created_at'] else ''

    cursor.close(); conn.close()
    return jsonify({'success': True, 'videos': videos, 'materials': materials})


# ── Delete a course (and its videos/materials via CASCADE) ────────────────────
@app.route('/teacher/course/delete/<int:course_id>', methods=['POST'])
def teacher_delete_course(course_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM courses WHERE id = %s AND created_by = %s", (course_id, teacher_id))
    course = cursor.fetchone()
    if not course:
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Course not found or unauthorized'}), 404

    # Delete associated files from disk
    cursor.execute("SELECT file_url FROM materials WHERE course_id = %s", (course_id,))
    for m in cursor.fetchall():
        try:
            fp = os.path.join(app.root_path, m['file_url'].strip('/'))
            if os.path.exists(fp): os.remove(fp)
        except Exception: pass

    cursor.execute("SELECT video_url FROM videos WHERE course_id = %s AND video_url LIKE '/static/%'", (course_id,))
    for v in cursor.fetchall():
        try:
            fp = os.path.join(app.root_path, v['video_url'].strip('/'))
            if os.path.exists(fp): os.remove(fp)
        except Exception: pass

    cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'success': True, 'message': f"Course '{course['title']}' deleted."})

# ── Edit a specific video title from a course ─────────────────────────────────
@app.route('/teacher/course/video/edit/<int:video_id>', methods=['POST'])
def teacher_edit_course_video(video_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    data = request.get_json(silent=True) or {}
    new_title = data.get('title', '').strip()
    if not new_title:
        return jsonify({'success': False, 'message': 'Title cannot be empty.'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM videos WHERE id = %s AND uploaded_by = %s", (video_id, teacher_id))
    if not cursor.fetchone():
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Video not found or unauthorized'}), 404

    cursor.execute("UPDATE videos SET title = %s WHERE id = %s", (new_title, video_id))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'success': True, 'message': 'Video title updated.', 'new_title': new_title})


# ── Delete a specific video from a course ─────────────────────────────────────
@app.route('/teacher/course/video/delete/<int:video_id>', methods=['POST'])
def teacher_delete_course_video(video_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, video_url FROM videos WHERE id = %s AND uploaded_by = %s", (video_id, teacher_id))
    video = cursor.fetchone()
    if not video:
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Video not found or unauthorized'}), 404

    if video['video_url'] and video['video_url'].startswith('/static/'):
        try:
            fp = os.path.join(app.root_path, video['video_url'].strip('/'))
            if os.path.exists(fp): os.remove(fp)
        except Exception: pass

    cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'success': True, 'message': 'Video deleted.'})


# ── Delete a specific material from a course ──────────────────────────────────
@app.route('/teacher/course/material/delete/<int:material_id>', methods=['POST'])
def teacher_delete_course_material(material_id):
    if not check_role(['teacher']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    teacher_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, file_url FROM materials WHERE id = %s AND uploaded_by = %s", (material_id, teacher_id))
    mat = cursor.fetchone()
    if not mat:
        cursor.close(); conn.close()
        return jsonify({'success': False, 'message': 'Material not found or unauthorized'}), 404

    if mat['file_url']:
        try:
            fp = os.path.join(app.root_path, mat['file_url'].strip('/'))
            if os.path.exists(fp): os.remove(fp)
        except Exception: pass

    cursor.execute("DELETE FROM materials WHERE id = %s", (material_id,))
    conn.commit()
    cursor.close(); conn.close()
    return jsonify({'success': True, 'message': 'Material deleted.'})



@app.route('/admin/content')
def admin_content():
    if not check_role(['admin']):
        return redirect(url_for('login'))
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT rc.*, u.name as reporter_name,
               CASE 
                   WHEN rc.content_type = 'Course' THEN c.title
                   WHEN rc.content_type = 'Video' THEN v.title
                   WHEN rc.content_type = 'Material' THEN m.title
                   WHEN rc.content_type = 'Class' THEN lc.topic
                   WHEN rc.content_type = 'Event' THEN e.title
               END as content_title,
               CASE 
                   WHEN rc.content_type = 'Course' THEN c.price
                   WHEN rc.content_type = 'Event' THEN e.price
                   ELSE 0.00
               END as content_price,
               CASE 
                   WHEN rc.content_type = 'Course' THEN c.price_type
                   ELSE 'paid'
               END as content_price_type
        FROM reported_content rc
        JOIN users u ON rc.reporter_id = u.id
        LEFT JOIN courses c ON rc.content_type = 'Course' AND rc.content_id = c.id
        LEFT JOIN videos v ON rc.content_type = 'Video' AND rc.content_id = v.id
        LEFT JOIN materials m ON rc.content_type = 'Material' AND rc.content_id = m.id
        LEFT JOIN live_classes lc ON rc.content_type = 'Class' AND rc.content_id = lc.id
        LEFT JOIN events e ON rc.content_type = 'Event' AND rc.content_id = e.id
    """)
    db_reports = cursor.fetchall()
    
    mock_data = {
        'pending': [],
        'reviewed': [],
        'approved': [],
        'removed': []
    }
    
    icon_map = {
        'Course': ('fa-book-open', '#eef2ff', '#2c2a99'),
        'Video': ('fa-video', '#fff3cd', '#ff9800'),
        'Material': ('fa-file-pdf', '#ffe5e5', '#d32f2f'),
        'Class': ('fa-wifi', '#e0f7fa', '#0097a7'),
        'Event': ('fa-calendar', '#f3e5f5', '#7b1fa2')
    }
    
    for r in db_reports:
        status = r['status']
        
        actions = []
        if status == 'pending':
            actions = ['approve', 'remove', 'dismiss']
        elif status in ('approved', 'dismissed'):
            actions = ['remove']
        elif status == 'removed':
            actions = ['restore']
            
        icon, icon_bg, icon_color = icon_map.get(r['content_type'], ('fa-file', '#f3f4f6', '#374151'))
        
        formatted = {
            'id': r['id'],
            'title': r['content_title'] if r['content_title'] else f"Deleted {r['content_type']}",
            'desc': r['reason'],
            'iconBg': icon_bg,
            'iconColor': icon_color,
            'icon': icon,
            'priority': r['priority'],
            'type': r['content_type'],
            'reporter': r['reporter_name'],
            'price': float(r['content_price']) if r['content_price'] is not None else 0.0,
            'price_type': r['content_price_type'],
            'date': r['created_at'].strftime('%Y-%m-%d') if isinstance(r['created_at'], datetime) else str(r['created_at']),
            'actions': actions
        }
        
        if status == 'pending':
            mock_data['pending'].append(formatted)
        elif status == 'removed':
            mock_data['removed'].append(formatted)
        elif status in ('approved', 'dismissed'):
            mock_data['approved'].append(formatted)
            
        if status != 'pending':
            mock_data['reviewed'].append(formatted)
            
    import json
    content_json = json.dumps(mock_data)
    
    cursor.close()
    conn.close()
    
    return render_template(
        'admin/content.html',
        pending_count=len(mock_data['pending']),
        reviewed_count=len(mock_data['reviewed']),
        approved_count=len(mock_data['approved']),
        removed_count=len(mock_data['removed']),
        content_json=content_json
    )

@app.route('/admin/content/moderate/<int:item_id>/<string:action>', methods=['POST'])
def admin_content_moderate(item_id, action):
    if not check_role(['admin']):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM reported_content WHERE id = %s", (item_id,))
    report = cursor.fetchone()
    if not report:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Report not found'}), 404
        
    status_map = {
        'approve': 'approved',
        'dismiss': 'dismissed',
        'remove': 'removed',
        'restore': 'pending'
    }
    
    new_status = status_map.get(action)
    if not new_status:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
    cursor.execute("UPDATE reported_content SET status = %s WHERE id = %s", (new_status, item_id))
    
    if action == 'approve' and request.is_json:
        req_data = request.get_json()
        if 'price' in req_data:
            try:
                new_price = float(req_data['price'])
                if report['content_type'] == 'Course':
                    new_price_type = 'paid' if new_price > 0 else 'free'
                    cursor.execute("UPDATE courses SET price = %s, price_type = %s WHERE id = %s", (new_price, new_price_type, report['content_id']))
                elif report['content_type'] == 'Event':
                    cursor.execute("UPDATE events SET price = %s WHERE id = %s", (new_price, report['content_id']))
            except ValueError:
                pass
    
    if action == 'remove':
        if report['content_type'] == 'Course':
            cursor.execute("DELETE FROM courses WHERE id = %s", (report['content_id'],))
        elif report['content_type'] == 'Video':
            cursor.execute("DELETE FROM videos WHERE id = %s", (report['content_id'],))
        elif report['content_type'] == 'Material':
            cursor.execute("DELETE FROM materials WHERE id = %s", (report['content_id'],))
        elif report['content_type'] == 'Class':
            cursor.execute("DELETE FROM live_classes WHERE id = %s", (report['content_id'],))
        elif report['content_type'] == 'Event':
            cursor.execute("DELETE FROM events WHERE id = %s", (report['content_id'],))
            
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/student/live-class')
def student_live_class():
    if not check_role(['student']):
        return redirect(url_for('login'))
        
    class_id = request.args.get('id')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    live_class = None
    if class_id:
        cursor.execute("""
            SELECT lc.*, u.name as teacher_name 
            FROM live_classes lc 
            JOIN users u ON lc.teacher_id = u.id 
            WHERE lc.id = %s
        """, (class_id,))
        db_lc = cursor.fetchone()
        if db_lc:
            live_class = {
                'id': db_lc['id'],
                'title': db_lc['topic'],
                'teacher': {
                    'name': db_lc['teacher_name']
                }
            }
            
    cursor.close()
    conn.close()
    return render_template('student/liveclass.html', live_class=live_class)

@app.route('/teacher/live-class')
def teacher_live_class():
    if not check_role(['teacher']):
        return redirect(url_for('login'))
        
    class_id = request.args.get('id')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    live_class = None
    if class_id:
        cursor.execute("SELECT * FROM live_classes WHERE id = %s AND teacher_id = %s", (class_id, session['user_id']))
        live_class = cursor.fetchone()
        
    cursor.close()
    conn.close()
    return render_template('teacher/teacher_live_class.html', live_class=live_class)


# Notification Utility Functions
def add_notification(user_id, message):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, message))
        conn.commit()
    except Exception as e:
        print("Error adding notification:", e)
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# Run Flask Server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
