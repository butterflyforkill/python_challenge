from datetime import timedelta
from typing import Tuple, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, text

from . import models, schemas


class UnableToBook(Exception):
    pass


def fetch_booking(db: Session, booking_id: int) -> models.Booking:
    return db.query(models.Booking).filter(models.Booking.id == booking_id).first()


def create_booking(db: Session, booking: schemas.BookingBase) -> models.Booking:
    (is_possible, reason) = is_booking_possible(db=db, booking=booking)
    if not is_possible:
        raise UnableToBook(reason)
    db_booking = models.Booking(
        guest_name=booking.guest_name, unit_id=booking.unit_id,
        check_in_date=booking.check_in_date, number_of_nights=booking.number_of_nights)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


# Extend an existing booking
def extend_booking(db: Session, booking_id: int, number_of_nights: int) -> models.Booking:
    # Fetch the existing booking
    existing_booking = fetch_booking(db=db, booking_id=booking_id)
    if not existing_booking:
        raise UnableToBook("Booking not found")


    # Check the new number of nights
    if number_of_nights <= existing_booking.number_of_nights:
        raise UnableToBook("Number of nights cannot be less than or equal to the existing booking")

    # Create a BookingBase instance for validation
    updated_booking = schemas.BookingBase(
        guest_name=existing_booking.guest_name,
        unit_id=existing_booking.unit_id,
        check_in_date=existing_booking.check_in_date,
        number_of_nights=number_of_nights
    )

    # Check if the new booking overlaps with any existing bookings
    possible, message = is_booking_possible(db, updated_booking, booking_id)
    if not possible:
        raise UnableToBook(message)

    # Update the booking with the new number of nights
    existing_booking.number_of_nights = number_of_nights
    db.commit()
    db.refresh(existing_booking)
    return existing_booking


def is_booking_possible(db: Session, booking: schemas.BookingBase, exclude_booking_id: Optional[int] = None) -> Tuple[bool, str]:
    # Calculate check_out_date for the new booking
    check_out_date = booking.check_in_date + timedelta(days=booking.number_of_nights)

    # Base filter for overlapping bookings
    base_filters = [
        models.Booking.check_in_date <= check_out_date,
        text("date(check_in_date, '+' || number_of_nights || ' days') >= :check_in_date").bindparams(check_in_date=booking.check_in_date)
    ]

    # Add exclusion for current booking if provided
    if exclude_booking_id is not None:
        base_filters.append(models.Booking.id != exclude_booking_id)

    # Check 1: Same guest, same unit with overlapping dates
    same_unit_filters = base_filters + [
        models.Booking.unit_id == booking.unit_id,
        models.Booking.guest_name == booking.guest_name
    ]
    is_same_guest_booking_same_unit = db.query(models.Booking).filter(and_(*same_unit_filters)).first()
    if is_same_guest_booking_same_unit:
        return False, "The given guest name cannot book the same unit multiple times"

    # Check 2: Same guest, multiple units with overlapping dates
    guest_filters = base_filters + [
        models.Booking.guest_name == booking.guest_name
    ]
    is_same_guest_already_booked = db.query(models.Booking).filter(and_(*guest_filters)).first()
    if is_same_guest_already_booked:
        return False, "The same guest cannot be in multiple units at the same time"

    # Check 3: Unit is available for the check-in date
    unit_filters = base_filters + [
        models.Booking.unit_id == booking.unit_id
    ]
    is_unit_booked = db.query(models.Booking).filter(and_(*unit_filters)).first()
    if is_unit_booked:
        return False, "For the given check-in date, the unit is already occupied"

    return True, "OK"
