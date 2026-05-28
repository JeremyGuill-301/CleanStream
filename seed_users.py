from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
# Added a 10-second timeout so it doesn't hang forever
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.Enum('OfficeAdmin', 'Cleaner', 'BusinessOwner'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

with app.app_context():
    db.create_all()
    print("--- Seeding users ---")

    print("Connecting to database...")
    joseph = User(
        username='joseph',
        full_name='Joseph Jimenez',
        role='OfficeAdmin',
        password_hash=generate_password_hash('CleanStream2026!')
    )
    jeremy = User(
        username='jeremy',
        full_name='Jeremy Guill',
        role='OfficeAdmin',
        password_hash=generate_password_hash('Braces4me!')
    )
    allison = User(
        username='allison',
        full_name='Allison Harris',
        role='BusinessOwner',
        password_hash=generate_password_hash('CleanStream2026!')
    )
    jacqueline = User(
        username='jacqueline',
        full_name='Jacqueline',
        role='OfficeAdmin',
        password_hash=generate_password_hash('CleanStream2026!')
    )
    cleaner_joe = User(
        username='cleaner_joe',
        full_name='Joe Cleaner',
        role='Cleaner',
        password_hash=generate_password_hash('clean')
    )
    cleaner_sue = User(
        username='cleaner_sue',
        full_name='Sue Cleaner',
        role='Cleaner',
        password_hash=generate_password_hash('clean')
    )
    cleaner_phyllis = User(
        username='cleaner_phyllis',
        full_name='Phyllis Cleaner',
        role='Cleaner',
        password_hash=generate_password_hash('clean')
    )

    usrs = [joseph, jeremy, allison, jacqueline, cleaner_joe, cleaner_sue, cleaner_phyllis]
    print("--- Adding users ---")
    for usr in usrs:
        print(f"--- {usr.full_name.title()} added ---")

    try:
        db.session.add_all([joseph, jeremy, allison, jacqueline, cleaner_joe, cleaner_sue, cleaner_phyllis])
        db.session.commit()
    except Exception as e:
        print(f"Error: {e}")
