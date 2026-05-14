#! /var/www/html/venv/bin/python
import mysql.connector
import json
import sys

def check_booking_conflict(cleaner_id, new_start, new_end):
    try:
        conn = mysql.connector.connect(
            host="localhost", user="root", 
            password="YOUR_PASSWORD", database="cleanstream_db"
        )
        cursor = conn.cursor(dictionary=True)

        # Query to find overlapping appointments for the same cleaner
        query = """
            SELECT * FROM appointments 
            WHERE cleaner_id = %s 
            AND (%s < end_time AND %s > scheduled_time)
        """
        cursor.execute(query, (cleaner_id, new_start, new_end))
        conflicts = cursor.fetchall()
        
        return len(conflicts) > 0
    except Exception as e:
        return str(e)
    finally:
        if 'conn' in locals(): conn.close()

# Example usage for API
if __name__ == "__main__":
    # has_conflict = check_booking_conflict(1, '2026-05-08 09:00:00', '2026-05-08 11:00:00')
    pass
