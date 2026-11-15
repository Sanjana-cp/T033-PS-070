import csv
from pathlib import Path

from utils.date_utils import parse_date, parse_ts
from utils.money_utils import to_money
from utils.validators import parse_bool


INPUT_FILES = {
    "hostels": "hostels.csv",
    "rooms": "rooms.csv",
    "mess_rate_card": "mess_rate_card.csv",
    "applicants": "applicants.csv",
    "leave_applications": "leave_applications.csv",
    "mess_attendance_monthly": "mess_attendance_monthly.csv",
    "mess_extras": "mess_extras.csv",
}


def _read_rows(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def read_hostels(path):
    return [
        {
            **row,
            "total_beds": int(row["total_beds"]),
        }
        for row in _read_rows(path)
    ]


def read_rooms(path):
    return [
        {
            **row,
            "floor": int(row["floor"]),
            "beds": int(row["beds"]),
            "ac": parse_bool(row["ac"]),
            "monthly_rent": to_money(row["monthly_rent"]),
        }
        for row in _read_rows(path)
    ]


def read_mess_rate_card(path):
    return [
        {
            **row,
            "price": to_money(row["price"]),
        }
        for row in _read_rows(path)
    ]


def read_applicants(path):
    result = []
    for row in _read_rows(path):
        result.append({
            **row,
            "year": int(row["year"]),
            "cgpa": float(row["cgpa"]),
            "international": parse_bool(row["international"]),
            "home_distance_km": float(row["home_distance_km"]),
            "disability": parse_bool(row["disability"]),
            "preferences": [
                row[key] for key in ("pref1", "pref2", "pref3") if row[key]
            ],
            "mixed_year_consent": parse_bool(row["mixed_year_consent"]),
            "application_ts": parse_ts(row["application_ts"]),
        })
    return result


def read_leave_applications(path):
    return [
        {
            **row,
            "from_date": parse_date(row["from_date"]),
            "to_date": parse_date(row["to_date"]),
            "submitted_date": parse_date(row["submitted_date"]),
        }
        for row in _read_rows(path)
    ]


def read_mess_attendance(path):
    return [
        {
            **row,
            "days_present": int(row["days_present"]),
        }
        for row in _read_rows(path)
    ]


def read_mess_extras(path):
    return [
        {
            **row,
            "date": parse_date(row["date"]),
            "quantity": int(row["quantity"]),
        }
        for row in _read_rows(path)
    ]


def load_inputs(data_dir):
    data_dir = Path(data_dir)
    return {
        "hostels": read_hostels(data_dir / INPUT_FILES["hostels"]),
        "rooms": read_rooms(data_dir / INPUT_FILES["rooms"]),
        "mess_rate_card": read_mess_rate_card(
            data_dir / INPUT_FILES["mess_rate_card"]
        ),
        "applicants": read_applicants(data_dir / INPUT_FILES["applicants"]),
        "leave_applications": read_leave_applications(
            data_dir / INPUT_FILES["leave_applications"]
        ),
        "mess_attendance_monthly": read_mess_attendance(
            data_dir / INPUT_FILES["mess_attendance_monthly"]
        ),
        "mess_extras": read_mess_extras(
            data_dir / INPUT_FILES["mess_extras"]
        ),
    }