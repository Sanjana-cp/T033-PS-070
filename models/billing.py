
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional, List


@dataclass
class Billing:
    student_id: str
    month: int
    year: int
    meal_plan: str

    rent: Decimal
    billable_days: int
    mess_rate: Decimal
    guest_meal_rate: Decimal

    attendance_days: int = 0
    rebate_days: int = 0
    guest_meals: int = 0
    extras_amount: Decimal = Decimal("0.00")

    penalty: Decimal = Decimal("0.00")
    amount_paid: Decimal = Decimal("0.00")

    due_date: Optional[date] = None
    flags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.student_id:
            raise ValueError("Student ID cannot be empty.")

        if self.meal_plan not in {"VEG", "NONVEG"}:
            raise ValueError("Meal plan must be VEG or NONVEG.")

        if not 1 <= self.month <= 12:
            raise ValueError("Month must be between 1 and 12.")

        if self.rent < 0:
            raise ValueError("Rent cannot be negative.")

        if self.billable_days < 0:
            raise ValueError("Billable days cannot be negative.")

        if self.attendance_days < 0:
            raise ValueError("Attendance days cannot be negative.")

        if self.rebate_days < 0:
            raise ValueError("Rebate days cannot be negative.")

        if self.rebate_days > self.billable_days:
            raise ValueError("Rebate days cannot exceed billable days.")

        if not 0 <= self.guest_meals <= 10:
            raise ValueError("Guest meals must be between 0 and 10.")

        if self.mess_rate < 0 or self.guest_meal_rate < 0:
            raise ValueError("Rates cannot be negative.")

        if self.extras_amount < 0:
            raise ValueError("Extras amount cannot be negative.")

        if not Decimal("0.00") <= self.penalty <= Decimal("300.00"):
            raise ValueError("Penalty must be between 0 and 300.")

        if self.amount_paid < 0:
            raise ValueError("Amount paid cannot be negative.")

        if self.attendance_days == 0 and self.rebate_days == 0:
            self.add_flag("NO_ATTENDANCE")

    def add_flag(self, flag: str):
        if flag and flag not in self.flags:
            self.flags.append(flag)

    @property
    def mess_days_billed(self) -> int:
        return self.billable_days - self.rebate_days

    @property
    def mess_amount(self) -> Decimal:
        return self.mess_rate * self.mess_days_billed

    @property
    def rebate_amount(self) -> Decimal:
        return self.mess_rate * self.rebate_days

    @property
    def guest_meal_amount(self) -> Decimal:
        return self.guest_meal_rate * self.guest_meals

    @property
    def total_amount(self) -> Decimal:
        return (
            self.rent
            + self.mess_amount
            + self.guest_meal_amount
            + self.extras_amount
            + self.penalty
        )

    @property
    def outstanding_amount(self) -> Decimal:
        return self.total_amount - self.amount_paid
