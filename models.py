from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ================= USER =================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    gender = db.Column(db.String(20))
    contact = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relations
    rides = db.relationship("Ride", backref="driver", lazy=True)
    bookings = db.relationship("Booking", backref="passenger", lazy=True)
    tickets = db.relationship("SupportTicket", backref="user", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)


# ================= RIDE =================
class Ride(db.Model):
    __tablename__ = "rides"

    id = db.Column(db.Integer, primary_key=True)

    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    vehicle_type = db.Column(db.String(50))
    route_from = db.Column(db.String(120))
    route_to = db.Column(db.String(120))

    departure_time = db.Column(db.String(50))
    seats_available = db.Column(db.Integer)

    women_only = db.Column(db.Boolean, default=False)
    helmet_status = db.Column(db.String(50))

    status = db.Column(db.String(20), default="Upcoming")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship(
        "Booking",
        backref="ride",
        lazy=True,
        cascade="all, delete"
    )

    locations = db.relationship(
        "RideLocation",
        backref="ride",
        lazy=True
    )


# ================= BOOKING =================
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    passenger_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"))

    status = db.Column(db.String(20), default="Booked")
    rating = db.Column(db.Integer)

    booked_at = db.Column(db.DateTime, default=datetime.utcnow)



# ================= RIDE LOCATION =================
class RideLocation(db.Model):
    __tablename__ = "ride_locations"

    id = db.Column(db.Integer, primary_key=True)

    ride_id = db.Column(db.Integer, db.ForeignKey("rides.id"))

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    speed = db.Column(db.Float)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= SUPPORT TICKET =================
class SupportTicket(db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    subject = db.Column(db.String(150))
    message = db.Column(db.Text)

    status = db.Column(db.String(20), default="Open")
    priority = db.Column(db.String(20), default="Normal")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= NOTIFICATION =================
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    title = db.Column(db.String(150))
    message = db.Column(db.Text)

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)