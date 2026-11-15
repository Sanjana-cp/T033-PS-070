from datetime import date
from decimal import Decimal

from engines.billing_engine import BillingEngine


def make_billing(sample_system):
    students = sample_system["students"]
    engine = sample_system["allotment_engine"]
    data = sample_system["data"]
    rooms = {
        room.room_id: room
        for hostel in sample_system["hostels"].values()
        for room in hostel.rooms
    }
    return BillingEngine(
        students,
        rooms,
        engine.allotments,
        leave_applications=data["leave_applications"],
        semester_start_dates={"2026-FALL": date(2026, 8, 1)},
    )


def test_rebate_edge_cases(sample_system):
    billing = make_billing(sample_system)

    assert billing.calculate_rebate(
        "STU-0466", "2026-FALL", "2026-09", date(2026, 8, 1)
    ) == 5
    assert len(
        billing.get_eligible_rebate_dates(
            "STU-0317", "2026-FALL", date(2026, 8, 1)
        )
    ) == 20


def test_penalty_reaches_cap(sample_system):
    billing = make_billing(sample_system)

    assert billing.calculate_late_penalty(
        "2026-09", date(2026, 11, 9)
    ) == Decimal("300.00")


def test_rent_proration_boundary(sample_system):
    billing = make_billing(sample_system)

    assert billing.calculate_rent(
        6000, "2026-08", date(2026, 8, 15)
    ) == Decimal("3000.00")
    assert billing.calculate_rent(
        6000, "2026-08", date(2026, 8, 16)
    ) == Decimal("6000.00")


def test_guest_meals_capped_at_ten(sample_system):
    billing = make_billing(sample_system)
    student_id = "STU-0010"
    room = billing.get_student_room(student_id)
    guest_meals = sum(
        row["quantity"]
        for row in sample_system["data"]["mess_extras"]
        if row["student_id"] == student_id
        and row["date"].strftime("%Y-%m") == "2026-10"
        and row["item_code"] == "GUEST_MEAL"
    )

    bill = billing.generate_bill(
        student_id,
        "2026-10",
        date(2026, 8, 1),
        attendance_days=20,
        semester_id="2026-FALL",
        guest_meals=guest_meals,
        semester_start_date=date(2026, 8, 1),
        monthly_rent=room.effective_monthly_rent,
    )

    assert guest_meals > 10
    assert bill["guest_meals"] == 10


def test_zero_attendance_flag(sample_system):
    billing = make_billing(sample_system)
    room = billing.get_student_room("STU-0622")

    bill = billing.generate_bill(
        "STU-0622",
        "2026-10",
        date(2026, 8, 1),
        attendance_days=0,
        semester_id="2026-FALL",
        semester_start_date=date(2026, 8, 1),
        monthly_rent=room.effective_monthly_rent,
    )

    assert bill["mess_days_billed"] > 0
    assert bill["flags"] == "NO_ATTENDANCE"


def test_hold_after_two_high_due_months(sample_system):
    billing = make_billing(sample_system)
    billing.bills[("STU-0212", "2026-08")] = {
        "total": Decimal("6000.00"),
        "penalty": Decimal("0.00"),
    }
    billing.bills[("STU-0212", "2026-09")] = {
        "total": Decimal("6000.00"),
        "penalty": Decimal("0.00"),
    }

    assert billing.update_hold_status(
        "STU-0212", date(2026, 10, 10)
    ) is True