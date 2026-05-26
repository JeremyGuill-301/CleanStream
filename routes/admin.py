from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='/templates')

@admin_bp.route('/')
@login_required
def index():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    return render_template('admin/base.html')

@admin_bp.route('/users')
@login_required
def users():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))

    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return jsonify({'error': 'Access denied'}), 403

    data = request.form
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username, full_name=full_name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'User added successfully'})

@admin_bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return jsonify({'error': 'Access denied'}), 403

    user = User.query.get_or_404(user_id)
    data = request.form

    user.full_name = data.get('full_name', user.full_name)
    user.role = data.get('role', user.role)

    username = data.get('username')
    if username != user.username and User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    user.username = username

    password = data.get('password')
    if password:
        user.set_password(password)

    db.session.commit()
    return jsonify({'success': True, 'message': 'User updated successfully'})

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return jsonify({'error': 'Access denied'}), 403

    if user_id == current_user.user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'User deleted successfully'})
