#!/usr/bin/env python3
"""
Seed script to populate test data for the financial dashboard.
This creates sample appointments with different statuses and costs.
"""

from app import app, db
from models import Appointment, User
from datetime import datetime, timedelta
import random

def seed_financial_data():
    """Create test appointments with revenue data"""
    
    with app.app_context():
        # Clear existing appointments (optional - comment out if you want to keep existing data)
        # Appointment.query.delete()
        
        # Get a cleaner user (or create one if needed)
        cleaners = User.query.filter_by(role='Cleaner').all()
        
        if not cleaners:
            print("No cleaners found. Please create cleaners first using seed_users.py")
            return
        
        # Generate sample appointments for the past 3 months
        base_date = datetime.now().date()
        service_costs = [50, 75, 100, 125, 150, 175, 200]
        statuses = ['Paid', 'Finished', 'Pending']
        
        appointments_created = 0
        
        for days_ago in range(90, 0, -1):
            if random.random() < 0.3:  # 30% chance of appointment on each day
                appointment_date = base_date - timedelta(days=days_ago)
                
                # Create appointment
                appointment = Appointment(
                    cleaner_id=random.choice(cleaners).id,
                    scheduled_time=datetime.combine(appointment_date, datetime.min.time()).replace(hour=random.randint(9, 16)),
                    end_time=datetime.combine(appointment_date, datetime.min.time()).replace(hour=random.randint(17, 20)),
                    status=random.choice(statuses),
                    cost=random.choice(service_costs),
                    service_notes=f"Sample cleaning appointment created for testing"
                )
                
                # If status is Paid, set paid_date
                if appointment.status == 'Paid':
                    days_after_scheduled = random.randint(0, 5)
                    appointment.paid_date = datetime.combine(
                        appointment_date + timedelta(days=days_after_scheduled),
                        datetime.min.time()
                    ).replace(hour=random.randint(9, 17))
                
                db.session.add(appointment)
                appointments_created += 1
        
        try:
            db.session.commit()
            print(f"✓ Successfully created {appointments_created} sample appointments for testing")
            
            # Print summary
            total_paid = db.session.query(db.func.sum(Appointment.cost)).filter(
                Appointment.status == 'Paid'
            ).scalar() or 0
            
            total_unpaid = db.session.query(db.func.sum(Appointment.cost)).filter(
                Appointment.status == 'Finished'
            ).scalar() or 0
            
            print(f"\nSummary:")
            print(f"  Total Paid Revenue: ${total_paid:.2f}")
            print(f"  Total Unpaid Revenue: ${total_unpaid:.2f}")
            print(f"  Total Revenue: ${total_paid + total_unpaid:.2f}")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating appointments: {e}")

if __name__ == '__main__':
    seed_financial_data()
