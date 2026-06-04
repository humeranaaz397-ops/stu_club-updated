import re

file_path = 'templates/student/learningprogress(s).html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def replace_style(match):
    style_content = match.group(1)
    # Escape quotes if necessary, though style_content shouldn't have single quotes here.
    return f"{{{{ 'style=\"{style_content}\"' | safe }}}}"

# Replace styles containing Jinja {{ ... }}
# Regex looks for style="..." where the content contains {{
content = re.sub(r'style="([^"]*?\{\{.*?\}\}[^"]*?)"', replace_style, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Styles refactored.")
