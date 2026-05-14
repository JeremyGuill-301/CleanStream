#! /var/www/html/venv/bin/python
import mysql.connector
import json

print("Content-Type: application/json\n")

db = mysql.connector.connect(host="localhost", user="root", password="CleanStream475#", database="cleanstream_db")
cursor = db.cursor(dictionary=True)
 
# Standardized query for CleanStream schema
query = """
    SELECT 
        c.first_name AS title, 
        a.scheduled_time AS start, 
        a.end_time AS end 
    FROM appointments a
    JOIN customer_contacts c ON a.user_id = c.customer_id;
"""
cursor.execute(query)
res = cursor.fetchall()

# Convert datetime objects to strings for JSON
for row in res:
    row['start'] = row['start'].isoformat()
    row['end'] = row['end'].isoformat()

print(json.dumps(res))
