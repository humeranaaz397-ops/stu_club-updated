import os
import re

TEMPLATES_DIR = 'templates'

mappings = {
    # teacher.xxx mappings
    r"teacher\.dashboard": "teacher_dashboard",
    r"teacher\.upload_assignment": "teacher_upload_material",
    r"teacher\.upload_video": "teacher_upload_video",
    r"teacher\.upload_course": "teacher_upload_course",
    r"teacher\.teacher_quiz": "teacher_quiz",
    r"teacher\.teacher_live_classes": "teacher_live_classes",
    r"teacher\.answer_qa": "teacher_qa",
    r"teacher\.post_notification": "teacher_post_notification",
    r"teacher\.teacher_chat": "teacher_chat",
    r"teacher\.find_people": "teacher_connections",
    r"teacher\.event_teacher": "teacher_events",
    r"teacher\.teacher_notification": "teacher_notifications",
    r"teacher\.teacher_profile": "teacher_profile",
    r"teacher\.teacher_live_class": "teacher_live_class",
    
    # student.xxx mappings
    r"student\.live_classes": "student_live_classes",
    r"student\.live_class": "student_live_class",
}

def patch_blueprints():
    print("Fixing blueprint url_for styles...")
    patched_count = 0
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if not file.endswith('.html'):
                continue
            
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            original = content
            
            for key, val in mappings.items():
                # Replace url_for('key') with url_for('val')
                pattern_single = r"url_for\('" + key + r"'"
                pattern_double = r'url_for\("' + key + r'"'
                
                content = re.sub(pattern_single, f"url_for('{val}'", content)
                content = re.sub(pattern_double, f'url_for("{val}"', content)
                
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Patched blueprint calls in: {filepath}")
                patched_count += 1
                
    print(f"Patching completed. Total files modified: {patched_count}")

if __name__ == '__main__':
    patch_blueprints()
