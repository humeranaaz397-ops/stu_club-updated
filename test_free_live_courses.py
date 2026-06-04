import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys

URL = "http://127.0.0.1:5000"

def run_verification():
    # Setup session with cookie jar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # 1. Log in as Student
    print("Step 1: Logging in as Student (sudharshanjaggula605@gmail.com)...")
    login_data = urllib.parse.urlencode({
        'email': 'sudharshanjaggula605@gmail.com',
        'password': 'sudha8897'
    }).encode('utf-8')
    
    req = urllib.request.Request(f"{URL}/login", data=login_data)
    try:
        res = opener.open(req)
        body = res.read().decode('utf-8')
        print("Login executed.")
    except Exception as e:
        print(f"Login failed: {e}")
        return
        
    # 2. Get /student/courses page and parse the embedded courses JSON
    print("\nStep 2: Fetching /student/courses to check seeded courses...")
    req = urllib.request.Request(f"{URL}/student/courses")
    try:
        res = opener.open(req)
        body = res.read().decode('utf-8')
        # Extract COURSES json from page
        import re
        match = re.search(r'const COURSES\s*=\s*(.*?);', body, re.DOTALL)
        if not match:
            print("FAILED: Could not find COURSES JSON inside page source!")
            return
        courses_json = match.group(1)
        courses = json.loads(courses_json)
        print(f"SUCCESS: Loaded {len(courses)} courses from the student page!")
        
        # Verify the seeded courses exist
        seeded_ids = {5, 6, 7}
        found_ids = {c['id'] for c in courses}
        if seeded_ids.issubset(found_ids):
            print("SUCCESS: Found all seeded courses (IDs 5, 6, 7) on the page!")
            for c in courses:
                if c['id'] in seeded_ids:
                    print(f" - Course {c['id']}: {c['title']} | Type: {c['type']} | Mode: {c['mode']}")
        else:
            print(f"FAILED: Missing some seeded courses. Seeded: {seeded_ids}, Found: {found_ids}")
            return
    except Exception as e:
        print(f"Failed to fetch student courses page: {e}")
        return

    # 3. Enroll in Free Course 5
    print("\nStep 3: Enrolling in Free Course 5 ('Python Programming for Beginners')...")
    req = urllib.request.Request(f"{URL}/enroll-course/5", data=b"") # POST request
    try:
        res = opener.open(req)
        body = res.read().decode('utf-8')
        print("Enrollment request completed (redirected).")
    except Exception as e:
        print(f"Enrollment failed: {e}")
        return

    # 4. Access Course 5 learning player (/course/5)
    print("\nStep 4: Fetching /course/5 details...")
    req = urllib.request.Request(f"{URL}/course/5")
    try:
        res = opener.open(req)
        body = res.read().decode('utf-8')
        if "Introduction to Python" in body:
            print("SUCCESS: Course learning page loaded with video titles!")
        else:
            print("FAILED: Course page content incorrect or missing lessons.")
            return
    except Exception as e:
        print(f"Failed to fetch course details: {e}")
        return

    # 5. Send Video Progress Update (/progress) for Video 3
    print("\nStep 5: Updating progress for video_id = 3 (First video of course 5)...")
    progress_payload = json.dumps({'video_id': 3}).encode('utf-8')
    req = urllib.request.Request(f"{URL}/progress", data=progress_payload)
    req.add_header('Content-Type', 'application/json')
    try:
        res = opener.open(req)
        res_data = json.loads(res.read().decode('utf-8'))
        if res_data.get('success'):
            print("SUCCESS: Progress updated successfully!")
        else:
            print(f"FAILED: Progress response was not successful: {res_data}")
            return
    except Exception as e:
        print(f"Failed to update progress: {e}")
        return
        
    print("\nALL VERIFICATION STEPS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_verification()
