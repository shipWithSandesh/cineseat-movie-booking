import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
def test_user_books_two_premium_seats_end_to_end(page: Page, live_server):
    page.goto(live_server)
    page.get_by_test_id("movie-1").click()
    page.get_by_test_id("show-101").click()
    page.locator("[data-seat=G5]").click()
    page.locator("[data-seat=G6]").click()
    expect(page.locator("#total")).to_have_text("770")
    page.fill("#email", "sandesh@example.com")
    page.get_by_role("button", name="Book tickets").click()
    expect(page.get_by_test_id("confirmed")).to_be_visible()
    expect(page.locator("#booking-id")).to_have_text(re.compile(r"^[A-F0-9]{8}$"))


@pytest.mark.ui
def test_book_button_disabled_until_a_seat_is_picked(page: Page, live_server):
    page.goto(live_server)
    page.get_by_test_id("movie-2").click()
    page.get_by_test_id("show-201").click()
    expect(page.get_by_role("button", name="Book tickets")).to_be_disabled()
    page.locator("[data-seat=A1]").click()
    expect(page.get_by_role("button", name="Book tickets")).to_be_enabled()
