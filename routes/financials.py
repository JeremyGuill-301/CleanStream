from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Appointment, User
from datetime import datetime, timedelta
from sqlalchemy import func, case
import calendar

financials_bp = Blueprint('financials', __name__, url_prefix='/financials', template_folder='/templates')

@financials_bp.route("/")
@login_required
def dashboard():
    if current_user.role != 'BusinessOwner':
        return redirect(url_for('main.dashboard'))
    
    return render_template("financials/financials_dashboard.html")


@financials_bp.route("/api/dashboard-summary")
@login_required
def get_dashboard_summary():
    """Get summary metrics for the dashboard"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get current date info for calculations
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())
    
    # Last month
    if today.month == 1:
        last_month_start = today.replace(year=today.year - 1, month=12, day=1)
    else:
        last_month_start = today.replace(month=today.month - 1, day=1)
    
    # Calculate last month end
    if today.month == 1:
        last_month_end = today.replace(year=today.year - 1, month=12, day=31)
    else:
        last_month_end = today.replace(day=1) - timedelta(days=1)
    
    # Total paid revenue (completed jobs with Paid status)
    total_paid = db.session.query(func.sum(Appointment.cost)).filter(
        Appointment.status == 'Paid'
    ).scalar() or 0
    
    # Unpaid revenue (Finished but not Paid)
    total_unpaid = db.session.query(func.sum(Appointment.cost)).filter(
        Appointment.status == 'Finished'
    ).scalar() or 0
    
    # This month paid revenue
    month_paid = db.session.query(func.sum(Appointment.cost)).filter(
        Appointment.status == 'Paid',
        func.date(Appointment.paid_date) >= start_of_month,
        func.date(Appointment.paid_date) <= today
    ).scalar() or 0
    
    # Last month paid revenue
    last_month_paid = db.session.query(func.sum(Appointment.cost)).filter(
        Appointment.status == 'Paid',
        func.date(Appointment.paid_date) >= last_month_start,
        func.date(Appointment.paid_date) <= last_month_end
    ).scalar() or 0
    
    # This week paid revenue
    week_paid = db.session.query(func.sum(Appointment.cost)).filter(
        Appointment.status == 'Paid',
        func.date(Appointment.paid_date) >= start_of_week,
        func.date(Appointment.paid_date) <= today
    ).scalar() or 0
    
    # Calculate month-over-month change
    mom_change = float(month_paid) - float(last_month_paid) if last_month_paid else float(month_paid)
    mom_percent = (mom_change / float(last_month_paid) * 100) if last_month_paid else 0
    
    return jsonify({
        "total_paid": float(total_paid),
        "total_unpaid": float(total_unpaid),
        "month_paid": float(month_paid),
        "week_paid": float(week_paid),
        "last_month_paid": float(last_month_paid),
        "mom_change": mom_change,
        "mom_percent": round(mom_percent, 2),
        "total_balance": float(total_paid)  # For now, balance equals paid revenue
    })


@financials_bp.route("/api/revenue-by-week")
@login_required
def get_revenue_by_week():
    """Get revenue data by week for the past 12 weeks"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    weeks_data = []
    today = datetime.now().date()
    
    # Get data for past 12 weeks
    for i in range(11, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7*i)
        week_end = week_start + timedelta(days=6)
        
        revenue = db.session.query(func.sum(Appointment.cost)).filter(
            Appointment.status == 'Paid',
            func.date(Appointment.paid_date) >= week_start,
            func.date(Appointment.paid_date) <= week_end
        ).scalar() or 0
        
        week_label = f"Week of {week_start.strftime('%m/%d')}"
        weeks_data.append({
            "week": week_label,
            "revenue": float(revenue),
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat()
        })
    
    return jsonify(weeks_data)


@financials_bp.route("/api/revenue-by-month")
@login_required
def get_revenue_by_month():
    """Get revenue data by month for the past 12 months"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    months_data = []
    today = datetime.now().date()
    
    # Get data for past 12 months
    for i in range(11, -1, -1):
        if today.month - i <= 0:
            month = today.month - i + 12
            year = today.year - 1
        else:
            month = today.month - i
            year = today.year
        
        # Get first and last day of month
        if month == 12:
            month_end = today.replace(year=year, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(year=year, month=month + 1, day=1) - timedelta(days=1)
        
        month_start = today.replace(year=year, month=month, day=1)
        
        revenue = db.session.query(func.sum(Appointment.cost)).filter(
            Appointment.status == 'Paid',
            func.date(Appointment.paid_date) >= month_start,
            func.date(Appointment.paid_date) <= month_end
        ).scalar() or 0
        
        month_label = calendar.month_abbr[month]
        months_data.append({
            "month": month_label,
            "revenue": float(revenue),
            "start_date": month_start.isoformat(),
            "end_date": month_end.isoformat()
        })
    
    return jsonify(months_data)


@financials_bp.route("/api/service-performance")
@login_required
def get_service_performance():
    """Get performance metrics by cleaner"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get performance data grouped by cleaner
    cleaner_stats = db.session.query(
        User.full_name,
        func.count(Appointment.apt_id).label('total_jobs'),
        func.sum(Appointment.cost).label('total_revenue'),
        func.count(func.case([(Appointment.status == 'Paid', 1)])).label('paid_jobs')
    ).outerjoin(
        Appointment, User.id == Appointment.cleaner_id
    ).filter(
        User.role == 'Cleaner'
    ).group_by(
        User.id, User.full_name
    ).all()
    
    stats = []
    for cleaner_name, total_jobs, total_revenue, paid_jobs in cleaner_stats:
        stats.append({
            "cleaner": cleaner_name or "Unknown",
            "total_jobs": total_jobs or 0,
            "paid_jobs": paid_jobs or 0,
            "total_revenue": float(total_revenue or 0),
            "completion_rate": round((paid_jobs / total_jobs * 100) if total_jobs else 0, 2)
        })
    
    return jsonify(stats)


@financials_bp.route("/api/recent-transactions")
@login_required
def get_recent_transactions():
    """Get recent paid and unpaid transactions"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get recent transactions (limit to 50)
    recent = db.session.query(
        Appointment.apt_id,
        Appointment.scheduled_time,
        Appointment.cost,
        Appointment.status,
        Appointment.paid_date,
        User.full_name
    ).join(
        User, Appointment.cleaner_id == User.id
    ).filter(
        Appointment.status.in_(['Finished', 'Paid'])
    ).order_by(
        Appointment.scheduled_time.desc()
    ).limit(50).all()
    
    transactions = []
    for apt_id, scheduled_time, cost, status, paid_date, cleaner_name in recent:
        transactions.append({
            "apt_id": apt_id,
            "date": scheduled_time.strftime('%Y-%m-%d') if scheduled_time else '',
            "cleaner": cleaner_name or "Unknown",
            "amount": float(cost or 0),
            "status": status,
            "paid_date": paid_date.strftime('%Y-%m-%d') if paid_date else ''
        })
    
    return jsonify(transactions)


@financials_bp.route("/api/utilization-rate")
@login_required
def get_utilization_rate():
    """Get cleaner utilization rates"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get utilization data
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    
    cleaner_stats = db.session.query(
        User.full_name,
        func.count(Appointment.apt_id).label('total_appointments'),
        func.count(func.case([(Appointment.status.in_(['Finished', 'Paid']), 1)])).label('completed_appointments')
    ).outerjoin(
        Appointment, User.id == Appointment.cleaner_id
    ).filter(
        User.role == 'Cleaner',
        func.date(Appointment.scheduled_time) >= start_of_month,
        func.date(Appointment.scheduled_time) <= today
    ).group_by(
        User.id, User.full_name
    ).all()
    
    utilization = []
    for cleaner_name, total, completed in cleaner_stats:
        completion_rate = round((completed / total * 100) if total else 0, 2)
        utilization.append({
            "cleaner": cleaner_name or "Unknown",
            "total_appointments": total or 0,
            "completed": completed or 0,
            "utilization": completion_rate
        })
    
    return jsonify(utilization)


@financials_bp.route("/api/revenue-by-cleaner")
@login_required
def get_revenue_by_cleaner():
    """Get detailed revenue breakdown by cleaner"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    
    # Get all cleaners with their revenue stats
    cleaner_stats = db.session.query(
        User.id,
        User.full_name,
        func.count(Appointment.apt_id).label('total_jobs'),
        func.sum(case((Appointment.status == 'Paid', Appointment.cost), else_=0)).label('paid_revenue'),
        func.sum(case((Appointment.status == 'Finished', Appointment.cost), else_=0)).label('unpaid_revenue'),
        func.count(case((Appointment.status == 'Paid', 1))).label('paid_jobs'),
        func.count(case((Appointment.status == 'Finished', 1))).label('unpaid_jobs'),
        func.avg(case((Appointment.status == 'Paid', Appointment.cost), else_=None)).label('avg_job_value')
    ).outerjoin(
        Appointment, User.id == Appointment.cleaner_id
    ).filter(
        User.role == 'Cleaner'
    ).group_by(
        User.id, User.full_name
    ).order_by(
        func.sum(case((Appointment.status.in_(['Paid', 'Finished']), Appointment.cost), else_=0)).desc()
    ).all()
    
    cleaners = []
    total_all_revenue = 0
    total_paid_revenue = 0
    total_unpaid_revenue = 0
    
    for cleaner_id, name, total_jobs, paid_rev, unpaid_rev, paid_jobs, unpaid_jobs, avg_val in cleaner_stats:
        total_rev = float(paid_rev or 0) + float(unpaid_rev or 0)
        total_all_revenue += total_rev
        total_paid_revenue += float(paid_rev or 0)
        total_unpaid_revenue += float(unpaid_rev or 0)
        
        # Get last 30 days stats for this cleaner
        last_30_days = db.session.query(
            func.count(Appointment.apt_id),
            func.sum(case((Appointment.status.in_(['Paid', 'Finished']), Appointment.cost), else_=0))
        ).filter(
            Appointment.cleaner_id == cleaner_id,
            func.date(Appointment.scheduled_time) >= today - timedelta(days=30),
            func.date(Appointment.scheduled_time) <= today
        ).first()
        
        cleaners.append({
            "cleaner_id": cleaner_id,
            "name": name or "Unknown",
            "total_jobs": total_jobs or 0,
            "paid_jobs": paid_jobs or 0,
            "unpaid_jobs": unpaid_jobs or 0,
            "paid_revenue": float(paid_rev or 0),
            "unpaid_revenue": float(unpaid_rev or 0),
            "total_revenue": total_rev,
            "avg_job_value": round(float(avg_val or 0), 2),
            "last_30_days_jobs": last_30_days[0] or 0,
            "last_30_days_revenue": float(last_30_days[1] or 0)
        })
    
    # Calculate percentages
    for cleaner in cleaners:
        cleaner['revenue_percent'] = round((cleaner['total_revenue'] / total_all_revenue * 100) if total_all_revenue else 0, 1)
        cleaner['collection_rate'] = round((cleaner['paid_revenue'] / cleaner['total_revenue'] * 100) if cleaner['total_revenue'] else 0, 1)
    
    return jsonify({
        "cleaners": cleaners,
        "summary": {
            "total_cleaners": len([c for c in cleaners if c['total_jobs'] > 0]),
            "total_revenue": total_all_revenue,
            "total_paid_revenue": total_paid_revenue,
            "total_unpaid_revenue": total_unpaid_revenue,
            "overall_collection_rate": round((total_paid_revenue / total_all_revenue * 100) if total_all_revenue else 0, 1)
        }
    })


@financials_bp.route("/api/monthly-revenue-breakdown")
@login_required
def get_monthly_revenue_breakdown():
    """Get detailed monthly revenue breakdown with trends"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    today = datetime.now().date()
    
    # Get data for past 12 months
    months_data = []
    
    for i in range(11, -1, -1):
        if today.month - i <= 0:
            month = today.month - i + 12
            year = today.year - 1
        else:
            month = today.month - i
            year = today.year
        
        # Get first and last day of month
        if month == 12:
            month_end = today.replace(year=year, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(year=year, month=month + 1, day=1) - timedelta(days=1)
        
        month_start = today.replace(year=year, month=month, day=1)
        
        # Get monthly stats
        month_stats = db.session.query(
            func.count(Appointment.apt_id).label('total_jobs'),
            func.sum(case((Appointment.status == 'Paid', Appointment.cost), else_=0)).label('paid_revenue'),
            func.sum(case((Appointment.status == 'Finished', Appointment.cost), else_=0)).label('unpaid_revenue'),
            func.count(case((Appointment.status == 'Paid', 1))).label('paid_jobs'),
            func.count(case((Appointment.status == 'Finished', 1))).label('unpaid_jobs')
        ).filter(
            func.date(Appointment.scheduled_time) >= month_start,
            func.date(Appointment.scheduled_time) <= month_end
        ).first()
        
        total_jobs = month_stats[0] or 0
        paid_rev = float(month_stats[1] or 0)
        unpaid_rev = float(month_stats[2] or 0)
        paid_jobs = month_stats[3] or 0
        unpaid_jobs = month_stats[4] or 0
        total_rev = paid_rev + unpaid_rev
        
        months_data.append({
            "month": calendar.month_abbr[month],
            "year": year,
            "month_num": month,
            "total_jobs": total_jobs,
            "paid_jobs": paid_jobs,
            "unpaid_jobs": unpaid_jobs,
            "paid_revenue": paid_rev,
            "unpaid_revenue": unpaid_rev,
            "total_revenue": total_rev,
            "start_date": month_start.isoformat(),
            "end_date": month_end.isoformat()
        })
    
    # Calculate month-over-month changes
    for i in range(len(months_data)):
        if i == 0:
            months_data[i]['mom_change'] = 0
            months_data[i]['mom_percent'] = 0
        else:
            prev_rev = months_data[i-1]['total_revenue']
            curr_rev = months_data[i]['total_revenue']
            change = curr_rev - prev_rev
            months_data[i]['mom_change'] = round(change, 2)
            months_data[i]['mom_percent'] = round((change / prev_rev * 100) if prev_rev else 0, 1)
    
    # Find best and worst months
    valid_months = [m for m in months_data if m['total_revenue'] > 0]
    best_month = max(valid_months, key=lambda x: x['total_revenue']) if valid_months else None
    worst_month = min(valid_months, key=lambda x: x['total_revenue']) if valid_months else None
    
    # Calculate totals
    total_all_revenue = sum(m['total_revenue'] for m in months_data)
    total_paid = sum(m['paid_revenue'] for m in months_data)
    total_unpaid = sum(m['unpaid_revenue'] for m in months_data)
    total_jobs = sum(m['total_jobs'] for m in months_data)
    avg_monthly = total_all_revenue / len([m for m in months_data if m['total_revenue'] > 0]) if any(m['total_revenue'] > 0 for m in months_data) else 0
    
    return jsonify({
        "months": months_data,
        "summary": {
            "total_revenue": round(total_all_revenue, 2),
            "total_paid_revenue": round(total_paid, 2),
            "total_unpaid_revenue": round(total_unpaid, 2),
            "total_jobs": total_jobs,
            "average_monthly_revenue": round(avg_monthly, 2),
            "best_month": best_month['month'] + ' ' + str(best_month['year']) if best_month else 'N/A',
            "best_month_revenue": best_month['total_revenue'] if best_month else 0,
            "worst_month": worst_month['month'] + ' ' + str(worst_month['year']) if worst_month else 'N/A',
            "worst_month_revenue": worst_month['total_revenue'] if worst_month else 0
        }
    })


@financials_bp.route("/api/unpaid-jobs-report")
@login_required
def get_unpaid_jobs_report():
    """Get unpaid jobs grouped by days late"""
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403
    
    # Get all unpaid (Finished) jobs
    today = datetime.now().date()
    unpaid_jobs = db.session.query(
        Appointment.apt_id,
        Appointment.scheduled_time,
        Appointment.end_time,
        Appointment.cost,
        User.full_name
    ).join(
        User, Appointment.cleaner_id == User.id
    ).filter(
        Appointment.status == 'Finished'
    ).order_by(
        Appointment.scheduled_time.asc()
    ).all()
    
    # Group jobs by lateness
    groups = {
        'two_weeks': [],
        'one_month': [],
        'ninety_days': [],
        'ninety_plus': []
    }
    
    total_amount = 0
    total_days_late = 0
    
    for apt_id, scheduled_time, end_time, cost, cleaner_name in unpaid_jobs:
        if scheduled_time is None:
            continue
            
        scheduled_date = scheduled_time.date()
        days_late = (today - scheduled_date).days
        
        total_amount += float(cost or 0)
        total_days_late += days_late
        
        job_data = {
            "apt_id": apt_id,
            "scheduled_date": scheduled_date.strftime('%Y-%m-%d'),
            "finished_date": end_time.strftime('%Y-%m-%d') if end_time else scheduled_date.strftime('%Y-%m-%d'),
            "cleaner_name": cleaner_name or "Unknown",
            "cost": float(cost or 0),
            "days_late": days_late
        }
        
        # Categorize by lateness
        if days_late <= 14:
            groups['two_weeks'].append(job_data)
        elif days_late <= 30:
            groups['one_month'].append(job_data)
        elif days_late <= 90:
            groups['ninety_days'].append(job_data)
        else:
            groups['ninety_plus'].append(job_data)
    
    # Sort each group by date (oldest first)
    for group_key in groups:
        groups[group_key].sort(key=lambda x: x['scheduled_date'])
    
    # Determine the most critical group
    most_critical = 'None'
    if groups['ninety_plus']:
        most_critical = '90+ Days Late'
    elif groups['ninety_days']:
        most_critical = '90 Days Late'
    elif groups['one_month']:
        most_critical = '1 Month Late'
    elif groups['two_weeks']:
        most_critical = '2 Weeks Late'
    
    # Build response with groups
    total_jobs = sum(len(v) for v in groups.values())
    average_days_late = round(total_days_late / total_jobs, 1) if total_jobs > 0 else 0
    
    report_groups = []
    
    if groups['ninety_plus']:
        report_groups.append({
            "group_name": "90+ Days Late (CRITICAL)",
            "jobs": groups['ninety_plus']
        })
    
    if groups['ninety_days']:
        report_groups.append({
            "group_name": "31-90 Days Late",
            "jobs": groups['ninety_days']
        })
    
    if groups['one_month']:
        report_groups.append({
            "group_name": "15-30 Days Late",
            "jobs": groups['one_month']
        })
    
    if groups['two_weeks']:
        report_groups.append({
            "group_name": "0-14 Days Late",
            "jobs": groups['two_weeks']
        })
    
    return jsonify({
        "summary": {
            "total_jobs": total_jobs,
            "total_amount": total_amount,
            "average_days_late": average_days_late,
            "most_critical_group": most_critical
        },
        "groups": report_groups
    })


HOURLY_RATE = 25.00

@financials_bp.route("/api/hours-summary")
@login_required
def get_hours_summary():
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403

    today = datetime.now().date()
    start_of_month = today.replace(day=1)
    start_of_week = today - timedelta(days=today.weekday())

    if today.month == 1:
        last_month_start = today.replace(year=today.year - 1, month=12, day=1)
        last_month_end = today.replace(year=today.year - 1, month=12, day=31)
    else:
        last_month_start = today.replace(month=today.month - 1, day=1)
        last_month_end = today.replace(day=1) - timedelta(days=1)

    hours_filter = (
        Appointment.actual_start_time.isnot(None),
        Appointment.actual_finish_time.isnot(None),
        Appointment.status.in_(['Finished', 'Paid'])
    )

    total_hours = db.session.query(func.sum(Appointment.hours_spent)).filter(*hours_filter).scalar() or 0

    month_hours = db.session.query(func.sum(Appointment.hours_spent)).filter(
        *hours_filter,
        func.date(Appointment.actual_finish_time) >= start_of_month,
        func.date(Appointment.actual_finish_time) <= today
    ).scalar() or 0

    last_month_hours = db.session.query(func.sum(Appointment.hours_spent)).filter(
        *hours_filter,
        func.date(Appointment.actual_finish_time) >= last_month_start,
        func.date(Appointment.actual_finish_time) <= last_month_end
    ).scalar() or 0

    week_hours = db.session.query(func.sum(Appointment.hours_spent)).filter(
        *hours_filter,
        func.date(Appointment.actual_finish_time) >= start_of_week,
        func.date(Appointment.actual_finish_time) <= today
    ).scalar() or 0

    avg_hours = db.session.query(func.avg(Appointment.hours_spent)).filter(*hours_filter).scalar() or 0

    total_jobs_with_hours = db.session.query(func.count(Appointment.apt_id)).filter(*hours_filter).scalar() or 0

    return jsonify({
        "total_hours": round(float(total_hours), 2),
        "month_hours": round(float(month_hours), 2),
        "last_month_hours": round(float(last_month_hours), 2),
        "week_hours": round(float(week_hours), 2),
        "avg_hours_per_job": round(float(avg_hours), 2),
        "total_jobs_with_hours": total_jobs_with_hours,
        "est_labor_cost": round(float(total_hours) * HOURLY_RATE, 2),
        "est_month_labor_cost": round(float(month_hours) * HOURLY_RATE, 2)
    })


@financials_bp.route("/api/hours-by-cleaner")
@login_required
def get_hours_by_cleaner():
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403

    hours_filter = (
        Appointment.actual_start_time.isnot(None),
        Appointment.actual_finish_time.isnot(None),
        Appointment.status.in_(['Finished', 'Paid'])
    )

    cleaner_stats = db.session.query(
        User.id,
        User.full_name,
        func.count(Appointment.apt_id).label('total_jobs'),
        func.sum(Appointment.hours_spent).label('total_hours'),
        func.avg(Appointment.hours_spent).label('avg_hours'),
        func.sum(Appointment.cost).label('total_revenue')
    ).join(
        Appointment, User.id == Appointment.cleaner_id
    ).filter(
        User.role == 'Cleaner',
        *hours_filter
    ).group_by(
        User.id, User.full_name
    ).order_by(
        func.sum(Appointment.hours_spent).desc()
    ).all()

    cleaners = []
    for cid, name, jobs, hours, avg_h, revenue in cleaner_stats:
        cleaners.append({
            "cleaner_id": cid,
            "name": name or "Unknown",
            "total_jobs": jobs or 0,
            "total_hours": round(float(hours or 0), 2),
            "avg_hours_per_job": round(float(avg_h or 0), 2),
            "total_revenue": float(revenue or 0),
            "est_labor_cost": round(float(hours or 0) * HOURLY_RATE, 2),
            "revenue_per_hour": round(float(revenue or 0) / float(hours or 1), 2)
        })

    summary = {
        "total_cleaners": len(cleaners),
        "total_hours": round(sum(c["total_hours"] for c in cleaners), 2),
        "total_revenue": round(sum(c["total_revenue"] for c in cleaners), 2),
        "total_labor_cost": round(sum(c["est_labor_cost"] for c in cleaners), 2)
    }

    return jsonify({"cleaners": cleaners, "summary": summary})


@financials_bp.route("/api/hours-by-week")
@login_required
def get_hours_by_week():
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403

    weeks_data = []
    today = datetime.now().date()

    for i in range(11, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7*i)
        week_end = week_start + timedelta(days=6)

        result = db.session.query(
            func.sum(Appointment.hours_spent),
            func.count(Appointment.apt_id),
            func.sum(Appointment.cost)
        ).filter(
            Appointment.actual_start_time.isnot(None),
            Appointment.actual_finish_time.isnot(None),
            Appointment.status.in_(['Finished', 'Paid']),
            func.date(Appointment.actual_finish_time) >= week_start,
            func.date(Appointment.actual_finish_time) <= week_end
        ).first()

        hours = float(result[0] or 0)
        jobs = result[1] or 0
        revenue = float(result[2] or 0)

        week_label = f"Week of {week_start.strftime('%m/%d')}"
        weeks_data.append({
            "week": week_label,
            "hours": round(hours, 2),
            "jobs": jobs,
            "revenue": round(revenue, 2),
            "labor_cost": round(hours * HOURLY_RATE, 2),
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat()
        })

    return jsonify(weeks_data)


@financials_bp.route("/api/employee-efficiency")
@login_required
def get_employee_efficiency():
    if current_user.role != 'BusinessOwner':
        return jsonify({"error": "Unauthorized"}), 403

    efficiency_filter = (
        Appointment.actual_start_time.isnot(None),
        Appointment.actual_finish_time.isnot(None),
        Appointment.scheduled_time.isnot(None),
        Appointment.end_time.isnot(None),
        Appointment.status.in_(['Finished', 'Paid'])
    )

    raw_data = db.session.query(
        User.id,
        User.full_name,
        Appointment.apt_id,
        Appointment.scheduled_time,
        Appointment.end_time,
        Appointment.hours_spent,
        Appointment.cost
    ).join(
        Appointment, User.id == Appointment.cleaner_id
    ).filter(
        User.role == 'Cleaner',
        *efficiency_filter
    ).order_by(
        User.full_name
    ).all()

    cleaner_map = {}
    for cid, name, apt_id, sched_time, end_time, hours, cost in raw_data:
        if cid not in cleaner_map:
            cleaner_map[cid] = {
                "cleaner_id": cid,
                "name": name or "Unknown",
                "jobs": [],
                "total_actual_hours": 0.0,
                "total_scheduled_hours": 0.0,
                "total_revenue": 0.0
            }
        actual = float(hours or 0)

        sched_seconds = 0
        if sched_time and end_time:
            sched_seconds = (end_time - sched_time).total_seconds()
        scheduled = round(sched_seconds / 3600, 2)

        cleaner_map[cid]["jobs"].append(apt_id)
        cleaner_map[cid]["total_actual_hours"] += actual
        cleaner_map[cid]["total_scheduled_hours"] += scheduled
        cleaner_map[cid]["total_revenue"] += float(cost or 0)

    cleaners = []
    total_actual = 0
    total_scheduled = 0
    total_revenue = 0

    for cid, data in cleaner_map.items():
        actual = round(data["total_actual_hours"], 2)
        scheduled = round(data["total_scheduled_hours"], 2)
        jobs = len(data["jobs"])
        revenue = round(data["total_revenue"], 2)

        if scheduled > 0:
            efficiency = round((scheduled - actual) / scheduled * 100, 1)
        else:
            efficiency = 0

        time_saved = round(scheduled - actual, 2)
        cost_saved = round(time_saved * HOURLY_RATE, 2)
        labor_cost = round(actual * HOURLY_RATE, 2)

        total_actual += actual
        total_scheduled += scheduled
        total_revenue += revenue

        cleaners.append({
            "cleaner_id": cid,
            "name": data["name"],
            "total_jobs": jobs,
            "total_actual_hours": actual,
            "total_scheduled_hours": scheduled,
            "avg_actual_per_job": round(actual / jobs, 2) if jobs else 0,
            "avg_scheduled_per_job": round(scheduled / jobs, 2) if jobs else 0,
            "efficiency": efficiency,
            "efficiency_ratio": round(actual / scheduled, 2) if scheduled > 0 else 0,
            "time_saved_hours": time_saved,
            "cost_saved": cost_saved,
            "total_revenue": revenue,
            "total_labor_cost": labor_cost
        })

    summary = {
        "total_actual_hours": round(total_actual, 2),
        "total_scheduled_hours": round(total_scheduled, 2),
        "total_time_saved": round(total_scheduled - total_actual, 2),
        "total_cost_saved": round((total_scheduled - total_actual) * HOURLY_RATE, 2),
        "total_revenue": round(total_revenue, 2),
        "total_labor_cost": round(total_actual * HOURLY_RATE, 2),
        "overall_efficiency": round(
            (total_scheduled - total_actual) / total_scheduled * 100
            if total_scheduled > 0 else 0, 1
        )
    }

    return jsonify({"cleaners": cleaners, "summary": summary})
