import pytest

EMAIL = "sandesh@example.com"


def book(api, seats, show_id=101, email=EMAIL):
    return api.post("/api/bookings", json={"show_id": show_id, "seats": seats, "email": email})


@pytest.mark.api
def test_filter_movies_by_language(api):
    titles = [m["title"] for m in api.get("/api/movies", params={"language": "kannada"}).json()]
    assert titles == ["Kantara"]


@pytest.mark.api
def test_seat_map_has_80_seats_all_free(api):
    seats = api.get("/api/shows/101/seats").json()
    assert len(seats) == 80 and not any(s["booked"] for s in seats)


@pytest.mark.api
def test_booking_confirms_and_marks_seats_taken(api):
    r = book(api, ["G5", "G6"])
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "CONFIRMED" and body["total"] == 770
    taken = {s["seat"] for s in api.get("/api/shows/101/seats").json() if s["booked"]}
    assert taken == {"G5", "G6"}


@pytest.mark.api
def test_double_booking_is_rejected(api):
    assert book(api, ["D4"]).status_code == 201
    r = book(api, ["D4", "D5"], email="other@example.com")
    assert r.status_code == 409 and "D4" in r.json()["detail"]


@pytest.mark.api
def test_same_seat_on_another_show_is_free(api):
    assert book(api, ["D4"]).status_code == 201
    assert book(api, ["D4"], show_id=102).status_code == 201


@pytest.mark.api
def test_cancel_releases_seats(api):
    booking = book(api, ["E1"]).json()
    assert api.delete(f"/api/bookings/{booking['id']}").json()["status"] == "CANCELLED"
    assert book(api, ["E1"]).status_code == 201
    assert api.delete(f"/api/bookings/{booking['id']}").status_code == 409


@pytest.mark.api
@pytest.mark.parametrize("payload,status", [
    ({"show_id": 101, "seats": [f"A{i}" for i in range(1, 8)], "email": EMAIL}, 422),
    ({"show_id": 101, "seats": ["A1", "A1"], "email": EMAIL}, 422),
    ({"show_id": 101, "seats": ["Z9"], "email": EMAIL}, 422),
    ({"show_id": 101, "seats": [], "email": EMAIL}, 422),
    ({"show_id": 101, "seats": ["A1"], "email": "not-an-email"}, 422),
    ({"show_id": 999, "seats": ["A1"], "email": EMAIL}, 404),
], ids=["over-limit", "duplicate", "invalid-seat", "empty", "bad-email", "unknown-show"])
def test_invalid_bookings(api, payload, status):
    assert api.post("/api/bookings", json=payload).status_code == status
