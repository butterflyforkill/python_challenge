from http import HTTPStatus

from fastapi import FastAPI, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .crud import UnableToBook
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


@app.post("/api/v1/booking", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingBase, db: Session = Depends(get_db)):
    try:
        return crud.create_booking(db=db, booking=booking)
    except UnableToBook as unable_to_book:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail=str(unable_to_book))


@app.put("/api/v1/booking/{booking_id}/extend", response_model=schemas.BookingResponse)
def extend_booking(booking_id: int, extend: schemas.BookingExtend, db: Session = Depends(get_db)):
    try:
        return crud.extend_booking(db=db, booking_id=booking_id, number_of_nights=extend.number_of_nights)
    except UnableToBook as unable_to_book:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail=str(unable_to_book))
