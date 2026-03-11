# Product Requirements Document: Timesheet Parser API

## 1. Problem Statement

Avvas manages monthly timesheets for contractors/consultants as `.xls` Excel files with a standardized merged-cell layout. Each file contains one person's monthly attendance data including daily hours worked, leave types, and billing summary. Currently, extracting summary data from these files requires manual review. When dealing with 100+ timesheets per month, this is time-consuming and error-prone.

## 2. Objective

Build a self-hosted, dockerized API service that can batch-process up to 100 Avvas monthly timesheet `.xls` files in a single request and return structured JSON output keyed by each person's unique Avvas-ID.

## 3. Target Users

- **HR/Operations teams** processing monthly contractor timesheets
- **Finance/Billing teams** needing billable day counts and hour totals
- **Internal tools/dashboards** that consume timesheet data programmatically

## 4. Input Specification

### File Format
- `.xls` (Microsoft Excel 97-2003 format)
- Contains merged cells for metadata and summary sections

### File Layout (Fixed Structure)

| Row(s) | Content | Details |
|--------|---------|---------|
| 0 | Title | "Avvas - Monthly Time Sheet" (merged across all columns) |
| 1-7 | Metadata | Label in col 0, value in cols 2-4 (merged). Fields: SAP C-USER No, SAP C-USER Name, SAP Team Name, Vendor, SAP Reporting Manager, Month, Avvas-ID |
| 8 | Spacer | Empty row |
| 9 | Header | Sl.No, Date, Day, Nature of Shift/Activity, Hours worked |
| 10-40 | Daily Entries | Up to 31 rows, one per day of the month |
| 41-47 | Summary | 7 summary rows with totals (label merged in cols 0-2, value in col 3) |

### Daily Entry Fields
| Column | Field | Type |
|--------|-------|------|
| 0 | Sl.No | Integer (1-31) |
| 1 | Date | Excel date serial or text (e.g., "01-Jan-26") |
| 2 | Day | Text (e.g., "Monday") |
| 3 | Nature of Shift/Activity | Text (optional — leave type, holiday, etc.) |
| 4 | Hours worked | Number (0 for off days) |

## 5. Output Specification

### Response Format (JSON)

```json
{
  "results": {
    "<Avvas-ID>": {
      "metadata": {
        "sap_user_no": "string",
        "sap_user_name": "string",
        "sap_team_name": "string",
        "vendor": "string",
        "sap_reporting_manager": "string",
        "month": "string"
      },
      "summary": {
        "Total Number of Hours worked": 145.0,
        "Total Client Holidays": 3,
        "Total Number of Days worked": 22,
        "Total billable days": 22,
        "Total EL taken": 0,
        "Total SL taken": 1,
        "Total CL taken": 1
      },
      "daily_entries": [
        {
          "sl_no": 1,
          "date": "01-Jan-26",
          "day": "Sunday",
          "nature_of_shift": "",
          "hours_worked": 0.0
        }
      ]
    }
  },
  "errors": [
    {
      "file": "bad_file.xls",
      "error": "description of what went wrong"
    }
  ]
}
```

### Key Behaviors
- Results are **keyed by Avvas-ID** (unique identifier per person)
- If Avvas-ID is empty in the file, the **filename** is used as the key
- Summary values are read directly from the file (rows 41-47)
- All successfully parsed files appear in `results`, all failures in `errors`

## 6. API Specification

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/parse` | Upload and parse timesheet files |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI (auto-generated) |

### POST /parse

- **Content-Type:** `multipart/form-data`
- **Field:** `files` (repeatable, up to 100 files)
- **Accepted formats:** `.xls` only
- **Response:** JSON as described in Section 5

### Constraints
- Maximum **100 files** per request (returns 400 if exceeded)
- Only `.xls` format supported (`.xlsx` files are rejected with error)
- Files are processed sequentially and cleaned up after parsing

## 7. Non-Functional Requirements

| Requirement | Specification |
|-------------|---------------|
| Deployment | Docker container via Docker Compose |
| Port | 8080 (configurable in docker-compose.yml) |
| Runtime | Python 3.12, FastAPI, Uvicorn |
| File cleanup | Uploaded files are deleted after processing |
| Restart policy | `unless-stopped` |

## 8. Assumptions & Constraints

- All input files follow the exact same merged-cell layout described in Section 4
- The XLS structure (row positions, column positions) is fixed and will not change
- Files are in `.xls` format (Excel 97-2003), not `.xlsx`
- The "Nature of Shift/Activity" column may contain values like "EL", "SL", "CL", "Client Holiday", or be empty for regular working days
- Summary rows in the file already contain pre-calculated totals

## 9. Future Enhancements (Out of Scope for v1)

- `.xlsx` support (would require switching from xlrd to openpyxl)
- Recalculate/validate summary totals from daily entries instead of trusting file values
- Database storage for historical tracking
- Authentication/API keys
- CSV/PDF export of results
- Web UI for file upload
- Automatic detection of leave types from "Nature of Shift/Activity" column values
