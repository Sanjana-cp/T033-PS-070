
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from models.room import Room


@dataclass
class Hostel:
    hostel_id: str
    hostel_name: str
    gender: str
    total_beds: int

    rooms: List["Room"] = field(default_factory=list)

    def __post_init__(self):
        if not self.hostel_id:
            raise ValueError("Hostel ID cannot be empty.")

        if not self.hostel_name:
            raise ValueError("Hostel name cannot be empty.")

        if self.gender not in {"M", "F"}:
            raise ValueError("Hostel gender must be M or F.")

        if self.total_beds < 0:
            raise ValueError("Total beds cannot be negative.")

    def add_room(self, room: "Room"):
        if room.hostel_id != self.hostel_id:
            raise ValueError(
                "Room does not belong to this hostel."
            )

        if any(existing.room_id == room.room_id for existing in self.rooms):
            raise ValueError(
                f"Room {room.room_id} already exists."
            )

        self.rooms.append(room)

    def get_room_count(self) -> int:
        return len(self.rooms)

    def get_total_beds(self) -> int:
        return sum(room.capacity for room in self.rooms)
    def validate_bed_capacity(self):
        actual_beds = self.get_total_beds()

        if actual_beds != self.total_beds:
            raise ValueError(
                f"Hostel {self.hostel_id}: "
                f"declared {self.total_beds} beds, "
                f"but rooms contain {actual_beds} beds."
            )