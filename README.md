# EO Table Management System

A dark-mode desktop application for managing EO (Engagement/Obligation) tracking data stored in an Excel workbook.

## Features

- **Per-user login** — select or create a user at startup; each user's Excel file path is remembered separately
- **Dark-mode UI** — built with CustomTkinter
- **Interactive data table** — view key columns with click-to-sort (ascending/descending) on any column
- **Status indicators** (based on `Status` field):
  - 🔴 Red — **Confirming Numbers** (`1st version complete`, `2nd version complete`)
  - 🟡 Yellow — **Contract & DM process** (`wait for contract approval`, `wait for contract sign`, `wait for DM`)
  - 🟢 Green — **Finish**
- **Default sort** — newest entries (by Update Date) shown first
- **Search / filter** — real-time text filter across all visible columns
- **Per-column filter** — right-click any column header to open a checkbox filter popup; filtered columns are marked with ◆; click anywhere outside to dismiss
- **Add & edit entries** — form dialog with:
  - Free-text fields for Platform, GTK Liability, DM #, PL, Rebate %
  - Dropdown selectors (A-Z sorted) for ODM, GBU, GTK Supplier, Sub-Category, Status
  - Sub-Category list is dynamically populated from existing Excel data
  - Dark-mode calendar date picker for Payment Received Date (blank by default, clearable with ✕)
- **Auto-calculated fields**:
  - `Actual Payment = Actual GTK Liability × (1 − Rebate %)` — rounded to 1 decimal
  - `Saving = GTK Liability − Actual Payment` — rounded to 1 decimal
  - `ESR need (Y/N)` — auto-set: `Y` if Actual Payment > 500,000, else `N`
  - `Payment Received Quarter` — HP fiscal quarter (Q1 = Nov/Dec/Jan, Q2 = Feb/Mar/Apr, Q3 = May/Jun/Jul, Q4 = Aug/Sep/Oct)
  - `Update Date` — auto-set to current timestamp on every save
- **Manage Options** — add/remove dropdown choices stored in `lookups.json`; bulk import from Excel supported
- **Writes back to Excel** — updates the `Data` sheet in the source workbook

## Fiscal Quarter Logic

| Quarter | Months        | FY Year based on |
|---------|---------------|-----------------|
| Q1      | Nov, Dec, Jan | January's year  |
| Q2      | Feb, Mar, Apr | Same year       |
| Q3      | May, Jun, Jul | Same year       |
| Q4      | Aug, Sep, Oct | Same year       |

Example: Nov 2025, Dec 2025, Jan 2026 → **FY26 Q1**

## Project Structure

```
EO-table-management-system/
├── main.py                  # Entry point
├── pyproject.toml           # Poetry configuration
├── poetry.toml              # in-project .venv setting
├── lookups.json             # Dropdown option lists (editable via UI)
├── config.json              # Auto-generated: user list + per-user Excel paths
└── app/
    ├── __init__.py
    ├── data_store.py        # Excel read/write + derived field calculations
    ├── main_window.py       # Main window (table view, top bar, filter)
    ├── entry_form.py        # Add / Edit entry dialog
    ├── user_selector.py     # Startup user selection dialog
    └── lookup_editor.py     # Manage dropdown options dialog
```

## Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)

### Install & Run

```powershell
# Clone the repo
git clone https://github.com/your-org/EO-table-management-system.git
cd EO-table-management-system

# Install dependencies
poetry install

# Launch the app
poetry run python main.py
```

## Excel Format

The app reads and writes to a sheet named **`Data`** in the target workbook.

Required columns (exact header text):

| Column | Input type |
|--------|-----------|
| Platform | Free text |
| ODM | Dropdown (`Foxconn`, `Inventec`, `Pegatron`, `Quanta`, `Wistron`) |
| GBU | Dropdown (`bDT`, `bNB`, `cDT`, `cNB`) |
| GTK Supplier | Dropdown (29 suppliers) |
| Sub-Category | Dropdown (dynamic from data + lookups.json) |
| GTK \nLiability $ | Free text (number) |
| Actual GTK \nLiability $ | Free text (number) |
| ESR need (Y/N) | **Auto-calculated** (Y if Actual Payment > 500,000) |
| Status | Dropdown |
| DM # | Free text |
| PL | Free text |
| Rebate Initiative % | Free text (number, e.g. `10` for 10%) |
| Actual Payment | **Auto-calculated** |
| Saving | **Auto-calculated** |
| Payment Received Date | Calendar picker |
| Payment Received Quarter | **Auto-calculated** |
| Update Date | **Auto-set** |

## Configuration

`config.json` is auto-created and managed by the app:

```json
{
  "users": ["Alice", "Bob"],
  "last_user": "Alice",
  "user_paths": {
    "Alice": "C:/path/to/EO_data.xlsx",
    "Bob": ""
  }
}
```

`lookups.json` stores dropdown options and can be edited via **Manage Options** in the UI or directly:

```json
{
  "ODM": ["Foxconn", "Inventec", "Pegatron", "Quanta", "Wistron"],
  "GBU": ["bDT", "bNB", "cDT", "cNB"],
  "GTK Supplier": ["AVC", "Auras", "BYS", "..."],
  "Sub-Category": [],
  "ESR need (Y/N)": ["Y", "N"],
  "Status": ["1st version complete", "2nd version complete", "Finish", "..."]
}
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| customtkinter | ≥5.2.2 | Dark-mode UI widgets |
| openpyxl | ≥3.1.5 | Excel read/write |
| tkcalendar | ≥1.6.1 | Calendar date picker |
