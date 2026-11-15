from datetime import datetime


def test_priority_boundary_scores(sample_system):
    engine = sample_system["allotment_engine"]
    students = sample_system["students"]

    assert engine.calculate_priority(students["STU-0553"]) == 94
    assert engine.calculate_priority(students["STU-0300"]) == 94


def test_first_year_single_preference_uses_fallback(sample_system):
    engine = sample_system["allotment_engine"]
    students = sample_system["students"]
    allotment = engine.allotments["STU-0377"]

    room = engine.hostels[allotment.assigned_hostel_id].rooms
    assigned = next(
        room for room in room
        if room.room_id == allotment.assigned_room_id
    )

    assert assigned.room_type != "SINGLE"
    assert "NO_PREFERENCE_MATCH" in allotment.flags


def test_disability_reservation_uses_accessible_floor(sample_system):
    engine = sample_system["allotment_engine"]
    allotment = engine.allotments["STU-0631"]
    room = next(
        room
        for hostel in engine.hostels.values()
        for room in hostel.rooms
        if room.room_id == allotment.assigned_room_id
    )

    assert "RESERVED_DISABILITY" in allotment.flags
    assert room.floor in (0, 1)


def test_day_seven_deadline_accepts_payment(sample_system):
    engine = sample_system["allotment_engine"]
    allotment = next(
        item for item in engine.allotments.values()
        if item.status == "ALLOTTED"
    )

    result = engine.process_deposit_payment(
        allotment.student_id,
        datetime(2026, 7, 27, 23, 59, 59),
    )

    assert result == "ACCEPTED"


def test_late_deposit_forfeits_and_promotes_waitlist(sample_system):
    engine = sample_system["allotment_engine"]
    allotment = next(
        item for item in engine.allotments.values()
        if item.status == "ALLOTTED"
    )
    room = next(
        room
        for hostel in engine.hostels.values()
        for room in hostel.rooms
        if room.room_id == allotment.assigned_room_id
    )
    occupants_before = set(room.occupants)

    result = engine.process_deposit_payment(
        allotment.student_id,
        datetime(2026, 7, 28, 0, 1),
    )

    assert result == "FORFEITED"
    assert allotment.status == "FORFEITED"
    assert set(room.occupants) - occupants_before