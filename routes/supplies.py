from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, Supplies, SupplyInventory, Vendors

supply_bp = Blueprint('supplies', __name__, url_prefix='/supplies', template_folder='/templates')

# Supplies routes
@supply_bp.route('/')
@login_required
def supplies_index():
    if current_user.role not in ['OfficeAdmin', 'BusinessOwner']:
        return redirect(url_for('mobile_view'))

    supplies = Supplies.query.all()
    return render_template('supplies/index.html', supplies=supplies)

@supply_bp.route('/supplies/add', methods=['POST'])
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
        return jsonify({'success': True, 'message': 'Supply added successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@supply_bp.route('/supplies/<int:supply_id>')
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
