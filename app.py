import os
from datetime import date, datetime, timedelta, time
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_migrate import Migrate
from models import User, Appointment, CustomerContact
from extensions import db, login_manager, migrate


# Define the Global Variable
# This points to the root directory of your project
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Use the Global Variable to define sub-paths
template_dir = os.path.join(BASE_DIR, 'templates')
static_dir = os.path.join(BASE_DIR, 'static')

load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:CleanStream475%23@35.171.82.228/cleanstream_db?charset=utf8mb4'
app.config['SECRET_KEY'] = 'CleanStream_Sprint3_2026'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
# Use the extension-managed LoginManager and Migrate instances so there's a single
# SQLAlchemy / LoginManager object shared across the codebase.
login_manager.init_app(app)
login_manager.login_view = 'login_page'


# --- CREATE TABLES ---
with app.app_context():
    db.create_all()
    print("Database connection established.")
    print("Tables created successfully.")
    print("----------------------------------------")
    print("Server is ready to accept requests.")


# Initialize Migration
migrate.init_app(app, db)

# Populate customer anniversaries on startup
def populate_anniversaries():
    from sqlalchemy import func as sa_func
    from sqlalchemy.exc import OperationalError
    try:
        customers_without = CustomerContact.query.filter(CustomerContact.anniversary.is_(None)).all()
        if not customers_without:
            return
        for c in customers_without:
            first_apt = (db.session.query(sa_func.min(Appointment.scheduled_time))
                         .filter(Appointment.customer_id == c.customer_id,
                                 Appointment.status != 'Cancelled')
                         .first())
            first_date = first_apt[0] if first_apt and first_apt[0] else None
            if first_date:
                c.anniversary = first_date.date() if hasattr(first_date, 'date') else first_date
            else:
                c.anniversary = c.created_at.date() if c.created_at else None
        db.session.commit()
    except OperationalError:
        db.session.rollback()

with app.app_context():
    populate_anniversaries()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---BLUEPRINTS---
from routes.main import main_bp
from routes.supplies import supply_bp
from routes.admin import admin_bp
from routes.financials import financials_bp
from routes.customers import customer_bp

app.register_blueprint(main_bp)
app.register_blueprint(supply_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(financials_bp)
app.register_blueprint(customer_bp)

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

@app.route('/appointments/<int:id>/start', methods=['POST'])
@login_required
def start_appointment(id):

    appointment = Appointment.query.get(id)

    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    appointment.status = "In Progress"
    appointment.actual_start_time = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": "Appointment started successfully"
    }), 200

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return redirect(url_for('mobile_view'))
    
    # Data for the admin dashboard and directory
    employees = User.query.all()
    pending = Appointment.query.filter(Appointment.status.in_(['Pending', 'Scheduled'])).count()
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

@app.route('/mobile/', defaults={'date_str': None})
@app.route('/mobile/<date_str>')
@login_required
def mobile_view(date_str):
    if current_user.role != 'Cleaner':
        return redirect(url_for('dashboard'))

    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = date.today()
    else:
        current_date = date.today()

    start_of_day = datetime.combine(current_date, time.min)
    end_of_day = datetime.combine(current_date, time.max)

    agenda = Appointment.query.filter(
        Appointment.cleaner_id == current_user.id,
        Appointment.scheduled_time >= start_of_day,
        Appointment.scheduled_time <= end_of_day
    ).all()

    prev_date = current_date - timedelta(days=1)
    next_date = current_date + timedelta(days=1)

    return render_template('mobile/agenda.html',
                           agenda=agenda,
                           current_date=current_date,
                           prev_date=prev_date,
                           next_date=next_date,
                           today=date.today())

@app.route('/update_status/<int:apt_id>', methods=['POST'])
@login_required
def update_status(apt_id):
    appointment = Appointment.query.get_or_404(apt_id)
    if appointment.cleaner_id == current_user.id:
       new_status = request.form.get('status')
       appointment.status = new_status
    
       if new_status == "In Progress" and not appointment.actual_start_time:
          appointment.actual_start_time = datetime.utcnow()

       if new_status == "Finished" and not appointment.actual_finish_time:
          appointment.actual_finish_time = datetime.utcnow()

       db.session.commit()

    return redirect(url_for(
        'mobile_view',
        date_str=appointment.scheduled_time.date()
    ))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True, port=5002)
