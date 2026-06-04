import mysql.connector
from app import DB_CONFIG

def seed_data():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # 1. Define courses to insert
    # id = 5 (5%3 = 2 -> live+recorded)
    # id = 6 (6%3 = 0 -> live)
    # id = 7 (7%3 = 1 -> recorded)
    courses_to_seed = [
        {
            'id': 5,
            'title': 'Python Programming for Beginners',
            'description': 'Master the fundamentals of Python programming from scratch. This course covers variables, loops, functions, and object-oriented programming with interactive coding exercises.',
            'category': 'Computer Science',
            'cover_image_url': '/static/images/course_default.jpg',
            'price_type': 'free',
            'price': 0.00,
            'created_by': 2 # Aditya (Teacher)
        },
        {
            'id': 6,
            'title': 'Advanced Data Science - Live Masterclass',
            'description': 'Join our interactive live sessions on Machine Learning, Neural Networks, and Data Analysis. Includes live projects and live Q&A sessions with industry experts.',
            'category': 'Data Science',
            'cover_image_url': '/static/images/course_default.jpg',
            'price_type': 'free', # Let's make it free so the student can access it immediately as well
            'price': 0.00,
            'created_by': 2
        },
        {
            'id': 7,
            'title': 'Intro to UI/UX Design & Figma',
            'description': 'Learn user interface and user experience design principles. Master Figma tools, wireframing, prototyping, and user testing through hands-on projects.',
            'category': 'Design',
            'cover_image_url': '/static/images/course_default.jpg',
            'price_type': 'free',
            'price': 0.00,
            'created_by': 2
        }
    ]
    
    print("Seeding courses...")
    for c in courses_to_seed:
        # Check if course already exists
        cursor.execute("SELECT id FROM courses WHERE id = %s", (c['id'],))
        if cursor.fetchone():
            print(f"Course {c['id']} already exists. Updating...")
            cursor.execute("""
                UPDATE courses 
                SET title=%s, description=%s, category=%s, price_type=%s, price=%s 
                WHERE id=%s
            """, (c['title'], c['description'], c['category'], c['price_type'], c['price'], c['id']))
        else:
            print(f"Inserting Course {c['id']}...")
            cursor.execute("""
                INSERT INTO courses (id, title, description, category, cover_image_url, price_type, price, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (c['id'], c['title'], c['description'], c['category'], c['cover_image_url'], c['price_type'], c['price'], c['created_by']))
    conn.commit()
    
    # 2. Define videos to insert for these courses
    videos_to_seed = [
        # Course 5: Python Programming
        {
            'title': 'Introduction to Python & Setup',
            'description': 'Learn why Python is so popular, set up your development environment, and write your first Hello World program.',
            'video_url': 'https://www.youtube.com/watch?v=kqtD5eraYb8',
            'uploaded_by': 2,
            'course_id': 5
        },
        {
            'title': 'Variables, Data Types, and Operators',
            'description': 'Understand how data is stored in Python variables, explore core data types like integers and strings, and use arithmetic operators.',
            'video_url': 'https://www.youtube.com/watch?v=ihk_Xg_K650',
            'uploaded_by': 2,
            'course_id': 5
        },
        {
            'title': 'Conditional Statements and Control Flow',
            'description': 'Learn how to make decisions in your code using if, elif, and else statements.',
            'video_url': 'https://www.youtube.com/watch?v=6iF8Xb7Z3oQ',
            'uploaded_by': 2,
            'course_id': 5
        },
        # Course 6: Advanced Data Science - Live
        {
            'title': 'Live Class 1: Introduction to Machine Learning',
            'description': 'Watch the recording of our first live masterclass covering Supervised vs Unsupervised learning models.',
            'video_url': 'https://www.youtube.com/watch?v=Gv9_4yM8F4M',
            'uploaded_by': 2,
            'course_id': 6
        },
        {
            'title': 'Live Class 2: Data Preprocessing and Cleaning',
            'description': 'Recording of our interactive session on handling missing data, encoding variables, and scaling features.',
            'video_url': 'https://www.youtube.com/watch?v=n8h67cZIPF8',
            'uploaded_by': 2,
            'course_id': 6
        },
        # Course 7: UI/UX Design & Figma
        {
            'title': 'What is UI vs UX Design?',
            'description': 'An overview of user interface design and user experience design principles and roles.',
            'video_url': 'https://www.youtube.com/watch?v=5CxXhyhT6F4',
            'uploaded_by': 2,
            'course_id': 7
        },
        {
            'title': 'Figma Basics: Interface & Tooling',
            'description': 'Walkthrough of Figma\'s canvas, layouts, vector networks, and layer hierarchy.',
            'video_url': 'https://www.youtube.com/watch?v=FTFaQWZBqA8',
            'uploaded_by': 2,
            'course_id': 7
        }
    ]
    
    print("\nSeeding videos...")
    for v in videos_to_seed:
        # Check if video already exists
        cursor.execute("SELECT id FROM videos WHERE title = %s AND course_id = %s", (v['title'], v['course_id']))
        if cursor.fetchone():
            print(f"Video '{v['title']}' already exists for Course {v['course_id']}. Skipping...")
        else:
            print(f"Inserting Video '{v['title']}' for Course {v['course_id']}...")
            cursor.execute("""
                INSERT INTO videos (title, description, video_url, uploaded_by, course_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (v['title'], v['description'], v['video_url'], v['uploaded_by'], v['course_id']))
            
    conn.commit()
    cursor.close()
    conn.close()
    print("\nDatabase seeding completed successfully!")

if __name__ == '__main__':
    seed_data()
