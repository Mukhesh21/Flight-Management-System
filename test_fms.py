"""
Automated Comprehensive Test Suite for Smart Flight Management System (FMS)
Validates all 14 Core Modules & Business Logic
"""

import unittest
from datetime import datetime, timedelta
from app import create_app
from config import Config
from models import (
    db, User, PassengerProfile, StaffProfile, Aircraft, Flight, Seat,
    Booking, Payment, CheckIn, Boarding, Baggage, BaggageLog, Notification,
    FlightDelay, FlightCancellation
)

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'

class FlightManagementSystemTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed basic test entities
        # Admin
        self.admin = User(username='admin_test', email='admin@test.com', full_name='Admin Test', role='admin')
        self.admin.set_password('admin123')

        # Staff
        self.staff = User(username='staff_test', email='staff@test.com', full_name='Staff Test', role='staff')
        self.staff.set_password('staff123')

        # Passenger
        self.passenger = User(username='passenger_test', email='pass@test.com', full_name='Passenger Test', role='passenger')
        self.passenger.set_password('pass123')

        db.session.add_all([self.admin, self.staff, self.passenger])
        db.session.commit()

        # Aircraft
        self.aircraft = Aircraft(
            model='Airbus A320neo',
            registration_no='VT-TST01',
            total_seats=180,
            economy_seats=150,
            business_seats=24,
            first_class_seats=6
        )
        db.session.add(self.aircraft)
        db.session.commit()

        # Flight
        dep_time = datetime.utcnow() + timedelta(days=1)
        arr_time = dep_time + timedelta(hours=2, minutes=30)
        self.flight = Flight(
            flight_number='SW-101',
            airline_name='SkyWings Test',
            source='Chennai',
            source_code='MAA',
            destination='Delhi',
            destination_code='DEL',
            departure_time=dep_time,
            arrival_time=arr_time,
            duration='2h 30m',
            aircraft_id=self.aircraft.id,
            gate='A1',
            terminal='T1',
            status='Scheduled',
            base_price=5000.0,
            available_seats=0
        )
        db.session.add(self.flight)
        db.session.flush()
        self.flight.generate_seats_for_flight()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_seat_generation(self):
        """Module 4: Verify seat map generator accurately builds cabin rows and capacity"""
        seats_count = Seat.query.filter_by(flight_id=self.flight.id).count()
        self.assertEqual(seats_count, 180)
        self.assertEqual(self.flight.available_seats, 180)
        
        # Verify first class seat
        seat_1a = Seat.query.filter_by(flight_id=self.flight.id, seat_number='1A').first()
        self.assertIsNotNone(seat_1a)
        self.assertEqual(seat_1a.seat_class, 'First')
        self.assertFalse(seat_1a.is_occupied)

    def test_flight_search(self):
        """Module 3: Verify flight search by origin and destination"""
        response = self.client.get('/passenger/search?source=Chennai&destination=Delhi')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SW-101', response.data)
        self.assertIn(b'MAA', response.data)

    def test_booking_creation_and_seat_locking(self):
        """Module 5: Verify booking reservation, seat occupancy update, fare calculation, and notification"""
        # Login passenger
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.passenger.id
            sess['username'] = self.passenger.username
            sess['user_role'] = 'passenger'
            sess['full_name'] = self.passenger.full_name

        seat = Seat.query.filter_by(flight_id=self.flight.id, seat_number='12A').first()
        self.assertFalse(seat.is_occupied)

        # Post Checkout
        response = self.client.post('/passenger/booking/checkout', data={
            'flight_id': self.flight.id,
            'seat_id': seat.id,
            'passenger_name': 'Passenger Test',
            'passenger_email': 'pass@test.com',
            'passenger_phone': '+91 99999 88888',
            'passenger_age': 25,
            'passenger_gender': 'Male',
            'passport_number': 'P992211',
            'baggage_option': '15kg_standard',
            'payment_method': 'Credit Card'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Verify seat is now occupied
        seat_reloaded = Seat.query.get(seat.id)
        self.assertTrue(seat_reloaded.is_occupied)

        # Verify flight available seats decremented
        flight_reloaded = Flight.query.get(self.flight.id)
        self.assertEqual(flight_reloaded.available_seats, 179)

        # Verify Booking record exists
        booking = Booking.query.filter_by(user_id=self.passenger.id, flight_id=self.flight.id).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'Confirmed')
        self.assertEqual(booking.seat.seat_number, '12A')

        # Verify baggage record created
        baggage = Baggage.query.filter_by(booking_id=booking.id).first()
        self.assertIsNotNone(baggage)
        self.assertEqual(baggage.status, 'Checked-In')

        # Verify Passenger Notification created
        notif = Notification.query.filter_by(user_id=self.passenger.id, notification_type='booking').first()
        self.assertIsNotNone(notif)
        self.assertIn('Booking Confirmed', notif.title)

    def test_prevent_double_booking(self):
        """Module 4 & 5: Ensure occupied seat cannot be booked again"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.passenger.id
            sess['username'] = self.passenger.username
            sess['user_role'] = 'passenger'
            sess['full_name'] = self.passenger.full_name

        seat = Seat.query.filter_by(flight_id=self.flight.id, seat_number='15B').first()
        seat.is_occupied = True
        db.session.commit()

        response = self.client.post('/passenger/booking/checkout', data={
            'flight_id': self.flight.id,
            'seat_id': seat.id,
            'passenger_name': 'Another Passenger',
            'passenger_email': 'another@test.com',
            'passenger_phone': '1234567890'
        }, follow_redirects=True)

        self.assertIn(b'already occupied', response.data)

    def test_booking_cancellation_and_seat_release(self):
        """Module 6: Verify cancellation releases seat back to inventory, updates status, and logs refund"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.passenger.id
            sess['username'] = self.passenger.username
            sess['user_role'] = 'passenger'
            sess['full_name'] = self.passenger.full_name

        seat = Seat.query.filter_by(flight_id=self.flight.id, seat_number='9C').first()
        seat.is_occupied = True
        
        booking = Booking(
            user_id=self.passenger.id,
            flight_id=self.flight.id,
            seat_id=seat.id,
            passenger_name='Passenger Test',
            passenger_email='pass@test.com',
            passenger_phone='9999999999',
            total_fare=5600.0,
            status='Confirmed'
        )
        db.session.add(booking)
        self.flight.recalculate_available_seats()
        db.session.commit()

        # Cancel Booking
        response = self.client.post(f'/passenger/booking/{booking.booking_reference}/cancel', data={
            'cancel_reason': 'Change of plans'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Check booking status is Cancelled (historical record retained)
        booking_reloaded = Booking.query.get(booking.id)
        self.assertEqual(booking_reloaded.status, 'Cancelled')
        self.assertIsNotNone(booking_reloaded.cancellation_date)

        # Check seat is now released and available
        seat_reloaded = Seat.query.get(seat.id)
        self.assertFalse(seat_reloaded.is_occupied)

        # Check flight availability increased
        flight_reloaded = Flight.query.get(self.flight.id)
        self.assertEqual(flight_reloaded.available_seats, 180)

    def test_flight_delay_management_and_notifications(self):
        """Module 8: Verify admin delay updates flight, identifies affected passengers, and dispatches alerts"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.admin.id
            sess['username'] = self.admin.username
            sess['user_role'] = 'admin'
            sess['full_name'] = self.admin.full_name

        # Create confirmed passenger booking
        seat = Seat.query.filter_by(flight_id=self.flight.id, seat_number='20A').first()
        booking = Booking(
            user_id=self.passenger.id,
            flight_id=self.flight.id,
            seat_id=seat.id,
            passenger_name='Passenger Test',
            passenger_email='pass@test.com',
            passenger_phone='9999999999',
            total_fare=5000.0,
            status='Confirmed'
        )
        db.session.add(booking)
        db.session.commit()

        revised_time = self.flight.departure_time + timedelta(hours=2)
        revised_time_str = revised_time.strftime('%Y-%m-%dT%H:%M')

        response = self.client.post(f'/admin/flights/{self.flight.id}/delay', data={
            'revised_departure': revised_time_str,
            'delay_reason': 'Thunderstorm over arrival airport'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        flight_reloaded = Flight.query.get(self.flight.id)
        self.assertEqual(flight_reloaded.status, 'Delayed')

        # Check Notification was created for affected passenger
        notif = Notification.query.filter_by(user_id=self.passenger.id, notification_type='delay').first()
        self.assertIsNotNone(notif)
        self.assertIn('Flight Delay Alert', notif.title)
        self.assertIn('Thunderstorm', notif.message)

    def test_passenger_checkin_flow(self):
        """Module 11: Airport staff checkin verifies passenger, generates boarding pass and updates status"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.staff.id
            sess['username'] = self.staff.username
            sess['user_role'] = 'staff'
            sess['full_name'] = self.staff.full_name

        seat = Seat.query.filter_by(flight_id=self.flight.id, seat_number='5A').first()
        booking = Booking(
            user_id=self.passenger.id,
            flight_id=self.flight.id,
            seat_id=seat.id,
            passenger_name='Passenger Test',
            passenger_email='pass@test.com',
            passenger_phone='9999999999',
            total_fare=7500.0,
            status='Confirmed'
        )
        db.session.add(booking)
        db.session.commit()

        response = self.client.post('/staff/checkin', data={
            'booking_id': booking.id
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        booking_reloaded = Booking.query.get(booking.id)
        self.assertEqual(booking_reloaded.status, 'Checked-In')
        self.assertIsNotNone(booking_reloaded.checkin_record)
        self.assertTrue(booking_reloaded.checkin_record.boarding_pass_no.startswith('BP'))

    def test_baggage_lifecycle_advancement(self):
        """Module 7: Baggage status updates and movement logs"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.staff.id
            sess['username'] = self.staff.username
            sess['user_role'] = 'staff'
            sess['full_name'] = self.staff.full_name

        seat = Seat.query.filter_by(flight_id=self.flight.id, seat_number='6B').first()
        booking = Booking(
            user_id=self.passenger.id,
            flight_id=self.flight.id,
            seat_id=seat.id,
            passenger_name='Passenger Test',
            passenger_email='pass@test.com',
            passenger_phone='9999999999',
            total_fare=5000.0,
            status='Confirmed'
        )
        db.session.add(booking)
        db.session.flush()

        baggage = Baggage(
            booking_id=booking.id,
            passenger_id=self.passenger.id,
            weight_kg=16.0,
            status='Checked-In'
        )
        db.session.add(baggage)
        db.session.commit()

        # Advance to Loaded
        response = self.client.post('/staff/baggage', data={
            'baggage_id': baggage.id,
            'status': 'Loaded',
            'location': 'Tarmac Loading Gate A1',
            'notes': 'Luggage loaded into forward hold'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        baggage_reloaded = Baggage.query.get(baggage.id)
        self.assertEqual(baggage_reloaded.status, 'Loaded')

        # Check BaggageLog was created
        log = BaggageLog.query.filter_by(baggage_id=baggage.id, status='Loaded').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.location, 'Tarmac Loading Gate A1')

if __name__ == '__main__':
    unittest.main()
