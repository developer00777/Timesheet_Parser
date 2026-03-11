# Timesheet Parser

## Project Overview
FastAPI-based dockerized service that batch-processes Avvas monthly timesheet `.xls` files (with merged cells) and returns structured JSON summaries keyed by Avvas-ID.

## Tech Stack
- **Language:** Python 3.12
- **Framework:** FastAPI + Uvicorn
- **XLS Parsing:** xlrd (v2.0.1, supports `.xls` format with `formatting_info=True` for merged cells)
- **Containerization:** Docker + Docker Compose
- **Port:** 8080 (host) -> 8000 (container)

## Project Structure
```
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, endpoints: POST /parse, GET /health
│   └── parser.py        # XLS parsing logic (merged cells, metadata, daily entries, summary)
├── src/                  # Legacy code (original domain models & interfaces, not used by the API)
│   ├── __init__.py
│   ├── interfaces.py
│   ├── models.py
│   └── xls_reader.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── Time Sheet.xls       # Sample input file
```

## XLS File Structure (Merged Cells)
- **Row 0:** Title ("Avvas - Monthly Time Sheet") — merged across all 5 cols
- **Rows 1-7:** Metadata — label in col 0, value in col 2 (merged cells cols 2-4)
  - Row 1: SAP C-USER No | Row 2: SAP C-USER Name | Row 3: SAP Team Name
  - Row 4: Vendor | Row 5: SAP Reporting Manager | Row 6: Month | Row 7: Avvas-ID
- **Row 8:** Empty spacer row
- **Row 9:** Header row (Sl.No, Date, Day, Nature of Shift/Activity, Hours worked)
- **Rows 10-40:** Daily entries (up to 31 days). Dates are xlrd date type (float serial numbers).
- **Rows 41-47:** Summary totals — label in col 0 (merged cols 0-2), value in col 3

## Key Design Decisions
- `xlrd.open_workbook(file_path, formatting_info=True)` is required to read merged cell info
- Metadata values are read by scanning cols 1+ for non-empty values (handles merged cell offsets)
- Daily entry parsing stops when col 0 contains text (summary labels) instead of a number
- When Avvas-ID is empty, the filename is used as the key in the response
- Summary values are read from col 3 (the first non-merged column after the label)

## Authentication
- API key based auth via `X-API-Key` header
- Key is set via `API_KEY` environment variable (default: `changeme`)
- Set in `docker-compose.yml` or via `.env` file: `API_KEY=your-secret-key`
- `/health` is unauthenticated; `/parse` requires the key

## Commands
```bash
# Build and run
docker compose up -d --build

# Build with custom API key
API_KEY=my-secret-key docker compose up -d --build

# Test health (no auth needed)
curl http://localhost:8080/health

# Parse single file
curl -H "X-API-Key: changeme" -F "files=@Time Sheet.xls" http://localhost:8080/parse

# Parse multiple files
curl -H "X-API-Key: changeme" -F "files=@file1.xls" -F "files=@file2.xls" http://localhost:8080/parse

# View logs
docker compose logs -f

# Stop
docker compose down
```

## API Endpoints
- `POST /parse` — Upload up to 100 `.xls` files, returns JSON with results keyed by Avvas-ID and an errors array. **Requires `X-API-Key` header.**
- `GET /health` — Health check, returns `{"status": "ok"}` (no auth)
- `GET /docs` — Swagger UI (supports "Authorize" button for API key)

## Conventions
- Keep parsing logic in `app/parser.py`, API routing in `app/main.py`
- Only `.xls` files are supported (not `.xlsx`) — xlrd v2 dropped xlsx support
- Uploaded files are written to `/tmp/timesheets/` inside the container and cleaned up after processing
- API key is passed via env var, never hardcoded in source
