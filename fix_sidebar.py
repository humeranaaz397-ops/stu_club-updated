import os
import glob

def fix_sidebar(directory, pattern, replacement):
    for filepath in glob.glob(os.path.join(directory, '*.html')):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if pattern in content:
            new_content = content.replace(pattern, replacement)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Fixed {filepath}')

student_pattern = '<li><a href="{{ url_for(\'student_chat\') }}"><i class="fa-solid fa-comment-dots"></i><span>Chat</span></a></li>'
student_replacement = '<li><a href="{{ url_for(\'student_chat\') }}"><i class="fa-solid fa-comment-dots"></i><span>Chat {% if unread_messages and unread_messages > 0 %}<span style="background: red; color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; font-weight: bold; margin-left: 5px;">{{ unread_messages }}</span>{% endif %}</span></a></li>'

teacher_pattern = '<li><a href="{{ url_for(\'teacher_chat\') }}"><i class="fa-regular fa-comment"></i><span> Chat</span></a></li>'
teacher_replacement = '<li><a href="{{ url_for(\'teacher_chat\') }}"><i class="fa-regular fa-comment"></i><span> Chat {% if unread_messages and unread_messages > 0 %}<span style="background: red; color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; font-weight: bold; margin-left: 5px;">{{ unread_messages }}</span>{% endif %}</span></a></li>'

bad_student_pattern = '<li class="active"><a href="{{ url_for(\'student_chat\') }}"><i class="fa-solid fa-comment-dots"></i><span>Chat {% if unread_messages and unread_messages > 0 %}<span style="background: red; color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; font-weight: bold; margin-left: 5px;">{{ unread_messages }}</span>{% endif %}</span></a></li>'

fix_sidebar('templates/student', student_pattern, student_replacement)
fix_sidebar('templates/teacher', teacher_pattern, teacher_replacement)

# Fix the bad active classes the user added
for filepath in glob.glob(os.path.join('templates/student', '*.html')):
    if 'chat(s).html' in filepath:
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if bad_student_pattern in content:
        new_content = content.replace(bad_student_pattern, student_replacement)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Fixed bad active class in {filepath}')
