from datetime import datetime
from flask import Blueprint, render_template, request
from models import Flight

flights_bp = Blueprint('flights', __name__, url_prefix='/flights')

@flights_bp.route('/schedule')
def schedule():
    """Live Airport Flight Information Display System (FIDS)"""
    departures = Flight.query.filter(
        Flight.status.in_(['Scheduled', 'Boarding', 'Delayed', 'Departed'])
    ).order_by(Flight.departure_time.asc()).limit(20).all()

    arrivals = Flight.query.filter(
        Flight.status.in_(['Scheduled', 'Departed', 'Delayed', 'Arrived'])
    ).order_by(Flight.arrival_time.asc()).limit(20).all()

    return render_template(
        'flights/schedule.html',
        departures=departures,
        arrivals=arrivals,
        now=datetime.utcnow()
    )
