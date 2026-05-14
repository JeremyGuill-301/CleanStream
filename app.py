import os
from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user, login_user, logout_user

# Define the Global Variable
# This points to the root directory of your project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Use the Global Variable to define sub-paths
template_dir = os.path.join(BASE_DIR, 'templates')
static_dir = os.path.join(BASE_DIR, 'static')
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:CleanStream475#@localhost/cleanstream_db'
app.config['SECRET_KEY'] = 'CleanStream_Sprint3_2026'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'

# --- MODELS ---
# Fixed unpacking to expect exactly 3 classes
from models import init_models
User, CustomerContact, Appointment = init_models(db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login_page'))
    if current_user.role == 'Cleaner':
        return redirect(url_for('mobile_view'))
    return redirect(url_for('dashboard'))

@app.route('/auth/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        # Check password hash (or plain text for legacy support)
        if user and (user.password_hash == password or user.check_password(password)):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('auth/login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return redirect(url_for('mobile_view'))
    
    # Data for the admin dashboard and directory
    employees = User.query.all()
    pending = Appointment.query.filter_by(status='Pending').count()
    return render_template('main/dashboard.html', employees=employees, pending=pending)

@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    if current_user.role != 'OfficeAdmin':
        return redirect(url_for('dashboard'))
    try:
        new_user = User(
            username=request.form.get('username'),
            full_name=request.form.get('full_name'),
            email=request.form.get('email'),
            role=request.form.get('role'),
            password_hash=User.hash_password(request.form.get('password'))
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User Added Successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}')
    return redirect(url_for('dashboard'))

@app.route('/mobile')
@login_required
def mobile_view():
    if current_user.role != 'Cleaner':
        return redirect(url_for('dashboard'))
    # Daily Agenda for cleaners
    agenda = Appointment.query.filter_by(cleaner_id=current_user.id).all()
    return render_template('mobile/agenda.html', agenda=agenda)

@app.route('/update_status/<int:apt_id>', methods=['POST'])
@login_required
def update_status(apt_id):
    appointment = Appointment.query.get_or_404(apt_id)
    if appointment.cleaner_id == current_user.id:
        appointment.status = request.form.get('status')
        db.session.commit()
    return redirect(url_for('mobile_view'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)
