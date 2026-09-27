"""
Seed database with realistic initial data for demonstration:
- 3 User Roles (Admin, Staff, Passengers)
- Aircraft Fleet (Airbus A320, Boeing 737, Boeing 787)
- Scheduled, Boarding, Delayed, and Arrived Flights
- Complete Seat Inventory for each flight
- Pre-existing Bookings, Payments, Check-ins, Baggage tracking tags, and Notifications
"""

from datetime import datetime, timedelta
from app import create_app
from models import (
    db, User, PassengerProfile, StaffProfile, Aircraft, Flight, Seat,
    Booking, Payment, CheckIn, Boarding, Baggage, BaggageLog, Notification, FlightDelay
)

def seed_database():
    app = create_app()
    with app.app_context():
        # Drop and recreate for fresh clean seed
        db.drop_all()
        db.create_all()

        print("Creating User Accounts...")
        # 1. Admin User
        admin_user = User(
            username='admin',
            email='admin@skywings.com',
            full_name='Capt. Rajesh Sharma',
            phone='+91 98765 43210',
            role='admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)

        # 2. Airport Staff User
        staff_user = User(
            username='staff',
            email='staff@skywings.com',
            full_name='Priya Nair',
            phone='+91 98765 12345',
            role='staff'
        )
        staff_user.set_password('staff123')
        db.session.add(staff_user)
        db.session.flush()

        staff_profile = StaffProfile(
            user_id=staff_user.id,
            employee_id='EMP-SKY-0104',
            department='Ground Operations & Check-In Desk',
            airport_code='DEL',
            designation='Senior Terminal Duty Officer'
        )
        db.session.add(staff_profile)

        # 3. Passenger 1 (Mukhesh P)
        mukhesh = User(
            username='mukhesh',
            email='mukhesh@example.com',
            full_name='Mukhesh P',
            phone='+91 91234 56789',
            role='passenger'
        )
        mukhesh.set_password('pass123')
        db.session.add(mukhesh)
        db.session.flush()

        mukhesh_profile = PassengerProfile(
            user_id=mukhesh.id,
            passport_number='Z9823412',
            nationality='Indian',
            date_of_birth=datetime(1998, 5, 14).date(),
            frequent_flyer_no='FF-SKY-88992',
            emergency_contact='+91 98765 00000',
            address='Anna Nagar, Chennai, Tamil Nadu'
        )
        db.session.add(mukhesh_profile)

        # 4. Passenger 2 (Sneha Rao)
        sneha = User(
            username='sneha',
            email='sneha.rao@example.com',
            full_name='Sneha Rao',
            phone='+91 94455 66778',
            role='passenger'
        )
        sneha.set_password('pass123')
        db.session.add(sneha)
        db.session.flush()

        sneha_profile = PassengerProfile(
            user_id=sneha.id,
            passport_number='K7123901',
            nationality='Indian',
            frequent_flyer_no='FF-SKY-45211'
        )
        db.session.add(sneha_profile)

        # 5. Passenger 3 (Aarav Mehta)
        aarav = User(
            username='aarav',
            email='aarav.mehta@example.com',
            full_name='Aarav Mehta',
            phone='+91 98877 11223',
            role='passenger'
        )
        aarav.set_password('pass123')
        db.session.add(aarav)

        print("Creating Aircraft Fleet...")
        a320 = Aircraft(
            model='Airbus A320neo',
            registration_no='VT-SKY201',
            total_seats=180,
            economy_seats=150,
            business_seats=24,
            first_class_seats=6,
            status='Active'
        )
        b737 = Aircraft(
            model='Boeing 737-800',
            registration_no='VT-SKY305',
            total_seats=160,
            economy_seats=136,
            business_seats=20,
            first_class_seats=4,
            status='Active'
        )
        b787 = Aircraft(
            model='Boeing 787-9 Dreamliner',
            registration_no='VT-SKY789',
            total_seats=290,
            economy_seats=240,
            business_seats=42,
            first_class_seats=8,
            status='Active'
        )
        a350 = Aircraft(
            model='Airbus A350-900',
            registration_no='VT-SKY900',
            total_seats=310,
            economy_seats=260,
            business_seats=40,
            first_class_seats=10,
            status='Active'
        )
        db.session.add_all([a320, b737, b787, a350])
        db.session.flush()

        print("Scheduling Flights & Generating Complete Seat Maps...")
        base_now = datetime.utcnow()

        # Flight 1: AI-202 Chennai -> Delhi (Featured in problem statement)
        f1_dep = base_now + timedelta(hours=5)
        f1_arr = f1_dep + timedelta(hours=2, minutes=50)
        f1 = Flight(
            flight_number='AI-202',
            airline_name='SkyWings Airlines',
            source='Chennai',
            source_code='MAA',
            destination='Delhi',
            destination_code='DEL',
            departure_time=f1_dep,
            arrival_time=f1_arr,
            duration='2h 50m',
            aircraft_id=a320.id,
            gate='A12',
            terminal='T1',
            status='Scheduled',
            base_price=5200.0,
            available_seats=0
        )
        db.session.add(f1)
        db.session.flush()
        f1.generate_seats_for_flight()

        # Flight 2: SW-405 Delhi -> Mumbai (Boarding soon)
        f2_dep = base_now + timedelta(hours=1, minutes=15)
        f2_arr = f2_dep + timedelta(hours=2, minutes=10)
        f2 = Flight(
            flight_number='SW-405',
            airline_name='SkyWings Airlines',
            source='Delhi',
            source_code='DEL',
            destination='Mumbai',
            destination_code='BOM',
            departure_time=f2_dep,
            arrival_time=f2_arr,
            duration='2h 10m',
            aircraft_id=b737.id,
            gate='B4',
            terminal='T3',
            status='Boarding',
            base_price=4500.0,
            available_seats=0
        )
        db.session.add(f2)
        db.session.flush()
        f2.generate_seats_for_flight()

        # Flight 3: SW-301 Bengaluru -> Kolkata (Delayed demo)
        f3_dep_orig = base_now + timedelta(hours=3)
        f3_dep_revised = base_now + timedelta(hours=5, minutes=30)
        f3_arr = f3_dep_revised + timedelta(hours=2, minutes=30)
        f3 = Flight(
            flight_number='SW-301',
            airline_name='SkyWings Express',
            source='Bengaluru',
            source_code='BLR',
            destination='Kolkata',
            destination_code='CCU',
            departure_time=f3_dep_revised,
            arrival_time=f3_arr,
            duration='2h 30m',
            aircraft_id=a320.id,
            gate='D7',
            terminal='T2',
            status='Delayed',
            base_price=4800.0,
            available_seats=0
        )
        db.session.add(f3)
        db.session.flush()
        f3.generate_seats_for_flight()

        # Log delay record for Flight 3
        delay_log = FlightDelay(
            flight_id=f3.id,
            original_departure=f3_dep_orig,
            revised_departure=f3_dep_revised,
            delay_reason='Heavy rain and low visibility at Kolkata NSCBI Airport',
            created_by=admin_user.id
        )
        db.session.add(delay_log)

        # Flight 4: SW-780 Mumbai -> Dubai (International Dreamliner)
        f4_dep = base_now + timedelta(days=1, hours=4)
        f4_arr = f4_dep + timedelta(hours=3, minutes=30)
        f4 = Flight(
            flight_number='SW-780',
            airline_name='SkyWings International',
            source='Mumbai',
            source_code='BOM',
            destination='Dubai',
            destination_code='DXB',
            departure_time=f4_dep,
            arrival_time=f4_arr,
            duration='3h 30m',
            aircraft_id=b787.id,
            gate='C22',
            terminal='T2 International',
            status='Scheduled',
            base_price=14900.0,
            available_seats=0
        )
        db.session.add(f4)
        db.session.flush()
        f4.generate_seats_for_flight()

        # Flight 5: SW-910 Delhi -> London Heathrow (Long Haul)
        f5_dep = base_now + timedelta(days=1, hours=8)
        f5_arr = f5_dep + timedelta(hours=9, minutes=15)
        f5 = Flight(
            flight_number='SW-910',
            airline_name='SkyWings International',
            source='Delhi',
            source_code='DEL',
            destination='London',
            destination_code='LHR',
            departure_time=f5_dep,
            arrival_time=f5_arr,
            duration='9h 15m',
            aircraft_id=a350.id,
            gate='G15',
            terminal='T3 International',
            status='Scheduled',
            base_price=38500.0,
            available_seats=0
        )
        db.session.add(f5)
        db.session.flush()
        f5.generate_seats_for_flight()

        # Flight 6: SW-112 Hyderabad -> Goa (Arrived earlier)
        f6_dep = base_now - timedelta(hours=4)
        f6_arr = base_now - timedelta(hours=2, minutes=45)
        f6 = Flight(
            flight_number='SW-112',
            airline_name='SkyWings Express',
            source='Hyderabad',
            source_code='HYD',
            destination='Goa',
            destination_code='GOI',
            departure_time=f6_dep,
            arrival_time=f6_arr,
            duration='1h 15m',
            aircraft_id=b737.id,
            gate='E2',
            terminal='T1',
            status='Arrived',
            base_price=3600.0,
            available_seats=0
        )
        db.session.add(f6)
        db.session.flush()
        f6.generate_seats_for_flight()

        print("Creating Sample Bookings, Payments, Check-ins, and Baggage...")

        # 1. Booking for Mukhesh P on AI-202 (Seat 12A)
        seat_12a = Seat.query.filter_by(flight_id=f1.id, seat_number='12A').first()
        if seat_12a:
            seat_12a.is_occupied = True
            b1 = Booking(
                booking_reference='BK10234',
                user_id=mukhesh.id,
                flight_id=f1.id,
                seat_id=seat_12a.id,
                passenger_name='Mukhesh P',
                passenger_email=mukhesh.email,
                passenger_phone=mukhesh.phone,
                passenger_age=26,
                passenger_gender='Male',
                passport_number='Z9823412',
                total_fare=5824.0,
                status='Confirmed'
            )
            db.session.add(b1)
            db.session.flush()

            p1 = Payment(
                booking_id=b1.id,
                payment_reference='PAY-99201A',
                amount=5824.0,
                payment_method='Credit Card',
                payment_status='Success'
            )
            db.session.add(p1)

            # Baggage for b1
            bg1 = Baggage(
                baggage_tag='BG-8921',
                booking_id=b1.id,
                passenger_id=mukhesh.id,
                weight_kg=15.0,
                baggage_type='Check-In',
                status='Checked-In'
            )
            db.session.add(bg1)
            db.session.flush()

            db.session.add(BaggageLog(
                baggage_id=bg1.id,
                status='Checked-In',
                location='Chennai International Airport (MAA) Counter 4',
                notes='Luggage tagged and accepted for flight AI-202',
                updated_by=staff_user.id
            ))

            db.session.add(Notification(
                user_id=mukhesh.id,
                title='Booking Confirmed! ✈️',
                message='Your flight AI-202 (Chennai ➔ Delhi) is confirmed for today. Seat 12A. Gate A12. Have a wonderful trip!',
                notification_type='booking',
                link_url='/passenger/booking/BK10234',
                is_read=True
            ))

        # 2. Booking for Mukhesh P on SW-405 (Boarding Flight, Checked-In)
        seat_3b = Seat.query.filter_by(flight_id=f2.id, seat_number='3B').first()
        if seat_3b:
            seat_3b.is_occupied = True
            b2 = Booking(
                booking_reference='BK88210',
                user_id=mukhesh.id,
                flight_id=f2.id,
                seat_id=seat_3b.id,
                passenger_name='Mukhesh P',
                passenger_email=mukhesh.email,
                passenger_phone=mukhesh.phone,
                passenger_age=26,
                passenger_gender='Male',
                total_fare=7875.0,
                status='Checked-In'
            )
            db.session.add(b2)
            db.session.flush()

            p2 = Payment(
                booking_id=b2.id,
                payment_reference='PAY-44120B',
                amount=7875.0,
                payment_method='UPI',
                payment_status='Success'
            )
            db.session.add(p2)

            checkin_rec = CheckIn(
                booking_id=b2.id,
                checkin_by=staff_user.id,
                boarding_pass_no='BP-SW405-001',
                gate=f2.gate,
                sequence_no=1
            )
            db.session.add(checkin_rec)

            bg2 = Baggage(
                baggage_tag='BG-4482',
                booking_id=b2.id,
                passenger_id=mukhesh.id,
                weight_kg=18.5,
                baggage_type='Check-In',
                status='In Transit'
            )
            db.session.add(bg2)
            db.session.flush()

            # Baggage progression logs
            db.session.add_all([
                BaggageLog(baggage_id=bg2.id, status='Checked-In', location='Delhi T3 Counter 12', timestamp=base_now - timedelta(minutes=90), updated_by=staff_user.id),
                BaggageLog(baggage_id=bg2.id, status='Security Checked', location='X-Ray Security Scanner B', timestamp=base_now - timedelta(minutes=60), updated_by=staff_user.id),
                BaggageLog(baggage_id=bg2.id, status='Loaded', location='Tarmac Loading Bay Gate B4', timestamp=base_now - timedelta(minutes=30), updated_by=staff_user.id),
                BaggageLog(baggage_id=bg2.id, status='In Transit', location='Cargo Hold 2 - Aircraft VT-SKY305', timestamp=base_now - timedelta(minutes=10), updated_by=staff_user.id),
            ])

            db.session.add(Notification(
                user_id=mukhesh.id,
                title='Boarding is Now Open! 📢',
                message='Flight SW-405 to Mumbai is now boarding at Gate B4. Please proceed to the gate.',
                notification_type='boarding',
                link_url='/passenger/booking/BK88210',
                is_read=False
            ))

        # 3. Booking for Sneha Rao on SW-301 (Delayed flight)
        seat_7c = Seat.query.filter_by(flight_id=f3.id, seat_number='7C').first()
        if seat_7c:
            seat_7c.is_occupied = True
            b3 = Booking(
                booking_reference='BK77109',
                user_id=sneha.id,
                flight_id=f3.id,
                seat_id=seat_7c.id,
                passenger_name='Sneha Rao',
                passenger_email=sneha.email,
                passenger_phone=sneha.phone,
                passenger_age=28,
                passenger_gender='Female',
                total_fare=5376.0,
                status='Confirmed'
            )
            db.session.add(b3)
            db.session.flush()

            p3 = Payment(
                booking_id=b3.id,
                payment_reference='PAY-77109C',
                amount=5376.0,
                payment_method='Net Banking',
                payment_status='Success'
            )
            db.session.add(p3)

            bg3 = Baggage(
                baggage_tag='BG-9901',
                booking_id=b3.id,
                passenger_id=sneha.id,
                weight_kg=14.0,
                baggage_type='Check-In',
                status='Security Checked'
            )
            db.session.add(bg3)

            # Delay notification for Sneha
            db.session.add(Notification(
                user_id=sneha.id,
                title='Flight SW-301 Delayed ⏰',
                message=f'Flight SW-301 to Kolkata has been rescheduled to {f3_dep_revised.strftime("%I:%M %p")} due to heavy rainfall at destination. Gate D7.',
                notification_type='delay',
                link_url='/passenger/booking/BK77109',
                is_read=False
            ))

        # 4. Booking for Aarav Mehta on SW-405 (Boarded)
        seat_8d = Seat.query.filter_by(flight_id=f2.id, seat_number='8D').first()
        if seat_8d:
            seat_8d.is_occupied = True
            b4 = Booking(
                booking_reference='BK99450',
                user_id=aarav.id,
                flight_id=f2.id,
                seat_id=seat_8d.id,
                passenger_name='Aarav Mehta',
                passenger_email=aarav.email,
                passenger_phone=aarav.phone,
                passenger_age=31,
                passenger_gender='Male',
                total_fare=5040.0,
                status='Boarded'
            )
            db.session.add(b4)
            db.session.flush()

            db.session.add(Payment(
                booking_id=b4.id,
                payment_reference='PAY-99450D',
                amount=5040.0,
                payment_method='Credit Card',
                payment_status='Success'
            ))

            db.session.add(CheckIn(
                booking_id=b4.id,
                checkin_by=staff_user.id,
                boarding_pass_no='BP-SW405-002',
                gate=f2.gate,
                sequence_no=2
            ))

            db.session.add(Boarding(
                booking_id=b4.id,
                boarded_by=staff_user.id,
                status='Boarded'
            ))

        # Recalculate available seats for all flights
        for flight in [f1, f2, f3, f4, f5, f6]:
            flight.recalculate_available_seats()

        db.session.commit()
        print("\n==================================================================")
        print("Database Seeded Successfully!")
        print("------------------------------------------------------------------")
        print("Demo Credentials for Testing:")
        print("1. Admin / Flight Dispatch:")
        print("   Username: admin    | Password: admin123")
        print("2. Airport Ground Staff (Check-in / Baggage / Boarding):")
        print("   Username: staff    | Password: staff123")
        print("3. Passenger (Sample Bookings & Baggage):")
        print("   Username: mukhesh  | Password: pass123")
        print("   Username: sneha    | Password: pass123")
        print("==================================================================\n")

if __name__ == '__main__':
    seed_database()
