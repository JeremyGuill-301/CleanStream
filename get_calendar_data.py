#!/usr/bin/python3
import mysql.connector
import json
from datetime import datetime

# Required header for the browser to accept the data
print("Content-Type: application/json\n")

try:
    # Connect to the database
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="CleanStream475#", 
        database="cleanstream_db"
    )
    cursor = db.cursor(dictionary=True)

    # JOIN appointments with customer_contacts using user_id
    query = """
        SELECT 
            c.first_name AS title, 
            a.scheduled_time AS start, 
            a.end_time AS end 
        FROM appointments a
        JOIN customer_contacts c ON a.user_id = c.customer_id;
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    # Convert datetime objects to strings so JSON can handle them
    for row in rows:
        if isinstance(row['start'], datetime):
            row['start'] = row['start'].isoformat()
        if isinstance(row['end'], datetime):
            row['end'] = row['end'].isoformat()

    # Send the data to the browser
    print(json.dumps(rows))

except Exception as e:
    # If there is an error, send it back as JSON so we can see it in the console
    print(json.dumps([{"title": "Error", "start": "2026-05-07", "description": str(e)}]))

finally:
    if 'db' in locals() and db.is_connected():
        cursor.close()
        db.close()
