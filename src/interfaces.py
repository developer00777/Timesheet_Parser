"""Abstractions following Interface Segregation and Dependency Inversion."""

from abc import ABC, abstractmethod
from typing import Optional

from src.models import TimesheetRecord, TimesheetSummary


class TimesheetReader(ABC):
    """Reads a single timesheet file and returns a TimesheetRecord."""

    @abstractmethod
    def read(self, file_path: str) -> TimesheetRecord:
        ...


class TimesheetRepository(ABC):
    """Stores and retrieves timesheet records."""

    @abstractmethod
    def save(self, record: TimesheetRecord) -> None:
        ...

    @abstractmethod
    def get_summary_by_avvas_id(self, avvas_id: str) -> Optional[TimesheetSummary]:
        ...

    @abstractmethod
    def get_all_summaries(self) -> list[dict]:
        ...

    @abstractmethod
    def get_record_by_avvas_id(self, avvas_id: str) -> Optional[TimesheetRecord]:
        ...


class SummaryCalculator(ABC):
    """Calculates summary from daily entries."""

    @abstractmethod
    def calculate(self, record: TimesheetRecord) -> TimesheetSummary:
        ...
