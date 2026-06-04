import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the connections count query for student dashboard
content = re.sub(
    r"cursor\.execute\(\"SELECT COUNT\(\*\) as count FROM connection_requests WHERE student_id = %s AND status = 'accepted'\", \(student_id,\)\)\n\s+connected_teachers_count = cursor\.fetchone\(\)\['count'\]",
    r"cursor.execute(\"SELECT COUNT(*) as count FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'\", (student_id, student_id))\n    connected_teachers_count = cursor.fetchone()['count']",
    content
)

# 2. Replace the IN (...) subqueries for student (live classes, materials, videos, chat, qa)
# Original pattern: SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'
# Note that this string is in triple quotes, and its execute takes (student_id,) or (student_id, student_id)
# We will just change the subquery, AND we need to update the execute parameters. 
# It's easier to manually replace the whole execute block for these.

# Upcoming classes (Line 274-282)
content = re.sub(
    r"cursor\.execute\(\"\"\"\n\s+SELECT lc\.\*, u\.name as teacher_name \n\s+FROM live_classes lc \n\s+JOIN users u ON lc\.teacher_id = u\.id \n\s+WHERE lc\.teacher_id IN \(\n\s+SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'\n\s+\) AND lc\.class_date >= CURDATE\(\)\n\s+ORDER BY lc\.class_date ASC, lc\.class_time ASC\n\s+\"\"\", \(student_id,\)\)",
    r"""cursor.execute(\"\"\"
        SELECT lc.*, u.name as teacher_name 
        FROM live_classes lc 
        JOIN users u ON lc.teacher_id = u.id 
        WHERE lc.teacher_id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        ) AND lc.class_date >= CURDATE()
        ORDER BY lc.class_date ASC, lc.class_time ASC
    \"\"\", (student_id, student_id))""",
    content
)

# Materials (Line 392-400)
content = re.sub(
    r"cursor\.execute\(\"\"\"\n\s+SELECT m\.\*, u\.name as teacher_name \n\s+FROM materials m \n\s+JOIN users u ON m\.uploaded_by = u\.id \n\s+WHERE m\.uploaded_by IN \(\n\s+SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'\n\s+\)\n\s+ORDER BY m\.created_at DESC\n\s+\"\"\", \(student_id,\)\)",
    r"""cursor.execute(\"\"\"
        SELECT m.*, u.name as teacher_name 
        FROM materials m 
        JOIN users u ON m.uploaded_by = u.id 
        WHERE m.uploaded_by IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
        ORDER BY m.created_at DESC
    \"\"\", (student_id, student_id))""",
    content
)

# Videos (Line 427-436)
content = re.sub(
    r"cursor\.execute\(\"\"\"\n\s+SELECT v\.\*, u\.name as teacher_name,\n\s+\(SELECT COUNT\(\*\) FROM watched_videos WHERE student_id = %s AND video_id = v\.id\) as watched\n\s+FROM videos v \n\s+JOIN users u ON v\.uploaded_by = u\.id \n\s+WHERE v\.uploaded_by IN \(\n\s+SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'\n\s+\)\n\s+ORDER BY v\.created_at DESC\n\s+\"\"\", \(student_id, student_id\)\)",
    r"""cursor.execute(\"\"\"
        SELECT v.*, u.name as teacher_name,
               (SELECT COUNT(*) FROM watched_videos WHERE student_id = %s AND video_id = v.id) as watched
        FROM videos v 
        JOIN users u ON v.uploaded_by = u.id 
        WHERE v.uploaded_by IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
        ORDER BY v.created_at DESC
    \"\"\", (student_id, student_id, student_id))""",
    content
)

# Live classes past/upcoming (Line 453-461)
content = re.sub(
    r"cursor\.execute\(\"\"\"\n\s+SELECT lc\.\*, u\.name as teacher_name \n\s+FROM live_classes lc \n\s+JOIN users u ON lc\.teacher_id = u\.id \n\s+WHERE lc\.teacher_id IN \(\n\s+SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'\n\s+\)\n\s+ORDER BY lc\.class_date DESC, lc\.class_time DESC\n\s+\"\"\", \(student_id,\)\)",
    r"""cursor.execute(\"\"\"
        SELECT lc.*, u.name as teacher_name 
        FROM live_classes lc 
        JOIN users u ON lc.teacher_id = u.id 
        WHERE lc.teacher_id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
        ORDER BY lc.class_date DESC, lc.class_time DESC
    \"\"\", (student_id, student_id))""",
    content
)

# Connected teachers for chat (Line 554-560)
content = re.sub(
    r"cursor\.execute\(\"\"\"\n\s+SELECT u\.id as teacher_id, u\.name \n\s+FROM users u \n\s+WHERE u\.id IN \(\n\s+SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'\n\s+\)\n\s+\"\"\", \(student_id,\)\)",
    r"""cursor.execute(\"\"\"
        SELECT u.id as teacher_id, u.name 
        FROM users u 
        WHERE u.id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
    \"\"\", (student_id, student_id))""",
    content
)

# Connected teachers for QA (Line 619-625)
content = re.sub(
    r"cursor\.execute\(\"\"\"\n\s+SELECT u\.id as teacher_id, u\.name \n\s+FROM users u \n\s+WHERE u\.id IN \(\n\s+SELECT teacher_id FROM connection_requests WHERE student_id = %s AND status = 'accepted'\n\s+\)\n\s+\"\"\", \(student_id,\)\)",
    r"""cursor.execute(\"\"\"
        SELECT u.id as teacher_id, u.name 
        FROM users u 
        WHERE u.id IN (
            SELECT receiver_id FROM connections WHERE sender_id = %s AND status = 'accepted'
            UNION
            SELECT sender_id FROM connections WHERE receiver_id = %s AND status = 'accepted'
        )
    \"\"\", (student_id, student_id))""",
    content
)

# 3. Handle specific request verifications (chat, qa)
content = content.replace(
    "cursor.execute(\"SELECT id FROM connection_requests WHERE student_id = %s AND teacher_id = %s AND status = 'accepted'\", (student_id, teacher_id))",
    "cursor.execute(\"SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)) AND status = 'accepted'\", (student_id, teacher_id, teacher_id, student_id))"
)

# Send connection request in student_connections
content = content.replace(
    "cursor.execute(\"SELECT id FROM connection_requests WHERE student_id = %s AND teacher_id = %s\", (student_id, teacher_id))",
    "cursor.execute(\"SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s))\", (student_id, teacher_id, teacher_id, student_id))"
)
content = content.replace(
    "cursor.execute(\"INSERT INTO connection_requests (student_id, teacher_id, status) VALUES (%s, %s, 'pending')\", (student_id, teacher_id))",
    "cursor.execute(\"INSERT INTO connections (sender_id, receiver_id, status) VALUES (%s, %s, 'pending')\", (student_id, teacher_id))"
)

# Connected teachers list in student_connections
content = re.sub(
    r"LEFT JOIN connection_requests cr ON cr\.teacher_id = u\.id AND cr\.student_id = %s",
    r"LEFT JOIN connections cr ON (cr.receiver_id = u.id AND cr.sender_id = %s) OR (cr.sender_id = u.id AND cr.receiver_id = %s)",
    content
)
content = re.sub(
    r"WHERE e\.student_id = %s AND u\.role = 'teacher' AND u\.status = 'approved'\n\s+\"\"\", \(student_id, student_id\)\)",
    r"WHERE e.student_id = %s AND u.role = 'teacher' AND u.status = 'approved'\n    \"\"\", (student_id, student_id, student_id))",
    content
)

# Student profile connection count
content = content.replace(
    "FROM connection_requests \n        WHERE student_id = %s AND status = 'accepted'",
    "FROM connections \n        WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'"
)
content = content.replace(
    "\"\"\", (student_id,))\n    connections_count = cursor.fetchone()['count']",
    "\"\"\", (student_id, student_id))\n    connections_count = cursor.fetchone()['count']"
)

# Teacher Dashboard count
content = content.replace(
    "cursor.execute(\"SELECT COUNT(*) as count FROM connection_requests WHERE teacher_id = %s AND status = 'accepted'\", (teacher_id,))",
    "cursor.execute(\"SELECT COUNT(*) as count FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'\", (teacher_id, teacher_id))"
)

# Teacher notify connected students (materials, videos, live classes, post notification)
# Replace all lines matching `cursor.execute("SELECT student_id FROM connection_requests WHERE teacher_id = %s AND status = 'accepted'", (teacher_id,))`
content = content.replace(
    "cursor.execute(\"SELECT student_id FROM connection_requests WHERE teacher_id = %s AND status = 'accepted'\", (teacher_id,))",
    "cursor.execute(\"SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as student_id FROM connections WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'\", (teacher_id, teacher_id, teacher_id))"
)

# Teacher connections page logic
content = content.replace(
    "cursor.execute(\"SELECT student_id FROM connection_requests WHERE id = %s AND teacher_id = %s\", (request_id, teacher_id))",
    "cursor.execute(\"SELECT sender_id as student_id FROM connections WHERE id = %s AND receiver_id = %s\", (request_id, teacher_id))"
)
content = content.replace(
    "cursor.execute(\"UPDATE connection_requests SET status = %s WHERE id = %s\", (new_status, request_id))",
    "cursor.execute(\"UPDATE connections SET status = %s WHERE id = %s\", (new_status, request_id))"
)
content = re.sub(
    r"FROM connection_requests cr \n\s+JOIN users u ON cr\.student_id = u\.id \n\s+JOIN student_profiles sp ON u\.id = sp\.user_id \n\s+WHERE cr\.teacher_id = %s\n\s+ORDER BY cr\.status DESC, cr\.created_at DESC",
    r"FROM connections cr \n        JOIN users u ON cr.sender_id = u.id \n        LEFT JOIN student_profiles sp ON u.id = sp.user_id \n        WHERE cr.receiver_id = %s\n        ORDER BY cr.status DESC, cr.created_at DESC",
    content
)

# Teacher chat verify connection
content = content.replace(
    "cursor.execute(\"SELECT id FROM connection_requests WHERE student_id = %s AND teacher_id = %s AND status = 'accepted'\", (student_id, teacher_id))",
    "cursor.execute(\"SELECT id FROM connections WHERE ((sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)) AND status = 'accepted'\", (student_id, teacher_id, teacher_id, student_id))"
)

# Teacher chat loaded connected students
content = re.sub(
    r"JOIN connection_requests cr ON cr\.student_id = u\.id \n\s+JOIN chats ch ON \(ch\.sender_id = u\.id AND ch\.receiver_id = %s\) \n\s+OR \(ch\.sender_id = %s AND ch\.receiver_id = u\.id\)\n\s+WHERE cr\.teacher_id = %s AND cr\.status = 'accepted'",
    r"JOIN connections cr ON (cr.sender_id = u.id AND cr.receiver_id = %s) OR (cr.receiver_id = u.id AND cr.sender_id = %s) \n        JOIN chats ch ON (ch.sender_id = u.id AND ch.receiver_id = %s) \n                      OR (ch.sender_id = %s AND ch.receiver_id = u.id)\n        WHERE cr.status = 'accepted'",
    content
)
# update the tuple for teacher chat (teacher_id, teacher_id, teacher_id)
content = re.sub(
    r"\"\"\", \(teacher_id, teacher_id, teacher_id\)\)",
    r"\"\"\", (teacher_id, teacher_id, teacher_id, teacher_id))",
    content
)


with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("app.py refactored!")
