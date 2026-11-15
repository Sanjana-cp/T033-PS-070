from pathlib import Path

from csv_io.csv_writer import (
    write_allotment,
    write_bills,
    write_dues,
    write_occupancy,
    write_settlements,
)


class ReportingEngine:
    def __init__(self, output_dir="data/output"):
        self.output_dir = Path(output_dir)
        self.allotments = []
        self.bills = []
        self.settlements = []
        self.dues = []
        self.occupancy = []

    def record_allotment(self, rows):
        self.allotments = list(rows)

    def record_bill(self, row):
        self.bills.append(dict(row))

    def record_settlement(self, row):
        self.settlements.append(dict(row))

    def record_dues(self, rows):
        self.dues.extend(dict(row) for row in rows)

    def record_occupancy(self, rows):
        self.occupancy.extend(dict(row) for row in rows)

    def write_outputs(self):
        write_allotment(self.output_dir / "allotment.csv", self.allotments)
        write_bills(self.output_dir / "bills.csv", self.bills)
        write_settlements(
            self.output_dir / "settlements.csv", self.settlements
        )
        write_dues(self.output_dir / "dues.csv", self.dues)
        write_occupancy(self.output_dir / "occupancy.csv", self.occupancy)