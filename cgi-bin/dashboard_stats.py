#!/var/www/html/venv/bin/python3
import mysql.connector
import json
import sys

# DATABASE SETTINGS 
db_config = {
    'host': 'localhost',
    'user': 'root',       # specific MySQL username
    'password': 'CleanStream475#', 
    'database': 'cleanstream_db'
}

print("Content-Type: application/json\n")

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Get count of appointments for today
    cursor.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date = CURDATE()")
    result = cursor.fetchone()
    count = result[0] if result else 0
    
    response = {
        "today_count": count,
        "status": "Connected"
    }
    print(json.dumps(response))
    
    cursor.close()
    conn.close()

except Exception as e:
    # If it fails, send the error back to the dashboard
    print(json.dumps({"today_count": "!", "status": str(e)}))
