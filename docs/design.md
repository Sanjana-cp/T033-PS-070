# Hostel Allotment and Mess Billing Engine

## Purpose

This Python application processes hostel applications, room assignments, lifecycle events, mess billing, payments, and reports. It reads the supplied CSV data and command stream, then writes evaluation CSV files.

## Architecture

- `csv_io/csv_reader.py` loads the seven input CSV files and converts values to Python types.
- `models/` defines students, hostels, rooms, allotments, and billing records.
- `engines/management_engine.py` registers students, hostels, rooms, and rate-card values.
- `engines/allotment_engine.py` applies eligibility, priority, preferences, reservations, deposit deadlines, and waitlist promotion.
- `engines/room_lifecycle_engine.py` handles joins, room changes, swaps, temporary vacancies, inspections, and vacating settlements.
- `engines/billing_engine.py` calculates rent, mess charges, rebates, guest meals, penalties, dues, payments, and HOLD status.
- `command_processor.py` reads commands in file order, skips blank lines and comments, and dispatches commands to the engines.
- `reporting_engine.py` collects report rows and writes the output CSV files.
- `main.py` loads the inputs, creates the engines, processes `commands.txt`, and writes reports.

## Data flow

1. `main.py` loads the sample CSV files through `csv_reader.py`.
2. The management engine registers hostels, rooms, and students; the rate card is loaded.
3. The command processor reads `commands.txt` from top to bottom.
4. Each command updates the relevant engine state. Expected business-rule rejections are recorded while processing continues.
5. Print commands collect report snapshots. At the end, the reporting engine writes:
   - `allotment.csv`
   - `bills.csv`
   - `settlements.csv`
   - `dues.csv`
   - `occupancy.csv`

## Key decisions

- Applicants under 25 km are allocated after regular-distance applicants.
- Applicant priority uses the stated CGPA, year, distance, and disability formula.
- Reserved disability beds are rounded up to a minimum of one when the percentage is fractional.
- First-year students are not assigned SINGLE rooms.
- A day-seven deposit is accepted through 23:59:59.
- Rent is prorated at the 15th-day boundary.
- Mess rebates require a qualifying leave application and are capped at 20 days per semester.
- Temporary absences of 30–90 days retain the bed at 50% rent with mess billing suspended; the bed is released only after 90 days.

See `docs/business_rules.md` for the complete BR-01 through BR-12 rules and decision log.

## Running

From the repository root, activate the virtual environment and run:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py