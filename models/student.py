
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Student:
    student_id: str
    student_name: str
    gender: str
    year: int
    cgpa: float
    category: str
    international: bool
    home_distance_km: float
    disability: bool
    preferences: List[str]
    mess_plan: str
    mixed_year_consent: bool
    application_ts: datetime

    def __post_init__(self):

        if not self.student_id:
            raise ValueError("Student ID cannot be empty.")

        if not self.student_name:
            raise ValueError("Student name cannot be empty.")

        if self.gender not in {"M", "F"}:
            raise ValueError("Gender must be M or F.")

        if self.year not in {1, 2, 3, 4}:
            raise ValueError("Student year must be between 1 and 4.")

        if not 0 <= self.cgpa <= 10:
            raise ValueError("CGPA must be between 0 and 10.")

        if self.home_distance_km < 0:
            raise ValueError("Home distance cannot be negative.")

        if self.category not in {"GEN", "OBC", "SC", "ST"}:
            raise ValueError("Invalid student category.")

        if self.mess_plan not in {"VEG", "NONVEG"}:
            raise ValueError("Mess plan must be VEG or NONVEG.")

        if len(self.preferences) > 3:
            raise ValueError("Maximum 3 room preferences allowed.")

        valid_room_types = {
            "SINGLE",
            "SINGLE_AC",
            "DOUBLE",
            "TRIPLE"
        }

        for room_type in self.preferences:
            if room_type not in valid_room_types:
                raise ValueError(
                    f"Invalid room preference: {room_type}"
                )
