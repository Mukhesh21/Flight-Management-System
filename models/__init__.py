from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User, PassengerProfile, StaffProfile
from models.flight import Aircraft, Flight, Seat, FlightDelay, FlightCancellation
from models.booking import Booking, Payment, CheckIn, Boarding
from models.baggage import Baggage, BaggageLog
from models.notification import Notification

__all__ = [
    'db',
    'User',
    'PassengerProfile',
    'StaffProfile',
    'Aircraft',
    'Flight',
    'Seat',
    'FlightDelay',
    'FlightCancellation',
    'Booking',
    'Payment',
    'CheckIn',
    'Boarding',
    'Baggage',
    'BaggageLog',
    'Notification'
]
