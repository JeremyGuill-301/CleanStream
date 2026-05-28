from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User, CustomerContact, Appointment
from datetime import datetime

main_bp = Blueprint('main', __name__, url_prefix='/main', template_folder='/templates')

# ==========================================
#  Core App Dashboard & Profile Routes
# ==========================================

@main_bp.route('/')
@login_required
def dashboard():
    #  Query the user table records so Jeremy's HTML template can loop through the!
    employees = User.query.all()
    
    #  Calculate the count of pending appointments from the database
    try:
        pending_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM appointments WHERE status IN ('Pending', 'Scheduled')")
        ).scalar()
    except Exception:
        pending_count = 0

    return render_template('main/dashboard.html', user=current_user, employees=employees, pending=pending_count)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('main/profile.html', user=current_user)


# ==========================================
#  Database-Aligned Scheduler API Endpoints
# ==========================================

@main_bp.route('/scheduler')
@login_required
def scheduler():
    """Renders the calendar management interface layout."""
    return render_template('main/scheduler.html')


@main_bp.route('/api/calendar-data')
@login_required
def get_calendar_data():
    """Fetches scheduled appointments aligned with the exact database schema columns."""
    try:
        #  FIXED: Query updated to match apt_id and fetch service_notes for the property name
        query = """
            SELECT 
                a.apt_id AS id,
                u.full_name AS title, 
                a.scheduled_time AS start, 
                a.end_time AS end,
                a.service_notes AS notes
            FROM appointments a
            JOIN user u ON a.cleaner_id = u.id
            WHERE a.status != 'Cancelled';
        """
        result = db.session.execute(db.text(query))
        
        events = []
        for row in result:
            try:
                r_id = row.id
                r_title = row.title
                r_start = row.start
                r_end = row.end
                r_notes = row.notes
            except AttributeError:
                r_id = row[0]
                r_title = row[1]
                r_start = row[2]
                r_end = row[3]
                r_notes = row[4]

            # If a property name exists in service_notes, append it visually to the calendar box
            display_title = r_title
            if r_notes:
                display_title = f"{r_title} ({r_notes})"

            events.append({
                'id': r_id,
                'title': display_title,
                'start': r_start.isoformat() if r_start else None,
                'end': r_end.isoformat() if r_end else None
            })
        return jsonify(events)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Calendar Error: {str(e)}"}), 500


@main_bp.route('/api/make-appointment')
@login_required
def make_appointment():
    """Saves an appointment using apt_id structure and avoids crashing the status ENUM constraints."""
    try:
        u_id = request.args.get('user_id')
        customer_id = request.args.get('customer_id')
        start = request.args.get('start_time')
        end = request.args.get('end_time')
        cost = request.args.get('cost')
        house = request.args.get('house', 'Not Assigned')
        
        if not u_id or not customer_id or not start or not end or not cost:
            return jsonify({"status": "error", "message": "Missing arguments"}), 400

        insert_query = """
            INSERT INTO appointments (cleaner_id, customer_id, scheduled_time, end_time, cost, service_notes, status) 
            VALUES (:cleaner_id, :customer_id, :start_time, :end_time, :cost, :service_notes, 'Scheduled')
        """
        db.session.execute(db.text(insert_query), {
            'cleaner_id': u_id,
            'customer_id': customer_id,
            'start_time': start,
            'end_time': end,
            'cost': cost,
            'service_notes': house
        })
        db.session.commit()
        return jsonify({"status": "success", "message": "Appointment created!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Insertion Error: {str(e)}"}), 500


@main_bp.route('/api/appointment/<int:appointment_id>')
@login_required
def get_appointment(appointment_id):
    """Returns full details for a single appointment."""
    try:
        apt = Appointment.query.get_or_404(appointment_id)
        cleaner = User.query.get(apt.cleaner_id)
        customer = CustomerContact.query.get(apt.customer_id)

        return jsonify({
            'apt_id': apt.apt_id,
            'cleaner_id': apt.cleaner_id,
            'cleaner_name': cleaner.full_name if cleaner else 'Unknown',
            'customer_id': apt.customer_id,
            'customer_name': f'{customer.last_name}, {customer.first_name}' if customer else 'Unknown',
            'customer_address': customer.full_address() if customer else '',
            'customer_phone': customer.phone if customer else '',
            'customer_email': customer.email if customer else '',
            'status': apt.status,
            'scheduled_time': apt.scheduled_time.isoformat() if apt.scheduled_time else None,
            'end_time': apt.end_time.isoformat() if apt.end_time else None,
            'actual_start_time': apt.actual_start_time.isoformat() if apt.actual_start_time else None,
            'actual_finish_time': apt.actual_finish_time.isoformat() if apt.actual_finish_time else None,
            'hours_spent': float(apt.hours_spent) if apt.hours_spent else None,
            'service_notes': apt.service_notes or '',
            'cost': float(apt.cost) if apt.cost else None,
            'paid_date': apt.paid_date.isoformat() if apt.paid_date else None,
            'created_at': apt.created_at.isoformat() if apt.created_at else None,
            'updated_at': apt.updated_at.isoformat() if apt.updated_at else None,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route('/api/update-appointment', methods=['POST'])
@login_required
def update_appointment():
    """Updates appointment fields based on status-based permissions."""
    try:
        apt_id = request.form.get('apt_id')
        apt = Appointment.query.get_or_404(apt_id)

        role = current_user.role
        is_admin = role in ('OfficeAdmin', 'BusinessOwner')
        is_same_day = apt.scheduled_time and apt.scheduled_time.date() == datetime.utcnow().date()

        # Determine permissions
        can_edit = False
        can_cancel = False

        if apt.status in ('Pending', 'Scheduled'):
            if is_same_day:
                can_edit = is_admin
                can_cancel = is_admin
            else:
                can_edit = True
                can_cancel = True
        elif apt.status == 'In Progress':
            can_edit = is_admin
            can_cancel = is_admin
        elif apt.status == 'Finished':
            can_edit = False
            can_cancel = False

        if not can_edit:
            return jsonify({"status": "error", "message": "You do not have permission to edit this appointment"}), 403

        # Update allowed fields
        cleaner_id = request.form.get('cleaner_id')
        start_time = request.form.get('scheduled_time')
        end_time = request.form.get('end_time')
        service_notes = request.form.get('service_notes')
        action = request.form.get('action')

        if cleaner_id:
            apt.cleaner_id = int(cleaner_id)
        if start_time:
            apt.scheduled_time = datetime.fromisoformat(start_time)
        if end_time:
            apt.end_time = datetime.fromisoformat(end_time)
        if service_notes is not None:
            apt.service_notes = service_notes

        # Handle cancel action
        if action == 'cancel' and can_cancel:
            apt.status = 'Cancelled'

        db.session.commit()
        return jsonify({"status": "success", "message": "Appointment updated successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Update Error: {str(e)}"}), 500


@main_bp.route('/api/delete-appointment', methods=['POST'])
@login_required
def delete_appointment():
    """Removes an appointment record safely using the apt_id column key constraint."""
    try:
        appointment_id = request.args.get('id')
        
        if not appointment_id:
            return jsonify({"status": "error", "message": "Missing target appointment identifier"}), 400

        #  FIXED: Target key mapped explicitly to apt_id
        delete_query = "DELETE FROM appointments WHERE apt_id = :id"
        db.session.execute(db.text(delete_query), {'id': appointment_id})
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Appointment deleted successfully."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Deletion Failure: {str(e)}"}), 500


@main_bp.route('/api/cleaners')
@login_required
def get_cleaners():
    """Queries your 'user' table for all active Cleaner records."""
    try:
        query = "SELECT id, full_name, email FROM user WHERE role = 'Cleaner' AND active = TRUE;"
        result = db.session.execute(db.text(query))
        
        cleaners = []
        for row in result:
            try:
                c_id = row.id
                c_name = row.full_name
                c_email = row.email
            except AttributeError:
                c_id = row[0]
                c_name = row[1]
                c_email = row[2]

            cleaners.append({
                'id': c_id,
                'full_name': c_name if c_name else "Unnamed Cleaner",
                'email': c_email if c_email is not None else 'No Email Provided'
            })
            
        return jsonify(cleaners)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Cleaner Pull Error: {str(e)}"}), 500


@main_bp.route('/api/last-cost/<int:customer_id>')
@login_required
def get_last_cost(customer_id):
    """Returns the cost from the most recent appointment for this customer."""
    try:
        last = (Appointment.query
                .filter(Appointment.customer_id == customer_id,
                        Appointment.cost.isnot(None))
                .order_by(Appointment.scheduled_time.desc())
                .first())
        return jsonify({
            'last_cost': float(last.cost) if last and last.cost else None
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@main_bp.route('/api/customers')
@login_required
def get_customers():
    """Returns all customer contacts from the customer_contacts table."""
    try:
        customers = CustomerContact.query.order_by(CustomerContact.last_name, CustomerContact.first_name).all()
        result = []
        for c in customers:
            result.append({
                'customer_id': c.customer_id,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'full_address': c.full_address()
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Customer Pull Error: {str(e)}"}), 500

