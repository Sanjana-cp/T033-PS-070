
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def validate_id(value, prefix):
    if not isinstance(value, str):
        raise ValueError("ID must be a string.")

    pattern = rf"^{re.escape(prefix)}-[A-Z0-9]+$"

    if not re.fullmatch(pattern, value):
        raise ValueError(f"Invalid ID: {value}")

    return value


def validate_student_id(student_id):
    return validate_id(student_id, "STU")


def validate_hostel_id(hostel_id):
    return validate_id(hostel_id, "HST")


def validate_gender(gender):
    if gender not in {"M", "F"}:
        raise ValueError("Gender must be M or F.")
    return gender


def validate_year(year):
    if isinstance(year, bool) or not isinstance(year, int) or year < 1:
        raise ValueError("Year must be a positive integer.")
    return year


def validate_room_type(room_type):
    if room_type not in {"SINGLE", "DOUBLE", "TRIPLE"}:
        raise ValueError("Invalid room type.")
    return room_type


def validate_preferences(preferences):
    if not isinstance(preferences, (list, tuple)):
        raise ValueError("Preferences must be a list.")

    if len(preferences) > 3:
        raise ValueError("Maximum 3 room preferences allowed.")

    valid_types = {"SINGLE", "DOUBLE", "TRIPLE", "SINGLE_AC"}

    if any(item not in valid_types for item in preferences):
        raise ValueError("Invalid room preference.")

    return list(preferences)


def validate_date(value):
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError("Invalid date.")
    return value


def validate_datetime(value):
    if not isinstance(value, datetime):
        raise ValueError("Invalid timestamp.")
    return value


def validate_money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid monetary amount.")

    if not amount.is_finite() or amount < 0:
        raise ValueError("Amount must be a non-negative finite value.")

    return amount.quantize(Decimal("0.01"))
