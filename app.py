import os
from datetime import datetime
from flask import Flask, render_template, session, g
from config import Config
from models import db, User, Notification, Flight
from routes import auth_bp, passenger_bp, admin_bp, staff_bp, flights_bp, api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(passenger_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(flights_bp)
    app.register_blueprint(api_bp)

    # Context processors for all Jinja templates
    @app.context_processor
    def inject_global_data():
        current_user = None
        unread_count = 0
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
            if current_user:
                unread_count = current_user.unread_notifications_count()

        return {
            'current_user': current_user,
            'unread_notifications_count': unread_count,
            'now': datetime.utcnow(),
            'app_name': 'SkyWings FMS'
        }

    # Template filters
    @app.template_filter('format_datetime')
    def format_datetime_filter(value, format='%b %d, %Y %I:%M %p'):
        if value is None:
            return ""
        return value.strftime(format)

    @app.template_filter('format_currency')
    def format_currency_filter(value):
        if value is None:
            return "₹0"
        return f"₹{value:,.2f}"

    # Main Home Page Route
    @app.route('/')
    def index():
        # Fetch featured live flights
        featured_flights = Flight.query.filter(
            Flight.status.in_(['Scheduled', 'Boarding', 'Delayed'])
        ).order_by(Flight.departure_time.asc()).limit(6).all()

        popular_routes = [
            {'from': 'Delhi (DEL)', 'to': 'Mumbai (BOM)', 'price': '₹4,500', 'duration': '2h 10m', 'image': 'del_bom'},
            {'from': 'Chennai (MAA)', 'to': 'Delhi (DEL)', 'price': '₹5,200', 'duration': '2h 50m', 'image': 'maa_del'},
            {'from': 'Bengaluru (BLR)', 'to': 'Kolkata (CCU)', 'price': '₹4,800', 'duration': '2h 30m', 'image': 'blr_ccu'},
            {'from': 'Mumbai (BOM)', 'to': 'Dubai (DXB)', 'price': '₹14,900', 'duration': '3h 30m', 'image': 'bom_dxb'},
            {'from': 'Delhi (DEL)', 'to': 'London (LHR)', 'price': '₹38,500', 'duration': '9h 15m', 'image': 'del_lhr'},
            {'from': 'Singapore (SIN)', 'to': 'Chennai (MAA)', 'price': '₹12,400', 'duration': '4h 00m', 'image': 'sin_maa'}
        ]

        return render_template('index.html', featured_flights=featured_flights, popular_routes=popular_routes)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Create tables automatically
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
