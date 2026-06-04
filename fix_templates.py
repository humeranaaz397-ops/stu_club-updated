"""
fix_templates.py
Batch-fixes all .html templates under /templates:
  - Replace raw .html sidebar/nav links with Flask url_for() equivalents
  - Fix logout() JS to use Flask /logout URL
  - Fix nav-actions hardcoded user names to use session.get('name')
Run once from project root: python fix_templates.py
"""
import os
import re

BASE = os.path.join(os.path.dirname(__file__), 'templates')

# ─────────────────────────────────────────────────────────────────────────────
# Mapping: raw filename → Flask url_for() call
# ─────────────────────────────────────────────────────────────────────────────
LINK_MAP = {
    # Student pages
    '"studentdashboard.html"'       : '"{{ url_for(\'student_dashboard\') }}"',
    '"q&a(s).html"'                 : '"{{ url_for(\'student_qa\') }}"',
    '"studymaterial(s).html"'       : '"{{ url_for(\'student_materials\') }}"',
    '"video(s).html"'               : '"{{ url_for(\'student_videos\') }}"',
    '"liveclasses(s).html"'         : '"{{ url_for(\'student_live_classes\') }}"',
    '"course.html"'                 : '"{{ url_for(\'student_courses\') }}"',
    '"findpeople(s).html"'          : '"{{ url_for(\'student_connections\') }}"',
    '"chat(s).html"'                : '"{{ url_for(\'student_chat\') }}"',
    '"learningprogress(s).html"'    : '"{{ url_for(\'student_dashboard\') }}"',
    '"notification(s).html"'        : '"{{ url_for(\'student_notifications\') }}"',
    '"studentprofile.html"'         : '"{{ url_for(\'student_profile\') }}"',
    '"apply_form.html"'             : '"{{ url_for(\'student_quizzes\') }}"',

    # Teacher pages
    '"teacherdashboard.html"'       : '"{{ url_for(\'teacher_dashboard\') }}"',
    '"uploadpdf.html"'              : '"{{ url_for(\'teacher_upload_material\') }}"',
    '"uploadvideo.html"'            : '"{{ url_for(\'teacher_upload_video\') }}"',
    '"quiz.html"'                   : '"{{ url_for(\'teacher_quiz\') }}"',
    '"teacher live classes.html"'   : '"{{ url_for(\'teacher_live_classes\') }}"',
    '"answer_q&a.html"'             : '"{{ url_for(\'teacher_qa\') }}"',
    '"post_notification.html"'      : '"{{ url_for(\'teacher_post_notification\') }}"',
    '"chat(T).html"'                : '"{{ url_for(\'teacher_chat\') }}"',
    '"findpeople(T).html"'          : '"{{ url_for(\'teacher_connections\') }}"',
    '"notification(t).html"'        : '"{{ url_for(\'teacher_notifications\') }}"',
    '"teacherprofile.html"'         : '"{{ url_for(\'teacher_profile\') }}"',
    '"uploadcourse.html"'           : '"{{ url_for(\'teacher_dashboard\') }}"',

    # Admin pages
    '"admindashboard.html"'         : '"{{ url_for(\'admin_dashboard\') }}"',
    '"adduser.html"'                : '"{{ url_for(\'admin_users\') }}"',
    '"addcourse.html"'              : '"{{ url_for(\'admin_courses\') }}"',
    '"reports.html"'                : '"{{ url_for(\'admin_messages\') }}"',
    '"notification.html"'           : '"{{ url_for(\'admin_notifications\') }}"',
    '"adminprofile.html"'           : '"{{ url_for(\'admin_profile\') }}"',
    '"settings.html"'               : '"{{ url_for(\'admin_notifications\') }}"',
    '"manage.html"'                 : '"{{ url_for(\'admin_users\') }}"',
    '"content.html"'                : '"{{ url_for(\'admin_courses\') }}"',
    '"analytics.html"'              : '"{{ url_for(\'admin_dashboard\') }}"',
    '"controlpanel.html"'           : '"{{ url_for(\'admin_dashboard\') }}"',

    # Public pages
    '"../login.html"'               : '"{{ url_for(\'login\') }}"',
    '"login.html"'                  : '"{{ url_for(\'login\') }}"',
    '"index.html"'                  : '"{{ url_for(\'home\') }}"',
    '"features.html"'               : '"{{ url_for(\'features\') }}"',
    '"contact.html"'                : '"{{ url_for(\'contact\') }}"',
    '"explore.html"'                : '"{{ url_for(\'explore\') }}"',

    # Event pages (no Flask route — keep pointing to dashboard)
    '"event.html"'                  : '"{{ url_for(\'student_dashboard\') }}"',
    '"event_teacher.html"'          : '"{{ url_for(\'teacher_dashboard\') }}"',
    '"./event_teacher.html"'        : '"{{ url_for(\'teacher_dashboard\') }}"',
}

# Logout JS fix
LOGOUT_OLD = "window.location.href = \"../login.html\";"
LOGOUT_NEW = "window.location.href = \"{{ url_for('logout') }}\";"

LOGOUT_OLD2 = "window.location.href=\"login.html\";"
LOGOUT_NEW2 = "window.location.href=\"{{ url_for('logout') }}\";"

# Hardcoded user name replacements in nav spans
NAME_PATTERNS = [
    (r'<span>Sudharshan</span>', '<span>{{ session.get(\'name\', \'Student\') }}</span>'),
    (r'<span>Aditya</span>',    '<span>{{ session.get(\'name\', \'Teacher\') }}</span>'),
    (r'<span>Humera</span>',    '<span>{{ session.get(\'name\', \'Admin\') }}</span>'),
]

# ─────────────────────────────────────────────────────────────────────────────
def fix_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Apply link replacements
    for old, new in LINK_MAP.items():
        content = content.replace(f'href={old}', f'href={new}')
        content = content.replace(f"href={old.replace('\"', chr(39))}", f'href={new}')

    # Fix logout JS
    content = content.replace(LOGOUT_OLD, LOGOUT_NEW)
    content = content.replace(LOGOUT_OLD2, LOGOUT_NEW2)

    # Fix hardcoded names
    for pattern, replacement in NAME_PATTERNS:
        content = re.sub(pattern, replacement, content)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  FIXED: {os.path.relpath(path, BASE)}')
    else:
        print(f'  ok   : {os.path.relpath(path, BASE)}')

# ─────────────────────────────────────────────────────────────────────────────
def main():
    count = 0
    for root, dirs, files in os.walk(BASE):
        for fname in files:
            if fname.endswith('.html'):
                fix_file(os.path.join(root, fname))
                count += 1
    print(f'\nDone. Processed {count} template files.')

if __name__ == '__main__':
    main()
