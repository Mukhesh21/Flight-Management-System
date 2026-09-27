from flask import Blueprint, jsonify, session, request
from models import db, Flight, Seat, Notification, Booking

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/flights/<int:flight_id>/seats')
def get_flight_seats(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    seats = Seat.query.filter_by(flight_id=flight.id).order_by(Seat.id.asc()).all()

    seats_data = []
    for s in seats:
        seats_data.append({
            'id': s.id,
            'seat_number': s.seat_number,
            'seat_class': s.seat_class,
            'is_occupied': s.is_occupied,
            'is_window': s.is_window,
            'is_aisle': s.is_aisle,
            'extra_price': s.extra_price
        })

    return jsonify({
        'flight_id': flight.id,
        'flight_number': flight.flight_number,
        'status': flight.status,
        'base_price': flight.base_price,
        'available_seats': flight.available_seats,
        'seats': seats_data
    })


@api_bp.route('/notifications/unread-count')
def unread_notifications_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
    return jsonify({'count': count})


@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
def mark_read(notif_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    notif = Notification.query.filter_by(id=notif_id, user_id=session['user_id']).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404


@api_bp.route('/flight-status')
def flight_status_lookup():
    flight_no = request.args.get('flight_no', '').strip().upper()
    if not flight_no:
        return jsonify({'error': 'Flight number required'}), 400
        
    flight = Flight.query.filter_by(flight_number=flight_no).order_by(Flight.departure_time.desc()).first()
    if not flight:
        return jsonify({'error': 'Flight not found'}), 404

    return jsonify({
        'flight_number': flight.flight_number,
        'airline': flight.airline_name,
        'source': f"{flight.source} ({flight.source_code})",
        'destination': f"{flight.destination} ({flight.destination_code})",
        'departure': flight.departure_time.strftime('%b %d, %Y %I:%M %p'),
        'arrival': flight.arrival_time.strftime('%b %d, %Y %I:%M %p'),
        'status': flight.status,
        'gate': flight.gate,
        'terminal': flight.terminal,
        'badge_class': flight.status_badge_class
    })
