from http import HTTPStatus

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .crud import ExtensionError, UnableToBook
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def hello_world():
    return {"message": "OK"}


# Changed response_model to schemas.Booking and input to schemas.BookingCreate
@app.post("/api/v1/booking", response_model=schemas.Booking)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_booking(db=db, booking=booking)
    except UnableToBook as unable_to_book:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=str(unable_to_book)
        )


# NEW: API for extending stays
@app.patch("/api/v1/booking/{booking_id}/extend", response_model=schemas.Booking)
def extend_booking(
    booking_id: int, extension: schemas.BookingExtend, db: Session = Depends(get_db)
):
    try:
        return crud.extend_booking(
            db=db, booking_id=booking_id, extra_nights=extension.extra_nights
        )
    except ExtensionError as extension_error:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail=str(extension_error)
        )
