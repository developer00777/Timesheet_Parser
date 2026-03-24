"""Parses .xls timesheet files with merged cells into structured data."""

import xlrd
from datetime import datetime


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


def parse_timesheet(file_path: str) -> dict:
    """Parse a single .xls timesheet and return structured dict."""
    wb = xlrd.open_workbook(file_path, formatting_info=True)
    sheet = wb.sheet_by_index(0)

    # Read metadata - values are in merged cell range starting at col 2
    def read_meta(row: int) -> str:
        for col in range(1, sheet.ncols):
            val = sheet.cell_value(row, col)
            if val:
                return str(val).strip()
        return ""

    avvas_id = read_meta(META_ROWS["avvas_id"])
    meta = {
        "sap_user_no": read_meta(META_ROWS["sap_user_no"]),
        "sap_user_name": read_meta(META_ROWS["sap_user_name"]),
        "sap_team_name": read_meta(META_ROWS["sap_team_name"]),
        "vendor": read_meta(META_ROWS["vendor"]),
        "sap_reporting_manager": read_meta(META_ROWS["sap_reporting_manager"]),
        "month": read_meta(META_ROWS["month"]),
    }

    # Read daily entries
    daily_entries = []
    for row in range(DATA_START_ROW, sheet.nrows):
        cell_type = sheet.cell_type(row, 0)
        if cell_type == xlrd.XL_CELL_TEXT:
            break  # Hit summary section
        if cell_type != xlrd.XL_CELL_NUMBER:
            continue

        sl_no = int(sheet.cell_value(row, 0))

        # Parse date
        date_val = None
        if sheet.cell_type(row, 1) == xlrd.XL_CELL_DATE:
            dt_tuple = xlrd.xldate_as_tuple(sheet.cell_value(row, 1), wb.datemode)
            date_val = datetime(*dt_tuple[:3]).strftime("%d-%b-%y")
        elif sheet.cell_type(row, 1) == xlrd.XL_CELL_TEXT:
            date_val = sheet.cell_value(row, 1).strip()

        day = str(sheet.cell_value(row, 2)).strip()
        nature = str(sheet.cell_value(row, 3)).strip() if sheet.cell_value(row, 3) else ""
        hours = float(sheet.cell_value(row, 4)) if sheet.cell_value(row, 4) else 0.0

        daily_entries.append({
            "sl_no": sl_no,
            "date": date_val,
            "day": day,
            "nature_of_shift": nature,
            "hours_worked": hours,
        })

    # Read summary from file
    summary_data = {}
    for row in range(DATA_START_ROW, sheet.nrows):
        label = str(sheet.cell_value(row, 0)).strip()
        for key_prefix, field_name in SUMMARY_LABELS.items():
            if label.startswith(key_prefix):
                val = sheet.cell_value(row, 3) or sheet.cell_value(row, 4) or 0
                summary_data[field_name] = float(val)
                break

    # Fall back to computing values from daily entries if summary section is missing/zero
    def _compute_from_entries(field: str, entries: list) -> float | int:
        if field == "total_hours_worked":
            return sum(e["hours_worked"] for e in entries)
        if field == "total_days_worked":
            return sum(1 for e in entries if e["hours_worked"] > 0)
        if field == "total_billable_days":
            return sum(1 for e in entries if e["hours_worked"] > 0)
        if field == "total_client_holidays":
            return sum(1 for e in entries if "holiday" in e["nature_of_shift"].lower())
        if field == "total_el_taken":
            return sum(1 for e in entries if e["nature_of_shift"].strip().upper() == "EL")
        if field == "total_sl_taken":
            return sum(1 for e in entries if e["nature_of_shift"].strip().upper() == "SL")
        if field == "total_cl_taken":
            return sum(1 for e in entries if e["nature_of_shift"].strip().upper() == "CL")
        return 0

    def _get(field: str, is_float: bool = False):
        val = summary_data.get(field, 0)
        if val == 0:
            val = _compute_from_entries(field, daily_entries)
        return float(val) if is_float else int(val)

    summary = {
        "Total Number of Hours worked": _get("total_hours_worked", is_float=True),
        "Total Client Holidays": _get("total_client_holidays"),
        "Total Number of Days worked": _get("total_days_worked"),
        "Total billable days": _get("total_billable_days"),
        "Total EL taken": _get("total_el_taken"),
        "Total SL taken": _get("total_sl_taken"),
        "Total CL taken": _get("total_cl_taken"),
    }

    return {
        "avvas_id": avvas_id,
        "metadata": meta,
        "summary": summary,
        "daily_entries": daily_entries,
    }
