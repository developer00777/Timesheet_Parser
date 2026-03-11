"""Domain models for timesheet data."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DailyEntry:
    sl_no: int
    date: date
    day: str
    nature_of_shift: str
    hours_worked: float


@dataclass
class TimesheetSummary:
    total_hours_worked: float
    total_client_holidays: int
    total_days_worked: int
    total_billable_days: int
    total_el_taken: int
    total_sl_taken: int
    total_cl_taken: int


@dataclass
class TimesheetRecord:
    avvas_id: str
    sap_user_no: str
    sap_user_name: str
    sap_team_name: str
    vendor: str
    sap_reporting_manager: str
    month: str
    daily_entries: list[DailyEntry] = field(default_factory=list)
    summary: Optional[TimesheetSummary] = None
