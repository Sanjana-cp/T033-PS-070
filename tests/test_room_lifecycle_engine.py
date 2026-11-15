from datetime import date

import pytest

from engines.room_lifecycle_engine import RoomLifecycleEngine


def make_lifecycle(sample_system):
    engine = sample_system["allotment_engine"]
    return RoomLifecycleEngine(
        sample_system["students"],
        sample_system["hostels"],
        engine.allotments,
    )


def test_join_date_is_recorded(sample_system):
    lifecycle = make_lifecycle(sample_system)

    record = lifecycle.record_join("STU-0586", date(2026, 8, 15))

    assert record["event"] == "JOIN"
    assert lifecycle.join_dates["STU-0586"] == date(2026, 8, 15)


def test_exactly_ninety_day_vacancy_retains_bed(sample_system):
    lifecycle = make_lifecycle(sample_system)

    record = lifecycle.temporary_vacate(
        "STU-0563",
        date(2026, 9, 1),
        date(2026, 11, 29),
        "INTERNSHIP",
    )

    assert record["duration"] == 90
    assert record["bed_released"] is False
    assert record["rent_percentage"] == 50
    assert record["mess_suspended"] is True


def test_swap_with_rent_difference_agreement(sample_system):
    lifecycle = make_lifecycle(sample_system)

    record = lifecycle.swap_rooms(
        "STU-0090",
        "STU-0047",
        date(2026, 9, 12),
        agree_rent_difference=True,
    )

    assert record["event"] == "ROOM_SWAP"
    assert record["student1_new_room"]
    assert record["student2_new_room"]


def test_room_change_blocked_by_hold(sample_system):
    lifecycle = make_lifecycle(sample_system)

    with pytest.raises(ValueError, match="HOLD"):
        lifecycle.change_room(
            "STU-0212",
            "DOUBLE",
            "2026-FALL",
            date(2026, 10, 20),
            outstanding_dues=0,
            hold=True,
        )


def test_inspection_damage_is_used_in_settlement(sample_system):
    lifecycle = make_lifecycle(sample_system)

    lifecycle.record_inspection(
        "STU-0048",
        date(2026, 11, 28),
        1850,
        "Broken cupboard door",
    )
    record = lifecycle.permanent_vacate(
        "STU-0048",
        date(2026, 11, 28),
        date(2026, 11, 25),
        deposit_amount=10000,
        unpaid_dues=0,
        damage_charges=lifecycle.inspections["STU-0048"]["damage_charges"],
    )

    assert record["damages"] == 1850
    assert record["notice_forfeit"] == 2500