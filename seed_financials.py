#!/usr/bin/env python3
"""
Seed script to populate test data for the financial dashboard.
This creates sample appointments with different statuses and costs.
"""

from app import app, db
from models import Appointment, User, CustomerContact
from datetime import datetime, timedelta
import random

def seed_financial_data():
    """Create test appointments with revenue data"""
    
    with app.app_context():
        # Clear existing appointments to start fresh
        Appointment.query.delete()
        db.session.commit()
        
        # Get a cleaner user (or create one if needed)
        cleaners = User.query.filter_by(role='Cleaner').all()
        
        if not cleaners:
            print("No cleaners found. Please create cleaners first using seed_users.py")
            return
        
        # Get customers for assigning to appointments
        customers = CustomerContact.query.all()
        if not customers:
            print("No customers found. Please create customers first using seed_users.py")
            return

        # Generate sample appointments for the past 3 months
        base_date = datetime.now().date()
        service_costs = [50, 75, 100, 125, 150, 175, 200]
        statuses = ['Paid', 'Finished', 'Scheduled']
        
        appointments_created = 0
        
        for days_ago in range(90, 0, -1):
            if random.random() < 0.7:  # 70% chance of appointment on each day
                appointment_date = base_date - timedelta(days=days_ago)
                
                # Random scheduled start hour (8 AM - 12 PM)
                start_hour = random.randint(8, 12)
                scheduled_start = datetime.combine(appointment_date, datetime.min.time()).replace(hour=start_hour)
                
                # Scheduled duration: 1-4 hours
                scheduled_duration_hours = random.randint(1, 4)
                scheduled_end = scheduled_start + timedelta(hours=scheduled_duration_hours)
                
                # Create appointment
                appointment = Appointment(
                    cleaner_id=random.choice(cleaners).id,
                    customer_id=random.choice(customers).customer_id,
                    scheduled_time=scheduled_start,
                    end_time=scheduled_end,
                    status=random.choice(statuses),
                    cost=random.choice(service_costs),
                    service_notes=f"Sample cleaning appointment created for testing"
                )
                
                # For Finished/Paid jobs, populate actual timing so hours_spent gets computed
                if appointment.status in ('Finished', 'Paid'):
                    # Actual start: 0-30 minutes after scheduled (being late or early)
                    late_minutes = random.randint(-15, 30)
                    appointment.actual_start_time = scheduled_start + timedelta(minutes=late_minutes)
                    
                    # Actual duration: varies from scheduled (80% to 120% of scheduled)
                    actual_duration_hours = scheduled_duration_hours * random.uniform(0.8, 1.2)
                    appointment.actual_finish_time = appointment.actual_start_time + timedelta(hours=actual_duration_hours)
                
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
