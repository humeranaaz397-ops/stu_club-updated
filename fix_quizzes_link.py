import os
import re

directory = 'templates/student'

for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Fix commented out Quizzes link
        fixed = content.replace(
            '<!-- <li><a href="{{ url_for(\'student_quizzes\') }}"><i class="fa-solid fa-clipboard-list"></i><span>Quizzes</span></a></li> -->',
            '<li><a href="{{ url_for(\'student_quizzes\') }}"><i class="fa-solid fa-clipboard-list"></i><span>Quizzes</span></a></li>'
        )

        if fixed != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"Fixed: {filename}")
        else:
            print(f"No change: {filename}")

print("Done.")
