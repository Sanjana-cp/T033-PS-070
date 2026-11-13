
from dataclasses import dataclass, field
from typing import List


@dataclass
class Room:
    room_id: str
    hostel_id: str
    block: str
    floor: int
    room_type: str
    beds: int
    ac: bool
    monthly_rent: float

    reserved_for: List[str] = field(default_factory=list)
    occupants: List[str] = field(default_factory=list)

    def __post_init__(self):
        valid_capacities = {
            "SINGLE": 1,
            "DOUBLE": 2,
            "TRIPLE": 3
        }

        if self.room_type not in valid_capacities:
            raise ValueError(
                f"Invalid room type: {self.room_type}"
            )

        if self.beds != valid_capacities[self.room_type]:
            raise ValueError(
                "Room beds do not match the room type."
            )

        if self.floor < 0:
            raise ValueError("Floor cannot be negative.")

        if self.monthly_rent < 0:
            raise ValueError("Monthly rent cannot be negative.")

        if len(self.occupants) > self.capacity:
            raise ValueError(
                "Initial occupants cannot exceed room capacity."
            )

        if len(self.occupants) != len(set(self.occupants)):
            raise ValueError(
                "Duplicate students cannot occupy the same room."
            )

    @property
    def capacity(self) -> int:
        return self.beds

    @property
    def effective_monthly_rent(self) -> float:
        if self.ac:
            return self.monthly_rent * 1.5

        return self.monthly_rent

    def get_available_beds(self) -> int:
        return self.capacity - len(self.occupants)

    def is_full(self) -> bool:
        return len(self.occupants) >= self.capacity

    def add_occupant(self, student_id: str):
        if self.is_full():
            raise ValueError("Room is already full.")

        if student_id in self.occupants:
            raise ValueError("Student is already in this room.")

        self.occupants.append(student_id)

    def remove_occupant(self, student_id: str):
        if student_id not in self.occupants:
            raise ValueError("Student is not in this room.")

        self.occupants.remove(student_id)
