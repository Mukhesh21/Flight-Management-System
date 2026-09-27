from datetime import datetime, timedelta
import csv
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, Response
from models import (
    db, User, Aircraft, Flight, Seat, Booking, Payment, Baggage, BaggageLog,
    Notification, FlightDelay, FlightCancellation, CheckIn, Boarding
)
from routes.auth import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # 1. Flight Status KPI Counts
    total_flights = Flight.query.count()
    scheduled_flights = Flight.query.filter_by(status='Scheduled').count()
    delayed_flights = Flight.query.filter_by(status='Delayed').count()
    cancelled_flights = Flight.query.filter_by(status='Cancelled').count()
    departed_flights = Flight.query.filter_by(status='Departed').count()
    arrived_flights = Flight.query.filter_by(status='Arrived').count()
    boarding_flights = Flight.query.filter_by(status='Boarding').count()

    # 2. Passenger & Booking KPI Counts
    total_passengers = User.query.filter_by(role='passenger').count()
    total_bookings = Booking.query.count()
    confirmed_bookings = Booking.query.filter_by(status='Confirmed').count()
    checked_in_passengers = Booking.query.filter_by(status='Checked-In').count()
    boarded_passengers = Booking.query.filter_by(status='Boarded').count()
    cancelled_bookings = Booking.query.filter_by(status='Cancelled').count()

    # 3. Available Seats across active flights
    total_seats_sum = db.session.query(db.func.sum(Flight.available_seats)).filter(
        Flight.status.in_(['Scheduled', 'Delayed'])
    ).scalar() or 0

    # 4. Baggage Logistics Counts
    baggage_total = Baggage.query.count()
    baggage_in_transit = Baggage.query.filter(Baggage.status.in_(['Loaded', 'In Transit'])).count()
    baggage_delivered = Baggage.query.filter_by(status='Delivered').count()

    # 5. Financial Overview
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.payment_status == 'Success').scalar() or 0.0

    # 6. Recent Flights
    recent_flights = Flight.query.order_by(Flight.departure_time.asc()).limit(8).all()
    
    # 7. Recent System Activity / Bookings
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(6).all()

    # 8. Chart Datasets (JSON serializable)
    flight_status_data = {
        'labels': ['Scheduled', 'Boarding', 'Departed', 'Delayed', 'Cancelled', 'Arrived'],
        'values': [scheduled_flights, boarding_flights, departed_flights, delayed_flights, cancelled_flights, arrived_flights]
    }

    baggage_status_data = {
        'labels': ['Checked-In', 'Security Checked', 'Loaded', 'In Transit', 'Arrived', 'Delivered'],
        'values': [
            Baggage.query.filter_by(status='Checked-In').count(),
            Baggage.query.filter_by(status='Security Checked').count(),
            Baggage.query.filter_by(status='Loaded').count(),
            Baggage.query.filter_by(status='In Transit').count(),
            Baggage.query.filter_by(status='Arrived').count(),
            Baggage.query.filter_by(status='Delivered').count(),
        ]
    }

    return render_template(
        'admin/dashboard.html',
        total_flights=total_flights,
        scheduled_flights=scheduled_flights,
        delayed_flights=delayed_flights,
        cancelled_flights=cancelled_flights,
        total_passengers=total_passengers,
        total_bookings=total_bookings,
        confirmed_bookings=confirmed_bookings,
        checked_in_passengers=checked_in_passengers,
        boarded_passengers=boarded_passengers,
        cancelled_bookings=cancelled_bookings,
        total_seats_sum=total_seats_sum,
        baggage_in_transit=baggage_in_transit,
        baggage_total=baggage_total,
        total_revenue=total_revenue,
        recent_flights=recent_flights,
        recent_bookings=recent_bookings,
        flight_status_data=flight_status_data,
        baggage_status_data=baggage_status_data
    )


@admin_bp.route('/flights')
@admin_required
def flights_list():
    status_filter = request.args.get('status', '')
    search_query = request.args.get('q', '').strip()

    query = Flight.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search_query:
        query = query.filter(
            (Flight.flight_number.ilike(f'%{search_query}%')) |
            (Flight.source.ilike(f'%{search_query}%')) |
            (Flight.destination.ilike(f'%{search_query}%')) |
            (Flight.source_code.ilike(f'%{search_query}%')) |
            (Flight.destination_code.ilike(f'%{search_query}%'))
        )

    flights = query.order_by(Flight.departure_time.desc()).all()
    return render_template('admin/flights_list.html', flights=flights, status_filter=status_filter, search_query=search_query)


@admin_bp.route('/flights/new', methods=['GET', 'POST'])
@admin_required
def new_flight():
    aircrafts = Aircraft.query.filter_by(status='Active').all()

    if request.method == 'POST':
        flight_number = request.form.get('flight_number', '').strip().upper()
        airline_name = request.form.get('airline_name', 'SkyWings Airlines').strip()
        source = request.form.get('source', '').strip()
        source_code = request.form.get('source_code', '').strip().upper()
        destination = request.form.get('destination', '').strip()
        destination_code = request.form.get('destination_code', '').strip().upper()
        
        dep_time_str = request.form.get('departure_time', '').strip()
        arr_time_str = request.form.get('arrival_time', '').strip()
        
        aircraft_id = request.form.get('aircraft_id', type=int)
        gate = request.form.get('gate', 'A1').strip()
        terminal = request.form.get('terminal', 'T3').strip()
        base_price = float(request.form.get('base_price', 4500.0))

        if not (flight_number and source and destination and dep_time_str and arr_time_str and aircraft_id):
            flash('Please fill in all required flight details.', 'danger')
            return render_template('admin/flight_form.html', aircrafts=aircrafts, is_new=True)

        try:
            dep_time = datetime.strptime(dep_time_str, '%Y-%m-%dT%H:%M')
            arr_time = datetime.strptime(arr_time_str, '%Y-%m-%dT%H:%M')

            if arr_time <= dep_time:
                flash('Arrival time must be after departure time.', 'danger')
                return render_template('admin/flight_form.html', aircrafts=aircrafts, is_new=True)

            # Calculate duration string
            diff = arr_time - dep_time
            hours, remainder = divmod(diff.seconds, 3600)
            minutes = remainder // 60
            duration_str = f"{hours}h {minutes}m"

            # Check duplicate flight number for exact same departure
            existing = Flight.query.filter_by(flight_number=flight_number, departure_time=dep_time).first()
            if existing:
                flash(f'Flight {flight_number} is already scheduled at this departure time.', 'danger')
                return render_template('admin/flight_form.html', aircrafts=aircrafts, is_new=True)

            flight = Flight(
                flight_number=flight_number,
                airline_name=airline_name,
                source=source,
                source_code=source_code,
                destination=destination,
                destination_code=destination_code,
                departure_time=dep_time,
                arrival_time=arr_time,
                duration=duration_str,
                aircraft_id=aircraft_id,
                gate=gate,
                terminal=terminal,
                status='Scheduled',
                base_price=base_price,
                available_seats=0
            )
            db.session.add(flight)
            db.session.flush()

            # Auto-generate seats based on aircraft configuration
            total_seats_generated = flight.generate_seats_for_flight()
            db.session.commit()

            flash(f'Flight {flight_number} created successfully with {total_seats_generated} seats generated!', 'success')
            return redirect(url_for('admin.flights_list'))

        except ValueError as e:
            flash(f'Invalid date/time format: {str(e)}', 'danger')

    return render_template('admin/flight_form.html', aircrafts=aircrafts, is_new=True)


@admin_bp.route('/flights/<int:flight_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    aircrafts = Aircraft.query.all()

    if request.method == 'POST':
        flight.flight_number = request.form.get('flight_number', flight.flight_number).strip().upper()
        flight.airline_name = request.form.get('airline_name', flight.airline_name).strip()
        flight.source = request.form.get('source', flight.source).strip()
        flight.source_code = request.form.get('source_code', flight.source_code).strip().upper()
        flight.destination = request.form.get('destination', flight.destination).strip()
        flight.destination_code = request.form.get('destination_code', flight.destination_code).strip().upper()
        
        old_gate = flight.gate
        new_gate = request.form.get('gate', flight.gate).strip()
        flight.gate = new_gate
        flight.terminal = request.form.get('terminal', flight.terminal).strip()
        flight.base_price = float(request.form.get('base_price', flight.base_price))

        dep_time_str = request.form.get('departure_time', '').strip()
        arr_time_str = request.form.get('arrival_time', '').strip()
        if dep_time_str and arr_time_str:
            flight.departure_time = datetime.strptime(dep_time_str, '%Y-%m-%dT%H:%M')
            flight.arrival_time = datetime.strptime(arr_time_str, '%Y-%m-%dT%H:%M')
            diff = flight.arrival_time - flight.departure_time
            hours, remainder = divmod(diff.seconds, 3600)
            minutes = remainder // 60
            flight.duration = f"{hours}h {minutes}m"

        # If gate changed, automatically notify all confirmed passengers!
        if old_gate != new_gate and new_gate:
            confirmed_bookings = flight.bookings.filter(Booking.status.in_(['Confirmed', 'Checked-In'])).all()
            for b in confirmed_bookings:
                gate_notif = Notification(
                    user_id=b.user_id,
                    title=f'Gate Change: Flight {flight.flight_number} 🚪',
                    message=f'Attention: The departure gate for Flight {flight.flight_number} ({flight.source_code} ➔ {flight.destination_code}) has been changed from Gate {old_gate} to Gate {new_gate}.',
                    notification_type='gate_change',
                    link_url=url_for('passenger.view_booking', booking_ref=b.booking_reference)
                )
                db.session.add(gate_notif)

        db.session.commit()
        flash(f'Flight {flight.flight_number} updated successfully.', 'success')
        return redirect(url_for('admin.flights_list'))

    return render_template('admin/flight_form.html', flight=flight, aircrafts=aircrafts, is_new=False)


@admin_bp.route('/flights/<int:flight_id>/status', methods=['POST'])
@admin_required
def update_flight_status(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    new_status = request.form.get('status', '').strip()

    valid_statuses = ['Scheduled', 'Boarding', 'Departed', 'Delayed', 'Cancelled', 'Arrived']
    if new_status not in valid_statuses:
        flash('Invalid flight status.', 'danger')
        return redirect(url_for('admin.flights_list'))

    old_status = flight.status
    flight.status = new_status

    # If status changes to Boarding, notify passengers!
    if new_status == 'Boarding' and old_status != 'Boarding':
        confirmed_bookings = flight.bookings.filter(Booking.status.in_(['Confirmed', 'Checked-In'])).all()
        for b in confirmed_bookings:
            boarding_notif = Notification(
                user_id=b.user_id,
                title=f'Boarding Started: Flight {flight.flight_number} ✈️',
                message=f'Boarding is now underway for Flight {flight.flight_number} at Gate {flight.gate}. Please proceed to the gate immediately with your boarding pass.',
                notification_type='boarding',
                link_url=url_for('passenger.view_booking', booking_ref=b.booking_reference)
            )
            db.session.add(boarding_notif)

    db.session.commit()
    flash(f'Flight {flight.flight_number} status updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('admin.flights_list'))


@admin_bp.route('/flights/<int:flight_id>/delay', methods=['GET', 'POST'])
@admin_required
def manage_delay(flight_id):
    flight = Flight.query.get_or_404(flight_id)

    if request.method == 'POST':
        revised_dep_str = request.form.get('revised_departure', '').strip()
        delay_reason = request.form.get('delay_reason', 'Operational / Weather constraints').strip()

        if not revised_dep_str or not delay_reason:
            flash('Please provide both the revised departure time and the reason for delay.', 'danger')
            return render_template('admin/delay_management.html', flight=flight)

        try:
            revised_dep = datetime.strptime(revised_dep_str, '%Y-%m-%dT%H:%M')
            original_dep = flight.departure_time

            # 1. Update Flight record
            flight.status = 'Delayed'
            flight.departure_time = revised_dep
            # Recalculate arrival if duration known
            diff = flight.arrival_time - original_dep
            flight.arrival_time = revised_dep + diff

            # 2. Record Flight Delay log
            delay_record = FlightDelay(
                flight_id=flight.id,
                original_departure=original_dep,
                revised_departure=revised_dep,
                delay_reason=delay_reason,
                created_by=session.get('user_id')
            )
            db.session.add(delay_record)

            # 3. Identify all confirmed / checked-in passengers and dispatch notifications
            affected_bookings = flight.bookings.filter(Booking.status.in_(['Confirmed', 'Checked-In'])).all()
            for b in affected_bookings:
                notif = Notification(
                    user_id=b.user_id,
                    title=f'Flight Delay Alert: {flight.flight_number} ⏰',
                    message=f'Flight {flight.flight_number} ({flight.source_code} ➔ {flight.destination_code}) has been delayed. Previous Departure: {original_dep.strftime("%I:%M %p")}, Revised Departure: {revised_dep.strftime("%I:%M %p")}. Reason: {delay_reason}. Gate: {flight.gate}.',
                    notification_type='delay',
                    link_url=url_for('passenger.view_booking', booking_ref=b.booking_reference)
                )
                db.session.add(notif)

            db.session.commit()

            flash(f'Flight {flight.flight_number} marked as Delayed. {len(affected_bookings)} affected passengers were automatically notified!', 'warning')
            return redirect(url_for('admin.flights_list'))

        except ValueError as e:
            flash(f'Invalid date format: {str(e)}', 'danger')

    return render_template('admin/delay_management.html', flight=flight)


@admin_bp.route('/flights/<int:flight_id>/cancel', methods=['GET', 'POST'])
@admin_required
def cancel_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)

    if flight.status == 'Cancelled':
        flash('This flight is already cancelled.', 'warning')
        return redirect(url_for('admin.flights_list'))

    if request.method == 'POST':
        cancellation_reason = request.form.get('cancellation_reason', 'Severe Weather / Air Traffic Control Directives').strip()

        if not cancellation_reason:
            flash('Please provide a reason for cancelling the flight.', 'danger')
            return render_template('admin/cancellations.html', flight=flight)

        try:
            # 1. Update Flight Status
            flight.status = 'Cancelled'

            # 2. Identify confirmed passengers
            affected_bookings = flight.bookings.filter(Booking.status.in_(['Confirmed', 'Checked-In'])).all()
            
            # 3. Create Flight Cancellation record
            cancellation_record = FlightCancellation(
                flight_id=flight.id,
                cancellation_reason=cancellation_reason,
                affected_passengers_count=len(affected_bookings),
                created_by=session.get('user_id')
            )
            db.session.add(cancellation_record)

            # 4. Notify affected passengers & mark booking refunds
            for b in affected_bookings:
                b.cancellation_reason = f'Flight Cancelled by Airline: {cancellation_reason}'
                if b.payment:
                    b.payment.payment_status = 'Refunded'

                notif = Notification(
                    user_id=b.user_id,
                    title=f'URGENT: Flight Cancelled ({flight.flight_number}) ❌',
                    message=f'We regret to inform you that Flight {flight.flight_number} from {flight.source} to {flight.destination} on {flight.departure_time.strftime("%b %d, %Y")} has been cancelled due to: {cancellation_reason}. A full refund is being processed to your original payment method.',
                    notification_type='cancellation',
                    link_url=url_for('passenger.view_booking', booking_ref=b.booking_reference)
                )
                db.session.add(notif)

            db.session.commit()
            flash(f'Flight {flight.flight_number} cancelled. {len(affected_bookings)} confirmed passengers have been notified of the cancellation and refund.', 'danger')
            return redirect(url_for('admin.flights_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Failed to cancel flight: {str(e)}', 'danger')

    return render_template('admin/cancellations.html', flight=flight)


@admin_bp.route('/aircraft', methods=['GET', 'POST'])
@admin_required
def aircraft_list():
    if request.method == 'POST':
        model = request.form.get('model', '').strip()
        reg_no = request.form.get('registration_no', '').strip().upper()
        economy = int(request.form.get('economy_seats', 150))
        business = int(request.form.get('business_seats', 24))
        first_class = int(request.form.get('first_class_seats', 6))
        total = economy + business + first_class

        if Aircraft.query.filter_by(registration_no=reg_no).first():
            flash(f'Aircraft with Registration No {reg_no} already exists.', 'danger')
        else:
            new_aircraft = Aircraft(
                model=model,
                registration_no=reg_no,
                total_seats=total,
                economy_seats=economy,
                business_seats=business,
                first_class_seats=first_class,
                status='Active'
            )
            db.session.add(new_aircraft)
            db.session.commit()
            flash(f'Aircraft {model} ({reg_no}) registered with capacity {total} seats.', 'success')

    aircrafts = Aircraft.query.all()
    return render_template('admin/aircraft_list.html', aircrafts=aircrafts)


@admin_bp.route('/bookings')
@admin_required
def bookings_list():
    search = request.args.get('q', '').strip()
    status = request.args.get('status', '')

    query = Booking.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            (Booking.booking_reference.ilike(f'%{search}%')) |
            (Booking.passenger_name.ilike(f'%{search}%')) |
            (Booking.passenger_email.ilike(f'%{search}%'))
        )

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return render_template('admin/bookings_list.html', bookings=bookings, search=search, status=status)


@admin_bp.route('/passengers')
@admin_required
def passengers_list():
    passengers = User.query.filter_by(role='passenger').order_by(User.created_at.desc()).all()
    return render_template('admin/passengers_list.html', passengers=passengers)


@admin_bp.route('/reports')
@admin_required
def reports():
    report_type = request.args.get('type', 'flights')
    download = request.args.get('download') == 'csv'

    if report_type == 'flights':
        data = Flight.query.order_by(Flight.departure_time.desc()).all()
        if download:
            si = io.StringIO()
            cw = csv.writer(si)
            cw.writerow(['Flight No', 'Airline', 'From', 'To', 'Departure', 'Arrival', 'Aircraft', 'Status', 'Available Seats', 'Base Price'])
            for f in data:
                cw.writerow([f.flight_number, f.airline_name, f.source_code, f.destination_code, f.departure_time, f.arrival_time, f.aircraft.model if f.aircraft else 'N/A', f.status, f.available_seats, f.base_price])
            return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=flights_report.csv"})

    elif report_type == 'passengers':
        data = Booking.query.order_by(Booking.booking_date.desc()).all()
        if download:
            si = io.StringIO()
            cw = csv.writer(si)
            cw.writerow(['Booking Ref', 'Passenger Name', 'Email', 'Phone', 'Flight No', 'Seat', 'Status', 'Fare', 'Date'])
            for b in data:
                cw.writerow([b.booking_reference, b.passenger_name, b.passenger_email, b.passenger_phone, b.flight.flight_number, b.seat.seat_number if b.seat else 'N/A', b.status, b.total_fare, b.booking_date])
            return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=passengers_report.csv"})

    elif report_type == 'baggage':
        data = Baggage.query.order_by(Baggage.last_updated.desc()).all()
        if download:
            si = io.StringIO()
            cw = csv.writer(si)
            cw.writerow(['Baggage Tag', 'Booking Ref', 'Passenger', 'Flight No', 'Weight (kg)', 'Type', 'Status', 'Last Updated'])
            for bg in data:
                cw.writerow([bg.baggage_tag, bg.booking.booking_reference if bg.booking else 'N/A', bg.passenger.full_name if bg.passenger else 'N/A', bg.booking.flight.flight_number if bg.booking and bg.booking.flight else 'N/A', bg.weight_kg, bg.baggage_type, bg.status, bg.last_updated])
            return Response(si.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=baggage_report.csv"})

    return render_template('admin/reports.html', report_type=report_type, data=data)
