from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from models import (
    db, User, Flight, Seat, Booking, Payment, Baggage, BaggageLog,
    Notification, CheckIn, Boarding
)
from routes.auth import staff_required

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/desk')
@staff_required
def desk():
    today_flights = Flight.query.filter(
        Flight.status.in_(['Scheduled', 'Boarding', 'Delayed'])
    ).order_by(Flight.departure_time.asc()).limit(10).all()

    total_checkins_today = CheckIn.query.count()
    total_boarded_today = Boarding.query.filter_by(status='Boarded').count()
    active_baggage_count = Baggage.query.filter(Baggage.status != 'Delivered').count()

    recent_checkins = CheckIn.query.order_by(CheckIn.checkin_time.desc()).limit(5).all()

    return render_template(
        'staff/desk.html',
        today_flights=today_flights,
        total_checkins_today=total_checkins_today,
        total_boarded_today=total_boarded_today,
        active_baggage_count=active_baggage_count,
        recent_checkins=recent_checkins
    )


@staff_bp.route('/checkin', methods=['GET', 'POST'])
@staff_required
def checkin():
    search_query = request.args.get('q', '').strip()
    booking = None

    if search_query:
        booking = Booking.query.filter(
            (Booking.booking_reference == search_query.upper()) |
            (Booking.passenger_name.ilike(f'%{search_query}%')) |
            (Booking.passenger_email.ilike(f'%{search_query}%'))
        ).first()

        if not booking:
            flash(f'No booking found matching: "{search_query}". Please verify the Booking Reference.', 'warning')

    if request.method == 'POST':
        booking_id = request.form.get('booking_id', type=int)
        booking = Booking.query.get_or_404(booking_id)

        # Validations
        if booking.status == 'Cancelled':
            flash('Cannot check in a cancelled booking.', 'danger')
            return redirect(url_for('staff.checkin', q=booking.booking_reference))

        if booking.status in ['Checked-In', 'Boarded']:
            flash(f'Passenger is already checked in (Status: {booking.status}).', 'info')
            return redirect(url_for('staff.checkin', q=booking.booking_reference))

        if booking.flight.status in ['Cancelled', 'Departed', 'Arrived']:
            flash(f'Cannot check in. Flight {booking.flight.flight_number} is {booking.flight.status}.', 'danger')
            return redirect(url_for('staff.checkin', q=booking.booking_reference))

        try:
            # 1. Update Booking status
            booking.status = 'Checked-In'

            # 2. Sequence number
            existing_checkins = CheckIn.query.join(Booking).filter(Booking.flight_id == booking.flight_id).count()
            seq_no = existing_checkins + 1

            # 3. Create CheckIn record
            checkin_rec = CheckIn(
                booking_id=booking.id,
                checkin_by=session.get('user_id'),
                gate=booking.flight.gate,
                sequence_no=seq_no
            )
            db.session.add(checkin_rec)
            db.session.flush()

            # 4. Update Baggage if exists
            for bg in booking.baggage_items:
                bg.status = 'Checked-In'
                log = BaggageLog(
                    baggage_id=bg.id,
                    status='Checked-In',
                    location=f"{booking.flight.source_code} Airport Desk",
                    notes='Checked in at airport counter by staff.',
                    updated_by=session.get('user_id')
                )
                db.session.add(log)

            # 5. Notify Passenger
            notif = Notification(
                user_id=booking.user_id,
                title='Check-In Successful! 🎫',
                message=f'You are checked in for Flight {booking.flight.flight_number}. Boarding Pass No: {checkin_rec.boarding_pass_no}, Seat: {booking.seat.seat_number}, Gate: {booking.flight.gate}. Please proceed to security.',
                notification_type='boarding',
                link_url=url_for('passenger.view_booking', booking_ref=booking.booking_reference)
            )
            db.session.add(notif)

            db.session.commit()
            flash(f'Passenger {booking.passenger_name} checked in successfully! Boarding Pass: {checkin_rec.boarding_pass_no}', 'success')
            return redirect(url_for('staff.checkin', q=booking.booking_reference))

        except Exception as e:
            db.session.rollback()
            flash(f'Check-in failed: {str(e)}', 'danger')

    return render_template('staff/checkin.html', booking=booking, search_query=search_query)


@staff_bp.route('/baggage', methods=['GET', 'POST'])
@staff_required
def baggage_desk():
    tag_query = request.args.get('tag', '').strip().upper()
    baggage = None

    if tag_query:
        baggage = Baggage.query.filter_by(baggage_tag=tag_query).first()
        if not baggage:
            flash(f'No baggage record found with Tag ID: {tag_query}', 'warning')

    if request.method == 'POST':
        baggage_id = request.form.get('baggage_id', type=int)
        new_status = request.form.get('status', '').strip()
        location = request.form.get('location', '').strip()
        notes = request.form.get('notes', '').strip()

        baggage = Baggage.query.get_or_404(baggage_id)
        valid_statuses = ['Checked-In', 'Security Checked', 'Loaded', 'In Transit', 'Arrived', 'Delivered']

        if new_status not in valid_statuses:
            flash('Invalid baggage status selected.', 'danger')
        else:
            old_status = baggage.status
            baggage.status = new_status
            baggage.last_updated = datetime.utcnow()

            # Create log entry
            log = BaggageLog(
                baggage_id=baggage.id,
                status=new_status,
                location=location or f"Terminal Operations ({new_status})",
                notes=notes,
                updated_by=session.get('user_id')
            )
            db.session.add(log)

            # Notify passenger of real-time baggage update
            notif = Notification(
                user_id=baggage.passenger_id,
                title=f'Baggage Status Updated: {new_status} 🧳',
                message=f'Your baggage tag {baggage.baggage_tag} is now: {new_status}. Location: {location or "Airport Area"}.',
                notification_type='baggage',
                link_url=url_for('passenger.track_baggage', tag=baggage.baggage_tag)
            )
            db.session.add(notif)

            db.session.commit()
            flash(f'Baggage {baggage.baggage_tag} status updated from "{old_status}" to "{new_status}". Passenger notified!', 'success')
            return redirect(url_for('staff.baggage_desk', tag=baggage.baggage_tag))

    recent_baggage = Baggage.query.order_by(Baggage.last_updated.desc()).limit(15).all()
    return render_template('staff/baggage_desk.html', baggage=baggage, tag_query=tag_query, recent_baggage=recent_baggage)


@staff_bp.route('/boarding', methods=['GET', 'POST'])
@staff_required
def boarding():
    flight_id = request.args.get('flight_id', type=int)
    active_flights = Flight.query.filter(
        Flight.status.in_(['Scheduled', 'Boarding', 'Delayed', 'Departed'])
    ).order_by(Flight.departure_time.asc()).all()

    selected_flight = None
    manifest = []
    total_passengers = 0
    checked_in_count = 0
    boarded_count = 0
    not_boarded_count = 0

    if flight_id:
        selected_flight = Flight.query.get(flight_id)
        if selected_flight:
            manifest = selected_flight.bookings.filter(Booking.status != 'Cancelled').order_by(Booking.passenger_name.asc()).all()
            total_passengers = len(manifest)
            checked_in_count = len([b for b in manifest if b.status in ['Checked-In', 'Boarded']])
            boarded_count = len([b for b in manifest if b.status == 'Boarded'])
            not_boarded_count = total_passengers - boarded_count

    # Action: Mark Boarded
    if request.method == 'POST':
        action = request.form.get('action')
        booking_id = request.form.get('booking_id', type=int)

        if action == 'board_single' and booking_id:
            booking = Booking.query.get_or_404(booking_id)
            
            # Validation: Passenger must be checked in before boarding
            if booking.status != 'Checked-In':
                flash(f'Cannot board passenger {booking.passenger_name} directly. Passenger must check in first.', 'danger')
                return redirect(url_for('staff.boarding', flight_id=booking.flight_id))

            booking.status = 'Boarded'
            boarding_rec = Boarding(
                booking_id=booking.id,
                boarded_by=session.get('user_id'),
                status='Boarded'
            )
            db.session.add(boarding_rec)

            notif = Notification(
                user_id=booking.user_id,
                title='Welcome Aboard! ✈️',
                message=f'You have successfully boarded Flight {booking.flight.flight_number}. Please locate Seat {booking.seat.seat_number}. Have a pleasant flight!',
                notification_type='boarding',
                link_url=url_for('passenger.view_booking', booking_ref=booking.booking_reference)
            )
            db.session.add(notif)
            db.session.commit()

            flash(f'Passenger {booking.passenger_name} marked as Boarded.', 'success')
            return redirect(url_for('staff.boarding', flight_id=booking.flight_id))

        elif action == 'start_boarding' and selected_flight:
            selected_flight.status = 'Boarding'
            # Notify all confirmed/checked in
            for b in selected_flight.bookings.filter(Booking.status.in_(['Confirmed', 'Checked-In'])):
                notif = Notification(
                    user_id=b.user_id,
                    title=f'Boarding Announcement: Flight {selected_flight.flight_number}',
                    message=f'Boarding has officially started at Gate {selected_flight.gate}. Please have your boarding pass and photo ID ready.',
                    notification_type='boarding',
                    link_url=url_for('passenger.view_booking', booking_ref=b.booking_reference)
                )
                db.session.add(notif)
            db.session.commit()
            flash(f'Flight {selected_flight.flight_number} status changed to "Boarding". Passengers notified.', 'info')
            return redirect(url_for('staff.boarding', flight_id=selected_flight.id))

    return render_template(
        'staff/boarding.html',
        active_flights=active_flights,
        selected_flight=selected_flight,
        manifest=manifest,
        total_passengers=total_passengers,
        checked_in_count=checked_in_count,
        boarded_count=boarded_count,
        not_boarded_count=not_boarded_count
    )
