"""
Inventory validation and reconciliation utilities

This module provides functions to:
1. Calculate accurate inventory counts from transaction history
2. Detect discrepancies between stored and calculated counts
3. Validate inventory transactions before processing
4. Log all inventory corrections for audit trails
"""

from datetime import datetime
from sqlalchemy import func
import sys
import os

# Ensure project root is on sys.path so imports work when running from this utilities subdir
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class InventoryReconciliationError(Exception):
    """Raised when inventory reconciliation fails"""
    pass


class InventoryValidationError(Exception):
    """Raised when inventory validation fails"""
    pass


def calculate_inventory_total(db, supply_id):
    """
    Calculate the true inventory count from transaction history.
    
    Formula: SUM(Delivered Orders) - SUM(Stock Taken) - SUM(Adjustments)
    
    Args:
        db: SQLAlchemy database instance
        supply_id: The supply ID to calculate for
        
    Returns:
        dict: {
            'calculated_count': int,
            'incoming': int,
            'outgoing': int,
            'adjustments': int,
            'transactions': list
        }
    """
    from models import SupplyInventory
    
    # Get all delivered order transactions
    delivered_orders = SupplyInventory.query.filter_by(
        supply_id=supply_id,
        transaction_type='Order',
        status='Delivered'
    ).all()
    
    # Get all stock taken transactions
    stock_taken = SupplyInventory.query.filter_by(
        supply_id=supply_id,
        transaction_type='Stock Taken',
        status='Delivered'
    ).all()
    
    # Get all adjustment transactions
    adjustments = SupplyInventory.query.filter_by(
        supply_id=supply_id,
        transaction_type='Adjustment',
        status='Delivered'
    ).all()
    
    incoming = sum(t.quantity_ordered for t in delivered_orders)
    outgoing = sum(t.quantity_ordered for t in stock_taken)
    adjustment_total = sum(t.quantity_ordered for t in adjustments)
    
    calculated_count = incoming - outgoing - adjustment_total
    
    return {
        'calculated_count': calculated_count,
        'incoming': incoming,
        'outgoing': outgoing,
        'adjustments': adjustment_total,
        'transactions': {
            'delivered_orders': len(delivered_orders),
            'stock_taken': len(stock_taken),
            'adjustments': len(adjustments)
        }
    }


def detect_discrepancies(db, Supplies):
    """
    Detect all inventory discrepancies in the system.
    
    Returns a list of supplies where calculated count != stored count
    
    Args:
        db: SQLAlchemy database instance
        Supplies: The Supplies model class
        
    Returns:
        list: [{
            'supply_id': int,
            'name': str,
            'stored_count': int,
            'calculated_count': int,
            'discrepancy': int,
            'details': dict
        }, ...]
    """
    discrepancies = []
    supplies = Supplies.query.all()
    
    for supply in supplies:
        calc_result = calculate_inventory_total(db, supply.id)
        calculated = calc_result['calculated_count']
        
        if supply.current_count != calculated:
            discrepancies.append({
                'supply_id': supply.id,
                'name': supply.name,
                'stored_count': supply.current_count,
                'calculated_count': calculated,
                'discrepancy': supply.current_count - calculated,
                'details': calc_result
            })
    
    return discrepancies


def validate_inventory_transaction(db, Supplies, supply_id, quantity, transaction_type='Stock Taken'):
    """
    Validate that an inventory transaction is valid.
    
    Checks:
    - Quantity is positive
    - Supply exists
    - For stock taken: current_count has sufficient inventory
    - No negative inventory will result
    
    Args:
        db: SQLAlchemy database instance
        Supplies: The Supplies model class
        supply_id: The supply ID
        quantity: The quantity to transact
        transaction_type: Type of transaction ('Stock Taken', 'Order', 'Adjustment')
        
    Returns:
        dict: {'valid': bool, 'message': str, 'supply': Supplies or None}
        
    Raises:
        InventoryValidationError: If validation fails
    """
    # Validate quantity
    if quantity <= 0:
        raise InventoryValidationError(f"Quantity must be positive, got {quantity}")
    
    # Validate supply exists
    supply = Supplies.query.get(supply_id)
    if not supply:
        raise InventoryValidationError(f"Supply ID {supply_id} not found")
    
    # For stock taken, check if we have enough inventory
    if transaction_type == 'Stock Taken':
        if supply.current_count < quantity:
            raise InventoryValidationError(
                f"Insufficient inventory for {supply.name}. "
                f"Available: {supply.current_count}, Requested: {quantity}"
            )
    
    return {
        'valid': True,
        'message': 'Transaction is valid',
        'supply': supply
    }


def record_inventory_correction(db, InventoryAudit, Supplies, supply_id, new_count, audit_type, 
                                reason=None, user_id=None, calculated_count=None):
    """
    Record an inventory correction in the audit log.
    
    Args:
        db: SQLAlchemy database instance
        InventoryAudit: The InventoryAudit model class
        Supplies: The Supplies model class
        supply_id: The supply ID being corrected
        new_count: The corrected count
        audit_type: Type of audit ('Discrepancy Found', 'Manual Correction', 'Reconciliation', 'Validation Failed')
        reason: Optional reason for correction
        user_id: Optional user ID who made the correction
        calculated_count: Optional calculated count for reference
        
    Returns:
        InventoryAudit: The created audit record
    """
    supply = Supplies.query.get(supply_id)
    if not supply:
        raise InventoryReconciliationError(f"Supply ID {supply_id} not found")
    
    previous_count = supply.current_count
    
    audit_record = InventoryAudit(
        supply_id=supply_id,
        audit_type=audit_type,
        previous_count=previous_count,
        new_count=new_count,
        calculated_count=calculated_count,
        reason=reason,
        corrected_by_user_id=user_id,
        created_at=datetime.now()
    )
    
    # Update the supply's current count
    supply.current_count = new_count
    
    db.session.add(audit_record)
    db.session.commit()
    
    return audit_record


def reconcile_inventory(db, Supplies, SupplyInventory, InventoryAudit, specific_supply_id=None, user_id=None):
    """
    Reconcile inventory by fixing all discrepancies.
    
    Args:
        db: SQLAlchemy database instance
        Supplies: The Supplies model class
        SupplyInventory: The SupplyInventory model class
        InventoryAudit: The InventoryAudit model class
        specific_supply_id: Optional - only reconcile this supply
        user_id: Optional - user ID performing the reconciliation
        
    Returns:
        dict: {
            'total_supplies': int,
            'discrepancies_found': int,
            'corrections_made': list,
            'summary': str
        }
    """
    if specific_supply_id:
        supplies_to_check = [Supplies.query.get(specific_supply_id)]
        if not supplies_to_check[0]:
            raise InventoryReconciliationError(f"Supply ID {specific_supply_id} not found")
    else:
        supplies_to_check = Supplies.query.all()
    
    corrections_made = []
    
    for supply in supplies_to_check:
        calc_result = calculate_inventory_total(db, supply.id)
        calculated = calc_result['calculated_count']
        
        if supply.current_count != calculated:
            # Record the correction
            audit = record_inventory_correction(
                db=db,
                InventoryAudit=InventoryAudit,
                Supplies=Supplies,
                supply_id=supply.id,
                new_count=calculated,
                audit_type='Reconciliation',
                reason=f"Automatic reconciliation. Previous: {supply.current_count}, Calculated: {calculated}",
                user_id=user_id,
                calculated_count=calculated
            )
            
            corrections_made.append({
                'supply_id': supply.id,
                'name': supply.name,
                'previous_count': supply.current_count,
                'corrected_count': calculated,
                'incoming': calc_result['incoming'],
                'outgoing': calc_result['outgoing'],
                'audit_record_id': audit.id
            })
    
    summary = f"Reconciliation complete. Found {len(corrections_made)} discrepanc{'y' if len(corrections_made) == 1 else 'ies'}."
    
    return {
        'total_supplies': len(supplies_to_check),
        'discrepancies_found': len(corrections_made),
        'corrections_made': corrections_made,
        'summary': summary
    }


def get_inventory_health_report(db, Supplies, SupplyInventory):
    """
    Generate a comprehensive inventory health report.
    
    Returns detailed information about inventory accuracy across the system.
    
    Args:
        db: SQLAlchemy database instance
        Supplies: The Supplies model class
        SupplyInventory: The SupplyInventory model class
        
    Returns:
        dict: {
            'total_supplies': int,
            'supplies_with_discrepancies': int,
            'discrepancies': list,
            'pending_orders': list,
            'low_stock_alerts': list,
            'overall_accuracy': float
        }
    """
    all_supplies = Supplies.query.all()
    discrepancies = detect_discrepancies(db, Supplies)
    
    # Get pending orders
    pending_orders = SupplyInventory.query.filter(
        SupplyInventory.transaction_type == 'Order',
        SupplyInventory.status.in_(['Pending', 'Shipped'])
    ).all()
    
    # Get low stock alerts
    low_stock = [s for s in all_supplies if s.needs_restocking()]
    
    accuracy_percentage = ((len(all_supplies) - len(discrepancies)) / len(all_supplies) * 100) if all_supplies else 100
    
    return {
        'total_supplies': len(all_supplies),
        'supplies_with_discrepancies': len(discrepancies),
        'discrepancies': discrepancies,
        'pending_orders': [
            {
                'id': o.id,
                'supply_id': o.supply_id,
                'quantity': o.quantity_ordered,
                'status': o.status,
                'expected_delivery': o.expected_delivery_date.isoformat() if o.expected_delivery_date else None
            }
            for o in pending_orders
        ],
        'low_stock_alerts': [
            {
                'supply_id': s.id,
                'name': s.name,
                'current_count': s.current_count,
                'minimum_threshold': s.minimum_threshold,
                'unit': s.unit
            }
            for s in low_stock
        ],
        'overall_accuracy': round(accuracy_percentage, 2)
    }
