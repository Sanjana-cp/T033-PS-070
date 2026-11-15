
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


TWO_PLACES = Decimal("0.01")


def to_decimal(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid monetary amount.")

    if not amount.is_finite():
        raise ValueError("Monetary amount must be finite.")

    return amount


def round_money(value):
    return to_decimal(value).quantize(
        TWO_PLACES,
        rounding=ROUND_HALF_UP
    )


def add_money(*amounts):
    total = sum(
        (to_decimal(amount) for amount in amounts),
        Decimal("0.00")
    )
    return round_money(total)


def subtract_money(amount, deduction):
    return round_money(
        to_decimal(amount) - to_decimal(deduction)
    )


def multiply_money(amount, multiplier):
    return round_money(
        to_decimal(amount) * to_decimal(multiplier)
    )


def calculate_percentage(amount, percentage):
    return round_money(
        to_decimal(amount) * to_decimal(percentage) / Decimal("100")
    )


def format_money(amount):
    return f"{round_money(amount):.2f}"

def to_money(value):
    return round_money(value)


def percent_of(amount, pct):
    return calculate_percentage(amount, pct)


def fmt_money(value):
    return format_money(value)