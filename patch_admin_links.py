import os
import re

directory = 'templates/admin'

# We want to replace url_for('admin_dashboard') with url_for('admin_controlpanel') 
# ONLY when the link is for "Control Panel"

def patch_links():
    for filename in os.listdir(directory):
        if filename.endswith('.html'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find the Control Panel link
            # It usually looks like: <a href="{{ url_for('admin_dashboard') }}"><i class="fa-solid fa-gamepad"></i><span>Control Panel</span></a>
            
            # Use regex to replace only the Control panel link
            content = re.sub(
                r'href="\{\{\s*url_for\(\'admin_dashboard\'\)\s*\}\}"(><i[^>]*fa-gamepad[^>]*></i><span>Control Panel)',
                r'href="{{ url_for(\'admin_controlpanel\') }}"\1',
                content
            )

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
    print("Links patched successfully.")

patch_links()
