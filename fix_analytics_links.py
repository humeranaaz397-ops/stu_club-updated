import os
import re

directory = 'templates/admin'

for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix Analytics link: replace url_for('admin_dashboard') only when it's for Analytics span
        fixed = re.sub(
            r'href="\{\{\s*url_for\(\'admin_dashboard\'\)\s*\}\}"(><i[^>]*fa-chart-line[^>]*></i><span>Analytics)',
            r"href=\"{{ url_for('admin_analytics') }}\"\1",
            content
        )

        if fixed != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"Fixed: {filename}")
        else:
            print(f"No change: {filename}")

print("Done.")
