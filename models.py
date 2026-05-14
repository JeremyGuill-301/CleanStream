from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

def init_models(db):
    class User(UserMixin, db.Model):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        full_name = db.Column(db.String(120))
        email = db.Column(db.String(120), unique=True)
        password_hash = db.Column(db.String(255))
        role = db.Column(db.Enum('OfficeAdmin', 'Cleaner', 'BusinessOwner'), nullable=False)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)
        
        @staticmethod
        def hash_password(password):
            return generate_password_hash(password)

    # Re-adding this class to fix the "not enough values to unpack" error
    class CustomerContact(db.Model):
        __tablename__ = 'customer_contacts'
        customer_id = db.Column(db.Integer, primary_key=True)

    class Appointment(db.Model):
        __tablename__ = 'appointments'
        apt_id = db.Column(db.Integer, primary_key=True)
        cleaner_id = db.Column(db.Integer, nullable=False)
        status = db.Column(db.Enum('Pending', 'In Progress', 'Finished', 'Busy', 'Cancelled'), default='Pending')
        scheduled_time = db.Column(db.DateTime)
        end_time = db.Column(db.DateTime)
        service_notes = db.Column(db.Text)

    # Returning 3 items now to match app.py expectation
    return User, CustomerContact, Appointment
