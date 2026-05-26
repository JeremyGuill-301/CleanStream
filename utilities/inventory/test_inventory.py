"""
Unit tests for inventory validation and reconciliation logic

Run with: python3 -m pytest test_inventory.py -v
"""

import sys
import os
import pytest
from datetime import datetime

# Ensure project root is on sys.path when running tests from utilities/inventory
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, db, Supplies, SupplyInventory, InventoryAudit, Vendors, User
from inventory_utils import (
    calculate_inventory_total,
    detect_discrepancies,
    validate_inventory_transaction,
    reconcile_inventory,
    record_inventory_correction,
    get_inventory_health_report,
    InventoryValidationError,
    InventoryReconciliationError
)


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def setup_test_data(client):
    """Set up test data in the database"""
    with app.app_context():
        # Create test vendor
        vendor = Vendors(
            name='Test Vendor',
            email='test@vendor.com',
            phone='555-0000'
        )
        db.session.add(vendor)
        db.session.commit()
        
        # Create test supply
        supply = Supplies(
            name='Test Cleaner',
            description='Test supply',
            current_count=100,
            minimum_threshold=10,
            unit='bottles'
        )
        db.session.add(supply)
        db.session.commit()
        
        return {
            'vendor_id': vendor.id,
            'supply_id': supply.id
        }


class TestCalculateInventoryTotal:
    """Test the calculate_inventory_total function"""
    
    def test_calculate_with_delivered_orders(self, setup_test_data):
        """Test calculation with delivered orders"""
        with app.app_context():
            supply_id = setup_test_data['supply_id']
            
            # Add a delivered order
            order = SupplyInventory(
                supply_id=supply_id,
                vendor_id=setup_test_data['vendor_id'],
                quantity_ordered=50,
                transaction_type='Order',
                status='Delivered',
                order_date=datetime.now()
            )
            db.session.add(order)
            db.session.commit()
            
            result = calculate_inventory_total(db, supply_id)
            
            assert result['calculated_count'] == 50
            assert result['incoming'] == 50
            assert result['outgoing'] == 0
            assert result['transactions']['delivered_orders'] == 1
    
    def test_calculate_with_stock_taken(self, setup_test_data):
        """Test calculation with stock taken"""
        with app.app_context():
            supply_id = setup_test_data['supply_id']
            
            # Add order
            order = SupplyInventory(
                supply_id=supply_id,
                vendor_id=setup_test_data['vendor_id'],
                quantity_ordered=50,
                transaction_type='Order',
                status='Delivered'
            )
            db.session.add(order)
            
            # Add stock taken
            usage = SupplyInventory(
                supply_id=supply_id,
                quantity_ordered=15,
                transaction_type='Stock Taken',
                status='Delivered',
                taken_by_user_id=None
            )
            db.session.add(usage)
            db.session.commit()
            
            result = calculate_inventory_total(db, supply_id)
            
            assert result['calculated_count'] == 35  # 50 - 15
            assert result['incoming'] == 50
            assert result['outgoing'] == 15
    
    def test_calculate_with_adjustments(self, setup_test_data):
        """Test calculation with adjustments"""
        with app.app_context():
            supply_id = setup_test_data['supply_id']
            
            # Add order
            order = SupplyInventory(
                supply_id=supply_id,
                vendor_id=setup_test_data['vendor_id'],
                quantity_ordered=50,
                transaction_type='Order',
                status='Delivered'
            )
            db.session.add(order)
            
            # Add adjustment (subtraction)
            adjustment = SupplyInventory(
                supply_id=supply_id,
                quantity_ordered=10,
                transaction_type='Adjustment',
                status='Delivered'
            )
            db.session.add(adjustment)
            db.session.commit()
            
            result = calculate_inventory_total(db, supply_id)
            
            assert result['calculated_count'] == 40  # 50 - 10
            assert result['adjustments'] == 10


class TestValidateInventoryTransaction:
    """Test the validate_inventory_transaction function"""
    
    def test_valid_stock_taken_with_sufficient_inventory(self, setup_test_data):
        """Test valid stock taken transaction"""
        with app.app_context():
            result = validate_inventory_transaction(
                db=db,
                Supplies=Supplies,
                supply_id=setup_test_data['supply_id'],
                quantity=50,
                transaction_type='Stock Taken'
            )
            
            assert result['valid'] is True
            assert result['supply'].id == setup_test_data['supply_id']
    
    def test_invalid_stock_taken_with_insufficient_inventory(self, setup_test_data):
        """Test invalid stock taken with insufficient inventory"""
        with app.app_context():
            with pytest.raises(InventoryValidationError) as exc_info:
                validate_inventory_transaction(
                    db=db,
                    Supplies=Supplies,
                    supply_id=setup_test_data['supply_id'],
                    quantity=200,  # More than the 100 available
                    transaction_type='Stock Taken'
                )
            
            assert 'Insufficient inventory' in str(exc_info.value)
    
    def test_invalid_quantity_zero(self, setup_test_data):
        """Test invalid transaction with zero quantity"""
        with app.app_context():
            with pytest.raises(InventoryValidationError) as exc_info:
                validate_inventory_transaction(
                    db=db,
                    Supplies=Supplies,
                    supply_id=setup_test_data['supply_id'],
                    quantity=0,
                    transaction_type='Stock Taken'
                )
            
            assert 'must be positive' in str(exc_info.value)
    
    def test_invalid_supply_id(self, setup_test_data):
        """Test invalid supply ID"""
        with app.app_context():
            with pytest.raises(InventoryValidationError) as exc_info:
                validate_inventory_transaction(
                    db=db,
                    Supplies=Supplies,
                    supply_id=99999,
                    quantity=10,
                    transaction_type='Stock Taken'
                )
            
            assert 'not found' in str(exc_info.value)


class TestRecordInventoryCorrection:
    """Test the record_inventory_correction function"""
    
    def test_record_correction_creates_audit_entry(self, setup_test_data):
        """Test that corrections create audit entries"""
        with app.app_context():
            supply_id = setup_test_data['supply_id']
            
            audit = record_inventory_correction(
                db=db,
                InventoryAudit=InventoryAudit,
                Supplies=Supplies,
                supply_id=supply_id,
                new_count=75,
                audit_type='Manual Correction',
                reason='Test correction',
                user_id=None,
                calculated_count=75
            )
            
            assert audit.id is not None
            assert audit.previous_count == 100
            assert audit.new_count == 75
            assert audit.audit_type == 'Manual Correction'
            
            # Verify supply was updated
            supply = Supplies.query.get(supply_id)
            assert supply.current_count == 75
    
    def test_invalid_supply_id_for_correction(self, setup_test_data):
        """Test correction with invalid supply ID"""
        with app.app_context():
            with pytest.raises(InventoryReconciliationError) as exc_info:
                record_inventory_correction(
                    db=db,
                    InventoryAudit=InventoryAudit,
                    Supplies=Supplies,
                    supply_id=99999,
                    new_count=50,
                    audit_type='Manual Correction',
                    reason='Test'
                )
            
            assert 'not found' in str(exc_info.value)


class TestDetectDiscrepancies:
    """Test the detect_discrepancies function"""
    
    def test_no_discrepancies_when_accurate(self, setup_test_data):
        """Test that accurate inventory has no discrepancies"""
        with app.app_context():
            # Start with initial count that matches transactions (none = 0)
            supply = Supplies.query.get(setup_test_data['supply_id'])
            supply.current_count = 0  # Match the calculated count
            db.session.commit()
            
            discrepancies = detect_discrepancies(db, Supplies)
            assert len(discrepancies) == 0
    
    def test_detect_discrepancy_when_present(self, setup_test_data):
        """Test detection of discrepancies"""
        with app.app_context():
            supply_id = setup_test_data['supply_id']
            
            # Add order to create a discrepancy
            order = SupplyInventory(
                supply_id=supply_id,
                vendor_id=setup_test_data['vendor_id'],
                quantity_ordered=50,
                transaction_type='Order',
                status='Delivered'
            )
            db.session.add(order)
            
            # Don't update the supply's current_count (simulating a bug)
            db.session.commit()
            
            discrepancies = detect_discrepancies(db, Supplies)
            
            assert len(discrepancies) == 1
            assert discrepancies[0]['supply_id'] == supply_id
            assert discrepancies[0]['discrepancy'] == 50  # 100 (stored) - 50 (calculated)


class TestGetInventoryHealthReport:
    """Test the get_inventory_health_report function"""
    
    def test_health_report_structure(self, setup_test_data):
        """Test that health report has all required fields"""
        with app.app_context():
            report = get_inventory_health_report(db, Supplies, SupplyInventory)
            
            assert 'total_supplies' in report
            assert 'supplies_with_discrepancies' in report
            assert 'discrepancies' in report
            assert 'pending_orders' in report
            assert 'low_stock_alerts' in report
            assert 'overall_accuracy' in report
    
    def test_low_stock_detection(self, setup_test_data):
        """Test that low stock is detected"""
        with app.app_context():
            # Set supply close to minimum threshold
            supply = Supplies.query.get(setup_test_data['supply_id'])
            supply.current_count = 5
            supply.minimum_threshold = 10
            db.session.commit()
            
            report = get_inventory_health_report(db, Supplies, SupplyInventory)
            
            assert len(report['low_stock_alerts']) == 1
            assert report['low_stock_alerts'][0]['supply_id'] == setup_test_data['supply_id']


class TestReconcileInventory:
    """Test the reconcile_inventory function"""
    
    def test_reconciliation_fixes_discrepancies(self, setup_test_data):
        """Test that reconciliation fixes all discrepancies"""
        with app.app_context():
            supply_id = setup_test_data['supply_id']
            
            # Create a discrepancy
            order = SupplyInventory(
                supply_id=supply_id,
                vendor_id=setup_test_data['vendor_id'],
                quantity_ordered=50,
                transaction_type='Order',
                status='Delivered'
            )
            db.session.add(order)
            db.session.commit()
            
            # Verify discrepancy exists
            discrepancies_before = detect_discrepancies(db, Supplies)
            assert len(discrepancies_before) == 1
            
            # Reconcile
            result = reconcile_inventory(
                db=db,
                Supplies=Supplies,
                SupplyInventory=SupplyInventory,
                InventoryAudit=InventoryAudit
            )
            
            assert result['discrepancies_found'] == 1
            
            # Verify discrepancy is fixed
            discrepancies_after = detect_discrepancies(db, Supplies)
            assert len(discrepancies_after) == 0
            
            # Verify supply count was corrected to the calculated total (50)
            supply = Supplies.query.get(supply_id)
            assert supply.current_count == 50  # Only the delivered order


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
