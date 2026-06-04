import os
import re

TEMPLATES_DIR = 'templates'

replacements = {
    # Auth
    r'templates/login\.html': '/login',
    r'login\.html': '/login',
    
    # Teacher links
    r'\.?/?notification\(t\)\.html': '/teacher/notifications',
    r'\.?/?notification\(T\)\.html': '/teacher/notifications',
    r'\.?/?event_teacher\.html': '/teacher/events',
    r'\.?/?teacherprofile\.html': '/teacher/profile',
    r'\.?/?answer_q&a\.html': '/teacher/qa',
    r'\.?/?quiz\.html': '/teacher/quiz',
    r'\.?/?teacher live classes\.html': '/teacher/live-classes',
    r'\.?/?teacher_live_class\.html': '/teacher/live-classes',
    r'\.?/?post_notification\.html': '/teacher/post-notification',
    r'\.?/?chat\(T\)\.html': '/teacher/chat',
    r'\.?/?findpeople\(T\)\.html': '/teacher/connections',
    r'\.?/?teacherdashboard\.html': '/teacher/dashboard',
    r'\.?/?uploadpdf\.html': '/teacher/upload-material',
    r'\.?/?uploadvideo\.html': '/teacher/upload-video',
    r'\.?/?uploadcourse\.html': '/teacher/upload-course',

    # Student links
    r'\.?/?notification\(s\)\.html': '/student/notifications',
    r'\.?/?event\.html': '/student/events',
    r'\.?/?q&a\(s\)\.html': '/student/qa',
    r'\.?/?studymaterial\(s\)\.html': '/student/materials',
    r'\.?/?video\(s\)\.html': '/student/videos',
    r'\.?/?liveclasses\(s\)\.html': '/student/live-classes',
    r'\.?/?findpeople\(s\)\.html': '/student/connections',
    r'\.?/?chat\(s\)\.html': '/student/chat',
    r'\.?/?learningprogress\(s\)\.html': '/student/progress',
    r'\.?/?coures\.html': '/student/courses',
    r'\.?/?courses\.html': '/student/courses',
    r'\.?/?studentprofile\.html': '/student/profile',

    # Admin links
    r'\.?/?admindashboard\.html': '/admin/dashboard',
    r'\.?/?admindashboared\.html': '/admin/dashboard',
    r'\.?/?manage\.html': '/admin/manage',
    r'\.?/?content\.html': '/admin/content',
    r'\.?/?controlpanel\.html': '/admin/controlpanel',
    r'\.?/?analytics\.html': '/admin/analytics',
    r'\.?/?reports\.html': '/admin/messages',
    r'\.?/?events\.html': '/admin/events',
    r'\.?/?settings\.html': '/admin/settings',
    r'\.?/?adminprofile\.html': '/admin/profile',
    r'\.?/?notification\.html': '/admin/notifications',
    r'\.?/?adduser\.html': '/admin/users',
    r'\.?/?addmeterial\.html': '/admin/upload-material',
    r'\.?/?addcourse\.html': '/admin/courses',
    r'\.?/?addviedo\.html': '/admin/upload-video',
    r'\.?/?post\.html': '/admin/post-notification',
}

def run_patching():
    print("Scanning templates for hardcoded HTML references...")
    patched_count = 0
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if not file.endswith('.html'):
                continue
            
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            original = content
            
            # Apply all replacements
            for pattern, replacement in replacements.items():
                # We want to replace it only when inside quotes or as a link, e.g. "coures.html" or 'coures.html'
                # Let's match: "pattern" or 'pattern'
                double_quote_pattern = r'"' + pattern + r'"'
                single_quote_pattern = r"'" + pattern + r"'"
                
                content = re.sub(double_quote_pattern, f'"{replacement}"', content, flags=re.IGNORECASE)
                content = re.sub(single_quote_pattern, f"'{replacement}'", content, flags=re.IGNORECASE)
                
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Patched links in: {filepath}")
                patched_count += 1
                
    print(f"Patching completed. Total files modified: {patched_count}")

if __name__ == '__main__':
    run_patching()
