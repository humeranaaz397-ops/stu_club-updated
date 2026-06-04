import os

TEMPLATES_DIR = 'templates'

def fix_backslashes():
    print("Fixing backslashes in templates...")
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if not file.endswith('.html'):
                continue
                
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            original = content
            
            # Replace backslashed quotes with normal quotes inside Jinja brackets
            # e.g., url_for(\'endpoint\') -> url_for('endpoint')
            content = content.replace("url_for(\\'", "url_for('")
            content = content.replace("url_for(\\'", "url_for('")
            content = content.replace("\\')", "')")
            content = content.replace("\\')", "')")
            
            # Let's also do a direct replace of url_for(\'teacher_upload_course\') to cover both double and single backslash situations
            content = content.replace("url_for(\\'teacher_upload_course\\')", "url_for('teacher_upload_course')")
            content = content.replace("url_for(\'teacher_upload_course\')", "url_for('teacher_upload_course')")
            
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed: {filepath}")
                
    print("Backslash fix complete!")

if __name__ == '__main__':
    fix_backslashes()
