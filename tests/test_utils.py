from datetime import date, datetime
from decimal import Decimal

from utils.date_utils import (
    bill_due_date,
    deposit_deadline,
    inclusive_days,
    month_bounds,
    parse_date,
    parse_ts,
    penalty_days,
)
from utils.money_utils import fmt_money, percent_of, to_money
from utils.validators import parse_bool


def test_money_rounding_and_formatting():
    assert to_money("12.345") == Decimal("12.35")
    assert fmt_money("12") == "12.00"
    assert percent_of("200", "12.5") == Decimal("25.00")


def test_date_and_timestamp_parsing():
    assert parse_date("2026-08-15") == date(2026, 8, 15)
    assert parse_ts("2026-07-20 10:00:00") == datetime(2026, 7, 20, 10)


def test_month_bounds_and_following_month_due_date():
    assert month_bounds("2026-09") == (
        date(2026, 9, 1),
        date(2026, 9, 30),
    )
    assert bill_due_date("2026-12") == date(2027, 1, 10)


def test_penalty_days_and_inclusive_days():
    assert penalty_days(date(2026, 10, 10), date(2026, 11, 9)) == 30
    assert inclusive_days(date(2026, 9, 1), date(2026, 11, 29)) == 90


def test_deposit_deadline_is_end_of_day_seven():
    assert deposit_deadline(datetime(2026, 7, 20, 10)) == datetime(
        2026, 7, 27, 23, 59, 59
    )


def test_parse_bool():
    assert parse_bool("true") is True
    assert parse_bool("False") is False