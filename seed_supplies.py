#!/usr/bin/env python3
"""
Seed script for populating the database with:
- 10 Vendors
- 25 Cleaning Supplies
- 25-30 Orders (with random vendor assignments)
- 5 Stock Removal records (by random cleaners)
"""

import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

from models import User, Supplies, Vendors, SupplyInventory
from extensions import db
from app import app

# Fake vendor data
VENDOR_DATA = [
    {
        'name': 'CleanPro Supplies Inc.',
        'contact_info': 'John Smith',
        'email': 'sales@cleanprosupplies.com',
        'phone': '(555) 123-4567',
        'address': '1000 Industrial Blvd',
        'city': 'Atlanta',
        'state': 'GA',
        'zip_code': '30301',
        'website': 'www.cleanprosupplies.com'
    },
    {
        'name': 'EcoClean Solutions',
        'contact_info': 'Sarah Johnson',
        'email': 'orders@ecoclean.com',
        'phone': '(555) 234-5678',
        'address': '2500 Green Way',
        'city': 'Portland',
        'state': 'OR',
        'zip_code': '97201',
        'website': 'www.ecoclean.com'
    },
    {
        'name': 'Superior Janitorial Supply',
        'contact_info': 'Mike Rodriguez',
        'email': 'contact@superiorjan.com',
        'phone': '(555) 345-6789',
        'address': '500 Commerce Ave',
        'city': 'Dallas',
        'state': 'TX',
        'zip_code': '75201',
        'website': 'www.superiorjan.com'
    },
    {
        'name': 'Midwest Chemical Corp',
        'contact_info': 'Patricia Lee',
        'email': 'sales@midwestchem.com',
        'phone': '(555) 456-7890',
        'address': '1200 Factory Lane',
        'city': 'Chicago',
        'state': 'IL',
        'zip_code': '60601',
        'website': 'www.midwestchem.com'
    },
    {
        'name': 'Bright & Shiny Distributors',
        'contact_info': 'David Chen',
        'email': 'orders@brightshiny.com',
        'phone': '(555) 567-8901',
        'address': '3000 Distribution Center Dr',
        'city': 'Los Angeles',
        'state': 'CA',
        'zip_code': '90001',
        'website': 'www.brightshiny.com'
    },
    {
        'name': 'FastClean Direct',
        'contact_info': 'Emma Wilson',
        'email': 'sales@fastcleandirect.com',
        'phone': '(555) 678-9012',
        'address': '750 Swift Ave',
        'city': 'Denver',
        'state': 'CO',
        'zip_code': '80201',
        'website': 'www.fastcleandirect.com'
    },
    {
        'name': 'ProTech Maintenance Supply',
        'contact_info': 'James Martinez',
        'email': 'orders@protechmaint.com',
        'phone': '(555) 789-0123',
        'address': '850 Tech Park Way',
        'city': 'Austin',
        'state': 'TX',
        'zip_code': '73301',
        'website': 'www.protechmaint.com'
    },
    {
        'name': 'AllPurpose Cleaning Co.',
        'contact_info': 'Rebecca Taylor',
        'email': 'sales@allpurposeclean.com',
        'phone': '(555) 890-1234',
        'address': '1600 Service Road',
        'city': 'Seattle',
        'state': 'WA',
        'zip_code': '98101',
        'website': 'www.allpurposeclean.com'
    },
    {
        'name': 'NorthStar Supply Group',
        'contact_info': 'Kevin Anderson',
        'email': 'contact@northstarsupply.com',
        'phone': '(555) 901-2345',
        'address': '2200 Northern Blvd',
        'city': 'Minneapolis',
        'state': 'MN',
        'zip_code': '55401',
        'website': 'www.northstarsupply.com'
    },
    {
        'name': 'GreenBrand Eco Solutions',
        'contact_info': 'Lisa Anderson',
        'email': 'sales@greenbrandeco.com',
        'phone': '(555) 012-3456',
        'address': '900 Sustainable St',
        'city': 'Boulder',
        'state': 'CO',
        'zip_code': '80301',
        'website': 'www.greenbrandeco.com'
    }
]

# Cleaning supplies data
SUPPLIES_DATA = [
    {'name': 'Microfiber Cloths', 'description': 'Premium microfiber cleaning cloths, pack of 12', 'unit': 'pack', 'category': 'Tools'},
    {'name': 'All-Purpose Cleaner', 'description': 'Multi-surface all-purpose spray cleaner', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Glass Cleaner', 'description': 'Streak-free glass and window cleaner', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Disinfectant Spray', 'description': 'Hospital-grade disinfectant spray', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Bathroom Cleaner', 'description': 'Tile and grout bathroom cleaner', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Floor Stripper', 'description': 'Professional floor stripper solution', 'unit': 'gallons', 'category': 'Chemicals'},
    {'name': 'Vacuum Bags', 'description': 'Commercial vacuum bags, pack of 10', 'unit': 'pack', 'category': 'Consumables'},
    {'name': 'Trash Liners', 'description': '55-gallon heavy-duty trash bags', 'unit': 'box', 'category': 'Consumables'},
    {'name': 'Mop Heads', 'description': 'Microfiber mop heads for commercial mops', 'unit': 'pack', 'category': 'Tools'},
    {'name': 'Squeegees', 'description': 'Professional window squeegees, 12-inch', 'unit': 'each', 'category': 'Tools'},
    {'name': 'Dust Mops', 'description': 'Disposable dust mop pads', 'unit': 'pack', 'category': 'Tools'},
    {'name': 'Broom Handles', 'description': 'Aluminum broom handles', 'unit': 'each', 'category': 'Tools'},
    {'name': 'Toilet Brush', 'description': 'Commercial toilet brushes with holder', 'unit': 'each', 'category': 'Tools'},
    {'name': 'Grout Brush', 'description': 'Stiff-bristle grout brushes', 'unit': 'pack', 'category': 'Tools'},
    {'name': 'Degreaser', 'description': 'Heavy-duty kitchen degreaser', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Floor Wax', 'description': 'Commercial-grade floor polish and wax', 'unit': 'gallons', 'category': 'Chemicals'},
    {'name': 'Air Freshener', 'description': 'Professional air freshener spray', 'unit': 'bottles', 'category': 'Fragrances'},
    {'name': 'Carpet Cleaner', 'description': 'Deep carpet cleaning solution', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Upholstery Cleaner', 'description': 'Fabric and upholstery cleaner', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Stainless Steel Cleaner', 'description': 'Metal polish and cleaner for stainless steel', 'unit': 'bottles', 'category': 'Chemicals'},
    {'name': 'Latex Gloves', 'description': 'Nitrile latex gloves, box of 100', 'unit': 'box', 'category': 'Safety'},
    {'name': 'Face Masks', 'description': 'N95 respirator masks, box of 50', 'unit': 'box', 'category': 'Safety'},
    {'name': 'Safety Goggles', 'description': 'Protective safety goggles', 'unit': 'each', 'category': 'Safety'},
    {'name': 'Aprons', 'description': 'Waterproof work aprons', 'unit': 'each', 'category': 'Safety'},
    {'name': 'Bleach Solution', 'description': '3% sodium hypochlorite disinfectant', 'unit': 'gallons', 'category': 'Chemicals'},
]

def seed_database():
    """Main function to seed the database"""
    with app.app_context():
        try:
            print("Starting database seeding...")
            
            # 1. Add Vendors (only if we have less than 10)
            existing_vendors = Vendors.query.count()
            vendors_to_add = max(0, 10 - existing_vendors)
            if vendors_to_add > 0:
                print(f"\n1. Adding {vendors_to_add} vendors...")
                vendors = []
                for vendor_data in VENDOR_DATA[:vendors_to_add]:
                    vendor = Vendors(**vendor_data)
                    db.session.add(vendor)
                    vendors.append(vendor)
                db.session.commit()
                print(f"   ✓ Added {len(vendors)} vendors")
            else:
                print("\n1. Skipping vendors (already have 10+)")
                vendors = Vendors.query.all()
            
            # 2. Add Supplies (only if we have less than 25)
            existing_supplies = Supplies.query.count()
            supplies_to_add = max(0, 25 - existing_supplies)
            if supplies_to_add > 0:
                print(f"\n2. Adding {supplies_to_add} cleaning supplies...")
                supplies = []
                for supply_data in SUPPLIES_DATA[:supplies_to_add]:
                    supply = Supplies(
                        **supply_data,
                        minimum_threshold=random.randint(3, 8),
                        current_count=0  # Will be updated by orders
                    )
                    db.session.add(supply)
                    supplies.append(supply)
                db.session.commit()
                print(f"   ✓ Added {len(supplies)} cleaning supplies")
            else:
                print("\n2. Skipping supplies (already have 25+)")
                supplies = Supplies.query.all()
            
            # Get fresh lists
            vendors = Vendors.query.all()
            supplies = Supplies.query.all()
            
            # 3. Add Orders (25-30)
            print("\n3. Adding 25-30 orders with random vendors...")
            num_orders = random.randint(25, 30)
            for i in range(num_orders):
                supply = random.choice(supplies)
                vendor = random.choice(vendors)
                quantity = random.randint(5, 50)
                cost = Decimal(str(random.uniform(10.00, 200.00))).quantize(Decimal('0.01'))
                
                # Randomize order dates within the last 60 days
                days_ago = random.randint(0, 60)
                order_date = datetime.now() - timedelta(days=days_ago)
                
                # Expected delivery is 3-10 days after order
                expected_delivery = order_date + timedelta(days=random.randint(3, 10))
                
                # Some orders are already delivered, some pending/shipped
                status_choices = ['Delivered', 'Delivered', 'Delivered', 'Shipped', 'Pending']
                status = random.choice(status_choices)
                
                actual_delivery = None
                if status == 'Delivered':
                    # Delivered between order date and expected delivery
                    actual_delivery = order_date + timedelta(days=random.randint(3, 10))
                
                order = SupplyInventory(
                    supply_id=supply.id,
                    vendor_id=vendor.id,
                    quantity_ordered=quantity,
                    order_date=order_date,
                    expected_delivery_date=expected_delivery,
                    actual_delivery_date=actual_delivery,
                    status=status,
                    cost=cost,
                    notes=f"Order #{i+1} for {supply.name}",
                    transaction_type='Order'
                )
                db.session.add(order)
                
                # Update supply current_count if delivered
                if status == 'Delivered':
                    supply.current_count += quantity
                    supply.last_restocked = actual_delivery
            
            db.session.commit()
            print(f"   ✓ Added {num_orders} orders")
            
            # 4. Add Stock Removal Records (5 records)
            print("\n4. Adding 5 stock removal records by random cleaners...")
            
            # Get cleaner users
            cleaners = User.query.filter_by(role='Cleaner').all()
            
            if not cleaners:
                print("   ⚠ No cleaners found in database. Skipping stock removal records.")
                print("   Please create some Cleaner users first, then run this script again.")
            else:
                removals_added = 0
                attempts = 0
                max_attempts = 20  # Prevent infinite loop
                
                while removals_added < 5 and attempts < max_attempts:
                    attempts += 1
                    supply = random.choice(supplies)
                    
                    # Only attempt removal if we have stock
                    if supply.current_count > 0:
                        cleaner = random.choice(cleaners)
                        # Take a reasonable amount (not more than what we have)
                        max_to_take = min(10, supply.current_count)
                        if max_to_take < 1:
                            continue
                            
                        quantity = random.randint(1, max_to_take)
                        
                        # Randomize taken_at within last 30 days
                        days_ago = random.randint(0, 30)
                        taken_at = datetime.now() - timedelta(days=days_ago)
                        
                        reasons = [
                            'Stock used for scheduled cleaning appointment',
                            'Restocked cleaner kit for field work',
                            'Used during routine maintenance',
                            'Replaced damaged/empty supply',
                            'Used for deep cleaning project'
                        ]
                        
                        # Create the removal record
                        # Assign a random vendor (even though logically stock taken doesn't come from vendor,
                        # we do this to avoid DB constraint issues if vendor_id cannot be NULL)
                        removal_vendor = random.choice(vendors)
                        removal = SupplyInventory(
                            supply_id=supply.id,
                            vendor_id=removal_vendor.id,
                            quantity_ordered=quantity,
                            status='Delivered',  # Using known working value
                            transaction_type='Adjustment',
                            taken_by_user_id=cleaner.id,
                            taken_at=taken_at,
                            reason=random.choice(reasons),
                            quantity_remaining=supply.current_count - quantity  # What will be left after removal
                        )
                        db.session.add(removal)
                        
                        # Update supply current_count
                        supply.current_count -= quantity
                        removals_added += 1
                        print(f"     → Removed {quantity} units of '{supply.name}' (Cleaner ID: {cleaner.id})")
                
                # Commit all at once to avoid autoflush issues
                db.session.commit()
                print(f"   ✓ Added {removals_added} stock removal records")
            
            print("\n✅ Database seeding completed successfully!")
            
            # Print summary
            print("\n--- Summary ---")
            print(f"Vendors in DB: {Vendors.query.count()}")
            print(f"Supplies in DB: {Supplies.query.count()}")
            print(f"Total Inventory Transactions: {SupplyInventory.query.count()}")
            print(f"Orders: {SupplyInventory.query.filter_by(transaction_type='Order').count()}")
            print(f"Stock Removals (Adjustments): {SupplyInventory.query.filter_by(transaction_type='Adjustment').count()}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during seeding: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    seed_database()