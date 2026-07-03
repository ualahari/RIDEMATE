from app import app, db
from models import User, Ride

with app.app_context():

    driver = User(
        name="Test Driver",
        contact="9999999999",
        email="driver@test.com",
        password="1234"
    )

    db.session.add(driver)
    db.session.commit()

    ride = Ride(
        route_from="Vijayawada",
        route_to="Vellore",
        seats_available=4,
        driver_id=driver.id
    )

    db.session.add(ride)
    db.session.commit()

    print("Test data created successfully")