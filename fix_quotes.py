import os
import re

directory = 'templates/admin'

for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix escaped quotes introduced by the previous patch
        # Change url_for(\'admin_controlpanel\') -> url_for('admin_controlpanel')
        fixed = content.replace("url_for(\\'admin_controlpanel\\')", "url_for('admin_controlpanel')")
        
        if fixed != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"Fixed: {filename}")
        else:
            print(f"No change: {filename}")

print("Done.")
