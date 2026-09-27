# ✈️ Smart Flight Management System (FMS)

An enterprise-grade, Python & Flask-based Flight Management and Airport Operations Platform.

Developed to solve real-world operational challenges in commercial aviation—including manual flight scheduling, double-booking, overbooking, delayed passenger communication, disconnected baggage tracking, and disjointed airport check-in desks.

---

## 🌟 Key Features & Problem-Solving Capabilities

### 1. 🛡️ Role-Based Access Control (RBAC) & Security
- **Passenger:** Search & filter flights, smart visual seat picker, booking checkout with baggage add-ons, printable boarding passes, baggage lifecycle tracking, cancellation with instant seat release, and real-time in-app alerts.
- **Airline Staff / Admin:** Centralized operations dashboard, CRUD flight scheduling, delay management with auto-passenger broadcast, flight cancellation directives with refund tagging, aircraft fleet management, master bookings directory, and exportable CSV/printable reports.
- **Airport Ground Staff:** Dedicated operational desk for passenger search & check-in, baggage status advancement scanner, and live boarding gate manifest check-offs.
- **Security:** Secure password hashing with Werkzeug/bcrypt, role-based route decorators, parameterized SQL queries via SQLAlchemy, and clean session management.

### 2. 💺 Smart Visual Seat Selection
- Realistic aircraft fuselage visualization (First Class 2x2, Business Class 2x2, Economy Class 3x3 with aisle gap).
- Prevents double-booking via real-time concurrency locking.
- Dynamic fare calculation updating in real time (Base Fare + Cabin Class Extra + Airport Taxes + Baggage Fee).
- Automatically releases seats back to inventory upon booking cancellation.

### 3. ⏰ Flight Delay & Cancellation Management
- **Delay Management:** When an administrator reschedules a departure time and provides an official reason, the system instantly identifies all confirmed passengers on that flight and broadcasts in-app delay alerts.
- **Cancellation Directives:** Cancels flight schedules, disables further seat purchases, tags confirmed bookings for refund processing, and issues emergency broadcast notifications.

### 4. 🧳 Real-Time Baggage Lifecycle Tracker
- Tracks luggage through the 6-stage airport pipeline:
  $$\text{Checked-In} \longrightarrow \text{Security Checked} \longrightarrow \text{Loaded} \longrightarrow \text{In Transit} \longrightarrow \text{Arrived} \longrightarrow \text{Delivered}$$
- Ground staff scanner portal to advance checkpoint statuses with location notes.
- Passenger self-service tracking with visual timeline progress bars and movement logs.

### 5. 🎫 Airport Check-In & Boarding Gate Manifest
- **Check-In Desk:** Search reservations by PNR Reference (e.g. `BK10234`) or Passenger Name, verify seat assignment, issue boarding pass numbers, and activate luggage tags.
- **Boarding Gate Controller:** Live passenger manifest showing Checked-In vs Boarded vs Remaining counts with 1-click boarding verification and printable manifest reports.

### 6. 📊 Admin KPI Dashboard & Analytical Reports
- Live metrics for scheduled, delayed, cancelled, arrived, and departed flights.
- Interactive **Chart.js** data visualizations for Fleet Status Distribution and Baggage Handling Pipeline.
- Exportable & printable reports: **Flight Performance Report**, **Passenger Manifest Report**, and **Baggage Logistics Report** (with CSV download).

---

## 🏗️ Project Architecture

```
flight_management_system/
│
├── app.py                     # Application factory, Jinja filters, context processors & error handlers
├── config.py                  # Environment config (SQLite default, MySQL configurable)
├── seed_data.py               # Rich realistic database seeder for instant demo
├── test_fms.py                # Automated unittest suite validating all 14 modules
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── .env.example               # Environment variables template
│
├── models/                    # Relational Database Models (SQLAlchemy)
│   ├── __init__.py            # DB instance & model exports
│   ├── user.py                # User, PassengerProfile, StaffProfile
│   ├── flight.py              # Aircraft, Flight, Seat, FlightDelay, FlightCancellation
│   ├── booking.py             # Booking, Payment, CheckIn, Boarding
│   ├── baggage.py             # Baggage, BaggageLog
│   └── notification.py        # Notification
│
├── routes/                    # Modular Blueprint Controllers
│   ├── __init__.py
│   ├── auth.py                # Registration, Login, Logout, Profile, RBAC decorators
│   ├── passenger.py           # Dashboard, Search, Seat Select, Checkout, Ticket, Baggage, Cancel
│   ├── admin.py               # Admin Dashboard, Flights CRUD, Delays, Cancellations, Fleet, Reports
│   ├── staff.py               # Check-In Counter, Baggage Scanner, Boarding Gate Manifest
│   ├── flights.py             # Public Airport Radar (FIDS) Schedule Board
│   └── api.py                 # REST APIs for Seats, Unread notifications, Live Flight Radar
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Modern responsive navbar, radar modal, notifications badge, footer
│   ├── index.html             # Airline hero, search bar, live flight cards, feature showcase
│   ├── auth/                  # login.html, register.html, profile.html
│   ├── passenger/             # dashboard.html, search_results.html, seat_selection.html,
│   │                          # booking_review.html, booking_confirmation.html, my_bookings.html,
│   │                          # baggage_track.html, notifications.html
│   ├── admin/                 # dashboard.html, flights_list.html, flight_form.html,
│   │                          # delay_management.html, cancellations.html, aircraft_list.html,
│   │                          # bookings_list.html, passengers_list.html, reports.html
│   ├── staff/                 # desk.html, checkin.html, baggage_desk.html, boarding.html
│   ├── flights/               # schedule.html (FIDS Departures & Arrivals)
│   └── errors/                # 404.html, 500.html
│
├── static/
│   ├── css/
│   │   └── custom.css         # Airline theme, visual fuselage styling, ticket aesthetics, timelines
│   └── js/
│       ├── main.js            # Notifications polling, live radar lookup, alert auto-dismiss
│       ├── seatmap.js         # Visual aircraft seat selector & dynamic pricing calculation
│       └── charts.js          # Admin dashboard Chart.js initialization
│
└── database/
    └── schema.sql             # SQL Schema definition (MySQL 8.0+ & SQLite compatible)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- pip package manager

### 2. Installation
Clone or navigate to the project directory:
```bash
cd "d:/Flight management System"
```

Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Seed Database with Realistic Demo Data
Run the database seed script to populate demo users, aircrafts, flights, seat layouts, bookings, and baggage tracking records:
```bash
python seed_data.py
```

### 4. Run the Application
Launch the Flask development server:
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🔑 Demo Login Credentials

The application provides 1-click auto-fill demo buttons on the login page (`/login`) for convenience:

| Role | Username | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Airline Admin** | `admin` | `admin123` | Master Operations Dashboard, Flight CRUD, Delay Dispatch, Cancellations, Fleet Management, Reports |
| **Airport Staff** | `staff` | `staff123` | Check-In Counter, Boarding Gate Manifest, Baggage Checkpoint Scanner |
| **Passenger (Demo 1)** | `mukhesh` | `pass123` | Flight Booking, Seat Selection, Ticket View, Baggage Live Tracker, Notifications |
| **Passenger (Demo 2)** | `sneha` | `pass123` | Flight Search, Bookings & Cancellation Management |

---

## 🧪 Running Automated Tests

Run the complete test suite to verify all business rules, database constraints, and module endpoints:
```bash
python -m unittest test_fms.py
```

---

## 🗄️ Database Configuration (SQLite or MySQL)

By default, the application runs on **SQLite** for zero-configuration testing. To connect to **MySQL**, configure your database connection string in `.env`:

```env
# Example MySQL configuration
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/flight_management_db
```
The raw relational schema is also available in [`database/schema.sql`](file:///d:/Flight%20management%20System/database/schema.sql).
