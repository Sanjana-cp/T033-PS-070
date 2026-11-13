
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Allotment:
    student_id: str
    application_timestamp: datetime

    priority_score: float = 0.0
    assigned_hostel_id: Optional[str] = None
    assigned_room_id: Optional[str] = None
    assigned_room_type: Optional[str] = None

    status: str = "PENDING"
    flags: List[str] = field(default_factory=list)
    waitlist_position: Optional[int] = None
    deposit_paid_at: Optional[datetime] = None

    def __post_init__(self):
        valid_statuses = {
            "PENDING",
            "ALLOTTED",
            "WAITLISTED",
            "FORFEITED",
            "INELIGIBLE"
        }

        if not self.student_id:
            raise ValueError("Student ID cannot be empty.")

        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid allotment status: {self.status}"
            )

    def add_flag(self, flag: str):
        if flag and flag not in self.flags:
            self.flags.append(flag)

    def assign_room(
        self,
        room_id: str,
        hostel_id: Optional[str] = None,
        room_type: Optional[str] = None
    ):
        if not room_id:
            raise ValueError("Room ID cannot be empty.")

        self.assigned_room_id = room_id
        self.assigned_hostel_id = hostel_id
        self.assigned_room_type = room_type
        self.status = "ALLOTTED"
        self.waitlist_position = None

    def add_to_waitlist(self, position: int):
        if position < 1:
            raise ValueError("Waitlist position must be positive.")

        self.assigned_hostel_id = None
        self.assigned_room_id = None
        self.assigned_room_type = None
        self.status = "WAITLISTED"
        self.waitlist_position = position

    def mark_forfeited(self):
        self.status = "FORFEITED"

    def mark_ineligible(self):
        self.status = "INELIGIBLE"

    def record_deposit(self, paid_at: datetime):
        self.deposit_paid_at = paid_at
