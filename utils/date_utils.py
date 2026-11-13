
from datetime import date, datetime, timedelta
import calendar


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError("Date must use YYYY-MM-DD format.")


def parse_datetime(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        raise ValueError(
            "Timestamp must use YYYY-MM-DD HH:MM:SS format."
        )


def get_month_start(year, month):
    return date(year, month, 1)


def get_month_end(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def get_date_range(start_date, end_date):
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    if end_date < start_date:
        raise ValueError("End date cannot precede start date.")

    days = (end_date - start_date).days
    return [
        start_date + timedelta(days=i)
        for i in range(days + 1)
    ]


def days_between(start_date, end_date):
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    return (end_date - start_date).days


def is_leap_year(year):
    return calendar.isleap(year)
