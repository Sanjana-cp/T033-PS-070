from datetime import datetime
from pathlib import Path

import pytest

from csv_io.csv_reader import load_inputs
from engines.allotment_engine import AllotmentEngine
from models.allotment import Allotment
from models.hostel import Hostel
from models.room import Room
from models.student import Student


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA = ROOT / "T033-PS-070-sample-data"


@pytest.fixture
def sample_system():
    data = load_inputs(SAMPLE_DATA)

    hostels = {
        row["hostel_id"]: Hostel(**row)
        for row in data["hostels"]
    }
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

    allotment_engine = AllotmentEngine(students, hostels)
    applicants = [
        Allotment(
            student_id=student.student_id,
            application_timestamp=student.application_ts,
        )
        for student in students.values()
    ]
    allotment_engine.run_allotment(
        applicants, datetime(2026, 7, 20, 10, 0)
    )

    return {
        "data": data,
        "hostels": hostels,
        "students": students,
        "allotment_engine": allotment_engine,
    }