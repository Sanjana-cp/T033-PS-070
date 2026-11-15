
from datetime import date
from typing import Dict, Optional


class RoomLifecycleEngine:

    def __init__(
        self,
        students: Dict,
        hostels: Dict,
        allotments: Dict
    ):
        self.students = students
        self.hostels = hostels
        self.allotments = allotments

        # Tracks room changes during each semester.
        self.room_changes = {}

        # Tracks students who are temporarily away.
        self.temporary_vacancies = {}

        # Records room lifecycle events for billing integration.
        self.lifecycle_records = []

        self.join_dates = {}
        self.inspections = {}

    # --------------------------------------------------
    # HELPER METHODS
    # --------------------------------------------------

    def get_room(self, room_id):
        for hostel in self.hostels.values():
            for room in hostel.rooms:
                if room.room_id == room_id:
                    return room

        return None

    def get_student_room(self, student_id):
        allotment = self.allotments.get(student_id)

        if allotment is None or allotment.status != "ALLOTTED":
            return None

        return self.get_room(allotment.assigned_room_id)

    def get_hostel_for_room(self, room):
        return self.hostels.get(room.hostel_id)

    def has_outstanding_dues(self, outstanding_dues):
        return outstanding_dues > 2000

    def is_room_compatible(self, student, room):
        if room.is_full():
            return False

        hostel = self.get_hostel_for_room(room)

        if hostel is None or hostel.gender != student.gender:
            return False

        if student.year == 1 and room.room_type == "SINGLE":
            return False

        if student.disability and room.floor not in (0, 1):
            return False

        for occupant_id in room.occupants:
            existing_student = self.students[occupant_id]

            if existing_student.year != student.year:
                if not (
                    student.mixed_year_consent
                    and existing_student.mixed_year_consent
                ):
                    return False

        return True

    def find_available_room(self, student, requested_type):
        matching_rooms = []

        for hostel in self.hostels.values():
            if hostel.gender != student.gender:
                continue

            for room in hostel.rooms:
                if room.room_type != requested_type:
                    continue

                if self.is_room_compatible(student, room):
                    matching_rooms.append(room)

        if not matching_rooms:
            return None

        return min(
            matching_rooms,
            key=lambda room: room.effective_monthly_rent
        )

    # --------------------------------------------------
    # 1. ROOM CHANGE
    # --------------------------------------------------

    def change_room(
        self,
        student_id,
        requested_type,
        semester_id,
        change_date,
        outstanding_dues=0,
        hold=False,
    ):
        if student_id not in self.students:
            raise ValueError("Unknown student.")

        if not isinstance(change_date, date):
            raise ValueError("Invalid room change date.")

        if outstanding_dues < 0:
            raise ValueError("Outstanding dues cannot be negative.")

        student = self.students[student_id]
        allotment = self.allotments.get(student_id)

        if allotment is None or allotment.status != "ALLOTTED":
            raise ValueError("Student does not have an active allotment.")

        if self.has_outstanding_dues(outstanding_dues):
            raise ValueError("Room change blocked due to outstanding dues.")

        if hold:
            raise ValueError("Room change blocked due to HOLD.")

        if self.temporary_vacancies.get(student_id):
            raise ValueError("Temporarily vacating students cannot change rooms.")

        if requested_type not in {"SINGLE", "DOUBLE", "TRIPLE"}:
            raise ValueError("Invalid requested room type.")

        if student.year == 1 and requested_type == "SINGLE":
            raise ValueError("First-year students cannot occupy SINGLE rooms.")

        change_key = (student_id, semester_id)
        if change_key in self.room_changes:
            raise ValueError("Room change already used this semester.")

        old_room = self.get_student_room(student_id)
        if old_room is None:
            raise ValueError("Current room could not be found.")

        if old_room.room_type == requested_type:
            raise ValueError("Student already occupies this room type.")

        new_room = self.find_available_room(student, requested_type)
        if new_room is None:
            raise ValueError("No compatible room with available capacity.")

        old_room.remove_occupant(student_id)
        new_room.add_occupant(student_id)

        old_room_id = old_room.room_id
        allotment.assign_room(
            room_id=new_room.room_id,
            hostel_id=new_room.hostel_id,
            room_type=new_room.room_type,
        )

        self.room_changes[change_key] = change_date

        record = {
            "event": "ROOM_CHANGE",
            "student_id": student_id,
            "date": change_date,
            "old_room_id": old_room_id,
            "new_room_id": new_room.room_id,
            "old_rent": old_room.effective_monthly_rent,
            "new_rent": new_room.effective_monthly_rent,
            "billing_rent": max(
                old_room.effective_monthly_rent,
                new_room.effective_monthly_rent,
            ),
        }

        self.lifecycle_records.append(record)
        return record
    # --------------------------------------------------
    # 2. ROOM SWAP
    # --------------------------------------------------

    def swap_rooms(
        self,
        student1_id,
        student2_id,
        swap_date,
        agree_rent_difference=False,
        student1_consent=True,
        student2_consent=True
    ):

        if student1_id == student2_id:
            raise ValueError("A student cannot swap with themselves.")

        if not isinstance(swap_date, date):
            raise ValueError("Invalid swap date.")

        if student1_id not in self.students:
            raise ValueError("First student does not exist.")

        if student2_id not in self.students:
            raise ValueError("Second student does not exist.")

        if not student1_consent or not student2_consent:
            raise ValueError("Both students must consent to the swap.")

        student1 = self.students[student1_id]
        student2 = self.students[student2_id]

        room1 = self.get_student_room(student1_id)
        room2 = self.get_student_room(student2_id)

        if room1 is None or room2 is None:
            raise ValueError("Both students must have active allotments.")

        if room1.room_id == room2.room_id:
            raise ValueError("Both students already share the same room.")

        if self.temporary_vacancies.get(student1_id):
            raise ValueError("First student is temporarily away.")

        if self.temporary_vacancies.get(student2_id):
            raise ValueError("Second student is temporarily away.")

        if (
            room1.room_type != room2.room_type
            and not agree_rent_difference
        ):
            raise ValueError(
                "Different room types require rent difference consent."
            )

        if student1.year == 1 and room2.room_type == "SINGLE":
            raise ValueError("First-year student cannot occupy SINGLE.")

        if student2.year == 1 and room1.room_type == "SINGLE":
            raise ValueError("First-year student cannot occupy SINGLE.")

        if student1.disability and room2.floor not in (0, 1):
            raise ValueError("First student's destination floor is invalid.")

        if student2.disability and room1.floor not in (0, 1):
            raise ValueError("Second student's destination floor is invalid.")

        # Validate mixed-year compatibility after removing both students.
        room1.remove_occupant(student1_id)
        room2.remove_occupant(student2_id)

        compatible1 = self.is_room_compatible(student1, room2)
        compatible2 = self.is_room_compatible(student2, room1)

        if not compatible1 or not compatible2:
            room1.add_occupant(student1_id)
            room2.add_occupant(student2_id)
            raise ValueError("Swap violates room compatibility rules.")

        room2.add_occupant(student1_id)
        room1.add_occupant(student2_id)

        allotment1 = self.allotments[student1_id]
        allotment2 = self.allotments[student2_id]

        allotment1.assign_room(
            room_id=room2.room_id,
            hostel_id=room2.hostel_id,
            room_type=room2.room_type
        )

        allotment2.assign_room(
            room_id=room1.room_id,
            hostel_id=room1.hostel_id,
            room_type=room1.room_type
        )

        record = {
            "event": "ROOM_SWAP",
            "date": swap_date,
            "student1_id": student1_id,
            "student2_id": student2_id,
            "student1_new_room": room2.room_id,
            "student2_new_room": room1.room_id,
            "billing_rent": max(
                room1.effective_monthly_rent,
                room2.effective_monthly_rent
            )
        }

        self.lifecycle_records.append(record)

        return record

    # --------------------------------------------------
    # 3. TEMPORARY VACATING
    # --------------------------------------------------

    def temporary_vacate(
        self,
        student_id,
        from_date,
        to_date,
        reason
    ):

        if student_id not in self.students:
            raise ValueError("Unknown student.")

        if not isinstance(from_date, date) or not isinstance(to_date, date):
            raise ValueError("Invalid temporary vacancy dates.")

        if to_date < from_date:
            raise ValueError("End date cannot precede start date.")

        if not reason:
            raise ValueError("Temporary vacancy reason is required.")

        if student_id in self.temporary_vacancies:
            raise ValueError("Student already has a temporary vacancy.")

        room = self.get_student_room(student_id)

        if room is None:
            raise ValueError("Student has no active room.")

        duration = (to_date - from_date).days + 1

        record = {
            "student_id": student_id,
            "from_date": from_date,
            "to_date": to_date,
            "reason": reason,
            "duration": duration,
            "room_id": room.room_id,
            "bed_released": duration > 90,
            "rent_percentage": 50 if duration >= 30 and duration <= 90 else 100,
            "mess_suspended": duration >= 30
        }

        if duration > 90:
            room.remove_occupant(student_id)

            self.move_to_top_of_waitlist(student_id)

        self.temporary_vacancies[student_id] = record

        self.lifecycle_records.append({
            "event": "TEMPORARY_VACATE",
            **record
        })

        return record

    # --------------------------------------------------
    # 4. RETURN FROM TEMPORARY VACANCY
    # --------------------------------------------------

    def return_from_temporary_vacate(self, student_id, return_date):

        if student_id not in self.temporary_vacancies:
            raise ValueError("No temporary vacancy found for student.")

        if not isinstance(return_date, date):
            raise ValueError("Invalid return date.")

        record = self.temporary_vacancies[student_id]

        if return_date < record["from_date"]:
            raise ValueError("Return date precedes vacancy date.")

        actual_duration = (
            return_date - record["from_date"]
        ).days + 1

        room = self.get_room(record["room_id"])

        if actual_duration > 90:
            allotment = self.allotments[student_id]

            if allotment.status == "WAITLISTED":
                result = "WAITLISTED"
            else:
                result = "BED_RELEASED"

        else:
            if room is None:
                raise ValueError("Original room could not be found.")

            if student_id not in room.occupants:
                if room.is_full():
                    self.move_to_top_of_waitlist(student_id)
                    result = "WAITLISTED"
                else:
                    room.add_occupant(student_id)
                    result = "BED_RETAINED"
            else:
                result = "BED_RETAINED"

        del self.temporary_vacancies[student_id]

        return_record = {
            "event": "RETURN",
            "student_id": student_id,
            "return_date": return_date,
            "actual_duration": actual_duration,
            "result": result
        }

        self.lifecycle_records.append(return_record)

        return return_record

    # --------------------------------------------------
    # WAITLIST HELPER
    # --------------------------------------------------

    def move_to_top_of_waitlist(self, student_id):

        allotment = self.allotments[student_id]

        existing_waitlist = sorted(
            [
                item
                for item in self.allotments.values()
                if item.status == "WAITLISTED"
                and item.student_id != student_id
            ],
            key=lambda item: item.waitlist_position
        )

        for position, item in enumerate(existing_waitlist, start=2):
            item.waitlist_position = position

        allotment.add_to_waitlist(1)

    # --------------------------------------------------
    # 5. PERMANENT VACATING AND SETTLEMENT
    # --------------------------------------------------
    def record_join(self, student_id, join_date):
        if student_id not in self.students:
            raise ValueError("Unknown student.")
        if not isinstance(join_date, date):
            raise ValueError("Invalid join date.")
        if self.get_student_room(student_id) is None:
            raise ValueError("Student has no active room.")
        if student_id in self.join_dates:
            raise ValueError("Join date already recorded.")

        self.join_dates[student_id] = join_date
        record = {
            "event": "JOIN",
            "student_id": student_id,
            "date": join_date,
        }
        self.lifecycle_records.append(record)
        return record

    def record_inspection(self, student_id, inspection_date, damage_charges, reason):
        if student_id not in self.students:
            raise ValueError("Unknown student.")
        if not isinstance(inspection_date, date):
            raise ValueError("Invalid inspection date.")
        if damage_charges < 0:
            raise ValueError("Damage charges cannot be negative.")
        if not reason:
            raise ValueError("Inspection reason is required.")
        if self.get_student_room(student_id) is None:
            raise ValueError("Student has no active room.")

        record = {
            "event": "INSPECTION",
            "student_id": student_id,
            "date": inspection_date,
            "damage_charges": damage_charges,
            "reason": reason,
        }
        self.inspections[student_id] = record
        self.lifecycle_records.append(record)
        return record

    def permanent_vacate(
        self,
        student_id,
        vacate_date,
        notice_date,
        deposit_amount,
        unpaid_dues,
        damage_charges
    ):

        if student_id not in self.students:
            raise ValueError("Unknown student.")

        if not isinstance(vacate_date, date):
            raise ValueError("Invalid vacate date.")

        if notice_date is not None and not isinstance(notice_date, date):
            raise ValueError("Invalid notice date.")

        if min(deposit_amount, unpaid_dues, damage_charges) < 0:
            raise ValueError("Settlement amounts cannot be negative.")

        if student_id in self.temporary_vacancies:
            raise ValueError(
                "Student must complete or cancel temporary vacancy first."
            )

        allotment = self.allotments.get(student_id)

        if allotment is None or allotment.status != "ALLOTTED":
            raise ValueError("Student does not have an active allotment.")

        room = self.get_student_room(student_id)

        if room is None:
            raise ValueError("Assigned room could not be found.")

        notice_days = (
            (vacate_date - notice_date).days
            if notice_date is not None
            else 0
        )

        if notice_days < 0:
            raise ValueError("Notice date cannot be after vacate date.")

        notice_forfeit = (
            deposit_amount * 0.25
            if notice_days < 7
            else 0
        )

        refund = (
            deposit_amount
            - unpaid_dues
            - damage_charges
            - notice_forfeit
        )

        recoverable = refund < 0

        room.remove_occupant(student_id)

        allotment.assigned_room_id = None
        allotment.assigned_hostel_id = None
        allotment.assigned_room_type = None

        settlement = {
            "student_id": student_id,
            "vacate_date": vacate_date,
            "deposit": round(deposit_amount, 2),
            "unpaid_dues": round(unpaid_dues, 2),
            "damages": round(damage_charges, 2),
            "notice_forfeit": round(notice_forfeit, 2),
            "refund": round(max(refund, 0), 2),
            "recoverable": round(abs(min(refund, 0)), 2),
            "status": "RECOVERABLE" if recoverable else "SETTLED"
        }

        self.lifecycle_records.append({
            "event": "PERMANENT_VACATE",
            **settlement
        })

        return settlement
