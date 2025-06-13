import datetime

from pydantic import BaseModel


class BookingBase(BaseModel):
    guest_name: str
    unit_id: str
    check_in_date: datetime.date
    number_of_nights: int

    class Config:
        orm_mode = True


class BookingExtend(BaseModel):
    number_of_nights: int

class BookingResponse(BookingBase):
    id: int
