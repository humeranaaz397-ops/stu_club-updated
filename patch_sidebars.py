import os
import re

def patch_sidebars():
    admin_dir = 'templates/admin'
    if not os.path.exists(admin_dir):
        print(f"Error: {admin_dir} not found.")
        return
        
    files = [f for f in os.listdir(admin_dir) if f.endswith('.html')]
    
    # Pattern to find Manage Users link in list items
    pattern = re.compile(r'(<li[^>]*>\s*<a[^>]*href=["\']/admin/manage["\'][^>]*>.*?Manage\s+Users.*?</a>\s*</li>)', re.IGNORECASE | re.DOTALL)
    
    payment_li = '\n      <li><a href="/admin/dashboard?tab=payments"><i class="fa-solid fa-indian-rupee-sign"></i><span>Payments</span></a></li>'
    
    for fname in files:
        fpath = os.path.join(admin_dir, fname)
        content = open(fpath, encoding='utf-8').read()
        
        # Check if already patched
        if '/admin/dashboard?tab=payments' in content:
            print(f"File {fname} is already patched.")
            continue
            
        match = pattern.search(content)
        if match:
            print(f"Patching sidebar in {fname}...")
            matched_text = match.group(1)
            # Insert the payments list item right after the matched list item
            new_content = content.replace(matched_text, matched_text + payment_li)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            print(f"Manage Users link not found in {fname}.")

if __name__ == "__main__":
    patch_sidebars()
