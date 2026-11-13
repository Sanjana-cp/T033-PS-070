
from decimal import Decimal
from typing import Dict

from models.student import Student
from models.hostel import Hostel


class ManagementEngine:

    def __init__(self):
        self.students: Dict[str, Student] = {}
        self.hostels: Dict[str, Hostel] = {}

        self.mess_rate_card: Dict[str, Decimal] = {
            "VEG": Decimal("150.00"),
            "NONVEG": Decimal("180.00")
        }

        self.guest_meal_rate = Decimal("80.00")

        self.extras_rate_card: Dict[str, Decimal] = {
            "EGG_CURRY": Decimal("35.00"),
            "CHICKEN_CURRY": Decimal("90.00"),
            "FRESH_JUICE": Decimal("30.00"),
            "CURD_CUP": Decimal("15.00"),
            "SPECIAL_DINNER": Decimal("120.00")
        }

    def register_student(self, student: Student):
        if student.student_id in self.students:
            raise ValueError(
                f"Student {student.student_id} is already registered."
            )

        self.students[student.student_id] = student

    def register_hostel(self, hostel: Hostel):
        if hostel.hostel_id in self.hostels:
            raise ValueError(
                f"Hostel {hostel.hostel_id} is already registered."
            )

        self.hostels[hostel.hostel_id] = hostel

    def register_rate_card(self, rates: Dict[str, Decimal]):
        required_codes = {
            "VEG_DAY",
            "NONVEG_DAY",
            "GUEST_MEAL",
            "EGG_CURRY",
            "CHICKEN_CURRY",
            "FRESH_JUICE",
            "CURD_CUP",
            "SPECIAL_DINNER"
        }

        if set(rates) != required_codes:
            raise ValueError(
                "Rate card must contain exactly the required item codes."
            )

        if any(price < 0 for price in rates.values()):
            raise ValueError("Rate card prices cannot be negative.")

        self.mess_rate_card = {
            "VEG": rates["VEG_DAY"],
            "NONVEG": rates["NONVEG_DAY"]
        }

        self.guest_meal_rate = rates["GUEST_MEAL"]

        self.extras_rate_card = {
            code: price
            for code, price in rates.items()
            if code not in {
                "VEG_DAY",
                "NONVEG_DAY",
                "GUEST_MEAL"
            }
        }
    def validate_all_hostel_capacities(self):
        for hostel in self.hostels.values():
            hostel.validate_bed_capacity()
            