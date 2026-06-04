import os
import re

directory = 'templates/admin'

for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix any escaped quotes around url_for calls
        fixed = content.replace('\\"{{ url_for(', '"{{ url_for(').replace(') }}\\"', ') }}"')
        
        # Also fix if admin_analytics still has escaped quotes
        fixed = fixed.replace("url_for(\\'admin_analytics\\')", "url_for('admin_analytics')")
        
        if fixed != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"Fixed: {filename}")
        else:
            print(f"No change: {filename}")

print("Done.")
