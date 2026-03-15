import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app, get_db

Path("data").mkdir(parents=True, exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Fixtures and data
GUEST_A_UNIT_1 = {
    "unit_id": "1",
    "guest_name": "GuestA",
    "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
    "number_of_nights": 5,
}

GUEST_A_UNIT_2 = {
    "unit_id": "2",
    "guest_name": "GuestA",
    "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
    "number_of_nights": 5,
}

GUEST_B_UNIT_1 = {
    "unit_id": "1",
    "guest_name": "GuestB",
    "check_in_date": datetime.date.today().strftime("%Y-%m-%d"),
    "number_of_nights": 5,
}


@pytest.fixture()
def test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.mark.freeze_time("2023-05-21")
def test_create_fresh_booking(test_db):
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text


@pytest.mark.freeze_time("2023-05-21")
def test_same_guest_same_unit_booking(test_db):
    # First booking succeeds
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Same guest, same unit, same date → overlap → should fail
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Unit is already occupied during these dates."


@pytest.mark.freeze_time("2023-05-21")
def test_same_guest_different_unit_booking(test_db):
    # First booking succeeds
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Same guest, different unit, same date → guest overlap → should fail
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_2)
    assert response.status_code == 400, response.text
    assert (
        response.json()["detail"]
        == "Guest already has an overlapping booking elsewhere."
    )


@pytest.mark.freeze_time("2023-05-21")
def test_different_guest_same_unit_booking(test_db):
    # First booking succeeds
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Different guest, same unit, same date → unit overlap → should fail
    response = client.post("/api/v1/booking", json=GUEST_B_UNIT_1)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Unit is already occupied during these dates."


@pytest.mark.freeze_time("2023-05-21")
def test_different_guest_same_unit_booking_different_date(test_db):
    # First booking succeeds
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    assert response.status_code == 200, response.text

    # Different guest, same unit, next day → still overlaps (since 5 nights) → should fail
    next_day = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    overlapping_booking = {
        "unit_id": "1",
        "guest_name": "GuestB",
        "check_in_date": next_day,
        "number_of_nights": 5,
    }
    response = client.post("/api/v1/booking", json=overlapping_booking)
    assert response.status_code == 400, response.text
    assert response.json()["detail"] == "Unit is already occupied during these dates."


# Tests for the new extension feature
@pytest.mark.freeze_time("2023-05-21")
def test_successful_extension(test_db):
    # 1. Create initial booking (5 nights)
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    booking_id = response.json()["id"]
    original_checkout = response.json()["check_out_date"]  # 2023-05-26

    # 2. Extend by 2 nights
    extension_payload = {"extra_nights": 2}
    response = client.patch(
        f"/api/v1/booking/{booking_id}/extend", json=extension_payload
    )

    assert response.status_code == 200
    data = response.json()
    assert data["number_of_nights"] == 7
    # Checkout should now be 2 nights later than original
    expected_checkout = (
        datetime.date.fromisoformat(original_checkout) + datetime.timedelta(days=2)
    ).isoformat()
    assert data["check_out_date"] == expected_checkout


@pytest.mark.freeze_time("2023-05-21")
def test_extension_conflict_with_other_guest(test_db):
    # 1. Guest A books Unit 1 from May 21 to May 24 (3 nights)
    guest_a_booking = {
        "unit_id": "1",
        "guest_name": "GuestA",
        "check_in_date": "2023-05-21",
        "number_of_nights": 3,
    }
    resp_a = client.post("/api/v1/booking", json=guest_a_booking)
    booking_id = resp_a.json()["id"]

    # 2. Guest B books Unit 1 from May 25 to May 27 (2 nights)
    # Note: May 24 is the gap (A leaves 24th, B arrives 25th)
    guest_b_booking = {
        "unit_id": "1",
        "guest_name": "GuestB",
        "check_in_date": "2023-05-25",
        "number_of_nights": 2,
    }
    client.post("/api/v1/booking", json=guest_b_booking)

    # 3. Guest A tries to extend by 2 nights (Extending into Guest B's time)
    # A's new checkout would be May 26th, which overlaps with B's May 25th start.
    extension_payload = {"extra_nights": 2}
    response = client.patch(
        f"/api/v1/booking/{booking_id}/extend", json=extension_payload
    )

    assert response.status_code == 400
    assert "The unit is booked by someone else" in response.json()["detail"]


@pytest.mark.freeze_time("2023-05-21")
def test_extend_non_existent_booking(test_db):
    extension_payload = {"extra_nights": 2}
    response = client.patch("/api/v1/booking/9999/extend", json=extension_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Booking not found."


@pytest.mark.freeze_time("2023-05-21")
def test_extension_invalid_nights(test_db):
    # Create a booking
    response = client.post("/api/v1/booking", json=GUEST_A_UNIT_1)
    booking_id = response.json()["id"]

    # Try to extend with 0 nights (Pydantic Field(gt=0) should catch this)
    response = client.patch(
        f"/api/v1/booking/{booking_id}/extend", json={"extra_nights": 0}
    )
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation)
