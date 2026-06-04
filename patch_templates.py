import os
import re

TEMPLATES_DIR = 'templates'

def patch_templates():
    print("Starting template patching...")
    
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if not file.endswith('.html'):
                continue
                
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            original = content
            
            # 1. Fix auth.logout -> logout
            content = content.replace("url_for('auth.logout')", "url_for('logout')")
            content = content.replace("url_for(\"auth.logout\")", "url_for('logout')")
            
            # 2. Patch sidebar inside teacher templates to add "Create Course"
            # (only if the file is a teacher template and doesn't already contain teacher_upload_course)
            if 'templates\\teacher' in root or 'templates/teacher' in root:
                if 'teacher_upload_course' not in content:
                    # Let's search for the Upload Video li and insert the Create Course li after it
                    video_li_pattern = r'(<li[^>]*>\s*<a href="\{\{\s*url_for\(\'teacher_upload_video\'\)\s*\}\}">.*?</a>\s*</li>)'
                    
                    # If this is uploadcourse.html, it has a custom sidebar, which we'll handle separately
                    if file != 'uploadcourse.html':
                        replacement = r'\1\n        <li><a href="{{ url_for(\'teacher_upload_course\') }}"><i class="fa-solid fa-folder-plus"></i> <span>Create Course</span></a></li>'
                        content = re.sub(video_li_pattern, replacement, content, flags=re.DOTALL)
            
            # 3. Special handling for templates/teacher/uploadcourse.html
            if file == 'uploadcourse.html':
                # Replace the sidebar links
                sidebar_content = """    <!-- SIDEBAR -->
    <aside class="sidebar">

      <ul>

        <li>
          <a href="/teacher/dashboard">
            <i class="fa-solid fa-grip"></i>
            <span> Dashboard</span>
          </a>
        </li>

        <li>
          <a href="/upload-assignment">
            <i class="fa-solid fa-upload"></i>
            <span>Upload Material</span>
          </a>
        </li>

        <li>
          <a href="/upload-video">
            <i class="fa-solid fa-video"></i>
            <span>Upload Video</span>
          </a>
        </li>
        <li class="active">
          <a href="/upload-course">
            <i class="fa-solid fa-folder-plus"></i>
            <span>Create Course</span>
          </a>
        </li>
        </li>
        <li>
          <a href="quiz.html">
            <i class="fa-solid fa-clipboard-list"></i>
            <span>Create Quiz</span>
          </a>
        </li>

        <li>
          <a href="teacher live classes.html">
            <i class="fa-solid fa-wifi"></i>
            <span>Live Classes</span>
          </a>
        </li>

        <li>
          <a href="answer_q&a.html">
            <i class="fa-solid fa-circle-question"></i>
            <span>Answer Q&A</span>
          </a>
        </li>

        <li>
          <a href="post_notification.html">
            <i class="fa-regular fa-bell"></i>
            <span>Post Notification</span>
          </a>
        </li>

        <li>
          <a href="chat(T).html">
            <i class="fa-regular fa-comment"></i>
            <span> Chat</span>
          </a>
        </li>

        <li>
          <a href="findpeople(T).html">
            <i class="fa-solid fa-users"></i>
            <span>Find People</span>
          </a>
        </li>

      </ul>

    </aside>"""
                
                new_sidebar = """    <!-- SIDEBAR -->
    <aside class="sidebar">
      <ul>
        <li><a href="{{ url_for('teacher_dashboard') }}"><i class="fa-solid fa-grip"></i><span>Dashboard</span></a></li>
        <li><a href="{{ url_for('teacher_upload_material') }}"><i class="fa-solid fa-upload"></i><span>Upload Material</span></a></li>
        <li><a href="{{ url_for('teacher_upload_video') }}"><i class="fa-solid fa-video"></i><span>Upload Video</span></a></li>
        <li class="active"><a href="{{ url_for('teacher_upload_course') }}"><i class="fa-solid fa-folder-plus"></i><span>Create Course</span></a></li>
        <li><a href="{{ url_for('teacher_quiz') }}"><i class="fa-solid fa-clipboard-list"></i><span>Create Quiz</span></a></li>
        <li><a href="{{ url_for('teacher_live_classes') }}"><i class="fa-solid fa-wifi"></i><span>Live Classes</span></a></li>
        <li><a href="{{ url_for('teacher_qa') }}"><i class="fa-solid fa-circle-question"></i><span>Answer Q&A</span></a></li>
        <li><a href="{{ url_for('teacher_post_notification') }}"><i class="fa-regular fa-bell"></i><span>Post Notification</span></a></li>
        <li><a href="{{ url_for('teacher_chat') }}"><i class="fa-regular fa-comment"></i><span>Chat</span></a></li>
        <li><a href="{{ url_for('teacher_connections') }}"><i class="fa-solid fa-users"></i><span>Find People</span></a></li>
      </ul>
    </aside>"""
                
                content = content.replace(sidebar_content, new_sidebar)
                
                # Also fix AJAX form action
                content = content.replace('fetch("{{ url_for(\'teacher.upload_course\') }}",', 'fetch("{{ url_for(\'teacher_upload_course\') }}",')
                content = content.replace("fetch('{{ url_for(\'teacher.upload_course\') }}',", "fetch('{{ url_for(\'teacher_upload_course\') }}',")
            
            # 4. Make Admin name "Humera" dynamic in Admin templates
            if 'templates\\Admin' in root or 'templates/Admin' in root:
                content = content.replace('<span class="uname">Humera</span>', '<span class="uname">{{ current_user.name if current_user else \'Admin\' }}</span>')
                content = content.replace('<span>Humera</span>', '<span>{{ current_user.name if current_user else \'Admin\' }}</span>')
                
            if content != original:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Patched: {filepath}")
                
    print("Template patching complete!")

if __name__ == '__main__':
    patch_templates()
