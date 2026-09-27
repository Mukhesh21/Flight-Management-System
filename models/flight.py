from datetime import datetime
from models import db

class Aircraft(db.Model):
    __tablename__ = 'aircraft'

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(80), nullable=False) # e.g., 'Airbus A320neo', 'Boeing 737-800', 'Boeing 787-9 Dreamliner'
    registration_no = db.Column(db.String(30), unique=True, nullable=False) # e.g., 'VT-SKY101'
    total_seats = db.Column(db.Integer, nullable=False, default=180)
    economy_seats = db.Column(db.Integer, nullable=False, default=150)
    business_seats = db.Column(db.Integer, nullable=False, default=24)
    first_class_seats = db.Column(db.Integer, nullable=False, default=6)
    status = db.Column(db.String(20), default='Active') # 'Active', 'Maintenance', 'Standby'

    flights = db.relationship('Flight', backref='aircraft', lazy='dynamic')

    def __repr__(self):
        return f'<Aircraft {self.model} ({self.registration_no})>'


class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), nullable=False, index=True) # e.g. 'SW-202'
    airline_name = db.Column(db.String(80), nullable=False, default='SkyWings Airlines')
    source = db.Column(db.String(80), nullable=False) # e.g. 'Chennai'
    source_code = db.Column(db.String(10), nullable=False, index=True) # e.g. 'MAA'
    destination = db.Column(db.String(80), nullable=False) # e.g. 'Delhi'
    destination_code = db.Column(db.String(10), nullable=False, index=True) # e.g. 'DEL'
    
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.String(30), nullable=True) # e.g. '2h 50m'
    
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    gate = db.Column(db.String(20), default='A1')
    terminal = db.Column(db.String(20), default='T3')
    
    # Flight Status: 'Scheduled', 'Boarding', 'Departed', 'Delayed', 'Cancelled', 'Arrived'
    status = db.Column(db.String(30), nullable=False, default='Scheduled', index=True)
    base_price = db.Column(db.Float, nullable=False, default=4500.0)
    available_seats = db.Column(db.Integer, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    seats = db.relationship('Seat', backref='flight', cascade='all, delete-orphan', lazy='dynamic')
    bookings = db.relationship('Booking', backref='flight', cascade='all, delete-orphan', lazy='dynamic')
    delays = db.relationship('FlightDelay', backref='flight', cascade='all, delete-orphan', lazy='dynamic')
    cancellations = db.relationship('FlightCancellation', backref='flight', cascade='all, delete-orphan', uselist=False)

    @property
    def is_bookable(self):
        return self.status in ['Scheduled', 'Delayed'] and self.available_seats > 0

    @property
    def status_badge_class(self):
        mapping = {
            'Scheduled': 'bg-primary',
            'Boarding': 'bg-warning text-dark',
            'Departed': 'bg-info text-dark',
            'Delayed': 'bg-danger',
            'Cancelled': 'bg-secondary',
            'Arrived': 'bg-success'
        }
        return mapping.get(self.status, 'bg-secondary')

    def recalculate_available_seats(self):
        occupied_count = self.seats.filter_by(is_occupied=True).count()
        total = self.seats.count()
        self.available_seats = max(0, total - occupied_count)
        return self.available_seats

    def generate_seats_for_flight(self):
        """Generates real seat layout matching aircraft configuration"""
        # First class: Rows 1-2 (1A, 1B, 1C, 1D -> 2-2 layout)
        # Business class: Rows 3-6 (3A, 3B, 3C, 3D -> 2-2 layout)
        # Economy class: Rows 7-25 (7A, 7B, 7C, 7D, 7E, 7F -> 3-3 layout)
        seats_to_add = []
        
        # Determine rows based on aircraft capacity
        fc_count = self.aircraft.first_class_seats if self.aircraft else 6
        biz_count = self.aircraft.business_seats if self.aircraft else 24
        econ_count = self.aircraft.economy_seats if self.aircraft else 150

        # First Class (2x2 layout, cols A, B, E, F)
        fc_rows = (fc_count + 3) // 4
        current_row = 1
        for r in range(1, fc_rows + 1):
            for col in ['A', 'B', 'E', 'F']:
                if len(seats_to_add) < fc_count:
                    seat_num = f"{current_row}{col}"
                    seat = Seat(
                        flight=self,
                        seat_number=seat_num,
                        seat_class='First',
                        is_occupied=False,
                        is_window=(col in ['A', 'F']),
                        is_aisle=(col in ['B', 'E']),
                        extra_price=self.base_price * 1.5
                    )
                    seats_to_add.append(seat)
            current_row += 1

        # Business Class (2x2 layout)
        biz_rows = (biz_count + 3) // 4
        biz_added = 0
        for r in range(1, biz_rows + 1):
            for col in ['A', 'B', 'E', 'F']:
                if biz_added < biz_count:
                    seat_num = f"{current_row}{col}"
                    seat = Seat(
                        flight=self,
                        seat_number=seat_num,
                        seat_class='Business',
                        is_occupied=False,
                        is_window=(col in ['A', 'F']),
                        is_aisle=(col in ['B', 'E']),
                        extra_price=self.base_price * 0.75
                    )
                    seats_to_add.append(seat)
                    biz_added += 1
            current_row += 1

        # Economy Class (3x3 layout: A, B, C | D, E, F)
        econ_added = 0
        while econ_added < econ_count:
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                if econ_added < econ_count:
                    seat_num = f"{current_row}{col}"
                    seat = Seat(
                        flight=self,
                        seat_number=seat_num,
                        seat_class='Economy',
                        is_occupied=False,
                        is_window=(col in ['A', 'F']),
                        is_aisle=(col in ['C', 'D']),
                        extra_price=0.0
                    )
                    seats_to_add.append(seat)
                    econ_added += 1
            current_row += 1

        db.session.add_all(seats_to_add)
        self.available_seats = len(seats_to_add)
        return len(seats_to_add)

    def __repr__(self):
        return f'<Flight {self.flight_number} {self.source_code}->{self.destination_code} [{self.status}]>'


class Seat(db.Model):
    __tablename__ = 'seats'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id', ondelete='CASCADE'), nullable=False, index=True)
    seat_number = db.Column(db.String(10), nullable=False) # e.g. '12A'
    seat_class = db.Column(db.String(20), nullable=False, default='Economy') # 'First', 'Business', 'Economy'
    is_occupied = db.Column(db.Boolean, default=False, nullable=False)
    is_window = db.Column(db.Boolean, default=False)
    is_aisle = db.Column(db.Boolean, default=False)
    extra_price = db.Column(db.Float, default=0.0)

    # Relationship to booking
    booking = db.relationship('Booking', backref='seat', uselist=False)

    __table_args__ = (
        db.UniqueConstraint('flight_id', 'seat_number', name='unique_flight_seat'),
    )

    def __repr__(self):
        return f'<Seat {self.seat_number} ({self.seat_class}) - Occupied: {self.is_occupied}>'


class FlightDelay(db.Model):
    __tablename__ = 'flight_delays'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id', ondelete='CASCADE'), nullable=False)
    original_departure = db.Column(db.DateTime, nullable=False)
    revised_departure = db.Column(db.DateTime, nullable=False)
    delay_reason = db.Column(db.String(255), nullable=False)
    notified_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f'<FlightDelay flight_id={self.flight_id} revised={self.revised_departure}>'


class FlightCancellation(db.Model):
    __tablename__ = 'flight_cancellations'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id', ondelete='CASCADE'), nullable=False, unique=True)
    cancellation_reason = db.Column(db.String(255), nullable=False)
    cancelled_at = db.Column(db.DateTime, default=datetime.utcnow)
    affected_passengers_count = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f'<FlightCancellation flight_id={self.flight_id}>'
