import os
import re

def patch_admin():
    admin_dir = 'templates/admin'
    if not os.path.exists(admin_dir):
        return
        
    files = [f for f in os.listdir(admin_dir) if f.endswith('.html')]
    # Look for the line containing /admin/analytics
    pattern = re.compile(r'(\s*<li[^>]*>\s*<a[^>]*href=["\']/admin/analytics["\'][^>]*>.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    
    new_li = '\n      <li><a href="/admin/teacher-performance"><i class="fa-solid fa-award"></i><span>Teacher Performance</span></a></li>'
    
    for fname in files:
        if fname == 'teacher_performance.html':
            continue
            
        fpath = os.path.join(admin_dir, fname)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
            
        if '/admin/teacher-performance' in content:
            continue
            
        match = pattern.search(content)
        if match:
            matched_text = match.group(1)
            # Insert the new li before the matched text
            new_content = content.replace(matched_text, new_li + matched_text)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Patched {fname}")

if __name__ == "__main__":
    patch_admin()
