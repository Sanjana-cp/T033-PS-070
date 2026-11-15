import csv
from pathlib import Path

ALLOTMENT_COLUMNS = [
    "student_id", "priority_score", "status", "hostel_id",
    "room_id", "room_type", "flags", "waitlist_position",
]

BILL_COLUMNS = [
    "student_id", "month", "rent", "mess_days_billed", "mess_rate",
    "mess_amount", "rebate_days", "rebate_amount", "guest_meals",
    "extras_amount", "penalty", "total", "flags",
]

SETTLEMENT_COLUMNS = [
    "student_id", "vacate_date", "deposit", "unpaid_dues", "damages",
    "notice_forfeit", "refund", "recoverable",
]

DUES_COLUMNS = [
    "as_of_date", "student_id", "outstanding", "months_over_5000", "hold",
]

OCCUPANCY_COLUMNS = [
    "date", "hostel_id", "beds", "occupied", "temporarily_vacant", "vacant",
]


def write_csv(path, columns, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_allotment(path, rows):
    write_csv(path, ALLOTMENT_COLUMNS, rows)


def write_bills(path, rows):
    write_csv(path, BILL_COLUMNS, rows)


def write_settlements(path, rows):
    write_csv(path, SETTLEMENT_COLUMNS, rows)


def write_dues(path, rows):
    write_csv(path, DUES_COLUMNS, rows)


def write_occupancy(path, rows):
    write_csv(path, OCCUPANCY_COLUMNS, rows)