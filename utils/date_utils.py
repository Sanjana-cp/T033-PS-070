import calendar
from datetime import date, datetime, time, timedelta


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError, AttributeError):
        raise ValueError("Date must use YYYY-MM-DD format.")


def parse_datetime(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError, AttributeError):
        raise ValueError(
            "Timestamp must use YYYY-MM-DD HH:MM:SS format."
        )


def parse_ts(value):
    return parse_datetime(value)


def get_month_start(year, month):
    return date(year, month, 1)


def get_month_end(year, month):
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, last_day)


def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def days_in_month(year, month):
    return get_days_in_month(year, month)


def get_date_range(start_date, end_date):
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    if end_date < start_date:
        raise ValueError("End date cannot precede start date.")

    days = (end_date - start_date).days
    return [start_date + timedelta(days=i) for i in range(days + 1)]


def days_between(start_date, end_date):
    start_date = parse_date(start_date)
    end_date = parse_date(end_date)
    return (end_date - start_date).days


def is_leap_year(year):
    return calendar.isleap(year)


def month_key(day):
    day = parse_date(day)
    return f"{day.year:04d}-{day.month:02d}"


def month_bounds(month):
    year, month_number = int(month[:4]), int(month[5:7])
    return (
        get_month_start(year, month_number),
        get_month_end(year, month_number),
    )


def bill_due_date(month):
    year, month_number = int(month[:4]), int(month[5:7])
    if month_number == 12:
        return date(year + 1, 1, 10)
    return date(year, month_number + 1, 10)


def penalty_days(due, paid_on):
    due = parse_date(due)
    paid_on = parse_date(paid_on)
    return max(0, (paid_on - due).days)


def inclusive_days(start, end):
    start = parse_date(start)
    end = parse_date(end)
    if end < start:
        raise ValueError("End date cannot precede start date.")
    return (end - start).days + 1


def deposit_deadline(published):
    if isinstance(published, str):
        published = parse_datetime(published)
    return datetime.combine(
        published.date() + timedelta(days=7),
        time(23, 59, 59),
    )


def is_first_half(day):
    day = parse_date(day)
    return day.day <= 15