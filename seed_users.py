from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
# Added a 10-second timeout so it doesn't hang forever
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:CleanStream475#@localhost/cleanstream_db?connect_timeout=10'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user' # table name
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255))
    full_name = db.Column(db.String(100))
    role = db.Column(db.Enum('OfficeAdmin', 'Cleaner', 'BusinessOwner'))

with app.app_context():
    print("Connecting to database...")
    # Just trying to add Joseph first to see if it works
    new_user = User(
        username='joseph',
        full_name='Joseph Jimenez',
        role='BusinessOwner',
        password_hash=generate_password_hash('CleanStream2026!')
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        print("--- SUCCESS: Joseph added ---")
    except Exception as e:
        print(f"Error: {e}")
