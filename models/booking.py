import uuid
from datetime import datetime
from models import db

def generate_booking_ref():
    return 'BK' + str(uuid.uuid4().hex[:6]).upper()

def generate_boarding_pass():
    return 'BP' + str(uuid.uuid4().hex[:8]).upper()

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False, default=generate_booking_ref, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id', ondelete='CASCADE'), nullable=False, index=True)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=False)
    
    # Passenger Details on Ticket
    passenger_name = db.Column(db.String(100), nullable=False)
    passenger_email = db.Column(db.String(120), nullable=False)
    passenger_phone = db.Column(db.String(20), nullable=False)
    passenger_age = db.Column(db.Integer, nullable=True)
    passenger_gender = db.Column(db.String(10), nullable=True) # Male, Female, Other
    passport_number = db.Column(db.String(30), nullable=True)

    # Pricing & Status
    total_fare = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Statuses: 'Confirmed', 'Checked-In', 'Boarded', 'Cancelled'
    status = db.Column(db.String(30), nullable=False, default='Confirmed', index=True)
    cancellation_date = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.String(255), nullable=True)

    # Relationships
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade='all, delete-orphan')
    baggage_items = db.relationship('Baggage', backref='booking', cascade='all, delete-orphan', lazy='dynamic')
    checkin_record = db.relationship('CheckIn', backref='booking', uselist=False, cascade='all, delete-orphan')
    boarding_record = db.relationship('Boarding', backref='booking', uselist=False, cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.status in ['Confirmed', 'Checked-In', 'Boarded']

    @property
    def can_cancel(self):
        return self.status == 'Confirmed' and self.flight.status in ['Scheduled', 'Delayed']

    @property
    def can_checkin(self):
        return self.status == 'Confirmed' and self.flight.status in ['Scheduled', 'Delayed', 'Boarding']

    @property
    def status_badge(self):
        mapping = {
            'Confirmed': 'bg-success',
            'Checked-In': 'bg-info text-dark',
            'Boarded': 'bg-primary',
            'Cancelled': 'bg-danger'
        }
        return mapping.get(self.status, 'bg-secondary')

    def __repr__(self):
        return f'<Booking {self.booking_reference} - {self.passenger_name} ({self.status})>'


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, unique=True)
    payment_reference = db.Column(db.String(40), unique=True, nullable=False, default=lambda: 'PAY' + str(uuid.uuid4().hex[:8]).upper())
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(30), default='Credit Card') # 'Credit Card', 'Debit Card', 'UPI', 'Net Banking'
    payment_status = db.Column(db.String(20), default='Success') # 'Success', 'Refunded', 'Failed'
    transaction_time = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.payment_reference} - Rs.{self.amount} ({self.payment_status})>'


class CheckIn(db.Model):
    __tablename__ = 'checkins'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, unique=True)
    checkin_time = db.Column(db.DateTime, default=datetime.utcnow)
    checkin_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    boarding_pass_no = db.Column(db.String(30), unique=True, nullable=False, default=generate_boarding_pass)
    gate = db.Column(db.String(20), nullable=True)
    sequence_no = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<CheckIn BP={self.boarding_pass_no} booking_id={self.booking_id}>'


class Boarding(db.Model):
    __tablename__ = 'boarding'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, unique=True)
    boarding_time = db.Column(db.DateTime, default=datetime.utcnow)
    boarded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='Boarded') # 'Boarded', 'No-Show'

    def __repr__(self):
        return f'<Boarding booking_id={self.booking_id} status={self.status}>'
