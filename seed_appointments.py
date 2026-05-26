from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import csv
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class CustomerContact(db.Model):
    __tablename__ = 'customer_contacts'
    customer_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    property_nickname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Appointment(db.Model):
    __tablename__ = 'appointments'
    apt_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer_contacts.customer_id'), nullable=False)
    cleaner_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('Pending', 'In Progress', 'Finished', 'Paid', 'Busy', 'Cancelled'), default='Pending')
    scheduled_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    service_notes = db.Column(db.Text)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    paid_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

def get_service_notes(customer_id, customer_map):
    """Generate contextual service notes based on customer"""
    if customer_id in customer_map:
        customer = customer_map[customer_id]
        property_name = customer['property_nickname']
        
        notes_templates = [
            f"Regular weekly cleaning at {property_name}",
            f"Deep clean scheduled for {property_name}",
            f"Maintenance cleaning at {property_name}",
            f"Standard cleaning service at {property_name}",
            f"Post-maintenance cleanup at {property_name}",
            f"Weekly tidying at {property_name}",
            f"Full property cleaning at {property_name}",
        ]
        return random.choice(notes_templates)
    return "General cleaning appointment"

def is_weekend(date):
    """Check if date is Saturday (5) or Sunday (6)"""
    return date.weekday() >= 5

def is_holiday(date):
    """Check if date is a major US holiday"""
    holidays = [
        (5, 26),   # Memorial Day (last Monday in May) - use 5/26
        (7, 4),    # Independence Day
        (9, 1),    # Labor Day (first Monday in September) - use 9/1
        (11, 27),  # Thanksgiving (fourth Thursday in November)
        (11, 28),  # Day after Thanksgiving
        (12, 25),  # Christmas
        (12, 26),  # Day after Christmas
    ]
    return (date.month, date.day) in holidays

def can_schedule(date):
    """Check if a date is available for scheduling (not weekend or holiday)"""
    return not is_weekend(date) and not is_holiday(date)

def generate_appointments_for_date_range(start_date, end_date, customers, cleaners, customer_map, regulars):
    """Generate appointments with sparse/busy day patterns"""
    appointments = []
    current_date = start_date
    apt_counter = 1
    
    # Pattern: 2 sparse days, 1 moderate day, 1 busy day, repeat
    pattern_day = 0
    days_with_appts = []
    
    while current_date <= end_date:
        if can_schedule(current_date):
            pattern_day = (pattern_day + 1) % 4
            
            # Determine how many appointments for this day
            if pattern_day in [0, 1]:  # Sparse days (0 or 1 appointment)
                num_appts = random.choices([0, 1], weights=[0.6, 0.4])[0]
            elif pattern_day == 2:  # Moderate day (2-3 appointments)
                num_appts = random.randint(2, 3)
            else:  # Busy day (3-5 appointments)
                num_appts = random.randint(3, 5)
            
            for i in range(num_appts):
                # Randomly choose a customer, but weight towards regulars for consistency
                if random.random() < 0.4:  # 40% chance of regular
                    customer_id = random.choice(regulars)
                else:
                    customer_id = random.choice(customers)
                
                # Random appointment time (9 AM to 5 PM, varying durations)
                hour = random.randint(9, 16)
                duration = random.randint(3, 6)  # 3-6 hour appointments
                scheduled_time = current_date.replace(hour=hour, minute=0, second=0)
                end_time = scheduled_time + timedelta(hours=duration)
                
                # Random status and cost
                status = random.choice(['Pending', 'Paid', 'Finished'])
                cost = random.randint(50, 250)
                
                paid_date = None
                if status == 'Paid':
                    paid_date = scheduled_time + timedelta(days=random.randint(1, 7))
                
                cleaner_id = random.choice(cleaners)
                
                appointment = {
                    'customer_id': customer_id,
                    'cleaner_id': cleaner_id,
                    'status': status,
                    'scheduled_time': scheduled_time,
                    'end_time': end_time,
                    'service_notes': get_service_notes(customer_id, customer_map),
                    'cost': cost,
                    'paid_date': paid_date,
                }
                appointments.append(appointment)
                apt_counter += 1
        
        current_date += timedelta(days=1)
    
    return appointments

with app.app_context():
    db.create_all()
    print("--- Seeding appointments ---")
    
    # Fetch all customers
    all_customers = db.session.query(CustomerContact).all()
    customer_ids = [c.customer_id for c in all_customers]
    customer_map = {c.customer_id: {'property_nickname': c.property_nickname, 'address': c.address} for c in all_customers}
    
    print(f"Found {len(customer_ids)} customers")
    
    # Choose 2-3 regular customers
    num_regulars = random.randint(2, 3)
    regulars = random.sample(customer_ids, num_regulars)
    print(f"Regulars: {regulars}")
    
    # Cleaner IDs available (from seed_users.py: 5, 6, 7)
    cleaners = [5, 6, 7]
    
    appointments = []
    apt_id = 1
    
    # Parse CSV and create appointments with proper customer assignment
    print("\n--- Processing CSV data ---")
    with open('appointments_data.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Randomly assign a customer
            customer_id = random.choice(customer_ids)
            
            # Parse datetime fields
            scheduled_time = datetime.strptime(row['scheduled_time'], '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(row['end_time'], '%Y-%m-%d %H:%M:%S')
            
            paid_date = None
            if row['paid_date'] != 'NULL':
                paid_date = datetime.strptime(row['paid_date'], '%Y-%m-%d %H:%M:%S')
            
            cost = None
            if row['cost'] != 'NULL':
                cost = float(row['cost'])
            
            service_notes = get_service_notes(customer_id, customer_map)
            
            appointment = Appointment(
                apt_id=apt_id,
                customer_id=customer_id,
                cleaner_id=int(row['cleaner_id']),
                status=row['status'],
                scheduled_time=scheduled_time,
                end_time=end_time,
                service_notes=service_notes,
                cost=cost,
                paid_date=paid_date,
            )
            appointments.append(appointment)
            apt_id += 1
            print(f"CSV Apt {apt_id}: Customer {customer_id} - {scheduled_time.strftime('%Y-%m-%d')}")
    
    # Generate appointments for May 21 - May 31
    print("\n--- Generating May appointments (21-31) ---")
    may_start = datetime(2026, 5, 21)
    may_end = datetime(2026, 5, 31)
    may_apts = generate_appointments_for_date_range(may_start, may_end, customer_ids, cleaners, customer_map, regulars)
    
    for apt_data in may_apts:
        appointment = Appointment(
            apt_id=apt_id,
            customer_id=apt_data['customer_id'],
            cleaner_id=apt_data['cleaner_id'],
            status=apt_data['status'],
            scheduled_time=apt_data['scheduled_time'],
            end_time=apt_data['end_time'],
            service_notes=apt_data['service_notes'],
            cost=apt_data['cost'],
            paid_date=apt_data['paid_date'],
        )
        appointments.append(appointment)
        apt_id += 1
    
    print(f"Added {len(may_apts)} May appointments")
    
    # Generate appointments for June, July, August
    print("\n--- Generating June appointments ---")
    june_start = datetime(2026, 6, 1)
    june_end = datetime(2026, 6, 30)
    june_apts = generate_appointments_for_date_range(june_start, june_end, customer_ids, cleaners, customer_map, regulars)
    for apt_data in june_apts:
        appointment = Appointment(
            apt_id=apt_id,
            customer_id=apt_data['customer_id'],
            cleaner_id=apt_data['cleaner_id'],
            status=apt_data['status'],
            scheduled_time=apt_data['scheduled_time'],
            end_time=apt_data['end_time'],
            service_notes=apt_data['service_notes'],
            cost=apt_data['cost'],
            paid_date=apt_data['paid_date'],
        )
        appointments.append(appointment)
        apt_id += 1
    print(f"Added {len(june_apts)} June appointments")
    
    print("\n--- Generating July appointments ---")
    july_start = datetime(2026, 7, 1)
    july_end = datetime(2026, 7, 31)
    july_apts = generate_appointments_for_date_range(july_start, july_end, customer_ids, cleaners, customer_map, regulars)
    for apt_data in july_apts:
        appointment = Appointment(
            apt_id=apt_id,
            customer_id=apt_data['customer_id'],
            cleaner_id=apt_data['cleaner_id'],
            status=apt_data['status'],
            scheduled_time=apt_data['scheduled_time'],
            end_time=apt_data['end_time'],
            service_notes=apt_data['service_notes'],
            cost=apt_data['cost'],
            paid_date=apt_data['paid_date'],
        )
        appointments.append(appointment)
        apt_id += 1
    print(f"Added {len(july_apts)} July appointments")
    
    print("\n--- Generating August appointments ---")
    august_start = datetime(2026, 8, 1)
    august_end = datetime(2026, 8, 31)
    august_apts = generate_appointments_for_date_range(august_start, august_end, customer_ids, cleaners, customer_map, regulars)
    for apt_data in august_apts:
        appointment = Appointment(
            apt_id=apt_id,
            customer_id=apt_data['customer_id'],
            cleaner_id=apt_data['cleaner_id'],
            status=apt_data['status'],
            scheduled_time=apt_data['scheduled_time'],
            end_time=apt_data['end_time'],
            service_notes=apt_data['service_notes'],
            cost=apt_data['cost'],
            paid_date=apt_data['paid_date'],
        )
        appointments.append(appointment)
        apt_id += 1
    print(f"Added {len(august_apts)} August appointments")
    
    # Generate weekly appointments for regulars through end of year
    print("\n--- Generating weekly appointments for regulars (Sept - Dec) ---")
    regular_apts_count = 0
    for regular_customer_id in regulars:
        current_date = datetime(2026, 9, 1)
        end_date = datetime(2026, 12, 31)
        
        while current_date <= end_date:
            # Only schedule on weekdays, not holidays
            if can_schedule(current_date):
                # Schedule on same weekday each week for consistency
                hour = random.randint(9, 14)
                duration = random.randint(3, 5)
                scheduled_time = current_date.replace(hour=hour, minute=0, second=0)
                end_time = scheduled_time + timedelta(hours=duration)
                
                status = random.choice(['Pending', 'Paid', 'Finished'])
                cost = random.randint(75, 200)
                paid_date = None
                if status == 'Paid':
                    paid_date = scheduled_time + timedelta(days=random.randint(1, 3))
                
                cleaner_id = random.choice(cleaners)
                
                appointment = Appointment(
                    apt_id=apt_id,
                    customer_id=regular_customer_id,
                    cleaner_id=cleaner_id,
                    status=status,
                    scheduled_time=scheduled_time,
                    end_time=end_time,
                    service_notes=get_service_notes(regular_customer_id, customer_map),
                    cost=cost,
                    paid_date=paid_date,
                )
                appointments.append(appointment)
                apt_id += 1
                regular_apts_count += 1
                
                # Move to next week
                current_date += timedelta(days=7)
            else:
                # Skip weekends/holidays
                current_date += timedelta(days=1)
    
    print(f"Added {regular_apts_count} weekly appointments for {num_regulars} regular customers")
    
    # Commit all appointments to database
    print("\n--- Committing to database ---")
    csv_count = 60  # Approximate count from CSV
    try:
        db.session.add_all(appointments)
        db.session.commit()
        print(f"✓ Successfully seeded {len(appointments)} total appointments")
        print(f"  - CSV appointments: {csv_count}")
        print(f"  - May appointments: {len(may_apts)}")
        print(f"  - June appointments: {len(june_apts)}")
        print(f"  - July appointments: {len(july_apts)}")
        print(f"  - August appointments: {len(august_apts)}")
        print(f"  - Regular customer weekly appointments: {regular_apts_count}")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
