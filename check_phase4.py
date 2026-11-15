from datetime import date, datetime

from csv_io.csv_reader import load_inputs
from engines.allotment_engine import AllotmentEngine
from engines.room_lifecycle_engine import RoomLifecycleEngine
from models.allotment import Allotment
from models.hostel import Hostel
from models.room import Room
from models.student import Student


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