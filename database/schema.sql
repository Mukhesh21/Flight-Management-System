-- Smart Flight Management System (FMS) Database Schema
-- Compatible with MySQL 8.0+ and SQLite 3

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'passenger',
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS passengers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    passport_number VARCHAR(30),
    nationality VARCHAR(50) DEFAULT 'Indian',
    date_of_birth DATE,
    frequent_flyer_no VARCHAR(30),
    emergency_contact VARCHAR(50),
    address VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    employee_id VARCHAR(30) NOT NULL UNIQUE,
    department VARCHAR(50) DEFAULT 'Ground Operations',
    airport_code VARCHAR(10) DEFAULT 'DEL',
    designation VARCHAR(50) DEFAULT 'Operations Officer',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS aircraft (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model VARCHAR(80) NOT NULL,
    registration_no VARCHAR(30) NOT NULL UNIQUE,
    total_seats INT NOT NULL DEFAULT 180,
    economy_seats INT NOT NULL DEFAULT 150,
    business_seats INT NOT NULL DEFAULT 24,
    first_class_seats INT NOT NULL DEFAULT 6,
    status VARCHAR(20) DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS flights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    airline_name VARCHAR(80) NOT NULL DEFAULT 'SkyWings Airlines',
    source VARCHAR(80) NOT NULL,
    source_code VARCHAR(10) NOT NULL,
    destination VARCHAR(80) NOT NULL,
    destination_code VARCHAR(10) NOT NULL,
    departure_time DATETIME NOT NULL,
    arrival_time DATETIME NOT NULL,
    duration VARCHAR(30),
    aircraft_id INT NOT NULL,
    gate VARCHAR(20) DEFAULT 'A1',
    terminal VARCHAR(20) DEFAULT 'T3',
    status VARCHAR(30) NOT NULL DEFAULT 'Scheduled',
    base_price DOUBLE NOT NULL DEFAULT 4500.0,
    available_seats INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aircraft_id) REFERENCES aircraft(id)
);

CREATE TABLE IF NOT EXISTS seats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    seat_class VARCHAR(20) NOT NULL DEFAULT 'Economy',
    is_occupied BOOLEAN DEFAULT FALSE,
    is_window BOOLEAN DEFAULT FALSE,
    is_aisle BOOLEAN DEFAULT FALSE,
    extra_price DOUBLE DEFAULT 0.0,
    UNIQUE(flight_id, seat_number),
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_reference VARCHAR(20) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    flight_id INT NOT NULL,
    seat_id INT NOT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    passenger_email VARCHAR(120) NOT NULL,
    passenger_phone VARCHAR(20) NOT NULL,
    passenger_age INT,
    passenger_gender VARCHAR(10),
    passport_number VARCHAR(30),
    total_fare DOUBLE NOT NULL,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'Confirmed',
    cancellation_date DATETIME,
    cancellation_reason VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
    FOREIGN KEY (seat_id) REFERENCES seats(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    payment_reference VARCHAR(40) NOT NULL UNIQUE,
    amount DOUBLE NOT NULL,
    payment_method VARCHAR(30) DEFAULT 'Credit Card',
    payment_status VARCHAR(20) DEFAULT 'Success',
    transaction_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS checkins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    checkin_by INT,
    boarding_pass_no VARCHAR(30) NOT NULL UNIQUE,
    gate VARCHAR(20),
    sequence_no INT,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (checkin_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS boarding (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE,
    boarding_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    boarded_by INT,
    status VARCHAR(20) DEFAULT 'Boarded',
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (boarded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS baggage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    baggage_tag VARCHAR(30) NOT NULL UNIQUE,
    booking_id INT NOT NULL,
    passenger_id INT NOT NULL,
    weight_kg DOUBLE NOT NULL DEFAULT 15.0,
    baggage_type VARCHAR(30) DEFAULT 'Check-In',
    status VARCHAR(30) NOT NULL DEFAULT 'Checked-In',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (passenger_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS baggage_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    baggage_id INT NOT NULL,
    status VARCHAR(30) NOT NULL,
    location VARCHAR(100) DEFAULT 'Airport Terminal',
    notes VARCHAR(255),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_by INT,
    FOREIGN KEY (baggage_id) REFERENCES baggage(id) ON DELETE CASCADE,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS flight_delays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    original_departure DATETIME NOT NULL,
    revised_departure DATETIME NOT NULL,
    delay_reason VARCHAR(255) NOT NULL,
    notified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS flight_cancellations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL UNIQUE,
    cancellation_reason VARCHAR(255) NOT NULL,
    cancelled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    affected_passengers_count INT DEFAULT 0,
    created_by INT,
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(30) DEFAULT 'system',
    is_read BOOLEAN DEFAULT FALSE,
    link_url VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
