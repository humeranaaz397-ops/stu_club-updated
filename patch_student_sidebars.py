import os
import re

def patch_sidebars():
    student_dir = 'templates/student'
    if not os.path.exists(student_dir):
        print(f"Error: {student_dir} not found.")
        return
        
    files = [f for f in os.listdir(student_dir) if f.endswith('.html')]
    
    # Pattern to find Q&A link in list items
    pattern1 = re.compile(r'(<li[^>]*>\s*<a[^>]*href=["\']/student/qa["\'][^>]*>.*?Q&A.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    pattern2 = re.compile(r'(<li[^>]*>\s*<a[^>]*href=["\']\{\{\s*url_for\([\'"]student_qa[\'"]\)\s*\}\}["\'][^>]*>.*?Q&A.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    
    quiz_li1 = '\n                <li><a href="/student/quizzes"><i class="fa-solid fa-list-check"></i><span>Quizzes</span></a></li>'
    quiz_li2 = '\n                <li><a href="{{ url_for(\'student_quizzes\') }}"><i class="fa-solid fa-list-check"></i><span>Quizzes</span></a></li>'
    
    for fname in files:
        fpath = os.path.join(student_dir, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
            
        # Check if already patched
        if 'student/quizzes' in content or 'student_quizzes' in content:
            print(f"File {fname} is already patched.")
            continue
            
        match1 = pattern1.search(content)
        match2 = pattern2.search(content)
        
        if match1:
            print(f"Patching sidebar in {fname} (pattern 1)...")
            matched_text = match1.group(1)
            new_content = content.replace(matched_text, matched_text + quiz_li1)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        elif match2:
            print(f"Patching sidebar in {fname} (pattern 2)...")
            matched_text = match2.group(1)
            new_content = content.replace(matched_text, matched_text + quiz_li2)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            print(f"Q&A link not found in {fname}.")

if __name__ == "__main__":
    patch_sidebars()
