# 🎬 CineSeat — Movie Ticket Booking (BookMyShow-style)

![CI](https://github.com/shipWithSandesh/cineseat-movie-booking/actions/workflows/ci.yml/badge.svg)

A movie booking app — browse movies, pick a show, choose seats on a live seat map, and book — built to showcase **test automation across every layer**.

## Features
- Movies with language filter, shows per theatre, 80-seat map in Silver / Gold / Premium tiers
- Real-time pricing with a 10% convenience fee
- Thread-safe seat locking: no double booking, even under concurrent requests
- Booking cancellation releases seats
- Validation: max 6 seats, no duplicates, valid seat codes, valid email

## Tech
FastAPI · Pydantic · vanilla JS · **Pytest** · **Playwright** · GitHub Actions

## Test strategy
| Layer | File | What it proves |
|---|---|---|
| Unit | `tests/test_pricing_unit.py` | seat tiers (boundary values), seat validation, fee maths |
| API | `tests/test_booking_api.py` | booking flow, double-booking 409, cancel/rebook, 6 parametrized negative cases |
| UI E2E | `tests/test_booking_ui.py` | full user journey in Chromium, button state rules |

Live-server fixture boots the app on a free port for UI tests; state resets before every test for isolation.

## Run
```bash
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --reload     # open http://127.0.0.1:8000
pytest                            # all tests
pytest -m ui --headed             # watch the browser
```

Built by **Sandesh Pande** · SDET / AI Test Automation Engineer
