import sys
import os
from datetime import datetime, timedelta

# Import the app module
import app
from app import get_db, update_student_streak

def test():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get a student (Sudharshan is id=3)
    student_id = 3
    
    # Set to yesterday, streak to 6, last_reward to 0
    yesterday = datetime.now().date() - timedelta(days=1)
    
    cursor.execute("""
        UPDATE student_profiles 
        SET current_streak = 6, longest_streak = 6, last_activity_date = %s, last_reward_streak = 0
        WHERE user_id = %s
    """, (yesterday, student_id))
    conn.commit()
    print("Set test conditions for student 3.")
    
    # Call the update function
    print("Calling update_student_streak...")
    update_student_streak(student_id)
    
    # Check results
    cursor.execute("SELECT current_streak, last_activity_date, last_reward_streak FROM student_profiles WHERE user_id = %s", (student_id,))
    res = cursor.fetchone()
    print(f"Results: {res}")
    
    cursor.execute("SELECT message FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (student_id,))
    notif = cursor.fetchone()
    print(f"Latest Notification: {notif}")
    
    cursor.execute("SELECT * FROM enrollments WHERE student_id = %s ORDER BY enrolled_at DESC LIMIT 1", (student_id,))
    enr = cursor.fetchone()
    print(f"Latest Enrollment: {enr}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    test()
