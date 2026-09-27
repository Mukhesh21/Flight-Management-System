from routes.auth import auth_bp
from routes.passenger import passenger_bp
from routes.admin import admin_bp
from routes.staff import staff_bp
from routes.flights import flights_bp
from routes.api import api_bp

__all__ = ['auth_bp', 'passenger_bp', 'admin_bp', 'staff_bp', 'flights_bp', 'api_bp']
