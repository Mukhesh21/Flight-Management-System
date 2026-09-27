from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from models import (
    db, User, Flight, Seat, Booking, Payment, Baggage, BaggageLog,
    Notification, FlightDelay, FlightCancellation, CheckIn
)
from routes.auth import login_required

passenger_bp = Blueprint('passenger', __name__, url_prefix='/passenger')

@passenger_bp.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get_or_404(session['user_id'])
    
    # Active Bookings
    active_bookings = Booking.query.filter(
        Booking.user_id == user.id,
        Booking.status.in_(['Confirmed', 'Checked-In', 'Boarded'])
    ).order_by(Booking.booking_date.desc()).all()

    # Past / Cancelled Bookings
    past_bookings = Booking.query.filter(
        Booking.user_id == user.id,
        Booking.status.in_(['Cancelled', 'Completed'])
    ).order_by(Booking.booking_date.desc()).limit(5).all()

    # Active Baggage items
    baggage_items = Baggage.query.filter_by(passenger_id=user.id).order_by(Baggage.last_updated.desc()).limit(5).all()

    # Recent notifications
    notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(6).all()

    # Featured / popular flights for quick booking
    featured_flights = Flight.query.filter(
        Flight.status.in_(['Scheduled', 'Delayed']),
        Flight.departure_time >= datetime.utcnow()
    ).order_by(Flight.departure_time.asc()).limit(4).all()

    return render_template(
        'passenger/dashboard.html',
        user=user,
        active_bookings=active_bookings,
        past_bookings=past_bookings,
        baggage_items=baggage_items,
        notifications=notifications,
        featured_flights=featured_flights
    )


@passenger_bp.route('/search')
def search():
    source = request.args.get('source', '').strip()
    destination = request.args.get('destination', '').strip()
    travel_date_str = request.args.get('date', '').strip()
    passengers_count = int(request.args.get('passengers', 1))
    max_price = request.args.get('max_price', '')
    airline = request.args.get('airline', '')

    query = Flight.query.filter(Flight.status.in_(['Scheduled', 'Delayed']))

    if source:
        query = query.filter((Flight.source.ilike(f'%{source}%')) | (Flight.source_code.ilike(f'%{source}%')))
    if destination:
        query = query.filter((Flight.destination.ilike(f'%{destination}%')) | (Flight.destination_code.ilike(f'%{destination}%')))

    if travel_date_str:
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
            start_datetime = datetime.combine(travel_date, datetime.min.time())
            end_datetime = datetime.combine(travel_date, datetime.max.time())
            query = query.filter(Flight.departure_time.between(start_datetime, end_datetime))
        except ValueError:
            pass

    if max_price:
        try:
            query = query.filter(Flight.base_price <= float(max_price))
        except ValueError:
            pass

    if airline:
        query = query.filter(Flight.airline_name.ilike(f'%{airline}%'))

    flights = query.order_by(Flight.departure_time.asc()).all()

    # Get distinct sources and destinations for dropdown autocomplete
    all_sources = db.session.query(Flight.source, Flight.source_code).distinct().all()
    all_destinations = db.session.query(Flight.destination, Flight.destination_code).distinct().all()

    return render_template(
        'passenger/search_results.html',
        flights=flights,
        source=source,
        destination=destination,
        travel_date=travel_date_str,
        passengers_count=passengers_count,
        all_sources=all_sources,
        all_destinations=all_destinations
    )


@passenger_bp.route('/flight/<int:flight_id>/seat-select')
@login_required
def seat_select(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    
    if flight.status == 'Cancelled':
        flash('This flight has been cancelled and cannot accept new bookings.', 'danger')
        return redirect(url_for('passenger.search'))
        
    if flight.available_seats <= 0:
        flash('Sorry, this flight is fully booked.', 'warning')
        return redirect(url_for('passenger.search'))

    # Load all seats ordered by seat number
    seats = Seat.query.filter_by(flight_id=flight.id).all()
    
    # Organize seats by class and row for realistic aircraft fuselage rendering
    # First Class: rows 1-2, Business: rows 3-6, Economy: rows 7+
    organized_seats = {
        'First': [],
        'Business': [],
        'Economy': []
    }
    for s in seats:
        organized_seats[s.seat_class].append(s)

    return render_template(
        'passenger/seat_selection.html',
        flight=flight,
        seats=seats,
        organized_seats=organized_seats
    )


@passenger_bp.route('/booking/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    user = User.query.get_or_404(session['user_id'])
    flight_id = request.args.get('flight_id', type=int) or request.form.get('flight_id', type=int)
    seat_id = request.args.get('seat_id', type=int) or request.form.get('seat_id', type=int)

    if not flight_id or not seat_id:
        flash('Please select a flight and seat first.', 'warning')
        return redirect(url_for('passenger.search'))

    flight = Flight.query.get_or_404(flight_id)
    seat = Seat.query.get_or_404(seat_id)

    # Validation: Flight status
    if flight.status == 'Cancelled':
        flash('Cannot book a cancelled flight.', 'danger')
        return redirect(url_for('passenger.search'))

    # Validation: Seat already booked
    if seat.is_occupied:
        flash(f'Seat {seat.seat_number} is already occupied. Please choose another seat.', 'danger')
        return redirect(url_for('passenger.seat_select', flight_id=flight.id))

    # Calculate pricing
    base_fare = flight.base_price
    seat_extra = seat.extra_price
    taxes = round(base_fare * 0.12, 2) # 12% airport taxes & GST
    
    if request.method == 'POST':
        # Form inputs
        passenger_name = request.form.get('passenger_name', '').strip()
        passenger_email = request.form.get('passenger_email', '').strip()
        passenger_phone = request.form.get('passenger_phone', '').strip()
        passenger_age = request.form.get('passenger_age', type=int)
        passenger_gender = request.form.get('passenger_gender', 'Male')
        passport_number = request.form.get('passport_number', '').strip()
        
        baggage_option = request.form.get('baggage_option', '15kg_standard') # '15kg_standard', '20kg_extra', '25kg_heavy'
        baggage_weight = 15.0
        baggage_fee = 0.0
        if baggage_option == '20kg_extra':
            baggage_weight = 20.0
            baggage_fee = 800.0
        elif baggage_option == '25kg_heavy':
            baggage_weight = 25.0
            baggage_fee = 1500.0

        total_fare = base_fare + seat_extra + taxes + baggage_fee
        payment_method = request.form.get('payment_method', 'Credit Card')

        # Re-check seat concurrency right before writing
        seat = Seat.query.filter_by(id=seat_id, is_occupied=False).with_for_update().first() if db.engine.name != 'sqlite' else Seat.query.get(seat_id)
        if seat.is_occupied:
            flash(f'Seat {seat.seat_number} was just booked by another user. Please select another seat.', 'danger')
            return redirect(url_for('passenger.seat_select', flight_id=flight.id))

        if flight.available_seats <= 0:
            flash('This flight is now sold out.', 'danger')
            return redirect(url_for('passenger.search'))

        try:
            # 1. Mark seat occupied
            seat.is_occupied = True

            # 2. Create Booking
            booking = Booking(
                user_id=user.id,
                flight_id=flight.id,
                seat_id=seat.id,
                passenger_name=passenger_name or user.full_name,
                passenger_email=passenger_email or user.email,
                passenger_phone=passenger_phone or user.phone or 'N/A',
                passenger_age=passenger_age,
                passenger_gender=passenger_gender,
                passport_number=passport_number,
                total_fare=total_fare,
                status='Confirmed'
            )
            db.session.add(booking)
            db.session.flush()

            # 3. Create Payment record
            payment = Payment(
                booking_id=booking.id,
                amount=total_fare,
                payment_method=payment_method,
                payment_status='Success'
            )
            db.session.add(payment)

            # 4. Create Baggage item & initial log
            baggage = Baggage(
                booking_id=booking.id,
                passenger_id=user.id,
                weight_kg=baggage_weight,
                baggage_type='Check-In',
                status='Checked-In'
            )
            db.session.add(baggage)
            db.session.flush()

            baggage_log = BaggageLog(
                baggage_id=baggage.id,
                status='Checked-In',
                location=f"{flight.source} Airport ({flight.source_code})",
                notes='Baggage registered at initial ticket booking.'
            )
            db.session.add(baggage_log)

            # 5. Decrement flight available seats
            flight.recalculate_available_seats()

            # 6. Create in-app Notification for Passenger
            confirmation_notif = Notification(
                user_id=user.id,
                title='Booking Confirmed! ✈️',
                message=f'Your flight {flight.flight_number} ({flight.source_code} ➔ {flight.destination_code}) on {flight.departure_time.strftime("%b %d, %Y at %I:%M %p")} is confirmed! Booking Ref: {booking.booking_reference}, Seat: {seat.seat_number}, Gate: {flight.gate}.',
                notification_type='booking',
                link_url=url_for('passenger.view_booking', booking_ref=booking.booking_reference)
            )
            db.session.add(confirmation_notif)

            db.session.commit()

            flash(f'Booking successful! Your reference is {booking.booking_reference}.', 'success')
            return redirect(url_for('passenger.view_booking', booking_ref=booking.booking_reference))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while processing your booking: {str(e)}', 'danger')
            return redirect(url_for('passenger.seat_select', flight_id=flight.id))

    return render_template(
        'passenger/booking_review.html',
        user=user,
        flight=flight,
        seat=seat,
        base_fare=base_fare,
        seat_extra=seat_extra,
        taxes=taxes,
        total_fare=base_fare + seat_extra + taxes
    )


@passenger_bp.route('/booking/<string:booking_ref>')
@login_required
def view_booking(booking_ref):
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    
    # Security: Ensure only the passenger owner or staff/admin can view
    if booking.user_id != session['user_id'] and session.get('user_role') not in ['admin', 'staff']:
        flash('You are not authorized to view this booking.', 'danger')
        return redirect(url_for('passenger.dashboard'))

    return render_template(
        'passenger/booking_confirmation.html',
        booking=booking,
        flight=booking.flight,
        seat=booking.seat,
        payment=booking.payment,
        baggage_items=booking.baggage_items.all(),
        checkin=booking.checkin_record
    )


@passenger_bp.route('/my-bookings')
@login_required
def my_bookings():
    user = User.query.get_or_404(session['user_id'])
    status_filter = request.args.get('status', 'all')

    query = Booking.query.filter_by(user_id=user.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    bookings = query.order_by(Booking.booking_date.desc()).all()

    return render_template(
        'passenger/my_bookings.html',
        bookings=bookings,
        status_filter=status_filter
    )


@passenger_bp.route('/booking/<string:booking_ref>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_ref):
    booking = Booking.query.filter_by(booking_reference=booking_ref).first_or_404()
    
    if booking.user_id != session['user_id'] and session.get('user_role') != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('passenger.my_bookings'))

    if booking.status == 'Cancelled':
        flash('This booking is already cancelled.', 'warning')
        return redirect(url_for('passenger.view_booking', booking_ref=booking_ref))

    if booking.status in ['Boarded', 'Departed']:
        flash('Cannot cancel a booking for a flight that has already boarded or departed.', 'danger')
        return redirect(url_for('passenger.view_booking', booking_ref=booking_ref))

    cancel_reason = request.form.get('cancel_reason', 'Cancelled by passenger')

    try:
        # 1. Update Booking status (do NOT permanently delete historical record)
        booking.status = 'Cancelled'
        booking.cancellation_date = datetime.utcnow()
        booking.cancellation_reason = cancel_reason

        # 2. Release seat back to inventory
        if booking.seat:
            booking.seat.is_occupied = False

        # 3. Update flight availability
        booking.flight.recalculate_available_seats()

        # 4. Refund payment status
        if booking.payment:
            booking.payment.payment_status = 'Refunded'

        # 5. Create cancellation notification
        notif = Notification(
            user_id=booking.user_id,
            title='Booking Cancelled',
            message=f'Your booking {booking.booking_reference} for flight {booking.flight.flight_number} has been cancelled. Seat {booking.seat.seat_number} has been released. Refund status: Processed.',
            notification_type='cancellation',
            link_url=url_for('passenger.view_booking', booking_ref=booking.booking_reference)
        )
        db.session.add(notif)

        db.session.commit()
        flash('Your booking has been cancelled and your seat released.', 'info')

    except Exception as e:
        db.session.rollback()
        flash(f'Failed to cancel booking: {str(e)}', 'danger')

    return redirect(url_for('passenger.view_booking', booking_ref=booking_ref))


@passenger_bp.route('/baggage/track')
@login_required
def track_baggage():
    user = User.query.get_or_404(session['user_id'])
    baggage_tag = request.args.get('tag', '').strip()

    searched_baggage = None
    if baggage_tag:
        searched_baggage = Baggage.query.filter_by(baggage_tag=baggage_tag).first()
        if not searched_baggage:
            flash(f'No baggage record found with Tag ID: {baggage_tag}', 'warning')

    # All passenger's baggage items
    user_baggage_list = Baggage.query.filter_by(passenger_id=user.id).order_by(Baggage.last_updated.desc()).all()

    return render_template(
        'passenger/baggage_track.html',
        searched_baggage=searched_baggage,
        user_baggage_list=user_baggage_list,
        baggage_tag=baggage_tag
    )


@passenger_bp.route('/notifications')
@login_required
def notifications():
    user = User.query.get_or_404(session['user_id'])
    filter_type = request.args.get('filter', 'all')

    query = Notification.query.filter_by(user_id=user.id)
    if filter_type == 'unread':
        query = query.filter_by(is_read=False)

    notifications_list = query.order_by(Notification.created_at.desc()).all()

    return render_template(
        'passenger/notifications.html',
        notifications=notifications_list,
        filter_type=filter_type
    )


@passenger_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=session['user_id']).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True})


@passenger_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('passenger.notifications'))
