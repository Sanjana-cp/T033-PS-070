
from typing import Dict, List
from datetime import datetime, time,timedelta

from models.student import Student
from models.hostel import Hostel
from models.allotment import Allotment


class AllotmentEngine:

    def __init__(
        self,
        students: Dict[str, Student],
        hostels: Dict[str, Hostel]
        
    ):
        self.students = students
        self.hostels = hostels
        self.allotments: Dict[str, Allotment] = {}
        self.reservations_released = False
        self.allotment_published_at = None
    
    def rank_applicants(self, applicants: List[Allotment]) -> List[Allotment]:
        return sorted(
            applicants,
            key=lambda allotment: (
                -self.calculate_priority(
                    self.students[allotment.student_id]
                ),
                -self.students[allotment.student_id].home_distance_km,
                allotment.application_timestamp
            )
        )

    def separate_applicants_by_eligibility(
        self,
        applicants: List[Allotment]
    ):
        regular_applicants = []
        local_applicants = []

        for allotment in applicants:
            student = self.students[allotment.student_id]

            if student.home_distance_km < 25:
                local_applicants.append(allotment)
            else:
                regular_applicants.append(allotment)

        return (
            self.rank_applicants(regular_applicants),
            self.rank_applicants(local_applicants)
        )

    def get_allocation_order(
        self,
        applicants: List[Allotment]
    ) -> List[Allotment]:

        regular_applicants, local_applicants = (
            self.separate_applicants_by_eligibility(applicants)
        )

        return regular_applicants + local_applicants

    
    def get_available_rooms(self, student: Student) -> List:
        available_rooms = []

        for hostel in self.hostels.values():
            if hostel.gender != student.gender:
                continue

            for room in hostel.rooms:
                if room.is_full():
                    continue

                if student.year == 1 and room.room_type == "SINGLE":
                    continue

                if student.disability and room.floor not in (0, 1):
                    continue

                # Check academic-year compatibility.
                if room.room_type in {"DOUBLE", "TRIPLE"}:
                    compatible = True

                    for occupant_id in room.occupants:
                        existing_student = self.students[occupant_id]

                        if existing_student.year != student.year:
                            if not (
                                student.mixed_year_consent
                                and existing_student.mixed_year_consent
                            ):
                                compatible = False
                                break

                    if not compatible:
                        continue

                available_rooms.append(room)

        return available_rooms

    def choose_room(self, student, allotment, available_rooms=None):
        if available_rooms is None:
            available_rooms = self.get_available_rooms(student)

        for preference in student.preferences:
            for room in available_rooms:
                if preference == "SINGLE_AC":
                    if room.room_type == "SINGLE" and room.ac:
                        return room

                elif preference == "SINGLE":
                    if room.room_type == "SINGLE" and not room.ac:
                        return room

                elif room.room_type == preference:
                    return room

        if available_rooms:
            cheapest_room = min(
                available_rooms,
                key=lambda room: room.effective_monthly_rent
            )

            allotment.add_flag("NO_PREFERENCE_MATCH")
            return cheapest_room

        return None

    def calculate_priority(self, student: Student) -> float:
        score = student.cgpa * 10
        score += student.year * 5

        if student.home_distance_km > 500:
            score += 10

        if student.disability:
            score += 20

        return score
    
    @staticmethod
    def calculate_reserved_beds(total_beds: int, percentage: float) -> int:
        from math import ceil

        if total_beds < 0:
            raise ValueError("Total beds cannot be negative.")

        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100.")

        return ceil(total_beds * percentage / 100)


    def get_hostel_reservation_quotas(self):
        quotas = {}

        for hostel in self.hostels.values():
            total_beds = hostel.total_beds

            quotas[hostel.hostel_id] = {
                "DISABILITY": self.calculate_reserved_beds(
                    total_beds, 5
                ),
                "INTERNATIONAL": self.calculate_reserved_beds(
                    total_beds, 10
                )
            }

        return quotas

    @staticmethod
    def get_student_reservation_categories(student: Student) -> List[str]:
        categories = []

        if student.disability:
            categories.append("DISABILITY")

        if student.international:
            categories.append("INTERNATIONAL")

        return categories

    @staticmethod
    def get_primary_reservation_category(student: Student):
        if student.disability:
            return "DISABILITY"

        if student.international:
            return "INTERNATIONAL"

        return None

    
    def get_reserved_bed_usage(self):
        usage = {}

        for hostel_id in self.hostels:
            usage[hostel_id] = {
                "DISABILITY": 0,
                "INTERNATIONAL": 0
            }

        for allotment in self.allotments.values():
            if allotment.status != "ALLOTTED":
                continue

            hostel_id = allotment.assigned_hostel_id

            if hostel_id not in usage:
                continue

            if "RESERVED_DISABILITY" in allotment.flags:
                usage[hostel_id]["DISABILITY"] += 1

            elif "RESERVED_INTERNATIONAL" in allotment.flags:
                usage[hostel_id]["INTERNATIONAL"] += 1

        return usage


    def get_remaining_reservations(self):
        quotas = self.get_hostel_reservation_quotas()
        usage = self.get_reserved_bed_usage()

        remaining = {}

        for hostel_id, hostel_quotas in quotas.items():
            remaining[hostel_id] = {}

            for category, quota in hostel_quotas.items():
                used = usage[hostel_id][category]

                remaining[hostel_id][category] = max(
                    0,
                    quota - used
                )

        return remaining
    
    def get_hostel_available_bed_counts(self):
        counts = {}

        for hostel_id, hostel in self.hostels.items():
            total_available = 0
            disability_eligible = 0

            for room in hostel.rooms:
                available = room.get_available_beds()

                total_available += available

                if room.floor in (0, 1):
                    disability_eligible += available

            counts[hostel_id] = {
                "TOTAL": total_available,
                "DISABILITY_ELIGIBLE": disability_eligible
            }

        return counts

    def get_protected_bed_counts(self):
        if self.reservations_released:
            return {
                hostel_id: {
                    "DISABILITY": 0,
                    "INTERNATIONAL": 0,
                    "TOTAL": 0
                }
                for hostel_id in self.hostels
            }
        remaining = self.get_remaining_reservations()
        available = self.get_hostel_available_bed_counts()

        protected = {}

        for hostel_id in self.hostels:
            total_available = available[hostel_id]["TOTAL"]
            ground_available = available[hostel_id]["DISABILITY_ELIGIBLE"]

            disability_beds = min(
                remaining[hostel_id]["DISABILITY"],
                ground_available
            )

            international_beds = min(
                remaining[hostel_id]["INTERNATIONAL"],
                total_available - disability_beds
            )

            protected[hostel_id] = {
                "DISABILITY": disability_beds,
                "INTERNATIONAL": international_beds,
                "TOTAL": disability_beds + international_beds
            }

        return protected

    def get_general_available_rooms(self, student: Student) -> List:
        available_rooms = self.get_available_rooms(student)
        protected = self.get_protected_bed_counts()
        bed_counts = self.get_hostel_available_bed_counts()

        general_rooms = []

        for room in available_rooms:
            hostel_id = room.hostel_id

            total_after_allocation = (
                bed_counts[hostel_id]["TOTAL"] - 1
            )

            if total_after_allocation < protected[hostel_id]["TOTAL"]:
                continue

            if room.floor in (0, 1):
                ground_after_allocation = (
                    bed_counts[hostel_id]["DISABILITY_ELIGIBLE"] - 1
                )

                if ground_after_allocation < protected[hostel_id]["DISABILITY"]:
                    continue

            general_rooms.append(room)

        return general_rooms

    def assign_student_to_room(
        self, student, allotment, room, reservation_flag=None
    ):
        
        for occupant_id in room.occupants:
            existing_student = self.students[occupant_id]

            if existing_student.year != student.year:
                allotment.add_flag("MIXED_YEAR_CONSENT")

        room.add_occupant(student.student_id)

        allotment.priority_score = self.calculate_priority(student)

        allotment.assign_room(
            room_id=room.room_id,
            hostel_id=room.hostel_id,
            room_type=room.room_type
        )

        if reservation_flag:
            allotment.add_flag(reservation_flag)

    def allocate_reserved_students(self, applicants, category):
        if category not in {"DISABILITY", "INTERNATIONAL"}:
            raise ValueError("Invalid reservation category")

        for allotment in applicants:
            self.allotments[allotment.student_id] = allotment

        ranked_applicants = self.rank_applicants(applicants)

        for allotment in ranked_applicants:
            student = self.students[allotment.student_id]

            if allotment.status != "PENDING":
                continue

            if self.get_primary_reservation_category(student) != category:
                continue

            for hostel_id, hostel in self.hostels.items():

                if hostel.gender != student.gender:
                    continue

                remaining = self.get_remaining_reservations()

                if remaining[hostel_id][category] <= 0:
                    continue

                available_rooms = [
                    room
                    for room in self.get_available_rooms(student)
                    if room.hostel_id == hostel_id
                ]

                room = self.choose_room(
                    student,
                    allotment,
                    available_rooms
                )

                if room is None:
                    continue

                reservation_flag = (
                    "RESERVED_DISABILITY"
                    if category == "DISABILITY"
                    else "RESERVED_INTERNATIONAL"
                )

                self.assign_student_to_room(
                    student,
                    allotment,
                    room,
                    reservation_flag
                )

                break
        
    def allocate_disability_reservations(self, applicants):
        self.allocate_reserved_students(
            applicants,
            "DISABILITY"
        )


    def allocate_international_reservations(self, applicants):
        self.allocate_reserved_students(
            applicants,
            "INTERNATIONAL"
        )


    def allocate_general_applicants(self, applicants):
        for allotment in self.rank_applicants(applicants):
            if allotment.status != "PENDING":
                continue

            student = self.students[allotment.student_id]

            available_rooms = self.get_general_available_rooms(student)

            room = self.choose_room(
                student,
                allotment,
                available_rooms
            )

            if room is None:
                continue

            self.assign_student_to_room(
                student,
                allotment,
                room
            )

    def release_unused_reservations(self):
        self.reservations_released = True


    def allocate_local_applicants(self, applicants):
        local_applicants = [
            allotment
            for allotment in applicants
            if self.students[allotment.student_id].home_distance_km < 25
        ]

        for allotment in local_applicants:
            self.allotments[allotment.student_id] = allotment

        for allotment in self.rank_applicants(local_applicants):
            if allotment.status != "PENDING":
                continue

            student = self.students[allotment.student_id]

            available_rooms = self.get_general_available_rooms(student)

            room = self.choose_room(
                student,
                allotment,
                available_rooms
            )

            if room is None:
                continue

            self.assign_student_to_room(
                student,
                allotment,
                room
            )
        
    def run_allotment(self, applicants, published_at: datetime):
        if len({a.student_id for a in applicants}) != len(applicants):
            raise ValueError("Duplicate applicant IDs found.")
        self.allotment_published_at = published_at
        self.reservations_released = False
        for allotment in applicants:
            if allotment.student_id not in self.students:
                raise ValueError(
                    f"Student {allotment.student_id} not registered."
                )

            if allotment.status != "PENDING":
                raise ValueError(
                    f"Allotment for {allotment.student_id} is not PENDING."
                )

        self.allotments = {
            allotment.student_id: allotment
            for allotment in applicants
        }

        regular_applicants, local_applicants = (
            self.separate_applicants_by_eligibility(applicants)
        )

        # Stage 1: Disability reservations
        self.allocate_disability_reservations(regular_applicants)

        # Stage 2: International reservations
        self.allocate_international_reservations(regular_applicants)

        # Stage 3: General allocation
        self.allocate_general_applicants(regular_applicants)

        # Stage 4: Release unused reserved beds
        self.release_unused_reservations()

        # Stage 5: Allocate local applicants
        self.allocate_local_applicants(local_applicants)

        # Stage 6: Generate waitlist
        self.generate_waitlist(applicants)

        return list(self.allotments.values())
    
    def get_deposit_deadline(self):
        if self.allotment_published_at is None:
            raise ValueError("Allotment list has not been published.")

        deadline_date = (
            self.allotment_published_at.date()
            + timedelta(days=7)
        )

        return datetime.combine(deadline_date, time(23,59))


    
    def process_deposit_payment(self, student_id, paid_at):
        if student_id not in self.allotments:
            raise ValueError("Unknown allotment student.")

        if not isinstance(paid_at, datetime):
            raise ValueError("Payment timestamp must be a datetime.")

        allotment = self.allotments[student_id]

        if allotment.status != "ALLOTTED":
            raise ValueError("Student does not have an active allotment.")

        if allotment.deposit_paid_at is not None:
            raise ValueError("Deposit has already been recorded.")

        if paid_at <= self.get_deposit_deadline():
            allotment.record_deposit(paid_at)
            return "ACCEPTED"

        # Find the room before forfeiting the allotment.
        assigned_room = None

        for hostel in self.hostels.values():
            for room in hostel.rooms:
                if room.room_id == allotment.assigned_room_id:
                    assigned_room = room
                    break

            if assigned_room is not None:
                break

        if assigned_room is None:
            raise ValueError("Assigned room could not be found.")

        allotment.mark_forfeited()
        assigned_room.remove_occupant(student_id)

        self.promote_waitlisted_student(assigned_room)

        return "FORFEITED"

    def promote_waitlisted_student(self, room):
        waitlisted = sorted(
            [
                allotment
                for allotment in self.allotments.values()
                if allotment.status == "WAITLISTED"
            ],
            key=lambda allotment: allotment.waitlist_position
        )

        hostel = self.hostels[room.hostel_id]

        for allotment in waitlisted:
            student = self.students[allotment.student_id]

            # Check hostel gender.
            if student.gender != hostel.gender:
                continue

            # First-year students cannot occupy SINGLE rooms.
            if student.year == 1 and room.room_type == "SINGLE":
                continue

            # Disabled students must be on floor 0 or 1.
            if student.disability and room.floor not in (0, 1):
                continue

            # Check mixed-year consent with existing occupants.
            compatible = True

            for occupant_id in room.occupants:
                existing_student = self.students[occupant_id]

                if existing_student.year != student.year:
                    if not (
                        student.mixed_year_consent
                        and existing_student.mixed_year_consent
                    ):
                        compatible = False
                        break

            if not compatible:
                continue

            # Check whether the offered room matches a preference.
            matches_preference = any(
                (
                    preference == "SINGLE_AC"
                    and room.room_type == "SINGLE"
                    and room.ac
                )
                or (
                    preference == "SINGLE"
                    and room.room_type == "SINGLE"
                    and not room.ac
                )
                or (
                    preference == room.room_type
                )
                for preference in student.preferences
            )

            if not matches_preference:
                allotment.add_flag("NO_PREFERENCE_MATCH")

            self.assign_student_to_room(
                student,
                allotment,
                room
            )
            # Recalculate positions for the remaining waitlisted students.
            remaining_waitlisted = sorted(
                [
                    item
                    for item in self.allotments.values()
                    if item.status == "WAITLISTED"
                ],
                key=lambda item: item.waitlist_position
            )

            for position, item in enumerate(remaining_waitlisted, start=1):
                item.waitlist_position = position


            return student.student_id

        return None

    
    def get_allotment_records(self):
        records = []

        for allotment in self.allotments.values():
            records.append({
                "student_id": allotment.student_id,
                "priority_score": round(allotment.priority_score, 2),
                "status": allotment.status,
                "hostel_id": allotment.assigned_hostel_id or "",
                "room_id": allotment.assigned_room_id or "",
                "room_type": allotment.assigned_room_type or "",
                "flags": ";".join(allotment.flags),
                "waitlist_position": (
                    allotment.waitlist_position
                    if allotment.waitlist_position is not None
                    else ""
                )
            })

        return records



    def generate_waitlist(self, applicants):
        allocation_order = self.get_allocation_order(applicants)

        waitlist_position = 1

        for allotment in allocation_order:
            if allotment.status != "PENDING":
                continue

            allotment.add_to_waitlist(waitlist_position)
            waitlist_position += 1

