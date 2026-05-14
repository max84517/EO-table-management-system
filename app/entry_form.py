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


# ─────────────────────────── Scrollable Dropdown ─────────────────────────────

class ScrollableDropdown(ctk.CTkFrame):
    """A dark-themed button that opens a scrollable Listbox popup for long option lists."""

    def __init__(self, master, variable: tk.StringVar, values: list[str],
                 width: int = 300, height: int = 34, font=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._var = variable
        self._values = values
        self._width = width
        self._font = font or ("Arial", 13)
        self._popup: Optional[tk.Toplevel] = None

        self._btn = ctk.CTkButton(
            self, text=self._var.get(), width=width, height=height,
            font=self._font, anchor="w",
            fg_color="#2b2b2b", hover_color="#3a3a3a",
            border_width=1, border_color="#555555",
            command=self._toggle_popup,
        )
        self._btn.pack(side="left")

        # Keep button label in sync with variable
        self._var.trace_add("write", lambda *_: self._btn.configure(text=self._var.get()))

    def _toggle_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
            return
        self._open_popup()

    def _open_popup(self):
        top = self.winfo_toplevel()
        popup = tk.Toplevel(top)
        self._popup = popup
        popup.overrideredirect(True)
        popup.configure(bg="#3a3a3a")  # thin border colour

        # Position below the button
        self.update_idletasks()
        bx = self._btn.winfo_rootx()
        by = self._btn.winfo_rooty() + self._btn.winfo_height() + 2
        popup.geometry(f"{self._width}x220+{bx}+{by}")

        frame = tk.Frame(popup, bg="#2b2b2b")
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        scrollbar = tk.Scrollbar(frame, orient="vertical", bg="#3a3a3a",
                                  troughcolor="#2b2b2b", relief="flat")
        lb = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            bg="#2b2b2b", fg="white",
            selectbackground="#1f538d", selectforeground="white",
            font=("Arial", 12), relief="flat",
            highlightthickness=0, borderwidth=0,
            activestyle="none",
        )
        scrollbar.config(command=lb.yview)
        scrollbar.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)

        for v in self._values:
            lb.insert("end", v)

        # Pre-select current value
        cur = self._var.get()
        if cur in self._values:
            idx = self._values.index(cur)
            lb.selection_set(idx)
            lb.see(idx)

        def _select(event=None):
            sel = lb.curselection()
            if sel:
                self._var.set(self._values[sel[0]])
            if self._popup and self._popup.winfo_exists():
                self._popup.destroy()
            self._popup = None

        lb.bind("<ButtonRelease-1>", _select)
        lb.bind("<Return>", _select)

        # Close on click outside (delay so this binding is installed after open)
        def _on_outside_click(event):
            if not (self._popup and self._popup.winfo_exists()):
                return
            wx = self._popup.winfo_rootx()
            wy = self._popup.winfo_rooty()
            ww = self._popup.winfo_width()
            wh = self._popup.winfo_height()
            if not (wx <= event.x_root <= wx + ww and wy <= event.y_root <= wy + wh):
                self._popup.destroy()
                self._popup = None
                top.unbind_all("<Button-1>")

        popup.after(100, lambda: top.bind_all("<Button-1>", _on_outside_click))

        # Mouse wheel scrolling
        def _mousewheel(event):
            lb.yview_scroll(int(-1 * (event.delta / 120)), "units")

        lb.bind("<MouseWheel>", _mousewheel)
        lb.focus_set()

    def get(self) -> str:
        return self._var.get()

    def set(self, value: str):
        self._var.set(value)

    def configure(self, **kwargs):
        if "state" in kwargs:
            self._btn.configure(state=kwargs.pop("state"))
        if kwargs:
            super().configure(**kwargs)


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

    def set_enabled(self, enabled: bool):
        """Enable or disable the calendar button and clear button."""
        state = "normal" if enabled else "disabled"
        self._btn.configure(state=state)
        self._clear_btn.configure(state=state)
        # Grey out the entry text to signal disabled state
        self._entry.configure(text_color="gray60" if not enabled else "white")

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
        self._deleted: bool = False          # True if user pressed Delete
        self._is_edit: bool = existing_row is not None
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
        if "Status" in self._vars:
            self._vars["Status"].trace_add("write", self._on_status_changed)
        if "Actual GTK \nLiability $" in self._vars:
            self._vars["Actual GTK \nLiability $"].trace_add("write", self._on_status_changed)

        # Set initial date-picker state
        self._on_status_changed()

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
                # Disable until conditions met (will be updated by trace)
                picker.set_enabled(False)

            elif field in FREE_TEXT_FIELDS:
                var = tk.StringVar()
                if existing_row and existing_row.get(field) is not None:
                    var.set(str(existing_row[field]))
                entry = ctk.CTkEntry(self, textvariable=var, width=INPUT_WIDTH, height=34, font=self._fl)
                entry.grid(row=row_num, column=1, sticky="w", **pad)
                self._vars[field] = var
                self._widgets[field] = entry

            else:
                options_sorted = sorted(self._lookups.get(field, []))
                var = tk.StringVar()
                if existing_row and existing_row.get(field) is not None:
                    var.set(str(existing_row[field]))
                elif options_sorted:
                    var.set(options_sorted[0])

                if field == "GTK Supplier":
                    # Use scrollable dropdown for long lists
                    widget = ScrollableDropdown(
                        self, variable=var, values=options_sorted,
                        width=INPUT_WIDTH, height=34,
                        font=self._fl,
                    )
                    widget.grid(row=row_num, column=1, sticky="w", **pad)
                    self._vars[field] = var
                    self._widgets[field] = widget
                else:
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
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=btn_row, column=0, columnspan=2, pady=(18, 16))

        ctk.CTkButton(
            btn_frame, text="Save", width=130, height=36,
            font=ctk.CTkFont(size=13, weight="bold"), command=self._on_save,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="Cancel", width=130, height=36,
            font=ctk.CTkFont(size=13), fg_color="gray40", hover_color="gray30",
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))

        # Delete button — only shown when editing an existing row
        if self._is_edit:
            ctk.CTkButton(
                btn_frame, text="Delete", width=130, height=36,
                font=ctk.CTkFont(size=13), fg_color="#8b1a1a", hover_color="#6b1010",
                command=self._on_delete,
            ).pack(side="left")

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

    def _on_status_changed(self, *_):
        """Enable Payment Received Date only when Status=Finish AND Actual GTK Liability filled."""
        picker = self._widgets.get("Payment Received Date")
        if picker is None:
            return
        status = self._vars.get("Status")
        actual = self._vars.get("Actual GTK \nLiability $")
        status_ok = status is not None and status.get().strip() == "Finish"
        actual_ok = actual is not None and actual.get().strip() not in ("", "0")
        picker.set_enabled(status_ok and actual_ok)

    # --------------------------------------------------- validation on save --
    def _on_save(self):
        from tkinter import messagebox as _mb
        # Guard 1: Status = Finish requires DM # to be filled
        status_var = self._vars.get("Status")
        dm_var     = self._vars.get("DM #")
        if status_var and status_var.get().strip() == "Finish":
            if not dm_var or not dm_var.get().strip():
                _mb.showwarning(
                    "Missing DM #",
                    "Please enter a DM # before setting Status to \"Finish\".",
                    parent=self,
                )
                return

        # Guard 2: Duplicate Platform + GTK Supplier check (Add mode only)
        if not self._is_edit and self._store:
            platform_val = (self._vars.get("Platform") or tk.StringVar()).get().strip()
            supplier_val = (self._vars.get("GTK Supplier") or tk.StringVar()).get().strip()
            if platform_val and supplier_val:
                duplicate = any(
                    str(r.get("Platform") or "").strip() == platform_val
                    and str(r.get("GTK Supplier") or "").strip() == supplier_val
                    for r in self._store.get_rows()
                )
                if duplicate:
                    proceed = _mb.askokcancel(
                        "Duplicate Entry",
                        f'A record with Platform "{platform_val}" and '
                        f'GTK Supplier "{supplier_val}" already exists.\n\n'
                        "Do you still want to add this entry?",
                        default="cancel",   # default focus on Cancel
                        parent=self,
                    )
                    if not proceed:
                        return
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

    def is_deleted(self) -> bool:
        return self._deleted

    def _on_delete(self):
        from tkinter import messagebox as _mb
        confirmed = _mb.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this entry?\nThis action cannot be undone.",
            default="no",
            parent=self,
        )
        if confirmed:
            self._deleted = True
            self.destroy()

    def _center(self, parent):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = max(0, sw // 2 - w // 2)
        y = max(0, sh // 2 - h // 2)
        self.geometry(f"+{x}+{y}")
