from datetime import datetime

from csv_io.csv_reader import load_inputs
from engines.allotment_engine import AllotmentEngine
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
    Allotment(student_id=student.student_id,
              application_timestamp=student.application_ts)
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
        f"hostel={result.assigned_hostel_id}",
        f"room={result.assigned_room_id}",
        f"flags={result.flags}",
    )

late_allotment = next(
    item for item in results
    if item.status == "ALLOTTED" and item.assigned_room_id
)
room = next(
    room
    for hostel in hostels.values()
    for room in hostel.rooms
    if room.room_id == late_allotment.assigned_room_id
)
occupants_before = set(room.occupants)

outcome = engine.process_deposit_payment(
    late_allotment.student_id,
    datetime(2026, 7, 28, 0, 1),
)

promoted_students = set(room.occupants) - occupants_before

print("Late payment outcome:", outcome)
print("Forfeited allotment status:", late_allotment.status)
print("Promoted into released room:", sorted(promoted_students))

on_time_allotment = next(
    item for item in results
    if item.status == "ALLOTTED" and item.deposit_paid_at is None
)

print(
    "On-time payment outcome:",
    engine.process_deposit_payment(
        on_time_allotment.student_id,
        datetime(2026, 7, 27, 23, 59, 59),
    ),
)