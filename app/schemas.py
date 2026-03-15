import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookingBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    guest_name: str
    unit_id: str
    check_in_date: datetime.date
    # Using Field(gt=0) prevents 0 or negative night bookings at the entry point
    number_of_nights: int = Field(..., gt=0)


class BookingCreate(BookingBase):
    """Schema for creating a new booking."""

    pass


class BookingExtend(BaseModel):
    """Schema for the extension stay API."""

    extra_nights: int = Field(
        ..., gt=0, description="Number of additional nights to add"
    )


class Booking(BookingBase):
    """
    Schema for the response returned to the user.
    Includes the ID and the calculated check_out_date.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    check_out_date: datetime.date
