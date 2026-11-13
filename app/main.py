"""CineSeat: a BookMyShow-style movie booking API with seat locking and pricing."""
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

app = FastAPI(title="CineSeat")
STATIC = Path(__file__).parent / "static"

MOVIES = [
    {"id": 1, "title": "Interstellar", "language": "English", "genre": "Sci-Fi", "rating": 8.7},
    {"id": 2, "title": "Kantara", "language": "Kannada", "genre": "Thriller", "rating": 8.3},
    {"id": 3, "title": "3 Idiots", "language": "Hindi", "genre": "Comedy", "rating": 8.4},
]
SHOWS = [
    {"id": 101, "movie_id": 1, "theatre": "PVR Orion Mall", "time": "18:30"},
    {"id": 102, "movie_id": 1, "theatre": "INOX Garuda", "time": "21:45"},
    {"id": 201, "movie_id": 2, "theatre": "Cinepolis Nexus", "time": "19:00"},
    {"id": 301, "movie_id": 3, "theatre": "PVR Orion Mall", "time": "16:15"},
]
ROWS, COLS = "ABCDEFGH", 10
PRICES = {"PREMIUM": 350, "GOLD": 250, "SILVER": 180}
CONVENIENCE_FEE_RATE = 0.10
MAX_SEATS = 6

_lock = Lock()
_booked: dict[int, set[str]] = {}
_bookings: dict[str, dict] = {}


def reset_state():
    _booked.clear()
    _bookings.clear()


def seat_class(seat: str) -> str:
    row = seat[0]
    return "PREMIUM" if row in "GH" else "GOLD" if row in "CDEF" else "SILVER"


def valid_seat(seat: str) -> bool:
    return len(seat) >= 2 and seat[0] in ROWS and seat[1:].isdigit() and 1 <= int(seat[1:]) <= COLS


def price_for(seats: list[str]) -> dict:
    subtotal = sum(PRICES[seat_class(s)] for s in seats)
    fee = round(subtotal * CONVENIENCE_FEE_RATE)
    return {"subtotal": subtotal, "convenience_fee": fee, "total": subtotal + fee}


class BookingRequest(BaseModel):
    show_id: int
    seats: list[str] = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _show(show_id: int) -> dict:
    show = next((s for s in SHOWS if s["id"] == show_id), None)
    if not show:
        raise HTTPException(404, "Show not found")
    return show


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/movies")
def movies(language: str | None = None):
    return [m for m in MOVIES if not language or m["language"].lower() == language.lower()]


@app.get("/api/movies/{movie_id}/shows")
def shows(movie_id: int):
    if not any(m["id"] == movie_id for m in MOVIES):
        raise HTTPException(404, "Movie not found")
    return [s for s in SHOWS if s["movie_id"] == movie_id]


@app.get("/api/shows/{show_id}/seats")
def seats(show_id: int):
    _show(show_id)
    taken = _booked.get(show_id, set())
    return [{"seat": f"{r}{c}", "class": seat_class(f"{r}{c}"), "price": PRICES[seat_class(f"{r}{c}")],
             "booked": f"{r}{c}" in taken} for r in ROWS for c in range(1, COLS + 1)]


@app.post("/api/quote")
def quote(req: BookingRequest):
    _validate(req)
    return price_for(req.seats)


def _validate(req: BookingRequest):
    _show(req.show_id)
    if len(req.seats) > MAX_SEATS:
        raise HTTPException(422, f"Max {MAX_SEATS} seats per booking")
    if len(set(req.seats)) != len(req.seats):
        raise HTTPException(422, "Duplicate seats")
    bad = [s for s in req.seats if not valid_seat(s)]
    if bad:
        raise HTTPException(422, f"Invalid seats: {bad}")


@app.post("/api/bookings", status_code=201)
def book(req: BookingRequest):
    _validate(req)
    with _lock:
        taken = _booked.setdefault(req.show_id, set())
        clash = sorted(set(req.seats) & taken)
        if clash:
            raise HTTPException(409, f"Seats already booked: {clash}")
        taken.update(req.seats)
        booking = {"id": uuid4().hex[:8].upper(), "show_id": req.show_id, "seats": sorted(req.seats),
                   "email": req.email, "status": "CONFIRMED", **price_for(req.seats)}
        _bookings[booking["id"]] = booking
    return booking


@app.get("/api/bookings/{booking_id}")
def get_booking(booking_id: str):
    if booking_id not in _bookings:
        raise HTTPException(404, "Booking not found")
    return _bookings[booking_id]


@app.delete("/api/bookings/{booking_id}")
def cancel(booking_id: str):
    booking = get_booking(booking_id)
    if booking["status"] == "CANCELLED":
        raise HTTPException(409, "Already cancelled")
    with _lock:
        _booked[booking["show_id"]].difference_update(booking["seats"])
        booking["status"] = "CANCELLED"
    return booking
