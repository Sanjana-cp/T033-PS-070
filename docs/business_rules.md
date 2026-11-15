# Business Rules and Decision Log

## Business rules

### BR-01 — Eligibility and priority
Applicants living less than 25 km away are allocated only after other eligible applicants. Priority is CGPA × 10, plus year × 5, plus 10 when distance is greater than 500 km, plus 20 for disability. Ties are resolved by distance descending, then application timestamp ascending.

### BR-02 — Room preferences
Process applicants in priority order and assign the first preference with available capacity. If none of the three preferences can be met, assign the cheapest available room type and add `NO_PREFERENCE_MATCH`. First-year students are never assigned SINGLE rooms.

### BR-03 — Reservations
Reserve 5% of each hostel’s beds for disability and 10% for international applicants. Disability applicants must be assigned to floor 0 or 1. Release unused reserved beds after the main allocation run, in waitlist order.

### BR-04 — Room compatibility and AC
DOUBLE and TRIPLE rooms may mix academic years only when both students consent. A room cannot mix hostel genders. AC rent is 1.5 times base rent, with a one-time AC deposit of ₹5,000.

### BR-05 — Deposit and acceptance
An allotted student must pay a refundable deposit equal to two months’ rent, plus the AC deposit if applicable, within seven days of publication. After the deadline, forfeit the allotment and offer the bed to the next compatible waitlisted student.

### BR-06 — Rent proration
Rent is charged monthly. Joining or vacating on or before the 15th incurs half-month rent; after the 15th incurs full-month rent. A room change during a month uses the higher room rent for that month.

### BR-07 — Room change and swap
A student may change rooms once per semester, subject to free capacity. Block room changes when dues exceed ₹2,000 or a HOLD applies. Swaps require both students’ consent; different room types also require agreement to the rent difference.

### BR-08 — Mess billing and rebates
Daily mess rates are ₹150 for VEG and ₹180 for NONVEG. A rebate requires at least five consecutive leave days, submitted at least two days before leave begins. Rebate equals the daily rate times eligible days, capped at 20 days per semester. No rebate applies during the semester’s first 15 days.

### BR-09 — Guest meals and extras
Guest meals cost ₹80 each and are capped at 10 per student per month. Add extras at the rate-card price. If a student has zero recorded attendance and no rebate in a month, bill the full mess amount and add `NO_ATTENDANCE`.

### BR-10 — Late payment and HOLD
Bills are due on the 10th of the following month. Charge ₹10 per late day starting on the 11th, capped at ₹300 per bill. Outstanding dues above ₹5,000 for two consecutive months create a HOLD that blocks room changes and the next semester’s allotment.

### BR-11 — Temporary vacancy
For internship or exchange absences of at least 30 days, retain the bed at 50% rent and suspend mess billing. After more than 90 days, release the bed and place the student at the top of the waitlist on return.

### BR-12 — Vacating settlement
Refund equals deposit minus unpaid dues, inspection damage charges, and any notice forfeiture. If the result is negative, record the balance as recoverable. Vacating without seven days’ notice forfeits 25% of the deposit. Print the settlement on the vacate date.

## Decision log

| Topic | Decision |
|---|---|
| 5% disability quota below one bed | Round up; HST-04’s 18 beds therefore reserve one disability bed. |
| Distance boundary | Exactly 25 km is regular eligibility; exactly 500 km receives no distance bonus. |
| Deposit deadline | Accept through 23:59:59 on calendar day seven after publication. |
| AC preference | Treat `SINGLE_AC` as a SINGLE room with AC enabled. |
| Penalty days | Use elapsed calendar days after the due date, at ₹10 per day, capped at ₹300. |
| Mess billing start | Bill starting on the recorded JOIN date; when absent, use 2026-08-01 as specified by the sample pack. |
| 90-day vacancy boundary | Exactly 90 days retains the bed; release applies only beyond 90 days. |