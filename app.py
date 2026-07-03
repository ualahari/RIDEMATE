from flask import Flask, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()

from models import (
    db,
    User,
    Ride,
    Booking,
    RideLocation,
    SupportTicket,
    Notification
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ---------------- HOME ---------------- #

@app.route("/")
def landing():
    return render_template("landing.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = User.query.filter_by(
            email=request.form.get("email")
        ).first()

        if user and check_password_hash(
                user.password,
                request.form.get("password")):

            session["user_id"] = user.id
            session["user_name"] = user.name

            # NEW
            session["gender"] = user.gender

            return redirect("/dashboard")

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        hashed_password = generate_password_hash(
            request.form.get("password")
        )

        user = User(
            name=request.form.get("name"),
            email=request.form.get("email"),
            password=hashed_password,

            gender=request.form.get("gender"),

            # NEW
            contact=request.form.get("contact"),

            emergency_contact=request.form.get(
                "emergency_contact"
            )
        )

        try:

            db.session.add(user)
            db.session.commit()
            flash(
                "Registration Successful",
                "success"
            )

            return redirect("/login")

        except Exception:

            db.session.rollback()

            flash(
                "Email already exists",
                "danger"
            )

    return render_template("register.html")
# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    total_bookings = Booking.query.count()

    completed = Booking.query.filter_by(
        status="Completed"
    ).count()

    carbon_saved = total_bookings * 2.5

    ride_success = (
        round((completed / total_bookings) * 100, 2)
        if total_bookings else 100
    )

    trust_score = round(
        4.5 + (min(total_bookings, 5) * 0.1),
        1
    )

    eco_impact = (
        "Platinum"
        if carbon_saved > 500
        else "Gold"
        if carbon_saved > 100
        else "Silver"
    )

    is_women_only = (
        request.args.get("women_only") == "true"
    )

    search = request.args.get("search", "")

    query = (
        db.session.query(Ride, User)
        .join(User, Ride.driver_id == User.id)
    )

    # Hide Women Only rides from male users
    if session.get("gender") != "Female":
        query = query.filter(Ride.women_only == False)

    # Female users can filter Women Only rides
    elif is_women_only:
        query = query.filter(Ride.women_only == True)

    if search:
        query = query.filter(
            Ride.route_to.contains(search)
        )

    rides = query.all()

    return render_template(
        "dashboard.html",
        user_name=session["user_name"],
        rides=rides,
        carbon_saved=carbon_saved,
        ride_success=ride_success,
        trust_score=trust_score,
        eco_impact=eco_impact,
        is_women_only=is_women_only
    )


# ---------------- OFFER RIDE ---------------- #

@app.route("/offer_ride", methods=["GET", "POST"])
def offer_ride():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        women_only = (
            request.form.get("is_women_only") == "true"
        )

        # Only female users can create Women Only rides
        if women_only and session.get("gender") != "Female":

            flash(
                "Only female users can create Women Only rides.",
                "danger"
            )

            return redirect("/offer_ride")

        ride = Ride(

            driver_id=session["user_id"],

            vehicle_type=request.form.get(
                "vehicle_type"
            ),

            route_from=request.form.get(
                "route_from"
            ),

            route_to=request.form.get(
                "route_to"
            ),

            departure_time=request.form.get(
                "departure_time"
            ),

            seats_available=int(
                request.form.get("seats_available")
            ),

            women_only=women_only,

            helmet_status=request.form.get(
                "helmet_status",
                "N/A"
            )
        )

        db.session.add(ride)
        db.session.commit()

        flash(
            "Ride Added Successfully",
            "success"
        )

        return redirect("/dashboard")

    return render_template(
        "offer_ride.html"
    )
# ---------------- BOOK RIDE ---------------- #
@app.route("/book/<int:ride_id>", methods=["POST"])
def book_ride(ride_id):

    if "user_id" not in session:
        return redirect("/login")

    ride = Ride.query.get_or_404(ride_id)

    # Prevent duplicate booking
    existing = Booking.query.filter_by(
        passenger_id=session["user_id"],
        ride_id=ride.id
    ).first()

    if existing:
        flash("You have already booked this ride.")
        return redirect("/ride_history")

    if ride.seats_available <= 0:
        flash("No seats available.")
        return redirect("/dashboard")

    booking = Booking(
        passenger_id=session["user_id"],
        ride_id=ride.id,
        status="Booked"
    )

    ride.seats_available -= 1

    db.session.add(booking)
    db.session.commit()

    flash("Ride booked successfully!")

    return redirect(f"/live_tracking/{ride.id}")

# ---------------- LIVE TRACKING ---------------- #

@app.route("/live_tracking/<int:ride_id>")
def live_tracking(ride_id):

    if "user_id" not in session:
        return redirect("/login")

    ride = Ride.query.get(ride_id)

    if ride is None:
        flash("Ride not found.", "danger")
        return redirect("/ride_history")

    booking = Booking.query.filter_by(
        ride_id=ride.id,
        passenger_id=session["user_id"]
    ).first()

    return render_template(
        "live_tracking.html",
        ride=ride,
        booking=booking
    )
@app.route("/ride_route")
def ride_route():

    if "user_id" not in session:
        return redirect("/login")

    # Latest booked ride
    booking = Booking.query.filter_by(
        passenger_id=session["user_id"]
    ).order_by(Booking.id.desc()).first()

    if booking:
        return redirect(f"/live_tracking/{booking.ride_id}")

    # Latest offered ride
    ride = Ride.query.filter_by(
        driver_id=session["user_id"]
    ).order_by(Ride.id.desc()).first()

    if ride:
        return redirect(f"/live_tracking/{ride.id}")

    flash("No rides available.")
    return redirect("/dashboard")
# ---------------- RIDE HISTORY ---------------- #
@app.route("/ride_history")
def ride_history():

    if "user_id" not in session:
        return redirect("/login")

    offered = Ride.query.filter_by(
        driver_id=session["user_id"]
    ).all()

    booked = (
        db.session.query(
            Ride,
            User,
            Booking.id
        )
        .join(
            Booking,
            Booking.ride_id == Ride.id
        )
        .join(
            User,
            Ride.driver_id == User.id
        )
        .filter(
            Booking.passenger_id == session["user_id"]
        )
        .all()
    )

    # Passenger list for each ride
    passenger_map = {}

    for ride in offered:

        passengers = (
            db.session.query(User)
            .join(
                Booking,
                Booking.passenger_id == User.id
            )
            .filter(
                Booking.ride_id == ride.id
            )
            .all()
        )

        passenger_map[ride.id] = passengers

    return render_template(
        "ride_history.html",
        booked_rides=booked,
        offered_rides=offered,
        passenger_map=passenger_map
    )

# ---------------- CANCEL RIDE ---------------- #

@app.route("/cancel_ride/<int:ride_id>", methods=["POST"])
def cancel_ride(ride_id):

    if "user_id" not in session:
        return redirect("/login")

    ride = Ride.query.get_or_404(ride_id)

    if ride.driver_id != session["user_id"]:

        flash(
            "Only the driver can cancel this ride.",
            "danger"
        )

        return redirect("/dashboard")

    bookings = Booking.query.filter_by(
        ride_id=ride.id
    ).all()

    # Restore seats
    ride.seats_available += len(bookings)

    # Delete all bookings
    for booking in bookings:
        db.session.delete(booking)

    # Delete ride
    db.session.delete(ride)

    db.session.commit()

    flash(
        "Ride cancelled successfully.",
        "success"
    )

    return redirect("/dashboard")
# ---------------- SUPPORT ---------------- #

@app.route("/support", methods=["GET", "POST"])
def support():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        ticket = SupportTicket(
            user_id=session["user_id"],
            subject=request.form.get("subject"),
            message=request.form.get("message")
        )

        db.session.add(ticket)
        db.session.commit()

        flash(
            "Support Ticket Submitted Successfully.",
            "success"
        )

        return redirect("/dashboard")

    return render_template("support.html")


# ---------------- API ---------------- #

@app.route("/api/stats")
def get_stats():

    total = Booking.query.count()

    completed = Booking.query.filter_by(
        status="Completed"
    ).count()

    carbon = total * 2.5

    success = (
        round((completed / total) * 100, 2)
        if total else 100
    )

    trust = round(
        4.5 + (min(total, 5) * 0.1),
        1
    )

    return jsonify({
        "carbon_saved": carbon,
        "ride_success": success,
        "trust_score": trust
    })


# ---------------- END RIDE ---------------- #

@app.route("/end_ride/<int:ride_id>", methods=["GET", "POST"])
def end_ride(ride_id):

    if "user_id" not in session:
        return redirect("/login")

    ride = Ride.query.get_or_404(ride_id)

    booking = Booking.query.filter_by(
        ride_id=ride.id,
        passenger_id=session["user_id"]
    ).first()

    if request.method == "POST":

        if booking:

            booking.rating = int(
                request.form.get("rating")
            )

            booking.status = "Completed"

            db.session.commit()

            flash(
                "Thank you for your feedback!",
                "success"
            )

        return redirect("/dashboard")

    return render_template(
        "review.html",
        ride=ride
    )


# ---------------- UPDATE LIVE LOCATION ---------------- #

@app.route("/update_location/<int:ride_id>", methods=["POST"])
def update_location(ride_id):

    data = request.get_json()

    location = RideLocation(

        ride_id=ride_id,

        latitude=data.get("latitude"),

        longitude=data.get("longitude"),

        speed=data.get("speed", 0)

    )

    db.session.add(location)

    db.session.commit()

    return jsonify(
        {
            "status": "success"
        }
    )


# ---------------- GET LIVE LOCATION ---------------- #

@app.route("/get_location/<int:ride_id>")
def get_location(ride_id):

    location = (

        RideLocation.query

        .filter_by(ride_id=ride_id)

        .order_by(RideLocation.updated_at.desc())

        .first()

    )

    if location is None:

        return jsonify({

            "latitude": None,

            "longitude": None,

            "speed": 0

        })

    return jsonify({

        "latitude": location.latitude,

        "longitude": location.longitude,

        "speed": location.speed,

        "time": location.updated_at.strftime("%H:%M:%S")

    })


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect("/login")


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )