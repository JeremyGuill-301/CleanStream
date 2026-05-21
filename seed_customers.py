from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
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

# Customer data - 55 records total
customers_data = [
    # User-provided records
    {"customer_id": 1, "first_name": "Robert", "last_name": "Smith", "address": "1042 Elm Street", "property_nickname": "Smith Residence", "phone": "(555) 101-1001", "email": "robert.smith@email.com"},
    {"customer_id": 2, "first_name": "Margaret", "last_name": "Miller", "address": "582 Oak Avenue", "property_nickname": "Miller Estate", "phone": "(555) 101-1002", "email": "margaret.miller@email.com"},
    {"customer_id": 3, "first_name": "Richard", "last_name": "Davis", "address": "904 Pine Road", "property_nickname": "Davis Luxury Rental", "phone": "(555) 101-1003", "email": "richard.davis@email.com"},
    {"customer_id": 4, "first_name": "Jennifer", "last_name": "Jones", "address": "12 Pineberry Way", "property_nickname": "Jones Apartment", "phone": "(555) 101-1004", "email": "jennifer.jones@email.com"},
    
    # Generated records in the same regional area
    {"customer_id": 5, "first_name": "William", "last_name": "Brown", "address": "237 Maple Drive", "property_nickname": "Brown Family Home", "phone": "(555) 101-1005", "email": "william.brown@email.com"},
    {"customer_id": 6, "first_name": "Elizabeth", "last_name": "Wilson", "address": "456 Cedar Lane", "property_nickname": "Wilson Manor", "phone": "(555) 101-1006", "email": "elizabeth.wilson@email.com"},
    {"customer_id": 7, "first_name": "David", "last_name": "Anderson", "address": "789 Birch Street", "property_nickname": "Anderson Cottage", "phone": "(555) 101-1007", "email": "david.anderson@email.com"},
    {"customer_id": 8, "first_name": "Susan", "last_name": "Taylor", "address": "321 Ash Avenue", "property_nickname": "Taylor Residence", "phone": "(555) 101-1008", "email": "susan.taylor@email.com"},
    {"customer_id": 9, "first_name": "Charles", "last_name": "Thomas", "address": "654 Spruce Road", "property_nickname": "Thomas Estate", "phone": "(555) 101-1009", "email": "charles.thomas@email.com"},
    {"customer_id": 10, "first_name": "Patricia", "last_name": "Jackson", "address": "147 Walnut Court", "property_nickname": "Jackson Villa", "phone": "(555) 101-1010", "email": "patricia.jackson@email.com"},
    
    {"customer_id": 11, "first_name": "Michael", "last_name": "White", "address": "258 Hickory Drive", "property_nickname": "White Haven", "phone": "(555) 101-1011", "email": "michael.white@email.com"},
    {"customer_id": 12, "first_name": "Barbara", "last_name": "Harris", "address": "369 Chestnut Street", "property_nickname": "Harris Home", "phone": "(555) 101-1012", "email": "barbara.harris@email.com"},
    {"customer_id": 13, "first_name": "Christopher", "last_name": "Martin", "address": "741 Sycamore Lane", "property_nickname": "Martin Properties", "phone": "(555) 101-1013", "email": "christopher.martin@email.com"},
    {"customer_id": 14, "first_name": "Linda", "last_name": "Thompson", "address": "852 Poplar Avenue", "property_nickname": "Thompson Sanctuary", "phone": "(555) 101-1014", "email": "linda.thompson@email.com"},
    {"customer_id": 15, "first_name": "Mark", "last_name": "Garcia", "address": "963 Laurel Street", "property_nickname": "Garcia Residence", "phone": "(555) 101-1015", "email": "mark.garcia@email.com"},
    
    {"customer_id": 16, "first_name": "Karen", "last_name": "Martinez", "address": "159 Dogwood Drive", "property_nickname": "Martinez Villa", "phone": "(555) 101-1016", "email": "karen.martinez@email.com"},
    {"customer_id": 17, "first_name": "Donald", "last_name": "Robinson", "address": "753 Magnolia Road", "property_nickname": "Robinson Estate", "phone": "(555) 101-1017", "email": "donald.robinson@email.com"},
    {"customer_id": 18, "first_name": "Nancy", "last_name": "Clark", "address": "357 Hawthorn Lane", "property_nickname": "Clark Retreat", "phone": "(555) 101-1018", "email": "nancy.clark@email.com"},
    {"customer_id": 19, "first_name": "Paul", "last_name": "Rodriguez", "address": "456 Juniper Court", "property_nickname": "Rodriguez Home", "phone": "(555) 101-1019", "email": "paul.rodriguez@email.com"},
    {"customer_id": 20, "first_name": "Lisa", "last_name": "Lewis", "address": "789 Cottonwood Street", "property_nickname": "Lewis Mansion", "phone": "(555) 101-1020", "email": "lisa.lewis@email.com"},
    
    {"customer_id": 21, "first_name": "Andrew", "last_name": "Lee", "address": "321 Fir Avenue", "property_nickname": "Lee Sanctuary", "phone": "(555) 101-1021", "email": "andrew.lee@email.com"},
    {"customer_id": 22, "first_name": "Betty", "last_name": "Walker", "address": "654 Larch Drive", "property_nickname": "Walker Properties", "phone": "(555) 101-1022", "email": "betty.walker@email.com"},
    {"customer_id": 23, "first_name": "Joshua", "last_name": "Hall", "address": "147 Thuja Lane", "property_nickname": "Hall Retreat", "phone": "(555) 101-1023", "email": "joshua.hall@email.com"},
    {"customer_id": 24, "first_name": "Dorothy", "last_name": "Allen", "address": "258 Juniper Road", "property_nickname": "Allen Estate", "phone": "(555) 101-1024", "email": "dorothy.allen@email.com"},
    {"customer_id": 25, "first_name": "Kenneth", "last_name": "Young", "address": "369 Dogwood Avenue", "property_nickname": "Young Villa", "phone": "(555) 101-1025", "email": "kenneth.young@email.com"},
    
    {"customer_id": 26, "first_name": "Sandra", "last_name": "King", "address": "741 Redbud Street", "property_nickname": "King Residence", "phone": "(555) 101-1026", "email": "sandra.king@email.com"},
    {"customer_id": 27, "first_name": "Kimberly", "last_name": "Wright", "address": "852 Crabapple Drive", "property_nickname": "Wright Haven", "phone": "(555) 101-1027", "email": "kimberly.wright@email.com"},
    {"customer_id": 28, "first_name": "Steven", "last_name": "Lopez", "address": "963 Sycamore Avenue", "property_nickname": "Lopez Properties", "phone": "(555) 101-1028", "email": "steven.lopez@email.com"},
    {"customer_id": 29, "first_name": "Angela", "last_name": "Hill", "address": "159 Serviceberry Lane", "property_nickname": "Hill Mansion", "phone": "(555) 101-1029", "email": "angela.hill@email.com"},
    {"customer_id": 30, "first_name": "Edward", "last_name": "Scott", "address": "753 Mulberry Court", "property_nickname": "Scott Estate", "phone": "(555) 101-1030", "email": "edward.scott@email.com"},
    
    {"customer_id": 31, "first_name": "Michelle", "last_name": "Green", "address": "357 Tamarack Street", "property_nickname": "Green Sanctuary", "phone": "(555) 101-1031", "email": "michelle.green@email.com"},
    {"customer_id": 32, "first_name": "Ronald", "last_name": "Adams", "address": "456 Boxwood Road", "property_nickname": "Adams Villa", "phone": "(555) 101-1032", "email": "ronald.adams@email.com"},
    {"customer_id": 33, "first_name": "Ashley", "last_name": "Nelson", "address": "789 Alder Avenue", "property_nickname": "Nelson Home", "phone": "(555) 101-1033", "email": "ashley.nelson@email.com"},
    {"customer_id": 34, "first_name": "Timothy", "last_name": "Carter", "address": "321 Elderberry Drive", "property_nickname": "Carter Retreat", "phone": "(555) 101-1034", "email": "timothy.carter@email.com"},
    {"customer_id": 35, "first_name": "Emily", "last_name": "Mitchell", "address": "654 Hackberry Lane", "property_nickname": "Mitchell Properties", "phone": "(555) 101-1035", "email": "emily.mitchell@email.com"},
    
    {"customer_id": 36, "first_name": "Jason", "last_name": "Perez", "address": "147 Sweetgum Street", "property_nickname": "Perez Estate", "phone": "(555) 101-1036", "email": "jason.perez@email.com"},
    {"customer_id": 37, "first_name": "Sarah", "last_name": "Roberts", "address": "258 Sassafras Avenue", "property_nickname": "Roberts Mansion", "phone": "(555) 101-1037", "email": "sarah.roberts@email.com"},
    {"customer_id": 38, "first_name": "Jeffrey", "last_name": "Phillips", "address": "369 Locust Road", "property_nickname": "Phillips Sanctuary", "phone": "(555) 101-1038", "email": "jeffrey.phillips@email.com"},
    {"customer_id": 39, "first_name": "Kathleen", "last_name": "Campbell", "address": "741 Ginkgo Court", "property_nickname": "Campbell Residence", "phone": "(555) 101-1039", "email": "kathleen.campbell@email.com"},
    {"customer_id": 40, "first_name": "Ryan", "last_name": "Parker", "address": "852 Neem Avenue", "property_nickname": "Parker Haven", "phone": "(555) 101-1040", "email": "ryan.parker@email.com"},
    
    {"customer_id": 41, "first_name": "Shirley", "last_name": "Evans", "address": "963 Cambium Street", "property_nickname": "Evans Properties", "phone": "(555) 101-1041", "email": "shirley.evans@email.com"},
    {"customer_id": 42, "first_name": "Jacob", "last_name": "Edwards", "address": "159 Xylem Drive", "property_nickname": "Edwards Estate", "phone": "(555) 101-1042", "email": "jacob.edwards@email.com"},
    {"customer_id": 43, "first_name": "Cynthia", "last_name": "Collins", "address": "753 Heartwood Lane", "property_nickname": "Collins Villa", "phone": "(555) 101-1043", "email": "cynthia.collins@email.com"},
    {"customer_id": 44, "first_name": "Gary", "last_name": "Stewart", "address": "357 Timber Road", "property_nickname": "Stewart Retreat", "phone": "(555) 101-1044", "email": "gary.stewart@email.com"},
    {"customer_id": 45, "first_name": "Katharine", "last_name": "Sanchez", "address": "456 Barkwood Avenue", "property_nickname": "Sanchez Home", "phone": "(555) 101-1045", "email": "katharine.sanchez@email.com"},
    
    {"customer_id": 46, "first_name": "Nicholas", "last_name": "Morris", "address": "789 Sapwood Court", "property_nickname": "Morris Sanctuary", "phone": "(555) 101-1046", "email": "nicholas.morris@email.com"},
    {"customer_id": 47, "first_name": "Angela", "last_name": "Rogers", "address": "321 Dendrite Street", "property_nickname": "Rogers Properties", "phone": "(555) 101-1047", "email": "angela.rogers@email.com"},
    {"customer_id": 48, "first_name": "Eric", "last_name": "Morgan", "address": "654 Cambial Lane", "property_nickname": "Morgan Mansion", "phone": "(555) 101-1048", "email": "eric.morgan@email.com"},
    {"customer_id": 49, "first_name": "Brenda", "last_name": "Peterson", "address": "147 Phloem Drive", "property_nickname": "Peterson Estate", "phone": "(555) 101-1049", "email": "brenda.peterson@email.com"},
    {"customer_id": 50, "first_name": "Jonathan", "last_name": "Powell", "address": "258 Vascular Road", "property_nickname": "Powell Residence", "phone": "(555) 101-1050", "email": "jonathan.powell@email.com"},
    
    {"customer_id": 51, "first_name": "Carolyn", "last_name": "Long", "address": "369 Xylem Avenue", "property_nickname": "Long Haven", "phone": "(555) 101-1051", "email": "carolyn.long@email.com"},
    {"customer_id": 52, "first_name": "Jerry", "last_name": "Patterson", "address": "741 Phloem Street", "property_nickname": "Patterson Properties", "phone": "(555) 101-1052", "email": "jerry.patterson@email.com"},
    {"customer_id": 53, "first_name": "Diane", "last_name": "Hughes", "address": "852 Cambium Road", "property_nickname": "Hughes Estate", "phone": "(555) 101-1053", "email": "diane.hughes@email.com"},
    {"customer_id": 54, "first_name": "Larry", "last_name": "Flores", "address": "963 Xylem Lane", "property_nickname": "Flores Sanctuary", "phone": "(555) 101-1054", "email": "larry.flores@email.com"},
    {"customer_id": 55, "first_name": "Joyce", "last_name": "Washington", "address": "159 Cambial Avenue", "property_nickname": "Washington Villa", "phone": "(555) 101-1055", "email": "joyce.washington@email.com"},
]

with app.app_context():
    db.create_all()
    print("--- Seeding customers ---")

    print("Connecting to database...")
    
    customers = []
    for customer_data in customers_data:
        customer = CustomerContact(
            customer_id=customer_data['customer_id'],
            first_name=customer_data['first_name'],
            last_name=customer_data['last_name'],
            property_nickname=customer_data['property_nickname'],
            email=customer_data['email'],
            phone=customer_data['phone'],
            address=customer_data['address'],
            city='Anytown',
            state='CA',
            zip_code='90210'
        )
        customers.append(customer)
        print(f"--- Customer {customer.customer_id}: {customer.first_name} {customer.last_name} ({customer.property_nickname}) added ---")

    try:
        db.session.add_all(customers)
        db.session.commit()
        print(f"\n--- Successfully seeded {len(customers)} customers ---")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()
