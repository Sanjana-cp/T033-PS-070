from datetime import date, datetime

from csv_io.csv_reader import load_inputs
from engines.allotment_engine import AllotmentEngine
from engines.room_lifecycle_engine import RoomLifecycleEngine
from models.allotment import Allotment
from models.hostel import Hostel
from models.room import Room
from models.student import Student
from engines.billing_engine import BillingEngine
from decimal import Decimal


data = load_inputs("T033-PS-070-sample-data")

hostels = {row["hostel_id"]: Hostel(**row) for row in data["hostels"]}
for row in data["rooms"]:
    hostels[row["hostel_id"]].add_room(Room(**row))

students = {}
for row in data["applicants"]:
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

applicants = [
    Allotment(
        student_id=student.student_id,
        application_timestamp=student.application_ts,
    )
    for student in students.values()
]

engine = AllotmentEngine(students, hostels)
results = engine.run_allotment(applicants, datetime(2026, 7, 20, 10, 0))

billing = BillingEngine(
    students,
    {
        room.room_id: room
        for hostel in hostels.values()
        for room in hostel.rooms
    },
    engine.allotments,
    leave_applications=data["leave_applications"],
    semester_start_dates={"2026-FALL": date(2026, 8, 1)},
)

print(
    "STU-0317 November rebate days:",
    billing.calculate_rebate(
        "STU-0317", "2026-FALL", "2026-11", date(2026, 8, 1)
    ),
)
print(
    "STU-0466 September rebate days:",
    billing.calculate_rebate(
        "STU-0466", "2026-FALL", "2026-09", date(2026, 8, 1)
    ),
)
print(
    "STU-0341 penalty:",
    billing.calculate_late_penalty("2026-09", date(2026, 11, 9)),
)

attendance = {
    (row["student_id"], row["month"]): row["days_present"]
    for row in data["mess_attendance_monthly"]
}
guest_meals = sum(
    row["quantity"]
    for row in data["mess_extras"]
    if row["student_id"] == "STU-0010"
    and row["date"].strftime("%Y-%m") == "2026-10"
    and row["item_code"] == "GUEST_MEAL"
)

room_0010 = billing.get_student_room("STU-0010")
bill_0010 = billing.generate_bill(
    "STU-0010",
    "2026-10",
    date(2026, 8, 1),
    attendance.get(("STU-0010", "2026-10"), 0),
    semester_id="2026-FALL",
    guest_meals=guest_meals,
    semester_start_date=date(2026, 8, 1),
    monthly_rent=room_0010.effective_monthly_rent,
)
print("STU-0010 guest meals billed:", bill_0010["guest_meals"])

room_0622 = billing.get_student_room("STU-0622")
bill_0622 = billing.generate_bill(
    "STU-0622",
    "2026-10",
    date(2026, 8, 1),
    attendance.get(("STU-0622", "2026-10"), 0),
    semester_id="2026-FALL",
    semester_start_date=date(2026, 8, 1),
    monthly_rent=room_0622.effective_monthly_rent,
)
print("STU-0622 flags:", bill_0622["flags"])

print(
    "STU-0317 semester rebate days:",
    len(
        billing.get_eligible_rebate_dates(
            "STU-0317",
            "2026-FALL",
            date(2026, 8, 1),
        )
    ),
)

print(
    "Join on 15th rent:",
    billing.calculate_rent(
        6000, "2026-08", date(2026, 8, 15)
    ),
)
print(
    "Join on 16th rent:",
    billing.calculate_rent(
        6000, "2026-08", date(2026, 8, 16)
    ),
)

ac_room = next(
    room
    for hostel in hostels.values()
    for room in hostel.rooms
    if room.ac
)
print(
    "AC rent multiplier:",
    ac_room.effective_monthly_rent
    == ac_room.monthly_rent * Decimal("1.5"),
)

billing.bills[("STU-0212", "2026-08")] = {
    "total": Decimal("6000.00"),
    "penalty": Decimal("0.00"),
}
billing.bills[("STU-0212", "2026-09")] = {
    "total": Decimal("6000.00"),
    "penalty": Decimal("0.00"),
}
print(
    "Two-month HOLD:",
    billing.update_hold_status("STU-0212", date(2026, 10, 10)),
)

for student_id in ("STU-0553", "STU-0300", "STU-0377", "STU-0631"):
    student = students[student_id]
    result = next(item for item in results if item.student_id == student_id)
    print(
        student_id,
        f"score={engine.calculate_priority(student):.2f}",
        f"status={result.status}",
        f"room={result.assigned_room_id}",
        f"flags={result.flags}",
    )

lifecycle = RoomLifecycleEngine(students, hostels, engine.allotments)

print("JOIN 15th:", lifecycle.record_join("STU-0586", date(2026, 8, 15)))
print("JOIN 16th:", lifecycle.record_join("STU-0293", date(2026, 8, 16)))

vacancy = lifecycle.temporary_vacate(
    "STU-0563",
    date(2026, 9, 1),
    date(2026, 11, 29),
    "INTERNSHIP",
)
print(
    "90-day vacancy:",
    vacancy["duration"],
    vacancy["bed_released"],
    vacancy["rent_percentage"],
    vacancy["mess_suspended"],
)

swap = lifecycle.swap_rooms(
    "STU-0090",
    "STU-0047",
    date(2026, 10, 1),
    agree_rent_difference=True,
    student1_consent=True,
    student2_consent=True,
)
print("Swap:", swap["event"], swap["billing_rent"])

try:
    lifecycle.change_room(
        "STU-0212",
        "DOUBLE",
        "2026-FALL",
        date(2026, 10, 20),
        outstanding_dues=0,
        hold=True,
    )
except ValueError as error:
    print("STU-0212 blocked:", error)

inspection = lifecycle.record_inspection(
    "STU-0048",
    date(2026, 11, 28),
    1850,
    "Broken cupboard door",
)
print("Inspection damage:", inspection["damage_charges"])

settlement = lifecycle.permanent_vacate(
    "STU-0048",
    date(2026, 11, 28),
    date(2026, 11, 25),
    deposit_amount=10000,
    unpaid_dues=0,
    damage_charges=lifecycle.inspections["STU-0048"]["damage_charges"],
)
print("Settlement damages:", settlement["damages"])

late_allotment = next(
    item for item in results
    if item.status == "ALLOTTED" and item.assigned_room_id
)
released_room = next(
    room
    for hostel in hostels.values()
    for room in hostel.rooms
    if room.room_id == late_allotment.assigned_room_id
)
occupants_before = set(released_room.occupants)

late_outcome = engine.process_deposit_payment(
    late_allotment.student_id,
    datetime(2026, 7, 28, 0, 1),
)
promoted = set(released_room.occupants) - occupants_before

print("Late deposit:", late_outcome)
print("Promoted:", sorted(promoted))