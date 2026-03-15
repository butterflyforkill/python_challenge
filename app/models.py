from sqlalchemy import CheckConstraint, Column, Date, Integer, String

from .database import Base


class Booking(Base):
    __tablename__ = "booking"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String, index=True)  # index for faster guest lookups
    unit_id = Column(String, index=True)  # index for faster unit lookups
    check_in_date = Column(Date, nullable=False)
    number_of_nights = Column(Integer, nullable=False)
    # Store the end date to make overlap queries fast and reliable
    check_out_date = Column(Date, nullable=False, index=True)

    __table_args__ = (
        # cannot book 0 nights
        CheckConstraint("number_of_nights > 0", name="min_nights_check"),
    )
