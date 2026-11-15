from pathlib import Path

from csv_io.csv_reader import load_inputs
from engines.management_engine import ManagementEngine
from models.hostel import Hostel
from models.room import Room
from models.student import Student


DATA_DIR = Path(__file__).parent / "T033-PS-070-sample-data"


def main():
    data = load_inputs(DATA_DIR)
    manager = ManagementEngine()

    for row in data["hostels"]:
        manager.register_hostel(Hostel(**row))

    for row in data["rooms"]:
        manager.register_room(Room(**row))

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
        manager.register_student(student)

    rates = {
        row["item_code"]: row["price"]
        for row in data["mess_rate_card"]
    }
    manager.register_rate_card(rates)
    manager.validate_all_hostel_capacities()

    print(f"Hostels: {len(manager.hostels)}")
    print(f"Rooms: {len(manager.rooms)}")
    print(f"Applicants: {len(manager.students)}")


if __name__ == "__main__":
    main()