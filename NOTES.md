# Developer Handover Notes

## Core Changes & Bug Fixes

### 1. Fixed Overlap Bug (Race Conditions & Logic)
* **The Issue:** The previous implementation only checked if a `check_in_date` matched exactly. This allowed new bookings to be created in the middle of an existing multi-night stay, leading to double-booked units.
* **The Fix:** I added a `check_out_date` column to the `Booking` model. This allows the use of the standard interval overlap formula: 
    ` (ExistingStart < NewEnd) AND (ExistingEnd > NewStart) `
* **Concurrency:** In SQLite, I wrapped the check and insert within a transaction block to mitigate race conditions where two users might attempt to book the same slot simultaneously.

### 2. Schema Refactoring
* **Separation of Concerns:** Split the Pydantic schemas into `BookingCreate`, `BookingExtend`, and `Booking` (the response model).
* **Why:** The original setup returned `BookingBase`, which stripped the auto-generated `id` from the API response. The frontend/client needs this `id` to identify specific bookings for extensions.
* **Validation:** Added `Field(gt=0)` constraints to ensure `number_of_nights` is always a positive integer at the API entry point.

### 3. New Feature: Stay Extension
* **Endpoint:** Added `PATCH /api/v1/booking/{booking_id}/extend`.
* **Logic:** The system calculates the new end date and verifies the unit is vacant for the additional nights. Crucially, the logic excludes the current `booking_id` from the conflict check to prevent the booking from "colliding with itself."

---

## Tech Debt & Implementation Notes

* **Database Migration:** If running on an existing `test.db` or `sql_app.db`, **you must delete the file**. SQLAlchemy’s `create_all` does not migrate existing tables to add the new `check_out_date` column.
* **Calculated Fields:** I chose to persist `check_out_date` in the database rather than calculating it on-the-fly. This allows for indexed queries, which is critical for performance as the booking volume grows.
* **SQLite Limitations:** SQLite doesn't support `FOR UPDATE` locks. The current transaction logic relies on SQLite's default file-locking behavior. For a production Postgres environment, I recommend switching to an `ExclusionConstraint` or row-level locking for better concurrency handling.

---

## Testing
* **New Coverage:** Added test cases covering successful extensions, "non-existent booking" errors, and edge-case conflicts (e.g., trying to extend into a future guest's stay).
* **Verification:** Verified that the API response now correctly includes both the `id` and the `check_out_date`.
