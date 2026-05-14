"""
Add / Edit row dialog — with a fully dark-themed date picker.
"""

from __future__ import annotations

import json
import os
import tkinter as tk
from datetime import date, datetime
from typing import Optional

import customtkinter as ctk
from tkcalendar import Calendar

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOKUPS_PATH = os.path.join(ROOT_DIR, "lookups.json")

# Fields entered by free-text input
FREE_TEXT_FIELDS = [
    "Platform",
    "GTK \nLiability $",
    "Actual GTK \nLiability $",
    "DM #",
    "PL",
    "Rebate Initiative %",
]

# All form fields (order matters for layout)
FORM_FIELDS = [
    "Platform",
    "ODM",
    "GBU",
    "GTK Supplier",
    "Sub-Category",
    "GTK \nLiability $",
    "Actual GTK \nLiability $",
    "Status",
    "DM #",
    "PL",
    "Rebate Initiative %",
    "Payment Received Date",
]

INPUT_WIDTH = 300
LABEL_WIDTH = 210
# Date picker breakdown: entry + gap + button = INPUT_WIDTH
_DATE_ENTRY_W = INPUT_WIDTH - 6 - 42  # = 252


def _load_lookups() -> dict:
    if os.path.exists(LOOKUPS_PATH):
        with open(LOOKUPS_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _label_text(field: str) -> str:
    return field.replace("\n", " ")


# ─────────────────────────────── Dark Date Picker ────────────────────────────

class DarkDatePicker(ctk.CTkFrame):
    """A dark-themed date picker: read-only CTkEntry + calendar popup button + clear button."""

    def __init__(self, master, initial_date: Optional[date] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        # None means "blank / not set"
        self._date: Optional[date] = initial_date
        self._var = tk.StringVar(value=self._date.strftime("%Y-%m-%d") if self._date else "")
        _fi = ctk.CTkFont(size=13)

        self._entry = ctk.CTkEntry(
            self, textvariable=self._var, width=_DATE_ENTRY_W, height=34,
            font=_fi, state="readonly",
        )
        self._entry.pack(side="left", padx=(0, 6))

        self._btn = ctk.CTkButton(
            self, text="📅", width=42, height=34,
            font=ctk.CTkFont(size=14),
            command=self._open_picker,
        )
        self._btn.pack(side="left", padx=(0, 4))

        self._clear_btn = ctk.CTkButton(
            self, text="✕", width=34, height=34,
            font=ctk.CTkFont(size=13),
            fg_color="gray35", hover_color="gray25",
            command=self._clear,
        )
        self._clear_btn.pack(side="left")

    def _open_picker(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(fg_color="#1e1e1e")

        # Calendar defaults to today if no date is set
        show_date = self._date or date.today()

        cal = Calendar(
            popup,
            selectmode="day",
            year=show_date.year,
            month=show_date.month,
            day=show_date.day,
            date_pattern="yyyy-mm-dd",
            background="#1f538d",
            foreground="white",
            headersbackground="#1f538d",
            headersforeground="white",
            normalbackground="#2b2b2b",
            normalforeground="white",
            weekendbackground="#2b2b2b",
            weekendforeground="#8ab4f8",
            othermonthforeground="#555555",
            othermonthweforeground="#555555",
            selectbackground="#1f538d",
            selectforeground="white",
            bordercolor="#3a3a3a",
            borderwidth=0,
            font=("Arial", 12),
        )
        cal.pack(padx=12, pady=(12, 6))

        ctk.CTkButton(
            popup, text="Confirm", width=120, height=34,
            font=ctk.CTkFont(size=13),
            command=lambda: self._confirm(cal, popup),
        ).pack(pady=(0, 12))

        popup.update_idletasks()
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        pw = popup.winfo_reqwidth()
        ph = popup.winfo_reqheight()
        popup.geometry(f"+{max(0, sw//2 - pw//2)}+{max(0, sh//2 - ph//2)}")

    def _confirm(self, cal: Calendar, popup: ctk.CTkToplevel):
        try:
            self._date = datetime.strptime(cal.get_date(), "%Y-%m-%d").date()
            self._var.set(self._date.strftime("%Y-%m-%d"))
        except Exception:
            pass
        popup.destroy()

    def _clear(self):
        self._date = None
        self._var.set("")

    def get_date(self) -> Optional[date]:
        if not self._var.get():
            return None
        try:
            return datetime.strptime(self._var.get(), "%Y-%m-%d").date()
        except ValueError:
            return self._date

    def get_date_str(self) -> str:
        """Returns 'YYYY-MM-DD' string or empty string if blank."""
        return self._var.get()


# ──────────────────────────────── Form Dialog ────────────────────────────────

class EntryFormDialog(ctk.CTkToplevel):
    """Modal dialog for adding or editing a row."""

    def __init__(self, parent, existing_row: Optional[dict] = None,
                 title: str = "Add Entry", store=None, pl_map: Optional[dict] = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, True)
        self.grab_set()

        self._lookups = _load_lookups()
        self._store = store
        self._pl_map: dict = pl_map or {}   # Family -> Product Line 2
        self._result: Optional[dict] = None
        self._widgets: dict[str, tk.Widget] = {}
        self._vars: dict[str, tk.Variable] = {}
        self._fl = ctk.CTkFont(size=13)
        self._fh = ctk.CTkFont(size=17, weight="bold")

        # PL auto-fill state
        self._auto_filling   = False   # True while we programmatically set PL
        self._pl_manually_set = False  # True once user types in PL field

        self._build_ui(existing_row)

        # After all vars are set: decide if existing PL was manually overridden
        if existing_row:
            platform    = str(existing_row.get("Platform") or "").strip().lower()
            existing_pl = str(existing_row.get("PL") or "").strip()
            map_pl      = self._pl_map.get(platform, "")
            if existing_pl and existing_pl != map_pl:
                self._pl_manually_set = True

        # Wire up traces AFTER initial values are loaded
        if "Platform" in self._vars:
            self._vars["Platform"].trace_add("write", self._on_platform_changed)
        if "PL" in self._vars:
            self._vars["PL"].trace_add("write", self._on_pl_changed)

        self._center(parent)

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self, existing_row: Optional[dict]):
        pad = {"padx": 14, "pady": 6}

        ctk.CTkLabel(self, text=self.title(), font=self._fh).grid(
            row=0, column=0, columnspan=2, pady=(16, 8)
        )

        for idx, field in enumerate(FORM_FIELDS):
            row_num = idx + 1
            ctk.CTkLabel(
                self, text=_label_text(field) + ":",
                anchor="e", width=LABEL_WIDTH, font=self._fl,
            ).grid(row=row_num, column=0, sticky="e", **pad)

            if field == "Payment Received Date":
                # Only pre-fill if editing an existing row with a date value
                init_date: Optional[date] = None
                if existing_row and existing_row.get(field):
                    raw = existing_row[field]
                    if isinstance(raw, (date, datetime)):
                        init_date = raw if isinstance(raw, date) else raw.date()
                    elif isinstance(raw, str) and raw.strip():
                        try:
                            init_date = datetime.strptime(raw.strip(), "%Y-%m-%d").date()
                        except ValueError:
                            pass
                picker = DarkDatePicker(self, initial_date=init_date)
                picker.grid(row=row_num, column=1, sticky="w", **pad)
                self._widgets[field] = picker

            elif field in FREE_TEXT_FIELDS:
                var = tk.StringVar()
                if existing_row and existing_row.get(field) is not None:
                    var.set(str(existing_row[field]))
                entry = ctk.CTkEntry(self, textvariable=var, width=INPUT_WIDTH, height=34, font=self._fl)
                entry.grid(row=row_num, column=1, sticky="w", **pad)
                self._vars[field] = var
                self._widgets[field] = entry

            else:
                if field == "Sub-Category" and self._store:
                    # Dynamic: unique values from Excel data
                    live = {
                        str(r.get("Sub-Category") or "").strip()
                        for r in self._store.get_rows()
                    }
                    seed = set(self._lookups.get(field, []))
                    options_sorted = sorted((live | seed) - {""})
                else:
                    options_sorted = sorted(self._lookups.get(field, []))
                var = tk.StringVar()
                if existing_row and existing_row.get(field) is not None:
                    var.set(str(existing_row[field]))
                elif options_sorted:
                    var.set(options_sorted[0])
                # CTkOptionMenu: dropdown width always matches button width (no mismatch)
                opt = ctk.CTkOptionMenu(
                    self, variable=var, values=options_sorted,
                    width=INPUT_WIDTH, height=34,
                    font=self._fl,
                    dropdown_font=ctk.CTkFont(size=13),
                )
                opt.grid(row=row_num, column=1, sticky="w", **pad)
                self._vars[field] = var
                self._widgets[field] = opt

        btn_row = len(FORM_FIELDS) + 1
        ctk.CTkButton(
            self, text="Save", width=130, height=36,
            font=ctk.CTkFont(size=13, weight="bold"), command=self._on_save,
        ).grid(row=btn_row, column=0, pady=(18, 16), padx=14, sticky="e")
        ctk.CTkButton(
            self, text="Cancel", width=130, height=36,
            font=ctk.CTkFont(size=13), fg_color="gray40", hover_color="gray30",
            command=self.destroy,
        ).grid(row=btn_row, column=1, pady=(18, 16), padx=14, sticky="w")

    # ----------------------------------------------------- PL auto-mapping --
    def _on_platform_changed(self, *_):
        """Auto-fill PL from the PL map whenever Platform changes."""
        if self._pl_manually_set:
            return
        platform = self._vars.get("Platform")
        pl_var   = self._vars.get("PL")
        if platform is None or pl_var is None:
            return
        auto_pl = self._pl_map.get(platform.get().strip().lower(), "")
        self._auto_filling = True
        pl_var.set(auto_pl)
        self._auto_filling = False

    def _on_pl_changed(self, *_):
        """Mark PL as manually set if the user typed in the PL field."""
        if self._auto_filling:
            return
        self._pl_manually_set = True

    # -------------------------------------------------------------- actions --
    def _on_save(self):
        row = {}
        for field in FORM_FIELDS:
            widget = self._widgets.get(field)
            if widget is None:
                row[field] = None
            elif field == "Payment Received Date":
                row[field] = widget.get_date_str()
            else:
                var = self._vars.get(field)
                row[field] = var.get() if var else None
        self._result = row
        self.destroy()

    def get_result(self) -> Optional[dict]:
        return self._result

    def _center(self, parent):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = max(0, sw // 2 - w // 2)
        y = max(0, sh // 2 - h // 2)
        self.geometry(f"+{x}+{y}")
