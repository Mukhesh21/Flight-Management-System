from datetime import datetime
from models import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    # Types: 'booking', 'delay', 'cancellation', 'gate_change', 'boarding', 'baggage', 'system'
    notification_type = db.Column(db.String(30), default='system', index=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    link_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @property
    def icon_class(self):
        mapping = {
            'booking': 'bi-ticket-perforated-fill text-success',
            'delay': 'bi-clock-history text-danger',
            'cancellation': 'bi-x-octagon-fill text-danger',
            'gate_change': 'bi-door-open-fill text-warning',
            'boarding': 'bi-airplane-engines text-primary',
            'baggage': 'bi-luggage-fill text-info',
            'system': 'bi-bell-fill text-secondary'
        }
        return mapping.get(self.notification_type, 'bi-bell-fill text-secondary')

    def __repr__(self):
        return f'<Notification {self.id} -> User {self.user_id}: {self.title}>'
