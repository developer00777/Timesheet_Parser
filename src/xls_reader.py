"""XLS file reader - Single Responsibility: only reads .xls files into domain models."""

import xlrd
from datetime import datetime

from src.interfaces import TimesheetReader
from src.models import TimesheetRecord, DailyEntry, TimesheetSummary


# Row indices in the XLS structure
META_ROWS = {
    "sap_user_no": 1,
    "sap_user_name": 2,
    "sap_team_name": 3,
    "vendor": 4,
    "sap_reporting_manager": 5,
    "month": 6,
    "avvas_id": 7,
}
HEADER_ROW = 9
DATA_START_ROW = 10
SUMMARY_LABELS = {
    "Total Number of Hours worked": "total_hours_worked",
    "Total Cleint Holidays": "total_client_holidays",
    "Total Number of Days worked": "total_days_worked",
    "Total billable days": "total_billable_days",
    "Total EL taken": "total_el_taken",
    "Total SL taken": "total_sl_taken",
    "Total CL taken": "total_cl_taken",
}


class XlsTimesheetReader(TimesheetReader):
    """Reads .xls timesheet files with the Avvas monthly format."""

    def read(self, file_path: str) -> TimesheetRecord:
        wb = xlrd.open_workbook(file_path)
        sheet = wb.sheet_by_index(0)

        record = TimesheetRecord(
            avvas_id=self._read_meta(sheet, META_ROWS["avvas_id"]),
            sap_user_no=self._read_meta(sheet, META_ROWS["sap_user_no"]),
            sap_user_name=self._read_meta(sheet, META_ROWS["sap_user_name"]),
            sap_team_name=self._read_meta(sheet, META_ROWS["sap_team_name"]),
            vendor=self._read_meta(sheet, META_ROWS["vendor"]),
            sap_reporting_manager=self._read_meta(sheet, META_ROWS["sap_reporting_manager"]),
            month=self._read_meta(sheet, META_ROWS["month"]),
        )

        record.daily_entries = self._read_daily_entries(sheet, wb)
        record.summary = self._read_summary(sheet)

        return record

    def _read_meta(self, sheet: xlrd.sheet.Sheet, row: int) -> str:
        """Metadata value is in column 1 or beyond (after the label in col 0)."""
        for col in range(1, sheet.ncols):
            val = sheet.cell_value(row, col)
            if val:
                return str(val).strip()
        return ""

    def _read_daily_entries(self, sheet: xlrd.sheet.Sheet, wb: xlrd.Book) -> list[DailyEntry]:
        entries = []
        for row in range(DATA_START_ROW, sheet.nrows):
            cell_type = sheet.cell_type(row, 0)
            cell_val = sheet.cell_value(row, 0)

            # Stop when we hit a summary label (text in col 0 that's not a number)
            if cell_type == xlrd.XL_CELL_TEXT:
                break

            if cell_type != xlrd.XL_CELL_NUMBER:
                continue

            sl_no = int(cell_val)
            date_val = self._parse_date(sheet, wb, row, 1)
            day = str(sheet.cell_value(row, 2)).strip()
            nature = str(sheet.cell_value(row, 3)).strip() if sheet.cell_value(row, 3) else ""
            hours = float(sheet.cell_value(row, 4)) if sheet.cell_value(row, 4) else 0.0

            entries.append(DailyEntry(
                sl_no=sl_no,
                date=date_val,
                day=day,
                nature_of_shift=nature,
                hours_worked=hours,
            ))

        return entries

    def _parse_date(self, sheet, wb, row, col):
        cell_type = sheet.cell_type(row, col)
        cell_val = sheet.cell_value(row, col)

        if cell_type == xlrd.XL_CELL_DATE:
            dt_tuple = xlrd.xldate_as_tuple(cell_val, wb.datemode)
            return datetime(*dt_tuple[:3]).date()
        elif cell_type == xlrd.XL_CELL_TEXT:
            for fmt in ("%d-%b-%y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(cell_val.strip(), fmt).date()
                except ValueError:
                    continue
        return None

    def _read_summary(self, sheet: xlrd.sheet.Sheet) -> TimesheetSummary:
        summary_data = {}
        for row in range(DATA_START_ROW, sheet.nrows):
            label = str(sheet.cell_value(row, 0)).strip()
            for key_prefix, field_name in SUMMARY_LABELS.items():
                if label.startswith(key_prefix):
                    val = sheet.cell_value(row, 3) or sheet.cell_value(row, 4) or 0
                    summary_data[field_name] = float(val)
                    break

        return TimesheetSummary(
            total_hours_worked=summary_data.get("total_hours_worked", 0),
            total_client_holidays=int(summary_data.get("total_client_holidays", 0)),
            total_days_worked=int(summary_data.get("total_days_worked", 0)),
            total_billable_days=int(summary_data.get("total_billable_days", 0)),
            total_el_taken=int(summary_data.get("total_el_taken", 0)),
            total_sl_taken=int(summary_data.get("total_sl_taken", 0)),
            total_cl_taken=int(summary_data.get("total_cl_taken", 0)),
        )
