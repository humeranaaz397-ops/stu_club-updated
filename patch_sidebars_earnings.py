import os
import re

def patch_admin():
    admin_dir = 'templates/admin'
    if not os.path.exists(admin_dir):
        return
        
    files = [f for f in os.listdir(admin_dir) if f.endswith('.html')]
    pattern = re.compile(r'(<li[^>]*>\s*<a[^>]*href=["\']/admin/content["\'][^>]*>.*?Content Moderation.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    new_li = '\n                <li><a href="/admin/teacher-performance"><i class="fa-solid fa-award"></i><span>Teacher Performance</span></a></li>'
    
    for fname in files:
        fpath = os.path.join(admin_dir, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
            
        if '/admin/teacher-performance' in content:
            continue
            
        match = pattern.search(content)
        if match:
            matched_text = match.group(1)
            new_content = content.replace(matched_text, matched_text + new_li)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)

def patch_teacher():
    teacher_dir = 'templates/teacher'
    if not os.path.exists(teacher_dir):
        return
        
    files = [f for f in os.listdir(teacher_dir) if f.endswith('.html')]
    pattern = re.compile(r'(<li[^>]*>\s*<a[^>]*href=["\']\{\{\s*url_for\([\'"]teacher_dashboard[\'"]\)\s*\}\}["\'][^>]*>.*?Dashboard.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    pattern2 = re.compile(r'(<li[^>]*>\s*<a[^>]*href=["\']/teacher/dashboard["\'][^>]*>.*?Dashboard.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    
    new_li = '\n                <li><a href="/teacher/earnings"><i class="fa-solid fa-wallet"></i><span>Earnings</span></a></li>'
    
    for fname in files:
        if fname == 'earnings.html':
            continue
        fpath = os.path.join(teacher_dir, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
            
        if '/teacher/earnings' in content:
            continue
            
        match = pattern.search(content)
        if not match:
            match = pattern2.search(content)
            
        if match:
            matched_text = match.group(1)
            new_content = content.replace(matched_text, matched_text + new_li)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)

if __name__ == "__main__":
    patch_admin()
    patch_teacher()
