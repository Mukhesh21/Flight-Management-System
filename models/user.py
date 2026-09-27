from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='passenger')  # 'passenger', 'admin', 'staff'
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    passenger_profile = db.relationship('PassengerProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='passenger_user', lazy='dynamic', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role in ['admin', 'staff']

    @property
    def is_passenger(self):
        return self.role == 'passenger'

    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.username} [{self.role}]>'


class PassengerProfile(db.Model):
    __tablename__ = 'passengers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    passport_number = db.Column(db.String(30), nullable=True)
    nationality = db.Column(db.String(50), default='Indian')
    date_of_birth = db.Column(db.Date, nullable=True)
    frequent_flyer_no = db.Column(db.String(30), nullable=True)
    emergency_contact = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<PassengerProfile user_id={self.user_id}>'


class StaffProfile(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    employee_id = db.Column(db.String(30), unique=True, nullable=False)
    department = db.Column(db.String(50), default='Ground Operations') # 'Ground Operations', 'Flight Dispatch', 'Security', 'Baggage Services'
    airport_code = db.Column(db.String(10), default='DEL')
    designation = db.Column(db.String(50), default='Operations Officer')

    def __repr__(self):
        return f'<StaffProfile employee_id={self.employee_id}>'
