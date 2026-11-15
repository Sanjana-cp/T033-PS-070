from datetime import date, datetime

from models.allotment import Allotment


def build_initial_handlers(
    allotment_engine, students, reporting, dependent_engines=()
):
    def run_allotment(fields):
        if len(fields) != 1:
            raise ValueError("RUN_ALLOTMENT expects one timestamp.")

        published_at = datetime.strptime(fields[0], "%Y-%m-%d %H:%M:%S")
        applicants = [
            Allotment(
                student_id=student.student_id,
                application_timestamp=student.application_ts,
            )
            for student in students.values()
        ]
        allotment_engine.run_allotment(applicants, published_at)

        for dependent_engine in dependent_engines:
            dependent_engine.allotments = allotment_engine.allotments

    def print_allotment(fields):
        if fields:
            raise ValueError("PRINT_ALLOTMENT takes no arguments.")
        reporting.record_allotment(
            allotment_engine.get_allotment_records()
        )

    def pay_deposit(fields):
        if len(fields) != 2:
            raise ValueError(
                "PAY_DEPOSIT expects student ID and timestamp."
            )
        paid_at = datetime.strptime(fields[1], "%Y-%m-%d %H:%M:%S")
        allotment_engine.process_deposit_payment(fields[0], paid_at)

    return {
        "RUN_ALLOTMENT": run_allotment,
        "PRINT_ALLOTMENT": print_allotment,
        "PAY_DEPOSIT": pay_deposit,
    }


def build_billing_handlers(billing_engine, reporting):
    def payment(fields):
        if len(fields) != 4:
            raise ValueError(
                "PAYMENT expects student ID, month, timestamp, and amount."
            )
        paid_at = datetime.strptime(fields[2], "%Y-%m-%d %H:%M:%S")
        billing_engine.record_payment(
            fields[0], fields[1], fields[3], paid_at
        )

    def print_bill(fields):
        if len(fields) != 2:
            raise ValueError("PRINT_BILL expects student ID and month.")
        bill = billing_engine.get_bill(fields[0], fields[1])
        if bill is None:
            raise ValueError("No bill exists for that student and month.")
        reporting.record_bill(bill)

    return {
        "PAYMENT": payment,
        "PRINT_BILL": print_bill,
    }


def build_lifecycle_handlers(lifecycle_engine, billing_engine, reporting):
    def parse_day(value):
        return date.fromisoformat(value)

    def join(fields):
        if len(fields) != 2:
            raise ValueError("JOIN expects student ID and date.")
        lifecycle_engine.record_join(fields[0], parse_day(fields[1]))

    def room_change(fields):
        if len(fields) != 3:
            raise ValueError(
                "ROOM_CHANGE expects student ID, room type, and timestamp."
            )
        student_id = fields[0]
        changed_at = datetime.strptime(fields[2], "%Y-%m-%d %H:%M:%S")
        semester_id = (
            f"{changed_at.year}-SPRING"
            if changed_at.month <= 6
            else f"{changed_at.year}-FALL"
        )
        lifecycle_engine.change_room(
            student_id,
            fields[1],
            semester_id,
            changed_at.date(),
            outstanding_dues=float(
                billing_engine.get_dues(student_id, changed_at.date())
            ),
            hold=billing_engine.update_hold_status(
                student_id, changed_at.date()
            ),
        )

    def swap(fields):
        if len(fields) != 4:
            raise ValueError(
                "SWAP expects two student IDs, timestamp, and agreement."
            )
        swap_date = datetime.strptime(fields[2], "%Y-%m-%d %H:%M:%S").date()
        lifecycle_engine.swap_rooms(
            fields[0],
            fields[1],
            swap_date,
            agree_rent_difference=fields[3].strip().lower() == "true",
        )

    def temporary_vacate(fields):
        if len(fields) != 4:
            raise ValueError(
                "TEMP_VACATE expects student ID, start date, end date, and reason."
            )
        lifecycle_engine.temporary_vacate(
            fields[0],
            parse_day(fields[1]),
            parse_day(fields[2]),
            fields[3],
        )

    def return_from_vacate(fields):
        if len(fields) != 2:
            raise ValueError("RETURN expects student ID and date.")
        lifecycle_engine.return_from_temporary_vacate(
            fields[0], parse_day(fields[1])
        )

    def inspection(fields):
        if len(fields) != 4:
            raise ValueError(
                "INSPECTION expects student ID, date, damages, and reason."
            )

        student_id = fields[0]
        inspection = lifecycle_engine.record_inspection(
            student_id,
            parse_day(fields[1]),
            float(fields[2]),
            fields[3],
        )

        for settlement in reporting.settlements:
            if settlement["student_id"] == student_id:
                settlement["damages"] = inspection["damage_charges"]
                balance = (
                    settlement["deposit"]
                    - settlement["unpaid_dues"]
                    - settlement["damages"]
                    - settlement["notice_forfeit"]
                )
                settlement["refund"] = round(max(balance, 0), 2)
                settlement["recoverable"] = round(max(-balance, 0), 2)
                break
    def vacate(fields):
        if len(fields) != 3:
            raise ValueError(
                "VACATE expects student ID, vacate date, and notice date."
            )

        student_id = fields[0]
        vacate_date = parse_day(fields[1])
        notice_date = parse_day(fields[2])
        room = lifecycle_engine.get_student_room(student_id)

        if room is None:
            raise ValueError("Student has no active room.")

        deposit = float(room.effective_monthly_rent) * 2
        if room.ac:
            deposit += 5000.0

        inspection_record = lifecycle_engine.inspections.get(student_id, {})
        damages = float(inspection_record.get("damage_charges", 0))
        dues = float(billing_engine.get_dues(student_id, vacate_date))

        settlement = lifecycle_engine.permanent_vacate(
            student_id,
            vacate_date,
            notice_date,
            deposit,
            dues,
            damages,
        )
        reporting.record_settlement({
            "student_id": settlement["student_id"],
            "vacate_date": settlement["vacate_date"],
            "deposit": settlement["deposit"],
            "unpaid_dues": settlement["unpaid_dues"],
            "damages": settlement["damages"],
            "notice_forfeit": settlement["notice_forfeit"],
            "refund": settlement["refund"],
            "recoverable": settlement["recoverable"],
        })

    return {
        "JOIN": join,
        "ROOM_CHANGE": room_change,
        "SWAP": swap,
        "TEMP_VACATE": temporary_vacate,
        "RETURN": return_from_vacate,
        "INSPECTION": inspection,
        "VACATE": vacate,
    }


def build_generate_bills_handler(
    billing_engine, students, data, lifecycle_engine, reporting
):
    rates = {
        row["item_code"]: row["price"]
        for row in data["mess_rate_card"]
    }
    attendance = {
        (row["student_id"], row["month"]): row["days_present"]
        for row in data["mess_attendance_monthly"]
    }

    def generate_bills(fields):
        if len(fields) != 1:
            raise ValueError("GENERATE_BILLS expects a YYYY-MM month.")

        month = fields[0]
        month_start, month_end = billing_engine.get_month_dates(month)
        semester_id = (
            f"{month_start.year}-SPRING"
            if month_start.month <= 6
            else f"{month_start.year}-FALL"
        )
        semester_start = (
            date(month_start.year, 1, 1)
            if semester_id.endswith("SPRING")
            else date(month_start.year, 8, 1)
        )

        extras = {}
        for row in data["mess_extras"]:
            if row["date"].strftime("%Y-%m") != month:
                continue

            item = extras.setdefault(
                row["student_id"], {"guests": 0, "amount": 0}
            )
            if row["item_code"] == "GUEST_MEAL":
                item["guests"] += row["quantity"]
            else:
                item["amount"] += rates[row["item_code"]] * row["quantity"]

        for student_id in students:
            room = billing_engine.get_student_room(student_id)
            if room is None:
                continue

            join_date = lifecycle_engine.join_dates.get(
                student_id, date(2026, 8, 1)
            )

            vacancy = lifecycle_engine.temporary_vacancies.get(student_id)
            vacancy_days = 0
            if vacancy and (
                vacancy["from_date"] <= month_end
                and vacancy["to_date"] >= month_start
            ):
                vacancy_days = vacancy["duration"]

            matching_changes = [
                record
                for record in lifecycle_engine.lifecycle_records
                if record.get("event") == "ROOM_CHANGE"
                and record.get("student_id") == student_id
                and record["date"].strftime("%Y-%m") == month
            ]
            room_change_rent = (
                matching_changes[-1]["billing_rent"]
                if matching_changes
                else None
            )

            extra = extras.get(
                student_id, {"guests": 0, "amount": 0}
            )
            bill = billing_engine.generate_bill(
                student_id=student_id,
                month=month,
                joining_date=join_date,
                attendance_days=attendance.get((student_id, month), 0),
                semester_id=semester_id,
                guest_meals=extra["guests"],
                extras_amount=extra["amount"],
                room_change_rent=room_change_rent,
                temporary_vacancy_days=vacancy_days,
                semester_start_date=semester_start,
                monthly_rent=room.effective_monthly_rent,
            )
            reporting.record_bill(bill)

    return generate_bills

class CommandProcessor:
    def __init__(self, handlers):
        self.handlers = handlers
        self.rejections = []

    def process_file(self, path):
        with open(path, "r", encoding="utf-8-sig") as command_file:
            for line_number, raw_line in enumerate(command_file, start=1):
                line = raw_line.strip()

                if not line or line.startswith("#"):
                    continue

                command, separator, arguments = line.partition("|")
                fields = arguments.split("|") if separator else []

                handler = self.handlers.get(command)
                if handler is None:
                    raise ValueError(
                        f"Unknown command {command!r} on line {line_number}."
                    )

                try:
                    handler(fields)
                except ValueError as error:
                    self.rejections.append(
                        f"Line {line_number}: {line} - {error}"
                    )
                except Exception as error:
                    raise ValueError(
                        f"Command failed on line {line_number}: {line}"
                    ) from error
                
        

