import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys
sys.path.append(r'c:\Users\rohit\OneDrive\Desktop\student\stu_club updated')
import re
import time

URL = "http://127.0.0.1:5000"

def run_test():
    timestamp = int(time.time())
    teacher_email = f"teacher_{timestamp}@gmail.com"
    
    # Setup session with cookie jar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # 1. Sign up new teacher
    print(f"Step 1: Signing up new teacher with email {teacher_email}...")
    boundary = "---WebKitFormBoundary12345"
    data = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="role2"\r\n\r\n'
        f"teacher\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="name"\r\n\r\n'
        f"Test Teacher {timestamp}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="age"\r\n\r\n'
        f"35\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="gender"\r\n\r\n'
        f"Male\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="email"\r\n\r\n'
        f"{teacher_email}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="phone"\r\n\r\n'
        f"1234567890\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="password"\r\n\r\n'
        f"pass123\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="confirm_password"\r\n\r\n'
        f"pass123\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="subject"\r\n\r\n'
        f"Mathematics\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="teacher_id"\r\n\r\n'
        f"T_{timestamp}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="experience"\r\n\r\n'
        f"5\r\n"
        f"--{boundary}--\r\n"
    ).encode('utf-8')
    
    req = urllib.request.Request(f"{URL}/signup", data=data)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    try:
        res = opener.open(req)
        body = res.read().decode('utf-8')
        print("Signup request executed.")
    except Exception as e:
        print(f"Signup failed: {e}")
        return
        
    # 2. Try logging in as the pending teacher
    print(f"\nStep 2: Testing login for pending teacher {teacher_email} (should fail/warn)...")
    login_data = urllib.parse.urlencode({
        'email': teacher_email,
        'password': 'pass123'
    }).encode('utf-8')
    
    req = urllib.request.Request(f"{URL}/login", data=login_data)
    res = opener.open(req)
    body = res.read().decode('utf-8')
    if "pending admin approval" in body:
        print("SUCCESS: Account login blocked correctly with pending warning!")
    else:
        print("FAILED: Account login was not blocked!")
        return
        
    # 3. Log in as Admin
    print("\nStep 3: Logging in as Admin...")
    admin_login_data = urllib.parse.urlencode({
        'email': 'humera08@gmail.com',
        'password': 'humera08'
    }).encode('utf-8')
    req = urllib.request.Request(f"{URL}/login", data=admin_login_data)
    res = opener.open(req)
    body = res.read().decode('utf-8')
    print("Logged in as Admin.")
    
    # 4. Fetch Manage Users page to find the new teacher ID
    print("\nStep 4: Fetching /admin/manage to get users JSON...")
    req = urllib.request.Request(f"{URL}/admin/manage")
    res = opener.open(req)
    body = res.read().decode('utf-8')
    
    # Find the JSON block
    match = re.search(r'const users = (\[.*?\]);', body)
    teacher_id = None
    if match:
        users = json.loads(match.group(1))
        for u in users:
            if u['email'] == teacher_email:
                teacher_id = u['id']
                print(f"Found teacher in list! ID = {teacher_id}, Status = {u['status']}")
                break
    else:
        print("FAILED: Could not parse users JSON from admin manage page.")
        return
        
    if not teacher_id:
        print("FAILED: Teacher not found in manage users list.")
        return
        
    # 5. Approve the teacher
    print(f"\nStep 5: Approving teacher with ID {teacher_id}...")
    req = urllib.request.Request(f"{URL}/approve-teacher/{teacher_id}", data=b'')
    res = opener.open(req)
    resp_body = json.loads(res.read().decode('utf-8'))
    print(f"Admin Approval Response: {resp_body}")
    
    # 6. Try logging in as the teacher now
    print("\nStep 6: Logging in as the approved teacher...")
    cj.clear()
    req = urllib.request.Request(f"{URL}/login", data=login_data)
    res = opener.open(req)
    body = res.read().decode('utf-8')
    if "Teacher Dashboard" in body or "teacher/dashboard" in res.geturl():
        print("SUCCESS: Approved teacher successfully logged in and reached Dashboard!")
    else:
        print("FAILED: Approved teacher could not log in.")
        return
        
    # 7. Student Purchase Flow
    print("\nStep 7: Logging in as Student...")
    cj.clear()
    student_login_data = urllib.parse.urlencode({
        'email': 'sudharshanjaggula605@gmail.com',
        'password': 'sudha8897'
    }).encode('utf-8')
    req = urllib.request.Request(f"{URL}/login", data=student_login_data)
    res = opener.open(req)
    body = res.read().decode('utf-8')
    print("Logged in as Student.")
    
    # Let's create a paid course to test checkout
    # Log in as Admin to make a paid course
    print("\nCreating a paid course...")
    cj.clear()
    req = urllib.request.Request(f"{URL}/login", data=admin_login_data)
    opener.open(req)
    
    course_title = f"Premium Math {timestamp}"
    course_boundary = "---WebKitFormBoundaryCourse"
    course_data = (
        f"--{course_boundary}\r\n"
        f'Content-Disposition: form-data; name="title"\r\n\r\n'
        f"{course_title}\r\n"
        f"--{course_boundary}\r\n"
        f'Content-Disposition: form-data; name="description"\r\n\r\n'
        f"Advanced math class.\r\n"
        f"--{course_boundary}\r\n"
        f'Content-Disposition: form-data; name="category"\r\n\r\n'
        f"Programming\r\n"
        f"--{course_boundary}\r\n"
        f'Content-Disposition: form-data; name="price_type"\r\n\r\n'
        f"paid\r\n"
        f"--{course_boundary}\r\n"
        f'Content-Disposition: form-data; name="price"\r\n\r\n'
        f"999.00\r\n"
        f"--{course_boundary}--\r\n"
    ).encode('utf-8')
    req = urllib.request.Request(f"{URL}/admin/courses", data=course_data)
    req.add_header("Content-Type", f"multipart/form-data; boundary={course_boundary}")
    res = opener.open(req)
    print("Premium Math Course created.")
    
    # Log in as Student again
    cj.clear()
    req = urllib.request.Request(f"{URL}/login", data=student_login_data)
    opener.open(req)
    
    # Get all courses to find the Premium Math Course ID
    req = urllib.request.Request(f"{URL}/student/courses")
    res = opener.open(req)
    body = res.read().decode('utf-8')
    
    match = re.search(r'const COURSES = (\[.*?\]);', body)
    course_id = None
    if match:
        courses = json.loads(match.group(1))
        for c in courses:
            if c['title'] == course_title:
                course_id = c['id']
                print(f"Found Premium Math Course ID = {course_id}")
                break
                
    if not course_id:
        print("FAILED: Could not find course ID.")
        return
        
    # Check out and upload payment screenshot
    print("\nSubmitting payment screenshot...")
    pay_boundary = "---WebKitFormBoundaryPay"
    pay_data = (
        f"--{pay_boundary}\r\n"
        f'Content-Disposition: form-data; name="course_id"\r\n\r\n'
        f"{course_id}\r\n"
        f"--{pay_boundary}\r\n"
        f'Content-Disposition: form-data; name="screenshot"; filename="dummy_screen.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
        f"dummy-image-bytes\r\n"
        f"--{pay_boundary}--\r\n"
    ).encode('utf-8')
    req = urllib.request.Request(f"{URL}/upload-payment", data=pay_data)
    req.add_header("Content-Type", f"multipart/form-data; boundary={pay_boundary}")
    res = opener.open(req)
    print("Payment screenshot uploaded.")
    
    # Log in as Admin to approve the payment
    cj.clear()
    req = urllib.request.Request(f"{URL}/login", data=admin_login_data)
    opener.open(req)
    
    req = urllib.request.Request(f"{URL}/admin/dashboard")
    res = opener.open(req)
    body = res.read().decode('utf-8')
    
    match = re.search(r'const payments = (\[.*?\]);', body)
    payment_id = None
    if match:
        payments = json.loads(match.group(1))
        for p in payments:
            if p['course_title'] == course_title and p['status'] == 'pending':
                payment_id = p['id']
                print(f"Found pending payment ID = {payment_id}")
                break
                
    if not payment_id:
        print("FAILED: Could not find pending payment ID in Admin Dashboard.")
        return
        
    print(f"\nApproving payment ID {payment_id}...")
    req = urllib.request.Request(f"{URL}/approve-payment/{payment_id}", data=b'')
    res = opener.open(req)
    resp_body = json.loads(res.read().decode('utf-8'))
    print(f"Admin Payment Approval Response: {resp_body}")
    
    # Log in as Student again and verify enrollment
    cj.clear()
    req = urllib.request.Request(f"{URL}/login", data=student_login_data)
    opener.open(req)
    
    req = urllib.request.Request(f"{URL}/student/courses")
    res = opener.open(req)
    body = res.read().decode('utf-8')
    
    match = re.search(r'const COURSES = (\[.*?\]);', body)
    if match:
        courses = json.loads(match.group(1))
        for c in courses:
            if c['id'] == course_id:
                print(f"\nSUCCESS: Student course enrollment status: Enrolled = {c['enrolled']}, Progress = {c['progress']}%")
                break

if __name__ == '__main__':
    run_test()
