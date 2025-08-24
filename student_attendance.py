# student_attendance.py
# Standalone beginner-friendly Student Attendance Tracker (no ERPNext required)

import os
import json
import csv
from dataclasses import dataclass, asdict
from datetime import datetime

VALID_STATUSES = ["Present", "Absent", "Late"]

@dataclass
class AttendanceRecord:
    student_name: str
    date: str
    status: str
    remarks: str = ""

    def clean(self):
        self.student_name = (self.student_name or "").strip().title()
        self.status = (self.status or "").strip().capitalize()
        self.date = (self.date or "").strip()
        self.remarks = (self.remarks or "").strip()

    def validate(self):
        self.clean()
        try:
            datetime.strptime(self.date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format, e.g., 2025-08-24")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(VALID_STATUSES)}")
        if self.status == "Absent" and not self.remarks:
            raise ValueError("Remarks are required when the student is Absent.")
        if not self.student_name:
            raise ValueError("Student name cannot be empty.")

class AttendanceDB:
    def _init_(self, path="data/attendance.json"):
        self.path = path
        folder = os.path.dirname(path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)
        self._data = self._load()

    def _load(self):
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def add_record(self, rec: AttendanceRecord):
        rec.validate()
        for r in self._data:
            if r["student_name"].lower() == rec.student_name.lower() and r["date"] == rec.date:
                raise ValueError(f"Attendance already exists for {rec.student_name} on {rec.date}.")
        self.data.append(rec.dict_)
        self._save()

    def list_records(self, student_name=None, date_from=None, date_to=None):
        records = self._data
        if student_name:
            s = student_name.strip().lower()
            records = [r for r in records if r["student_name"].lower() == s]
        if date_from:
            records = [r for r in records if r["date"] >= date_from]
        if date_to:
            records = [r for r in records if r["date"] <= date_to]
        return records

    def student_monthly_percentage(self, student_name, year, month):
        from datetime import datetime as dt
        s = student_name.strip().lower()
        chosen = []
        for r in self._data:
            if r["student_name"].lower() != s:
                continue
            try:
                d = dt.strptime(r["date"], "%Y-%m-%d").date()
            except Exception:
                continue
            if d.year == year and d.month == month:
                chosen.append(r)
        total = len(chosen)
        present = sum(1 for r in chosen if r["status"] == "Present")
        pct = round((present / total * 100), 2) if total else 0.0
        return total, present, pct

    def export_csv(self, out_path="attendance_export.csv"):
        fieldnames = ["student_name", "date", "status", "remarks"]
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._data)
        return out_path

def prompt_record():
    name = input("Student name: ").strip()
    date_str = input("Date (YYYY-MM-DD): ").strip()
    status = input("Status (Present/Absent/Late): ").strip()
    remarks = ""
    if status.lower() == "absent":
        remarks = input("Remarks (required if Absent): ").strip()
    return AttendanceRecord(name, date_str, status, remarks)

def print_records(records):
    if not records:
        print("\n(No records found.)\n")
        return
    print("\nStudent Name | Date       | Status  | Remarks")
    print("-" * 60)
    for r in records:
        print(f"{r['student_name']:<12} | {r['date']:<10} | {r['status']:<7} | {r.get('remarks','')}")
    print()

def main_menu():
    db = AttendanceDB()
    while True:
        print("\n=== Student Attendance Tracker ===")
        print("1) Mark attendance")
        print("2) List all records")
        print("3) Filter by student/date range")
        print("4) Student monthly % report")
        print("5) Export CSV")
        print("6) Exit")

        choice = input("Choose an option (1-6): ").strip()
        try:
            if choice == "1":
                rec = prompt_record()
                db.add_record(rec)
                print("✅ Attendance saved successfully!\n")
            elif choice == "2":
                records = db.list_records()
                print_records(records)
            elif choice == "3":
                s = input("Filter by student name (or ENTER to skip): ").strip() or None
                df = input("Date from YYYY-MM-DD (or ENTER): ").strip() or None
                dt = input("Date to   YYYY-MM-DD (or ENTER): ").strip() or None
                records = db.list_records(student_name=s, date_from=df, date_to=dt)
                print_records(records)
            elif choice == "4":
                s = input("Student name: ").strip()
                y = int(input("Year (e.g., 2025): ").strip())
                m = int(input("Month (1-12): ").strip())
                total, present, pct = db.student_monthly_percentage(s, y, m)
                print(f"\nReport for {s.title()} - {y}-{m:02d}")
                print(f"Total marked days: {total}")
                print(f"Days present:     {present}")
                print(f"Attendance %:     {pct}%\n")
            elif choice == "5":
                out = db.export_csv()
                print(f"\nCSV exported to: {out}\n")
            elif choice == "6":
                print("Goodbye! 👋")
                break
            else:
                print("Please choose a valid option (1-6).\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if _name_ == "_main_":
    main_menu()
