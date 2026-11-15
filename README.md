# PS-070 – Hostel Room Allotment and Mess Billing Engine — Sample Data Pack

Prepared by 10 SECONDS for Team T033.

## Files

| File | What it holds | Row count |
|---|---|---|
| `hostels.csv` | 4 hostels (gender, beds) | 4 data rows |
| `rooms.csv` | Rooms with type, floor, AC flag and base rent (600 beds) | 304 data rows |
| `mess_rate_card.csv` | Mess daily rates, guest meal and extras | 8 data rows |
| `applicants.csv` | 800 hostel applicants with priority inputs and preferences | 640 data rows |
| `leave_applications.csv` | Mess-rebate leave applications | 173 data rows |
| `mess_attendance_monthly.csv` | Days with at least one recorded mess meal, per resident per month | 2260 data rows |
| `mess_extras.csv` | Guest meals and extra items | 564 data rows |
| `commands.txt` | Allotment, deposits, joining, changes, swaps, temporary and permanent vacating, inspections, bills, payments and prints | 2821 command lines (excluding comments) |

Volumes in this sample are reduced for email delivery; the hidden evaluation set is larger and uses the same schema.

Row numbers quoted below are 1-based data-row numbers (the header is row 0). Line numbers for `commands.txt` are physical line numbers including comment lines.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals with 2 places (no commas, no symbol); percentages as plain numbers (12.5 means 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix. An empty cell means "not applicable / not supplied" and only occurs in columns whose notes say so.

### `hostels.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| hostel_id | string | HST-nn | — | — |
| hostel_name | string | — | — | — |
| gender | enum | — | M, F | — |
| total_beds | int | — | — | — |

### `rooms.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| room_id | string | R<h>-<block><floor><nn> | — | — |
| hostel_id | string | — | hostels.csv | — |
| block | string | — | A, B | — |
| floor | int | — | 0–3 | 0 = ground |
| room_type | enum | — | SINGLE, DOUBLE, TRIPLE | — |
| beds | int | — | 1–3 | — |
| ac | bool | — | — | rent x 1.5 and Rs 5,000 one-time AC deposit |
| monthly_rent | decimal | Rs per bed | — | base (non-AC) rent |

### `mess_rate_card.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| item_code | string | — | — | — |
| description | string | — | — | — |
| unit | string | — | — | — |
| price | decimal | Rs | — | — |

### `applicants.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| student_id | string | STU-nnnn | — | numbered by application_ts |
| student_name | string | — | — | — |
| gender | enum | — | M, F | — |
| year | int | — | 1–4 | — |
| cgpa | decimal | 2 dp | 0–10 | — |
| category | enum | — | GEN, OBC, SC, ST | — |
| international | bool | — | — | 10% reservation |
| home_distance_km | decimal | km, 1 dp | — | — |
| disability | bool | — | — | 5% reservation, floor 0 or 1 |
| pref1 | enum | — | SINGLE, SINGLE_AC, DOUBLE, TRIPLE | SINGLE_AC = AC single room |
| pref2 | enum | — | — | may be empty |
| pref3 | enum | — | — | may be empty |
| mess_plan | enum | — | VEG, NONVEG | — |
| mixed_year_consent | bool | — | — | — |
| application_ts | timestamp | — | — | final tie-break |

### `leave_applications.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| leave_id | string | LV-nnnn | — | — |
| student_id | string | — | applicants.csv | — |
| from_date | date | — | — | first day away |
| to_date | date | — | — | last day away |
| submitted_date | date | — | — | — |

### `mess_attendance_monthly.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| month | string | YYYY-MM | — | — |
| student_id | string | — | applicants.csv | — |
| days_present | int | — | — | — |

### `mess_extras.csv`

| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| date | date | — | — | — |
| student_id | string | — | applicants.csv | — |
| item_code | string | — | mess_rate_card.csv | — |
| quantity | int | — | — | — |

## Command file format

`commands.txt` holds one command per line in the form `COMMAND_NAME|arg1|arg2|...`. Commands must be processed strictly in file order. Lines starting with `#` are comments and blank lines are ignored. An empty argument (two adjacent `|`) means "not supplied". Every command used in this pack:

| Command | Arguments (in order) | Meaning |
|---|---|---|
| `RUN_ALLOTMENT` | `ts` | annual allotment; the list is published at ts |
| `PRINT_ALLOTMENT` | `` | allotment list and waitlist |
| `PAY_DEPOSIT` | `student_id|ts` | security deposit (2 months' rent, + AC deposit) paid |
| `JOIN` | `student_id|date` | student moves in on that date (default: 2026-08-01 if no JOIN command) |
| `ROOM_CHANGE` | `student_id|requested_type|ts` | change request |
| `SWAP` | `student_id_1|student_id_2|ts|agree_rent_difference` | swap rooms with both consents |
| `TEMP_VACATE` | `student_id|from_date|to_date|reason` | internship / exchange absence |
| `RETURN` | `student_id|date` | back from temporary vacating |
| `VACATE` | `student_id|vacate_date|notice_date` | permanent vacating |
| `INSPECTION` | `student_id|date|damage_amount|note` | room inspection at vacating |
| `GENERATE_BILLS` | `month` | monthly rent + mess bills (YYYY-MM), due on the 10th of the following month |
| `PAYMENT` | `student_id|bill_month|ts|amount` | amount FULL = whole bill including any penalty at that time |
| `PRINT_OCCUPANCY` | `date` | occupancy by hostel |
| `PRINT_DUES` | `date` | dues report |
| `PRINT_BILL` | `student_id|month` | monthly bill |

## Planted scenarios

Every edge case in the brief, mapped to the exact record where it occurs, followed by extra traps.

- **EC-01 Applicant with home distance exactly 25 km and exactly 500 km**
  - STU-0553: home distance exactly 25.0 km (not < 25 → regular eligibility); STU-0300: exactly 500.0 km (not > 500 → no +10 bonus); both CGPA 8.40, year 2 → priority score 94.00 each — `applicants.csv rows 300, 553`
- **EC-02 Reserved disability beds where 5% of a hostel's beds is less than 1**
  - HST-04 (Hemavathi Girls PG Annexe) has 18 beds → 5% disability reservation = 0.9 bed (decide 0 or 1); STU-0631 is a disabled first-year girl who must get floor 0 or 1 — `hostels.csv HST-04 (row 4); applicants.csv row 631`
- **EC-03 Deposit paid on day 7 at 23:59 versus day 8**
  - Allotment list published 2026-07-20 10:00. STU-0384 pays the deposit at 2026-07-27 23:59 (day 7 → accepted); STU-0017 pays at 2026-07-28 00:01 (day 8 → bed already offered to the waitlist) — `commands.txt line 453 and line 454`
- **EC-04 Joining on the 15th versus the 16th of the month**
  - STU-0586 joins on 2026-08-15 (on or before the 15th → half month's rent for August); STU-0293 joins on 2026-08-16 (full month) — `commands.txt line 456 and line 457`
- **EC-05 Leave of exactly 5 days applied exactly 2 days before**
  - STU-0466: leave 2026-09-21..09-25 (exactly 5 days) submitted 2026-09-19 (exactly 2 days before leaving) → rebate 5 x daily rate — `leave_applications.csv row 70`
- **EC-06 Rebate pushing the semester total to 21 days (last day disallowed)**
  - STU-0317: three valid 7-day leaves = 21 rebate days in the semester — the cap is 20, so the last day (2026-11-22) earns no rebate — `leave_applications.csv rows 14, 89, 154`
- **EC-07 Penalty reaching the Rs 300 cap on the 30th day**
  - STU-0341: September bill due 2026-10-10 is paid on 2026-11-09 — penalty days 10-11 … 11-09 = 30 → Rs 10 x 30 = Rs 300 = exactly the cap — `commands.txt line 1608`
- **EC-08 Temporary vacate of exactly 90 days**
  - STU-0563: internship TEMP_VACATE 2026-09-01..11-29 = exactly 90 days → keeps the bed at 50% rent with no mess billing (only beyond 90 days is the bed released) — `commands.txt line 458 and line 1820`
- **Extra traps (not in the brief, but realistic):**
  - STU-0377: first-year with only SINGLE / SINGLE_AC preferences — first-years never get SINGLE: cheapest free type + NO_PREFERENCE_MATCH — `applicants.csv row 377`
  - STU-0212 never pays her August–September bills (dues > Rs 2,000) and requests a ROOM_CHANGE on 2026-10-20 → blocked — `commands.txt line 1364`
  - STU-0048 gives only 3 days' notice (2026-11-25 for 2026-11-28) → 25% of the deposit forfeited, plus Rs 1,850 damages from the inspection; settlement printed on 2026-11-28 — `commands.txt line 1818 and line 1819`
  - STU-0090 (DOUBLE) and STU-0047 (TRIPLE) swap with both consents and agree to the rent difference — allowed despite different room types; September is billed at the higher rent — `commands.txt line 821`
  - STU-0010: 12 guest meals in October — only 10 allowed per month — `mess_extras.csv rows 268, 274, 282, 292, 302, 313 … 372 (12 rows)`
  - STU-0622: 0 mess days recorded in October and no rebate — billed in full and flagged NO_ATTENDANCE — `mess_attendance_monthly.csv row 1013`
  - STU-0376: 7-day leave starting 2026-08-10 — inside the first 15 days of the semester, no rebate — `leave_applications.csv row 1`

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

Produce these CSV files (header row, same conventions as above, rows sorted as stated). Where the brief is silent on a format detail the choice below is binding for evaluation.

### `allotment.csv`

One row per applicant.

Columns, in order: `student_id`, `priority_score`, `status`, `hostel_id`, `room_id`, `room_type`, `flags`, `waitlist_position`

### `bills.csv`

One row per resident per month.

Columns, in order: `student_id`, `month`, `rent`, `mess_days_billed`, `mess_rate`, `mess_amount`, `rebate_days`, `rebate_amount`, `guest_meals`, `extras_amount`, `penalty`, `total`, `flags`

### `settlements.csv`

One row per VACATE.

Columns, in order: `student_id`, `vacate_date`, `deposit`, `unpaid_dues`, `damages`, `notice_forfeit`, `refund`, `recoverable`

### `dues.csv`

One row per student with dues per PRINT_DUES.

Columns, in order: `as_of_date`, `student_id`, `outstanding`, `months_over_5000`, `hold`

### `occupancy.csv`

One row per hostel per PRINT_OCCUPANCY.

Columns, in order: `date`, `hostel_id`, `beds`, `occupied`, `temporarily_vacant`, `vacant`

Binding choices: allotment `status` ALLOTTED, WAITLISTED, FORFEITED (deposit late), INELIGIBLE; `flags` `;`-separated from NO_PREFERENCE_MATCH, RESERVED_DISABILITY, RESERVED_INTERNATIONAL, NO_ATTENDANCE, HOLD. Mess is billed from the joining date. Priority score to 2 dp.

## Running the project

Use Python 3.10 or newer. From the repository root, activate the project environment and run:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
