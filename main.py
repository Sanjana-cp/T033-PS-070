from datetime import date
from decimal import Decimal
from pathlib import Path

from command_processor import (
    CommandProcessor,
    build_billing_handlers,
    build_generate_bills_handler,
    build_initial_handlers,
    build_lifecycle_handlers,
)
from csv_io.csv_reader import load_inputs
from engines.allotment_engine import AllotmentEngine
from engines.billing_engine import BillingEngine
from engines.management_engine import ManagementEngine
from engines.room_lifecycle_engine import RoomLifecycleEngine
from models.hostel import Hostel
from models.room import Room
from models.student import Student
from reporting_engine import ReportingEngine


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "T033-PS-070-sample-data"
COMMAND_FILE = DATA_DIR / "commands.txt"


def build_students(rows):
    students = {}
    for row in rows:
        student = Student(
            student_id=row["student_id"],
            student_name=row["student_name"],
            gender=row["gender"],
            year=row["year"],
            cgpa=row["cgpa"],
            category=row["category"],
            international=row["international"],
            home_distance_km=row["home_distance_km"],
            disability=row["disability"],
            preferences=row["preferences"],
            mess_plan=row["mess_plan"],
            mixed_year_consent=row["mixed_year_consent"],
            application_ts=row["application_ts"],
        )
        students[student.student_id] = student
    return students


def build_report_handlers(billing, lifecycle, management, reporting):
    def print_dues(fields):
        if len(fields) != 1:
            raise ValueError("PRINT_DUES expects a date.")

        as_of_date = date.fromisoformat(fields[0])
        rows = []

        for student_id in management.students:
            months_over_5000 = sum(
                billing.get_outstanding(student_id, month, as_of_date)
                > Decimal("5000.00")
                for bill_student_id, month in billing.bills
                if bill_student_id == student_id
            )
            rows.append({
                "as_of_date": as_of_date,
                "student_id": student_id,
                "outstanding": billing.get_dues(student_id, as_of_date),
                "months_over_5000": months_over_5000,
                "hold": billing.update_hold_status(student_id, as_of_date),
            })

        reporting.record_dues(rows)

    def print_occupancy(fields):
        if len(fields) != 1:
            raise ValueError("PRINT_OCCUPANCY expects a date.")

        report_date = date.fromisoformat(fields[0])
        rows = []

        for hostel in management.hostels.values():
            beds = sum(room.capacity for room in hostel.rooms)
            hostel_room_ids = {room.room_id for room in hostel.rooms}
            temporary_ids = {
                student_id
                for student_id, record in lifecycle.temporary_vacancies.items()
                if not record["bed_released"]
                and record["from_date"] <= report_date <= record["to_date"]
                and record["room_id"] in hostel_room_ids
            }
            occupants = {
                student_id
                for room in hostel.rooms
                for student_id in room.occupants
            }
            temporarily_vacant = len(temporary_ids & occupants)
            occupied = len(occupants) - temporarily_vacant

            rows.append({
                "date": report_date,
                "hostel_id": hostel.hostel_id,
                "beds": beds,
                "occupied": occupied,
                "temporarily_vacant": temporarily_vacant,
                "vacant": beds - occupied - temporarily_vacant,
            })

        reporting.record_occupancy(rows)

    return {
        "PRINT_DUES": print_dues,
        "PRINT_OCCUPANCY": print_occupancy,
    }


def main():
    data = load_inputs(DATA_DIR)
    management = ManagementEngine()

    for row in data["hostels"]:
        management.register_hostel(Hostel(**row))

    for row in data["rooms"]:
        management.register_room(Room(**row))

    management.students = build_students(data["applicants"])
    management.register_rate_card({
        row["item_code"]: row["price"]
        for row in data["mess_rate_card"]
    })

    allotment = AllotmentEngine(management.students, management.hostels)
    rooms = {
        room.room_id: room
        for hostel in management.hostels.values()
        for room in hostel.rooms
    }

    billing = BillingEngine(
        management.students,
        rooms,
        allotment.allotments,
        leave_applications=data["leave_applications"],
        semester_start_dates={"2026-FALL": date(2026, 8, 1)},
    )
    lifecycle = RoomLifecycleEngine(
        management.students,
        management.hostels,
        allotment.allotments,
    )
    reporting = ReportingEngine(ROOT / "data" / "output")

    handlers = {}
    handlers.update(
        build_initial_handlers(
            allotment,
            management.students,
            reporting,
            dependent_engines=(billing, lifecycle),
        )
    )
    handlers.update(build_billing_handlers(billing, reporting))
    handlers.update(build_lifecycle_handlers(lifecycle, billing, reporting))
    handlers.update(
        build_report_handlers(billing, lifecycle, management, reporting)
    )
    handlers["GENERATE_BILLS"] = build_generate_bills_handler(
        billing,
        management.students,
        data,
        lifecycle,
        reporting,
    )

    processor = CommandProcessor(handlers)
    processor.process_file(COMMAND_FILE)

    for rejection in processor.rejections:
        if "VACATE|" in rejection or "INSPECTION|" in rejection:
            print(rejection)

    reporting.write_outputs()


if __name__ == "__main__":
    main()