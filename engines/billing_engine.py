
from datetime import date, datetime, timedelta
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP


class BillingEngine:
    VEG_RATE = Decimal("150.00")
    NONVEG_RATE = Decimal("180.00")
    GUEST_MEAL_RATE = Decimal("80.00")
    LATE_FEE_PER_DAY = Decimal("10.00")
    MAX_LATE_FEE = Decimal("300.00")
    MAX_REBATE_DAYS = 20
    MAX_GUEST_MEALS = 10

    def __init__(
        self,
        students,
        rooms,
        allotments,
        leave_applications=None,
        semester_start_dates=None
    ):
        self.students = students
        self.rooms = rooms
        self.allotments = allotments
        self.leave_applications = leave_applications or []
        self.semester_start_dates = semester_start_dates or {}

        self.bills = {}
        self.payments = {}
        self.hold_status = {}

    # --------------------------------------------------
    # GENERAL HELPERS
    # --------------------------------------------------

    @staticmethod
    def money(value):
        return Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    @staticmethod
    def get_value(record, field, default=None):
        if isinstance(record, dict):
            return record.get(field, default)
        return getattr(record, field, default)

    @staticmethod
    def parse_date(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise ValueError("Invalid date value.")

    @staticmethod
    def get_month_dates(month):
        year, month_number = map(int, month.split("-"))

        start = date(year, month_number, 1)
        end = date(
            year,
            month_number,
            monthrange(year, month_number)[1]
        )

        return start, end

    def get_student_room(self, student_id):
        allotment = self.allotments.get(student_id)

        if not allotment:
            return None

        room_id = self.get_value(
            allotment,
            "assigned_room_id"
        )

        if not room_id:
            return None

        return self.rooms.get(room_id)

    def get_student(self, student_id):
        return self.students.get(student_id)

    # --------------------------------------------------
    # RENT CALCULATION
    # --------------------------------------------------

    def calculate_rent(
        self,
        monthly_rent,
        month,
        joining_date,
        vacating_date=None,
        room_change_rent=None
    ):
        monthly_rent = self.money(monthly_rent)

        if room_change_rent is not None:
            monthly_rent = max(
                monthly_rent,
                self.money(room_change_rent)
            )

        month_start, month_end = self.get_month_dates(month)

        joining_date = self.parse_date(joining_date)

        if vacating_date is not None:
            vacating_date = self.parse_date(vacating_date)

        # No occupancy during this month.
        if joining_date > month_end:
            return self.money(0)

        if vacating_date is not None and vacating_date < month_start:
            return self.money(0)

        factor = Decimal("1.00")

        # Joining during this month.
        if month_start <= joining_date <= month_end:
            factor = (
                Decimal("0.50")
                if joining_date.day <= 15
                else Decimal("1.00")
            )

        # Vacating during this month.
        if vacating_date is not None:
            if month_start <= vacating_date <= month_end:
                vacate_factor = (
                    Decimal("0.50")
                    if vacating_date.day <= 15
                    else Decimal("1.00")
                )
                factor = max(factor, vacate_factor)

        return self.money(monthly_rent * factor)

    # --------------------------------------------------
    # MESS RATE
    # --------------------------------------------------

    def calculate_mess_rate(self, student_id):
        student = self.get_student(student_id)

        if not student:
            raise ValueError(
                f"Student {student_id} not found."
            )

        mess_plan = self.get_value(student, "mess_plan")

        if mess_plan == "VEG":
            return self.VEG_RATE

        if mess_plan == "NONVEG":
            return self.NONVEG_RATE

        raise ValueError(
            f"Invalid mess plan for {student_id}."
        )

    # --------------------------------------------------
    # LEAVE REBATE
    # --------------------------------------------------

    def get_eligible_rebate_dates(
        self,
        student_id,
        semester_id,
        semester_start_date
    ):
        semester_start_date = self.parse_date(
            semester_start_date
        )

        # Rebate starts from semester day 16.
        rebate_start_date = (
            semester_start_date + timedelta(days=15)
        )

        eligible_dates = set()

        applications = []

        for application in self.leave_applications:
            if self.get_value(
                application,
                "student_id"
            ) != student_id:
                continue

            start = self.parse_date(
                self.get_value(application, "from_date")
            )

            end = self.parse_date(
                self.get_value(application, "to_date")
            )

            submitted = self.parse_date(
                self.get_value(application, "submitted_date")
            )

            if end < start:
                continue

            duration = (end - start).days + 1

            # Minimum five consecutive leave days.
            if duration < 5:
                continue

            # Application must be submitted at least
            # two days before the leave begins.
            if (start - submitted).days < 2:
                continue

            applications.append((start, end))

        applications.sort(key=lambda item: item[0])

        # Apply the 20-day semester cap chronologically.
        for start, end in applications:
            current = max(start, rebate_start_date)

            while current <= end:
                if current not in eligible_dates:
                    if len(eligible_dates) >= self.MAX_REBATE_DAYS:
                        return eligible_dates

                    eligible_dates.add(current)

                current += timedelta(days=1)

        return eligible_dates

    def calculate_rebate(
        self,
        student_id,
        semester_id,
        month,
        semester_start_date=None
    ):
        if semester_start_date is None:
            semester_start_date = self.semester_start_dates.get(
                semester_id
            )

        if semester_start_date is None:
            raise ValueError(
                "Semester start date is required to calculate rebates."
            )

        month_start, month_end = self.get_month_dates(month)

        eligible_dates = self.get_eligible_rebate_dates(
            student_id,
            semester_id,
            semester_start_date
        )

        return sum(
            1
            for leave_date in eligible_dates
            if month_start <= leave_date <= month_end
        )

    # --------------------------------------------------
    # LATE PAYMENT PENALTY
    # --------------------------------------------------

    def calculate_late_penalty(self, month, as_of_date):
        _, month_end = self.get_month_dates(month)

        # Bills are due on the 10th of the next month.
        if month_end.month == 12:
            due_date = date(month_end.year + 1, 1, 10)
        else:
            due_date = date(
                month_end.year,
                month_end.month + 1,
                10
            )

        as_of_date = self.parse_date(as_of_date)

        if as_of_date <= due_date:
            return self.money(0)

        late_days = (as_of_date - due_date).days

        penalty = (
            self.LATE_FEE_PER_DAY * late_days
        )

        return min(
            penalty,
            self.MAX_LATE_FEE
        )

    # --------------------------------------------------
    # BILL GENERATION
    # --------------------------------------------------

    def generate_bill(
        self,
        student_id,
        month,
        joining_date,
        attendance_days,
        requested_rebate_days=None,
        semester_id=None,
        guest_meals=0,
        extras_amount=0,
        as_of_date=None,
        vacating_date=None,
        room_change_rent=None,
        temporary_vacancy_days=0,
        semester_start_date=None,
        monthly_rent=None
    ):
        if student_id not in self.students:
            raise ValueError(
                f"Unknown student: {student_id}"
            )

        if attendance_days < 0:
            raise ValueError(
                "Attendance days cannot be negative."
            )

        if guest_meals < 0:
            raise ValueError(
                "Guest meals cannot be negative."
            )

        if extras_amount < 0:
            raise ValueError(
                "Extras amount cannot be negative."
            )

        if temporary_vacancy_days < 0:
            raise ValueError(
                "Temporary vacancy days cannot be negative."
            )

        if semester_id is None:
            raise ValueError(
                "Semester ID is required for bill generation."
            )

        # Get rent from the student's current room
        # unless a rent value is supplied directly.
        if monthly_rent is None:
            room = self.get_student_room(student_id)

            if room is None:
                raise ValueError(
                    f"No assigned room found for {student_id}."
                )

            monthly_rent = self.get_value(
                room,
                "effective_monthly_rent",
                self.get_value(room, "monthly_rent")
            )

        if monthly_rent is None:
            raise ValueError(
                "Could not determine monthly room rent."
            )

        rent = self.calculate_rent(
            monthly_rent=monthly_rent,
            month=month,
            joining_date=joining_date,
            vacating_date=vacating_date,
            room_change_rent=room_change_rent
        )

        # Temporary vacancy rules:
        # 30 to 90 days: retain bed at 50% rent.
        # More than 90 days: bed released, no rent.
        if temporary_vacancy_days > 90:
            rent = self.money(0)

        elif temporary_vacancy_days >= 30:
            rent = self.money(rent * Decimal("0.50"))

        # Determine active days in the billing month.
        month_start, month_end = self.get_month_dates(month)

        joining_date = self.parse_date(joining_date)

        active_start = max(month_start, joining_date)
        active_end = month_end

        if vacating_date is not None:
            vacating_date = self.parse_date(vacating_date)
            active_end = min(active_end, vacating_date)

        if active_end < active_start:
            active_days = 0
        else:
            active_days = (
                active_end - active_start
            ).days + 1

        # Determine valid leave rebate days.
        rebate_days = self.calculate_rebate(
            student_id=student_id,
            semester_id=semester_id,
            month=month,
            semester_start_date=semester_start_date
        )

        rebate_days = min(rebate_days, active_days)

        # Temporary vacancy means no mess billing.
        if temporary_vacancy_days >= 30:
            mess_days_billed = 0
            rebate_days = 0
        else:
            mess_days_billed = max(
                0,
                active_days - rebate_days
            )

        mess_rate = self.calculate_mess_rate(student_id)

        mess_amount = self.money(
            mess_rate * mess_days_billed
        )

        # Guest meals are capped at 10 per month.
        billable_guest_meals = min(
            guest_meals,
            self.MAX_GUEST_MEALS
        )

        guest_amount = self.money(
            self.GUEST_MEAL_RATE * billable_guest_meals
        )

        extras_amount = self.money(extras_amount)

        flags = []

        if attendance_days == 0 and rebate_days == 0:
            flags.append("NO_ATTENDANCE")

        # Penalty is calculated as of the supplied date.
        if as_of_date is None:
            as_of_date = month_end

        penalty = self.calculate_late_penalty(
            month,
            as_of_date
        )

        total = self.money(
            rent
            + mess_amount
            + guest_amount
            + extras_amount
            + penalty
        )

        bill = {
            "student_id": student_id,
            "month": month,
            "rent": self.money(rent),
            "mess_days_billed": mess_days_billed,
            "mess_rate": self.money(mess_rate),
            "mess_amount": self.money(mess_amount),
            "rebate_days": rebate_days,
            "rebate_amount": self.money(
                mess_rate * rebate_days
            ),
            "guest_meals": billable_guest_meals,
            "extras_amount": extras_amount,
            "penalty": self.money(penalty),
            "total": total,
            "flags": ";".join(flags)
        }

        self.bills[(student_id, month)] = bill

        return bill

    # --------------------------------------------------
    # PAYMENT PROCESSING
    # --------------------------------------------------

    def record_payment(
        self,
        student_id,
        month,
        amount,
        paid_at=None
    ):
        key = (student_id, month)

        if key not in self.bills:
            raise ValueError(
                f"No bill found for {student_id}, {month}."
            )

        if paid_at is None:
            paid_at = date.today()
        else:
            paid_at = self.parse_date(paid_at)

        bill = self.bills[key]

        # Recalculate penalty as of payment date.
        penalty = self.calculate_late_penalty(
            month,
            paid_at
        )

        base_total = (
            bill["total"] - bill["penalty"]
        )

        current_total = self.money(
            base_total + penalty
        )

        bill["penalty"] = self.money(penalty)
        bill["total"] = current_total

        if isinstance(amount, str) and amount.upper() == "FULL":
            payment_amount = current_total
        else:
            payment_amount = self.money(amount)

        if payment_amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        self.payments.setdefault(key, Decimal("0.00"))

        self.payments[key] += payment_amount

        return self.get_outstanding(
            student_id,
            month,
            paid_at
        )

    # --------------------------------------------------
    # OUTSTANDING DUES
    # --------------------------------------------------

    def get_outstanding(
        self,
        student_id,
        month,
        as_of_date=None
    ):
        key = (student_id, month)

        if key not in self.bills:
            return self.money(0)

        bill = self.bills[key]

        if as_of_date is None:
            total = bill["total"]
        else:
            penalty = self.calculate_late_penalty(
                month,
                as_of_date
            )

            base_total = (
                bill["total"] - bill["penalty"]
            )

            total = self.money(base_total + penalty)

        paid = self.payments.get(
            key,
            Decimal("0.00")
        )

        return max(
            self.money(0),
            self.money(total - paid)
        )

    def get_dues(self, student_id, as_of_date=None):
        total_due = Decimal("0.00")

        for (bill_student_id, month) in self.bills:
            if bill_student_id != student_id:
                continue

            total_due += self.get_outstanding(
                student_id,
                month,
                as_of_date
            )

        return self.money(total_due)

    # --------------------------------------------------
    # HOLD STATUS
    # --------------------------------------------------

    def update_hold_status(self, student_id, as_of_date=None):
        student_months = []

        for bill_student_id, month in self.bills:
            if bill_student_id == student_id:
                student_months.append(month)

        student_months.sort()

        consecutive_high_months = 0
        previous_month = None
        hold = False

        for month in student_months:
            outstanding = self.get_outstanding(
                student_id,
                month,
                as_of_date
            )

            year, month_number = map(
                int,
                month.split("-")
            )

            current_index = year * 12 + month_number

            if outstanding > Decimal("5000.00"):
                if (
                    previous_month is not None
                    and current_index == previous_month + 1
                ):
                    consecutive_high_months += 1
                else:
                    consecutive_high_months = 1
            else:
                consecutive_high_months = 0

            if consecutive_high_months >= 2:
                hold = True

            previous_month = current_index

        self.hold_status[student_id] = hold

        return hold

    # --------------------------------------------------
    # BILL RETRIEVAL
    # --------------------------------------------------

    def get_bill(self, student_id, month):
        return self.bills.get((student_id, month))

    def get_all_bills(self):
        return list(self.bills.values())
