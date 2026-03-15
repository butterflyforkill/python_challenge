from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


class UnableToBook(Exception):
    pass


class ExtensionError(Exception):
    pass


def create_booking(db: Session, booking: schemas.BookingBase) -> models.Booking:
    # 1. Calculate the checkout date before the query
    new_start = booking.check_in_date
    new_end = booking.check_in_date + timedelta(days=booking.number_of_nights)

    # 2. Use a transaction block to prevent race conditions
    try:
        # Check for overlaps
        is_possible, reason = is_booking_possible(db, booking, new_end)

        if not is_possible:
            raise UnableToBook(reason)

        db_booking = models.Booking(
            guest_name=booking.guest_name,
            unit_id=booking.unit_id,
            check_in_date=new_start,
            number_of_nights=booking.number_of_nights,
            check_out_date=new_end,  # Save the pre-calculated date
        )

        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        print(
            f"--- SUCCESS: Created Booking #{db_booking.id} ---"
        )  # checking if the primary key working right
        return db_booking

    except Exception as e:
        db.rollback()
        raise e


def is_booking_possible(
    db: Session, booking: schemas.BookingBase, new_end
) -> tuple[bool, str]:
    new_start = booking.check_in_date

    # OVERLAP LOGIC:
    # (ExistingStart < NewEnd) AND (ExistingEnd > NewStart)

    # 1. Unit Check
    unit_conflict = (
        db.execute(
            select(models.Booking).where(
                models.Booking.unit_id == booking.unit_id,
                models.Booking.check_in_date < new_end,
                models.Booking.check_out_date > new_start,
            )
        )
        .scalars()
        .first()
    )

    if unit_conflict:
        return False, "Unit is already occupied during these dates."

    # 2. Guest Check
    guest_conflict = (
        db.execute(
            select(models.Booking).where(
                models.Booking.guest_name == booking.guest_name,
                models.Booking.check_in_date < new_end,
                models.Booking.check_out_date > new_start,
            )
        )
        .scalars()
        .first()
    )

    if guest_conflict:
        return False, "Guest already has an overlapping booking elsewhere."

    return True, "OK"


def extend_booking(db: Session, booking_id: int, extra_nights: int) -> models.Booking:
    # 1. Fetch the existing booking
    db_booking = (
        db.execute(select(models.Booking).where(models.Booking.id == booking_id))
        .scalars()
        .first()
    )

    if not db_booking:
        raise ExtensionError("Booking not found.")

    if extra_nights <= 0:
        raise ExtensionError("Extension must be at least 1 night.")

    # 2. Calculate the proposed new end date
    # New end = Current check_out_date + extra nights
    current_end = db_booking.check_out_date
    proposed_end = current_end + timedelta(days=extra_nights)

    # 3. Check if the unit is available for the extension period
    # We only need to check if ANY booking starts BETWEEN the current_end and proposed_end
    conflict = (
        db.execute(
            select(models.Booking).where(
                models.Booking.unit_id == db_booking.unit_id,
                models.Booking.id != booking_id,  # Don't check against itself
                models.Booking.check_in_date < proposed_end,
                models.Booking.check_out_date > current_end,
            )
        )
        .scalars()
        .first()
    )

    if conflict:
        raise ExtensionError(
            "Cannot extend stay: The unit is booked by someone else shortly after your current stay."
        )

    # 4. Update the booking
    db_booking.number_of_nights += extra_nights
    db_booking.check_out_date = proposed_end

    db.commit()
    db.refresh(db_booking)
    return db_booking
