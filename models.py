from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import Computed
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.Enum('OfficeAdmin', 'Cleaner', 'BusinessOwner'), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

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
    anniversary = db.Column(db.Date)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    #--- RELATIONSHIPS ---
    appointments = db.relationship("Appointment", back_populates="customer")

    def __repr__(self):
        return f'<CustomerContact {self.first_name} {self.last_name}>'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def full_address(self):
        return f'{self.address}, {self.city}, {self.state} {self.zip_code}'

class Appointment(db.Model):
    __tablename__ = 'appointments'
    apt_id = db.Column(db.Integer, primary_key=True)
    cleaner_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('Pending', 'Scheduled', 'In Progress', 'Finished', 'Paid', 'Busy', 'Cancelled'), default='Scheduled')
    scheduled_time = db.Column(db.DateTime)
    actual_start_time = db.Column(db.DateTime)
    actual_finish_time = db.Column(db.DateTime)
    hours_spent = db.Column(db.Numeric(5, 2), Computed("ROUND(TIMESTAMPDIFF(SECOND, actual_start_time, actual_finish_time) / 3600, 2)", persisted=True))
    end_time = db.Column(db.DateTime)
    service_notes = db.Column(db.Text)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    paid_date = db.Column(db.DateTime, nullable=True)
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)     # --- I4TP-29 TRACKING FLAG ATTRIBUTE ---
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    #--- RELATIONSHIPS ---
    customer_id = db.Column(db.Integer, db.ForeignKey('customer_contacts.customer_id'), nullable=False)
    customer = db.relationship("CustomerContact", back_populates="appointments")

class Supplies(db.Model):
    __tablename__ = 'supplies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    current_count = db.Column(db.Integer, nullable=False, default=0)
    minimum_threshold = db.Column(db.Integer, nullable=False, default=5)
    unit = db.Column(db.String(20), nullable=False, default='units')
    category = db.Column(db.String(50))
    last_restocked = db.Column(db.DateTime)
    preferred_vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    preferred_vendor = db.relationship('Vendors', backref='supplies_preferred')
    inventory_history = db.relationship('SupplyInventory', backref='supply', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Supplies {self.name}: {self.current_count} {self.unit}>'

    def needs_restocking(self):
        """Check if current stock is below minimum threshold"""
        return self.current_count <= self.minimum_threshold

class Vendors(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.String(200))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    inventory_transactions = db.relationship('SupplyInventory', backref='vendor', lazy=True, cascade='all, delete-orphan')

class SupplyInventory(db.Model):
    __tablename__ = 'supply_inventory'
    id = db.Column(db.Integer, primary_key=True)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, nullable=True)
    expected_delivery_date = db.Column(db.DateTime, nullable=True)
    actual_delivery_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Enum('Pending', 'Shipped', 'Delivered', 'Cancelled', 'Used'), default='Pending')
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    # New fields for tracking stock usage
    transaction_type = db.Column(db.Enum('Order', 'Stock Taken', 'Adjustment'), default='Order')
    taken_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    taken_at = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String(255), nullable=True)
    quantity_remaining = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationships
    taken_by_user = db.relationship('User', backref='supplies_taken')

    def __repr__(self):
        if self.transaction_type == 'Order':
            return f'<SupplyInventory Order: {self.quantity_ordered} units of supply_id {self.supply_id}>'
        else:
            return f'<SupplyInventory {self.transaction_type}: {self.quantity_ordered} units taken by user {self.taken_by_user_id}>'

    def is_order(self):
        """Check if this transaction is an incoming order"""
        return self.transaction_type == 'Order'

    def is_stock_usage(self):
        """Check if this transaction is a stock usage"""
        return self.transaction_type == 'Stock Taken'

class InventoryAudit(db.Model):
    __tablename__ = 'inventory_audit'
    id = db.Column(db.Integer, primary_key=True)
    supply_id = db.Column(db.Integer, db.ForeignKey('supplies.id'), nullable=False)
    audit_type = db.Column(db.Enum('Discrepancy Found', 'Manual Correction', 'Reconciliation', 'Validation Failed'), nullable=False)
    previous_count = db.Column(db.Integer, nullable=False)
    new_count = db.Column(db.Integer, nullable=False)
    calculated_count = db.Column(db.Integer, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    corrected_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relationships
    supply = db.relationship('Supplies', backref='audit_logs')
    corrected_by_user = db.relationship('User', backref='inventory_corrections')

    def __repr__(self):
        return f'<InventoryAudit supply_id={self.supply_id}: {self.audit_type}>'
