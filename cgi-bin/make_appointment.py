#! /var/www/html/venv/bin/python
import mysql.connector
import json
import cgi
import sys

# Required for web responses
print("Content-Type: application/json\n")

try:
    # Get form data
    form = cgi.FieldStorage()
    u_id = form.getvalue('user_id')
    start = form.getvalue('start_time')
    end = form.getvalue('end_time')

    db = mysql.connector.connect(
        host="localhost", user="root", 
        password="CleanStream475#", database="cleanstream_db"
    )
    cursor = db.cursor()

    # Use 'user_id'
    sql = "INSERT INTO appointments (user_id, scheduled_time, end_time, status) VALUES (%s, %s, %s, 'scheduled')"
    cursor.execute(sql, (u_id, start, end))
    db.commit()

    print(json.dumps({"status": "success", "message": "Appointment created!"}))

except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
finally:
    if 'db' in locals(): db.close()
