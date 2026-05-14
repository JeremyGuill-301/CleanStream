#!/usr/bin/python3
import cgi
import mysql.connector
import json
import sys

# Required for CGI to communicate with the browser
print("Content-Type: application/json\n")

try:
    # 1. Get Form Data
    form = cgi.FieldStorage()
    customer_id = form.getvalue('customer_id')
    cleaner_id = form.getvalue('cleaner_id')
    start_time = form.getvalue('start_time')
    end_time = form.getvalue('end_time')

    # 2. Connect to Database
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_PASSWORD_HERE", # Update this!
        database="cleanstream_db"
    )
    cursor = db.cursor()

    # 3. The Insert Query (Using user_id per schema)
    query = """
        INSERT INTO appointments (user_id, cleaner_id, scheduled_time, end_time, status)
        VALUES (%s, %s, %s, %s, 'Pending')
    """
    values = (customer_id, cleaner_id, start_time, end_time)
    
    cursor.execute(query, values)
    db.commit()

    print(json.dumps({"status": "success", "message": "Appointment scheduled!"}))

except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))

finally:
    if 'db' in locals() and db.is_connected():
        cursor.close()
        db.close()
