from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, Supplies, SupplyInventory, Vendors
from datetime import datetime

supply_bp = Blueprint('supplies', __name__, url_prefix='/supplies', template_folder='/templates')

# Supplies routes
@supply_bp.route('/')
@login_required
def supplies_index():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return redirect(url_for('mobile_view'))

    supplies = Supplies.query.all()
    return render_template('supplies/index.html', supplies=supplies)

@supply_bp.route('/add', methods=['POST'])
@login_required
def add_supply():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        data = request.get_json()
        new_supply = Supplies(
            name=data['name'],
            description=data.get('description', ''),
            current_count=int(data['current_count']),
            minimum_threshold=int(data['minimum_threshold']),
            unit=data.get('unit', 'units'),
            category=data.get('category', '')
        )
        db.session.add(new_supply)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Supply added successfully', 'supply_id': new_supply.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@supply_bp.route('/<int:supply_id>', methods=['GET'])
@login_required
def get_supply_details(supply_id):
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    try:
        supply = Supplies.query.get_or_404(supply_id)
        # Get inventory history for this supply
        inventory = SupplyInventory.query.filter_by(supply_id=supply_id).order_by(SupplyInventory.created_at.desc()).all()

        # Convert to dict for JSON serialization
        inventory_data = []
        for item in inventory:
            item_dict = {
                'id': item.id,
                'transaction_type': item.transaction_type,
                'quantity_ordered': item.quantity_ordered,
                'order_date': item.order_date.isoformat() if item.order_date else None,
                'taken_at': item.taken_at.isoformat() if item.taken_at else None,
                'status': item.status,
                'cost': float(item.cost) if item.cost else None,
                'notes': item.notes,
                'reason': item.reason,
                'vendor': {
                    'id': item.vendor.id,
                    'name': item.vendor.name
                } if item.vendor else None,
                'taken_by_user': {
                    'id': item.taken_by_user.id,
                    'full_name': item.taken_by_user.full_name
                } if item.taken_by_user else None
            }
            inventory_data.append(item_dict)

        supply_dict = {
            'id': supply.id,
            'name': supply.name,
            'description': supply.description,
            'current_count': supply.current_count,
            'minimum_threshold': supply.minimum_threshold,
            'unit': supply.unit,
            'category': supply.category,
            'last_restocked': supply.last_restocked.isoformat() if supply.last_restocked else None,
            'preferred_vendor_id': supply.preferred_vendor_id
        }

        return jsonify({
            'success': True,
            'supply': supply_dict,
            'inventory': inventory_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@supply_bp.route('/log-usage', methods=['POST'])
@login_required
def log_supply_usage():
    """Log when a cleaner takes supplies. Records usage and updates inventory."""
    try:
        data = request.get_json()
        supply_id = data.get('supply_id')
        quantity = int(data.get('quantity', 0))
        reason = data.get('reason', '')
        
        if quantity <= 0:
            return jsonify({'success': False, 'message': 'Quantity must be greater than 0'}), 400
        
        supply = Supplies.query.get_or_404(supply_id)
        
        # Create inventory log entry
        log_entry = SupplyInventory(
            supply_id=supply_id,
            quantity_ordered=quantity,
            transaction_type='Stock Taken',
            taken_by_user_id=current_user.id,
            taken_at=datetime.now(),
            reason=reason,
            quantity_remaining=supply.current_count - quantity,
            status='Delivered'  # Use 'Delivered' status for stock taken entries
        )
        
        # Update supply count
        supply.current_count -= quantity
        
        db.session.add(log_entry)
        db.session.commit()
        
        # Check if supply is now below threshold
        needs_restock = supply.current_count <= supply.minimum_threshold
        message = None
        
        if needs_restock:
            message = f"⚠️ {supply.name} is now below minimum threshold ({supply.current_count} {supply.unit} remaining)"
            flash(message, 'warning')
            # TODO: Send email notification to admin
        
        return jsonify({
            'success': True,
            'message': 'Supply usage logged successfully',
            'new_count': supply.current_count,
            'needs_restock': needs_restock,
            'restock_message': message
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@supply_bp.route('/mobile', methods=['GET'])
@login_required
def mobile_supply_intake():
    """Mobile-first page for cleaners to log supply usage."""
    supplies = Supplies.query.all()
    return render_template('supplies/mobile_intake.html', supplies=supplies)
