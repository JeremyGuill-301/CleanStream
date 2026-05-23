import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

print(f"[{datetime.now()}] Starting automated appointment reminder scan...")

# 1. Initialize standalone context environment
app = Flask(__name__)
db_url = os.environ.get("DATABASE_URL", "mysql+pymysql://root:CleanStream475%23@localhost/cleanstream_db")
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# SMTP Server Configurations (Falls back to standard local settings if env variables aren't set yet)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "your-cleanstream-email@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "your-app-password")

# 2. Database Model Mapping
class CustomerContact(db.Model):
    __tablename__ = 'customer_contacts'
    customer_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))

class Appointment(db.Model):
    __tablename__ = 'appointments'
    apt_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer_contacts.customer_id'))
    scheduled_time = db.Column(db.DateTime)
    reminder_sent = db.Column(db.Boolean, default=False)

# 3. Outbound Mail Sender Logic
def send_reminder_email(recipient_email, scheduled_time):
    if not recipient_email or recipient_email == "No Email Found":
        print("   X Skipping mail delivery: Invalid email address format.")
        return False

    msg = MIMEMultipart()
    msg['From'] = SMTP_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = "CleanStream - Reminder: Your Upcoming Cleaning Appointment Tomorrow!"

    # Clean styling for a professional team project appearance
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <h2 style="color: #0284c7;">Hello from CleanStream!</h2>
        <p>This is a friendly automated reminder that you have a cleaning appointment scheduled with us tomorrow:</p>
        <table style="border-collapse: collapse; width: 100%; max-width: 500px; margin: 20px 0;">
          <tr>
            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f9fafb;">Scheduled Time</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{scheduled_time.strftime('%I:%M %p')}</td>
          </tr>
          <tr>
            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; background-color: #f9fafb;">Scheduled Date</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{scheduled_time.strftime('%A, %B %d, %Y')}</td>
          </tr>
        </table>
        <p>If you need to make any changes or reschedule, please log into your CleanStream portal dashboard as soon as possible.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin-top: 30px;">
        <p style="font-size: 0.85em; color: #777;">This is an automated system notification. Please do not reply directly to this email message.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    try:
        # Establish connection secure channel
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"   ✓ Email notification successfully dispatched to {recipient_email}")
        return True
    except Exception as e:
        print(f"   X Failed to transmit email over SMTP: {e}")
        return False

# 4. Processing Engine Loop
with app.app_context():
    tomorrow_start = datetime.now().date() + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    upcoming_appointments = Appointment.query.filter(
        Appointment.scheduled_time >= tomorrow_start,
        Appointment.scheduled_time < tomorrow_end,
        Appointment.reminder_sent == False
    ).all()

    if not upcoming_appointments:
        print("No pending reminders found for tomorrow.")
    else:
        print(f"Found {len(upcoming_appointments)} reminders to process.")

        for appt in upcoming_appointments:
            customer = CustomerContact.query.get(appt.customer_id)
            customer_email = customer.email if customer else "No Email Found"
            
            print(f"--> Processing Customer ID {appt.customer_id} ({customer_email}) scheduled for {appt.scheduled_time}")
            
            # Fire email notification
            email_delivered = send_reminder_email(customer_email, appt.scheduled_time)
            
            # Flip database flag only if transmission succeeds
            if email_delivered:
                appt.reminder_sent = True
        
        db.session.commit()
        print("Database execution complete. Target flags successfully synchronized.")
