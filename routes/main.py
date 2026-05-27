from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User

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
            JOIN user u ON a.cleaner_id = u.id;
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
        start = request.args.get('start_time')
        end = request.args.get('end_time')
        house = request.args.get('house', 'Not Assigned')
        
        if not u_id or not start or not end:
            return jsonify({"status": "error", "message": "Missing arguments"}), 400

        #  FIXED: 'status' set to 'Scheduled' when a job is scheduled.
        # House string is safely preserved inside the TEXT field 'service_notes'.
        insert_query = """
            INSERT INTO appointments (cleaner_id, scheduled_time, end_time, service_notes, status) 
            VALUES (:cleaner_id, :start_time, :end_time, :service_notes, 'Scheduled')
        """
        db.session.execute(db.text(insert_query), {
            'cleaner_id': u_id,
            'start_time': start,
            'end_time': end,
            'service_notes': house
        })
        db.session.commit()
        return jsonify({"status": "success", "message": "Appointment created!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Insertion Error: {str(e)}"}), 500


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
    """Queries your 'user' table safely for all records where role='Cleaner'."""
    try:
        query = "SELECT id, full_name, email FROM user WHERE role = 'Cleaner';"
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

