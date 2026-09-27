import uuid
from datetime import datetime
from models import db

def generate_baggage_tag():
    return 'BG-' + str(uuid.uuid4().hex[:6]).upper()

class Baggage(db.Model):
    __tablename__ = 'baggage'

    id = db.Column(db.Integer, primary_key=True)
    baggage_tag = db.Column(db.String(30), unique=True, nullable=False, default=generate_baggage_tag, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False, index=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    weight_kg = db.Column(db.Float, nullable=False, default=15.0)
    baggage_type = db.Column(db.String(30), default='Check-In') # 'Cabin', 'Check-In', 'Heavy / Fragile'
    
    # Baggage statuses: 'Checked-In' -> 'Security Checked' -> 'Loaded' -> 'In Transit' -> 'Arrived' -> 'Delivered'
    status = db.Column(db.String(30), nullable=False, default='Checked-In', index=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    logs = db.relationship('BaggageLog', backref='baggage', cascade='all, delete-orphan', lazy='dynamic', order_by='BaggageLog.timestamp.asc()')
    passenger = db.relationship('User', backref='baggage_items')

    @property
    def status_step_index(self):
        steps = ['Checked-In', 'Security Checked', 'Loaded', 'In Transit', 'Arrived', 'Delivered']
        if self.status in steps:
            return steps.index(self.status) + 1
        return 1

    @property
    def status_badge_class(self):
        mapping = {
            'Checked-In': 'bg-secondary',
            'Security Checked': 'bg-info text-dark',
            'Loaded': 'bg-warning text-dark',
            'In Transit': 'bg-primary',
            'Arrived': 'bg-purple text-white',
            'Delivered': 'bg-success'
        }
        return mapping.get(self.status, 'bg-secondary')

    def __repr__(self):
        return f'<Baggage {self.baggage_tag} - {self.weight_kg}kg ({self.status})>'


class BaggageLog(db.Model):
    __tablename__ = 'baggage_logs'

    id = db.Column(db.Integer, primary_key=True)
    baggage_id = db.Column(db.Integer, db.ForeignKey('baggage.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(100), default='Airport Terminal')
    notes = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f'<BaggageLog {self.baggage_id} -> {self.status} at {self.timestamp}>'
