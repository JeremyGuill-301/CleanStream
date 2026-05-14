#! /var/www/html/venv/bin/python
import mysql.connector
import json

print("Content-Type: application/json\n")

try:
    conn = mysql.connector.connect(
        host="localhost", user="root", 
        password="CleanStream475#", database="cleanstream_db"
)   
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT customer_id, first_name, last_name, email_address, phone_number FROM customer_contacts")
    print(json.dumps(cursor.fetchall()))
except Exception as e:
    print(json.dumps([{"error": str(e)}]))
