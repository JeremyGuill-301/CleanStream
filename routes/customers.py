from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Appointment, User, CustomerContact
from sqlalchemy import func
from datetime import datetime, timedelta, date

customer_bp = Blueprint('customer', __name__, url_prefix='/customer', template_folder='/templates')

def tenure_text(anniversary):
    if not anniversary:
        return None
    if isinstance(anniversary, datetime):
        anniversary = anniversary.date()
    today = date.today()
    total_days = (today - anniversary).days
    if total_days < 0:
        return None
    years = total_days // 365
    remaining = total_days % 365
    months = remaining // 30
    days = remaining % 30
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days > 0 or not parts:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]

# Supplies routes
@customer_bp.route('/')
@login_required
def supplies_index():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return redirect(url_for('mobile_view'))

    customers = CustomerContact.query.order_by(CustomerContact.last_name, CustomerContact.first_name).all()
    now = datetime.now()
    sixty_days_ago = now - timedelta(days=60)

    # Revenue per customer (paid)
    revenue_query = (db.session.query(Appointment.customer_id, func.sum(Appointment.cost))
                    .filter(Appointment.status == 'Paid')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_revenue = {customer_id: float(revenue) for customer_id, revenue in revenue_query}

    # Outstanding balance per customer (Finished = work done, not paid)
    outstanding_query = (db.session.query(Appointment.customer_id, func.sum(Appointment.cost))
                    .filter(Appointment.status == 'Finished')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_outstanding = {customer_id: float(balance) for customer_id, balance in outstanding_query}

    # Overdue days: most recent Finished appointment end_time per customer
    overdue_query = (db.session.query(Appointment.customer_id, func.max(Appointment.end_time))
                    .filter(Appointment.status == 'Finished')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_overdue_days = {}
    for customer_id, last_finished in overdue_query:
        if last_finished:
            delta = now - last_finished
            cust_overdue_days[customer_id] = delta.days

    # Recent appointments (last 60 days) per customer
    recent_apts_query = (db.session.query(Appointment.customer_id, func.count(Appointment.apt_id))
                    .filter(Appointment.scheduled_time >= sixty_days_ago)
                    .filter(Appointment.scheduled_time <= now)
                    .filter(Appointment.status != 'Cancelled')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_has_recent = {customer_id: count > 0 for customer_id, count in recent_apts_query}

    # Future appointments per customer
    future_apts_query = (db.session.query(Appointment.customer_id, func.count(Appointment.apt_id))
                    .filter(Appointment.scheduled_time > now)
                    .filter(Appointment.status != 'Cancelled')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_has_future = {customer_id: count > 0 for customer_id, count in future_apts_query}

    # Last appointment date per customer (any status except Cancelled)
    last_apt_query = (db.session.query(Appointment.customer_id, func.max(Appointment.scheduled_time))
                    .filter(Appointment.status != 'Cancelled')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_last_apt = {customer_id: last_date for customer_id, last_date in last_apt_query}

    # Next future appointment date per customer
    next_apt_query = (db.session.query(Appointment.customer_id, func.min(Appointment.scheduled_time))
                    .filter(Appointment.scheduled_time > now)
                    .filter(Appointment.status != 'Cancelled')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_next_apt = {customer_id: next_date for customer_id, next_date in next_apt_query}

    # Total appointment count per customer
    total_apt_query = (db.session.query(Appointment.customer_id, func.count(Appointment.apt_id))
                    .filter(Appointment.status != 'Cancelled')
                    .group_by(Appointment.customer_id)
                    .all()
                    )
    cust_total_apts = {customer_id: count for customer_id, count in total_apt_query}

    cust_count = len(customers)
    context = {
        'customers': customers,
        'cust_revenue': cust_revenue,
        'cust_outstanding': cust_outstanding,
        'cust_overdue_days': cust_overdue_days,
        'cust_has_future': cust_has_future,
        'cust_has_recent': cust_has_recent,
        'cust_last_apt': cust_last_apt,
        'cust_next_apt': cust_next_apt,
        'cust_total_apts': cust_total_apts,
        'cust_count': cust_count,
        'sixty_days_ago': sixty_days_ago,
    }
    return render_template('customers/index.html', **context)

@customer_bp.route('/<int:customer_id>/details')
@login_required
def customer_details(customer_id):
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return jsonify({'error': 'Unauthorized'}), 403

    customer = CustomerContact.query.get_or_404(customer_id)
    now = datetime.now()

    # Last appointment date
    last_apt = (Appointment.query
                .filter(Appointment.customer_id == customer_id, Appointment.status != 'Cancelled')
                .order_by(Appointment.scheduled_time.desc())
                .first())

    # Next appointment date
    next_apt = (Appointment.query
                .filter(Appointment.customer_id == customer_id,
                        Appointment.scheduled_time > now,
                        Appointment.status != 'Cancelled')
                .order_by(Appointment.scheduled_time.asc())
                .first())

    # All jobs for this customer
    jobs = (Appointment.query
            .filter(Appointment.customer_id == customer_id)
            .order_by(Appointment.scheduled_time.desc())
            .all())

    # Payment history (Paid status)
    payments = (Appointment.query
                .filter(Appointment.customer_id == customer_id, Appointment.status == 'Paid')
                .order_by(Appointment.paid_date.desc())
                .all())

    # Outstanding balance (Finished but not paid)
    balance_row = (db.session.query(func.sum(Appointment.cost))
                   .filter(Appointment.customer_id == customer_id, Appointment.status == 'Finished')
                   .first())
    balance = float(balance_row[0]) if balance_row and balance_row[0] else 0.0

    return jsonify({
        'customer': {
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'phone': customer.phone,
            'email': customer.email,
            'address': customer.address,
            'city': customer.city,
            'state': customer.state,
            'zip_code': customer.zip_code,
            'property_nickname': customer.property_nickname,
            'anniversary': customer.anniversary.isoformat() if customer.anniversary else None,
            'tenure': tenure_text(customer.anniversary),
        },
        'last_job_date': last_apt.scheduled_time.isoformat() if last_apt and last_apt.scheduled_time else None,
        'next_job_date': next_apt.scheduled_time.isoformat() if next_apt and next_apt.scheduled_time else None,
        'balance': balance,
        'jobs': [{
            'apt_id': a.apt_id,
            'scheduled_time': a.scheduled_time.isoformat() if a.scheduled_time else None,
            'cleaner_name': User.query.get(a.cleaner_id).full_name if User.query.get(a.cleaner_id) else 'Unknown',
            'status': a.status,
            'cost': float(a.cost) if a.cost else 0.0,
            'service_notes': a.service_notes or '',
        } for a in jobs],
        'payments': [{
            'apt_id': a.apt_id,
            'paid_date': a.paid_date.isoformat() if a.paid_date else None,
            'cost': float(a.cost) if a.cost else 0.0,
            'service_notes': a.service_notes or '',
            'scheduled_time': a.scheduled_time.isoformat() if a.scheduled_time else None,
        } for a in payments],
    })
