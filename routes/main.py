from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db, User

main_bp = Blueprint('main', __name__, url_prefix='/main', template_folder='/templates')

@main_bp.route('/')
@login_required
def dashboard():
    return render_template('main/dashboard.html', user=current_user)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))

    return render_template('main/profile.html', user=current_user)
