from app import app
from extensions import db
from models import User

with app.app_context():
    # Create admin user
    admin = User(
        username='admin',
        full_name='Admin User',
        role='admin'
    )
    admin.set_password('admin123')

    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully!')
    print('Username: admin')
    print('Password: admin123')
