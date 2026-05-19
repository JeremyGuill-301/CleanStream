#!/usr/bin/env python3
"""
Inventory Reconciliation CLI Tool

This script identifies and fixes inventory discrepancies in the system.

Usage:
    python3 reconcile_inventory.py               # Check all supplies for discrepancies
    python3 reconcile_inventory.py --fix         # Fix all discrepancies
    python3 reconcile_inventory.py --supply 152  # Check specific supply
    python3 reconcile_inventory.py --fix --supply 152  # Fix specific supply
    python3 reconcile_inventory.py --report      # Generate health report
"""

import sys
import os
import argparse
from datetime import datetime

# Ensure project root is on sys.path so imports work when running from this directory
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models import Supplies, SupplyInventory, InventoryAudit
from app import app
from extensions import db
from inventory_utils import (
    calculate_inventory_total,
    detect_discrepancies,
    reconcile_inventory,
    get_inventory_health_report
)


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_supply_details(supply_id):
    """Print detailed information about a specific supply"""
    with app.app_context():
        supply = Supplies.query.get(supply_id)
        if not supply:
            print(f"❌ Supply ID {supply_id} not found")
            return
        
        calc_result = calculate_inventory_total(db, supply_id)
        
        print(f"\nSupply: {supply.name} (ID: {supply_id})")
        print(f"  Current Count (DB): {supply.current_count}")
        print(f"  Calculated Count:   {calc_result['calculated_count']}")
        print(f"  Discrepancy:        {supply.current_count - calc_result['calculated_count']}")
        print(f"\nTransaction Breakdown:")
        print(f"  Incoming (Delivered Orders): {calc_result['incoming']}")
        print(f"  Outgoing (Stock Taken):      {calc_result['outgoing']}")
        print(f"  Adjustments:                 {calc_result['adjustments']}")
        print(f"\nTransaction Details:")
        print(f"  Delivered Orders: {calc_result['transactions']['delivered_orders']}")
        print(f"  Stock Taken:      {calc_result['transactions']['stock_taken']}")
        print(f"  Adjustments:      {calc_result['transactions']['adjustments']}")


def check_discrepancies(supply_id=None):
    """Check for inventory discrepancies"""
    with app.app_context():
        if supply_id:
            print_header(f"Checking Supply #{supply_id}")
            print_supply_details(supply_id)
            return 0
        else:
            print_header("Scanning for Inventory Discrepancies")
            discrepancies = detect_discrepancies(db, Supplies)
            
            if not discrepancies:
                print("\n✅ No discrepancies found! Inventory is accurate.")
                return 0
            
            print(f"\n⚠️  Found {len(discrepancies)} discrepancy/discrepancies:\n")
            
            for disc in discrepancies:
                status = "❌" if abs(disc['discrepancy']) > 0 else "✓"
                print(f"{status} {disc['name']} (ID: {disc['supply_id']})")
                print(f"   Stored: {disc['stored_count']}, Calculated: {disc['calculated_count']}, " +
                      f"Diff: {disc['discrepancy']:+d}")
                print(f"   Incoming: {disc['details']['incoming']}, " +
                      f"Outgoing: {disc['details']['outgoing']}, " +
                      f"Adjustments: {disc['details']['adjustments']}")
                print()
            
            return len(discrepancies)


def fix_discrepancies(supply_id=None, user_id=None):
    """Fix inventory discrepancies"""
    with app.app_context():
        if supply_id:
            print_header(f"Reconciling Supply #{supply_id}")
        else:
            print_header("Reconciling All Supplies")
        
        try:
            result = reconcile_inventory(
                db=db,
                Supplies=Supplies,
                SupplyInventory=SupplyInventory,
                InventoryAudit=InventoryAudit,
                specific_supply_id=supply_id,
                user_id=user_id
            )
            
            if result['discrepancies_found'] == 0:
                print("\n✅ No discrepancies found. System is healthy!")
                return 0
            
            print(f"\n🔧 {result['summary']}\n")
            
            for correction in result['corrections_made']:
                print(f"Supply: {correction['name']} (ID: {correction['supply_id']})")
                print(f"  Previous Count: {correction['previous_count']}")
                print(f"  Corrected To:   {correction['corrected_count']}")
                print(f"  Incoming:       {correction['incoming']}")
                print(f"  Outgoing:       {correction['outgoing']}")
                print(f"  Audit Record:   #{correction['audit_record_id']}")
                print()
            
            print(f"✅ All corrections applied successfully!")
            return len(result['corrections_made'])
            
        except Exception as e:
            print(f"\n❌ Error during reconciliation: {str(e)}")
            import traceback
            traceback.print_exc()
            return -1


def generate_health_report():
    """Generate a comprehensive inventory health report"""
    with app.app_context():
        print_header("Inventory Health Report")
        
        report = get_inventory_health_report(db, Supplies, SupplyInventory)
        
        accuracy = report['overall_accuracy']
        if accuracy >= 95:
            status = "✅ EXCELLENT"
        elif accuracy >= 90:
            status = "⚠️  GOOD"
        elif accuracy >= 80:
            status = "⚠️  FAIR"
        else:
            status = "❌ POOR"
        
        print(f"\nOverall Accuracy: {status} ({accuracy}%)")
        print(f"Total Supplies: {report['total_supplies']}")
        print(f"Supplies with Discrepancies: {report['supplies_with_discrepancies']}")
        
        if report['supplies_with_discrepancies'] > 0:
            print(f"\n⚠️  Discrepancies ({report['supplies_with_discrepancies']}):")
            for disc in report['discrepancies']:
                print(f"  - {disc['name']}: {disc['discrepancy']:+d} (stored: {disc['stored_count']}, " +
                      f"calculated: {disc['calculated_count']})")
        
        if report['pending_orders']:
            print(f"\n📦 Pending Orders ({len(report['pending_orders'])}):")
            for order in report['pending_orders']:
                print(f"  - Supply ID {order['supply_id']}: {order['quantity']} units ({order['status']})")
        
        if report['low_stock_alerts']:
            print(f"\n🚨 Low Stock Alerts ({len(report['low_stock_alerts'])}):")
            for alert in report['low_stock_alerts']:
                print(f"  - {alert['name']}: {alert['current_count']}/{alert['minimum_threshold']} {alert['unit']}")
        
        if not report['pending_orders'] and not report['low_stock_alerts'] and report['supplies_with_discrepancies'] == 0:
            print("\n✅ All systems healthy!")


def main():
    parser = argparse.ArgumentParser(
        description='Inventory Reconciliation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 reconcile_inventory.py               # Check all supplies
  python3 reconcile_inventory.py --fix         # Fix all discrepancies
  python3 reconcile_inventory.py --supply 152  # Check supply #152
  python3 reconcile_inventory.py --fix --supply 152  # Fix supply #152
  python3 reconcile_inventory.py --report      # Generate health report
        '''
    )
    
    parser.add_argument('--fix', action='store_true', help='Fix discrepancies (default: check only)')
    parser.add_argument('--supply', type=int, help='Check/fix specific supply by ID')
    parser.add_argument('--report', action='store_true', help='Generate full inventory health report')
    parser.add_argument('--user', type=int, help='User ID performing the reconciliation (optional)')
    
    args = parser.parse_args()
    
    try:
        if args.report:
            generate_health_report()
        elif args.fix:
            count = fix_discrepancies(supply_id=args.supply, user_id=args.user)
            sys.exit(0 if count >= 0 else 1)
        else:
            count = check_discrepancies(supply_id=args.supply)
            if count > 0:
                print(f"\n💡 Run with --fix flag to correct these discrepancies")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
