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
    "Actual Payment",
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
    "Actual Payment",
    "DM Issued Date",
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
        if "Sub-Category" in self._vars:
            self._vars["Sub-Category"].trace_add("write", self._on_subcategory_changed)

        # Set initial date-picker state
        self._on_status_changed()
        # Set initial Actual Payment lock state
        self._on_subcategory_changed()

        self._center(parent)

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self, existing_row: Optional[dict]):
        pad = {"padx": 14, "pady": 6}

        ctk.CTkLabel(self, text=self.title(), font=self._fh).grid(
            row=0, column=0, columnspan=2, pady=(16, 8)
        )

        for idx, field in enumerate(FORM_FIELDS):
            row_num = idx + 1
            lbl = ctk.CTkLabel(
                self, text=_label_text(field) + ":",
                anchor="e", width=LABEL_WIDTH, font=self._fl,
            )
            lbl.grid(row=row_num, column=0, sticky="e", **pad)
            # Keep reference to Rebate Initiative and Actual GTK Liability labels for show/hide
            if field == "Rebate Initiative %":
                self._rebate_label = lbl
            if field == "Actual GTK \nLiability $":
                self._actual_gtk_label = lbl

            if field == "DM Issued Date":
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
                    raw_val = existing_row[field]
                    if field == "Rebate Initiative %" and raw_val not in (None, ""):
                        try:
                            fv = float(raw_val)
                            # Convert decimal fraction stored in Excel (e.g. 0.1) → integer display (10)
                            display_val = int(round(fv * 100)) if fv <= 1.0 else int(round(fv))
                            raw_val = str(display_val)
                        except (ValueError, TypeError):
                            raw_val = str(raw_val)
                    var.set(str(raw_val))
                elif field == "Rebate Initiative %":
                    var.set("10")  # default 10%
                entry = ctk.CTkEntry(self, textvariable=var, width=INPUT_WIDTH, height=34, font=self._fl)
                entry.grid(row=row_num, column=1, sticky="w", **pad)
                self._vars[field] = var
                self._widgets[field] = entry

                if field == "Actual Payment":
                    # Small hint label shown to the right when locked
                    hint = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11),
                                        text_color="gray55")
                    hint.grid(row=row_num, column=2, sticky="w", padx=(0, 8))
                    self._ap_hint_label = hint

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

    def _on_subcategory_changed(self, *_):
        """Lock Actual Payment entry when Sub-Category is Keyboard/Fingerprint/Touchpad.
        Also hide Rebate Initiative % for other sub-categories."""
        sub_var = self._vars.get("Sub-Category")
        ap_widget = self._widgets.get("Actual Payment")
        ap_label  = getattr(self, "_ap_hint_label", None)
        rebate_widget = self._widgets.get("Rebate Initiative %")
        rebate_label  = getattr(self, "_rebate_label", None)

        is_keyboard = sub_var is not None and sub_var.get().strip() in ("Keyboard", "Fingerprint/Touchpad")

        # Lock / unlock Actual Payment
        if ap_widget is not None:
            if is_keyboard:
                ap_widget.configure(state="disabled", text_color="gray50",
                                    placeholder_text="Auto-calculated")
            else:
                ap_widget.configure(state="normal", text_color="white",
                                    placeholder_text="")
        if ap_label:
            ap_label.configure(text="(auto-calculated)" if is_keyboard else "")

        # Show / hide Rebate Initiative %
        if rebate_widget is not None and rebate_label is not None:
            if is_keyboard:
                rebate_label.grid()
                rebate_widget.grid()
            else:
                rebate_label.grid_remove()
                rebate_widget.grid_remove()

        # Show / hide Actual GTK Liability $
        actual_gtk_widget = self._widgets.get("Actual GTK \nLiability $")
        actual_gtk_label  = getattr(self, "_actual_gtk_label", None)
        if actual_gtk_widget is not None and actual_gtk_label is not None:
            if is_keyboard:
                actual_gtk_label.grid()
                actual_gtk_widget.grid()
            else:
                actual_gtk_label.grid_remove()
                actual_gtk_widget.grid_remove()

    def _on_status_changed(self, *_):
        """Enable DM Issued Date whenever Status = Finish."""
        picker = self._widgets.get("DM Issued Date")
        if picker is None:
            return
        status = self._vars.get("Status")
        status_ok = status is not None and status.get().strip() == "Finish"
        picker.set_enabled(status_ok)

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
            elif field == "DM Issued Date":
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


# ──────────────────────────── Compact Date Picker ────────────────────────────

class CompactDatePicker(ctk.CTkFrame):
    """Minimal date picker for multi-entry rows: one button showing the date + one ✕."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._date: Optional[date] = None

        self._btn = ctk.CTkButton(
            self, text="Pick date", width=110, height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#1f538d", hover_color="#174b7a",
            command=self._open_picker,
        )
        self._btn.pack(side="left", padx=(0, 4))

        self._clear_btn = ctk.CTkButton(
            self, text="✕", width=28, height=30,
            font=ctk.CTkFont(size=11),
            fg_color="gray35", hover_color="#8b2020",
            command=self._clear,
        )
        self._clear_btn.pack(side="left")

    def _open_picker(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Select Date")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(fg_color="#1e1e1e")

        show_date = self._date or date.today()
        cal = Calendar(
            popup, selectmode="day",
            year=show_date.year, month=show_date.month, day=show_date.day,
            date_pattern="yyyy-mm-dd",
            background="#1f538d", foreground="white",
            headersbackground="#1f538d", headersforeground="white",
            normalbackground="#2b2b2b", normalforeground="white",
            weekendbackground="#2b2b2b", weekendforeground="#8ab4f8",
            othermonthforeground="#555555", othermonthweforeground="#555555",
            selectbackground="#1f538d", selectforeground="white",
            bordercolor="#3a3a3a", borderwidth=0, font=("Arial", 12),
        )
        cal.pack(padx=12, pady=(12, 6))
        ctk.CTkButton(popup, text="Confirm", width=120, height=34,
                      font=ctk.CTkFont(size=13),
                      command=lambda: self._confirm(cal, popup)).pack(pady=(0, 12))
        popup.update_idletasks()
        sw = popup.winfo_screenwidth(); sh = popup.winfo_screenheight()
        pw = popup.winfo_reqwidth();   ph = popup.winfo_reqheight()
        popup.geometry(f"+{max(0, sw//2 - pw//2)}+{max(0, sh//2 - ph//2)}")

    def _confirm(self, cal: Calendar, popup):
        try:
            self._date = datetime.strptime(cal.get_date(), "%Y-%m-%d").date()
            self._btn.configure(text=self._date.strftime("%Y-%m-%d"))
        except Exception:
            pass
        popup.destroy()

    def _clear(self):
        self._date = None
        self._btn.configure(text="Pick date")

    def get_date_str(self) -> str:
        return self._date.strftime("%Y-%m-%d") if self._date else ""


# ──────────────────────────── Multi-Entry Dialog ─────────────────────────────

class MultiEntryDialog(ctk.CTkToplevel):
    """Add multiple entries sharing the same Platform / ODM / GBU / PL / Status / DM #,
    each with its own Sub-Category, GTK Supplier, GTK Liability, etc."""

    # Per-row variable fields
    _ROW_FIELDS = [
        "Sub-Category",
        "GTK Supplier",
        "GTK \nLiability $",
        "Actual GTK \nLiability $",
        "Rebate Initiative %",
        "Actual Payment",
        "DM Issued Date",
    ]

    def __init__(self, parent, store=None, pl_map: Optional[dict] = None):
        super().__init__(parent)
        self.title("Add Multiple Entries")
        self.resizable(True, True)
        self.grab_set()

        self._store = store
        self._pl_map: dict = pl_map or {}
        self._lookups = _load_lookups()
        self._results: list[dict] = []

        # Shared field vars
        self._shared_vars: dict[str, tk.StringVar] = {
            f: tk.StringVar() for f in ["Platform", "ODM", "GBU", "PL", "Status", "DM #"]
        }
        # PL auto-fill state
        self._auto_filling = False
        self._pl_manually_set = False

        # Each item: dict of {field: tk.StringVar | DarkDatePicker}
        self._row_data: list[dict] = []
        self._row_frames: list[ctk.CTkFrame] = []

        self._build_ui()
        self._add_row()   # start with one empty row

        self._center(parent)

    def _build_ui(self):
        font13 = ctk.CTkFont(size=13)
        font_bold = ctk.CTkFont(size=14, weight="bold")

        # ── Shared fields ──
        shared_outer = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=8)
        shared_outer.pack(fill="x", padx=14, pady=(14, 6))

        ctk.CTkLabel(shared_outer, text="Shared Fields",
                     font=font_bold, text_color="#4db8ff").pack(anchor="w", padx=10, pady=(8, 4))

        shared_grid = ctk.CTkFrame(shared_outer, fg_color="transparent")
        shared_grid.pack(fill="x", padx=10, pady=(0, 8))

        shared_display = [
            ("Platform", "free"),
            ("ODM",      "dropdown"),
            ("GBU",      "dropdown"),
            ("Status",   "dropdown"),
            ("DM #",     "free"),
            ("PL",       "free"),
        ]

        odm_vals   = self._lookups.get("ODM", [])
        gbu_vals   = self._lookups.get("GBU", [])
        status_vals = self._lookups.get("Status", [])

        for i, (field, kind) in enumerate(shared_display):
            row_i, col_i = divmod(i, 3)
            lf = ctk.CTkFrame(shared_grid, fg_color="transparent")
            lf.grid(row=row_i, column=col_i, padx=8, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=_label_text(field),
                         font=font13, width=90, anchor="w").pack(side="left", padx=(0, 6))
            var = self._shared_vars[field]
            if kind == "free":
                w = ctk.CTkEntry(lf, textvariable=var, width=160, height=32, font=font13)
                w.pack(side="left")
            else:
                vals = {"ODM": odm_vals, "GBU": gbu_vals, "Status": status_vals}[field]
                w = ScrollableDropdown(lf, variable=var, values=vals, width=160, height=32, font=font13)
                w.pack(side="left")

        # Auto-fill PL from Platform
        self._shared_vars["Platform"].trace_add("write", self._on_platform_changed)
        self._shared_vars["PL"].trace_add("write", self._on_pl_changed)

        # ── Row section header ──
        row_header = ctk.CTkFrame(self, fg_color="transparent")
        row_header.pack(fill="x", padx=14, pady=(4, 0))
        ctk.CTkLabel(row_header, text="Per-Supplier Rows",
                     font=font_bold, text_color="#4db8ff").pack(side="left")
        ctk.CTkButton(row_header, text="+ Add Row", width=100, height=28,
                      font=ctk.CTkFont(size=12), fg_color="#2a5040", hover_color="#1e3a2e",
                      command=self._add_row).pack(side="right")

        # ── Scrollable rows container ──
        self._rows_scroll = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a", corner_radius=6)
        self._rows_scroll.pack(fill="both", expand=True, padx=14, pady=(4, 8))

        # ── Bottom buttons ──
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkButton(btn_row, text="Save All", width=120, height=34,
                      font=ctk.CTkFont(size=13),
                      command=self._on_save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancel", width=100, height=34,
                      font=ctk.CTkFont(size=13),
                      fg_color="gray35", hover_color="gray25",
                      command=self.destroy).pack(side="left")

        self.geometry("1100x620")

    def _add_row(self):
        idx = len(self._row_data)
        font12 = ctk.CTkFont(size=12)

        frame = ctk.CTkFrame(self._rows_scroll, fg_color="#2b2b2b", corner_radius=6)
        frame.pack(fill="x", pady=4, padx=2)

        # Row number label
        num_label = ctk.CTkLabel(frame, text=f"#{idx+1}", width=28,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="gray60")
        num_label.grid(row=0, column=0, padx=(6, 2), pady=6)

        lookups = self._lookups
        subcat_vals   = lookups.get("Sub-Category", [])
        supplier_vals = lookups.get("GTK Supplier", [])

        vars_: dict[str, tk.StringVar | CompactDatePicker] = {}
        vars_["_num_label"] = num_label
        col = 1
        for field in self._ROW_FIELDS:
            lf = ctk.CTkFrame(frame, fg_color="transparent")
            lf.grid(row=0, column=col, padx=4, pady=6, sticky="w")

            ctk.CTkLabel(lf, text=_label_text(field),
                         font=ctk.CTkFont(size=11), text_color="gray60",
                         anchor="w").pack(anchor="w")

            if field == "DM Issued Date":
                picker = CompactDatePicker(lf)
                picker.pack()
                vars_[field] = picker
            elif field == "Sub-Category":
                var = tk.StringVar()
                w = ScrollableDropdown(lf, variable=var, values=subcat_vals,
                                       width=130, height=30, font=("Arial", 12))
                w.pack()
                vars_[field] = var
                # Bind sub-category change to lock/unlock Actual Payment
                var.trace_add("write", lambda *_, i=idx: self._on_subcat_changed(i))
            elif field == "GTK Supplier":
                var = tk.StringVar()
                w = ScrollableDropdown(lf, variable=var, values=supplier_vals,
                                       width=130, height=30, font=("Arial", 12))
                w.pack()
                vars_[field] = var
            elif field == "Actual Payment":
                var = tk.StringVar()
                entry = ctk.CTkEntry(lf, textvariable=var, width=110, height=30, font=font12)
                entry.pack()
                vars_[field] = var
                # Store entry widget reference for enable/disable
                vars_["_ap_entry"] = entry
            else:
                var = tk.StringVar()
                # Rebate default
                if field == "Rebate Initiative %":
                    var.set("10")
                    # Bind to auto-calc
                    var.trace_add("write", lambda *_, i=idx: self._on_subcat_changed(i))
                if field == "Actual GTK \nLiability $":
                    var.trace_add("write", lambda *_, i=idx: self._on_subcat_changed(i))
                ctk.CTkEntry(lf, textvariable=var, width=110, height=30, font=font12).pack()
                vars_[field] = var

            col += 1

        # Remove button — trash icon, aligned with field widgets (bottom of cell)
        rm_frame = ctk.CTkFrame(frame, fg_color="transparent")
        rm_frame.grid(row=0, column=col, padx=(4, 6), pady=(20, 6), sticky="s")
        ctk.CTkButton(rm_frame, text="🗑", width=32, height=30,
                      font=ctk.CTkFont(size=14),
                      fg_color="gray35", hover_color="#8b2020",
                      command=lambda f=frame, i=idx: self._remove_row(f, i)).pack()

        self._row_data.append(vars_)
        self._row_frames.append(frame)

    def _remove_row(self, frame: ctk.CTkFrame, idx: int):
        if len(self._row_data) <= 1:
            return  # always keep at least one row
        frame.destroy()
        try:
            self._row_data.pop(idx)
            self._row_frames.pop(idx)
        except IndexError:
            pass
        # Re-number remaining rows
        for i, vars_ in enumerate(self._row_data):
            lbl = vars_.get("_num_label")
            if lbl and lbl.winfo_exists():
                lbl.configure(text=f"#{i+1}")

    def _on_subcat_changed(self, idx: int):
        """Auto-calculate Actual Payment for KB/FP rows; lock/unlock the entry."""
        try:
            vars_ = self._row_data[idx]
        except IndexError:
            return
        sub_var = vars_.get("Sub-Category")
        is_keyboard = (
            sub_var is not None
            and isinstance(sub_var, tk.StringVar)
            and sub_var.get().strip() in ("Keyboard", "Fingerprint/Touchpad")
        )
        ap_var   = vars_.get("Actual Payment")
        ap_entry = vars_.get("_ap_entry")
        if ap_entry and isinstance(ap_var, tk.StringVar):
            if is_keyboard:
                ap_entry.configure(state="disabled", text_color="gray50")
                # Auto-calculate
                try:
                    gtk_val  = float((vars_.get("Actual GTK \nLiability $") or tk.StringVar()).get() or 0)
                    reb_raw  = (vars_.get("Rebate Initiative %") or tk.StringVar()).get().strip()
                    reb      = float(reb_raw) if reb_raw else 0.0
                    reb_pct  = reb / 100.0 if reb > 1.0 else reb
                    ap_entry.configure(state="normal", text_color="gray50")
                    ap_var.set(str(round(gtk_val * (1 - reb_pct), 1)))
                    ap_entry.configure(state="disabled")
                except (ValueError, TypeError):
                    pass
            else:
                ap_entry.configure(state="normal", text_color="white")

    def _on_platform_changed(self, *_):
        if self._auto_filling or self._pl_manually_set:
            return
        platform = self._shared_vars["Platform"].get().strip().lower()
        auto_pl = self._pl_map.get(platform, "")
        self._auto_filling = True
        self._shared_vars["PL"].set(auto_pl)
        self._auto_filling = False

    def _on_pl_changed(self, *_):
        if self._auto_filling:
            return
        self._pl_manually_set = True

    def _on_save(self):
        from tkinter import messagebox as _mb
        platform = self._shared_vars["Platform"].get().strip()
        if not platform:
            _mb.showwarning("Missing Platform", "Please enter a Platform.", parent=self)
            return

        shared = {f: v.get().strip() for f, v in self._shared_vars.items()}

        rows_out = []
        for i, vars_ in enumerate(self._row_data):
            row = dict(shared)
            for field in self._ROW_FIELDS:
                if field == "DM Issued Date":
                    picker = vars_.get(field)
                    row[field] = picker.get_date_str() if isinstance(picker, CompactDatePicker) else ""
                elif field.startswith("_"):
                    continue
                else:
                    v = vars_.get(field)
                    row[field] = v.get().strip() if isinstance(v, tk.StringVar) else ""
            rows_out.append(row)

        if not rows_out:
            self.destroy()
            return

        self._results = rows_out
        self.destroy()

    def get_results(self) -> list[dict]:
        return self._results

    def _center(self, parent):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = max(0, sw // 2 - w // 2)
        y = max(0, sh // 2 - h // 2)
        self.geometry(f"+{x}+{y}")


# ──────────────────────────── Manage Platform Dialog ─────────────────────────

class ManagePlatformDialog(ctk.CTkToplevel):
    """Search for a Platform and edit all its supplier rows in one view."""

    _ROW_FIELDS = [
        "Sub-Category",
        "GTK Supplier",
        "GTK \nLiability $",
        "Actual GTK \nLiability $",
        "Rebate Initiative %",
        "Actual Payment",
        "DM Issued Date",
        "Status",
        "DM #",
    ]

    def __init__(self, parent, store=None, pl_map: Optional[dict] = None):
        super().__init__(parent)
        self.title("Manage Platform")
        self.resizable(True, True)
        self.grab_set()

        self._store = store
        self._pl_map: dict = pl_map or {}
        self._lookups = _load_lookups()
        self._shown_rows: list[tuple[int, dict]] = []
        self._row_data: list[dict] = []
        self._row_frames: list[ctk.CTkFrame] = []
        self._current_platform: str = ""

        self._build_ui()
        self.geometry("1340x700")
        self._center(parent)

    def _build_ui(self):
        font13 = ctk.CTkFont(size=13)
        font_bold = ctk.CTkFont(size=14, weight="bold")

        # Search bar
        search_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=8)
        search_frame.pack(fill="x", padx=14, pady=(14, 6))

        ctk.CTkLabel(search_frame, text="Search Platform:",
                     font=font_bold).pack(side="left", padx=(12, 6), pady=10)

        self._search_var = tk.StringVar()
        self._search_entry = ctk.CTkEntry(
            search_frame, textvariable=self._search_var,
            width=320, height=34, font=font13,
            placeholder_text="Type platform name...",
        )
        self._search_entry.pack(side="left", padx=(0, 6), pady=10)
        self._search_entry.bind("<Return>", lambda _: self._do_search())
        self._search_var.trace_add("write", self._on_search_type)

        ctk.CTkButton(search_frame, text="🔍", width=44, height=34,
                      font=ctk.CTkFont(size=14),
                      command=self._do_search).pack(side="left", padx=(0, 8))

        # Suggestion listbox
        self._suggest_frame = tk.Frame(self, bg="#2b2b2b", relief="flat")
        self._suggest_lb = tk.Listbox(
            self._suggest_frame, bg="#2b2b2b", fg="white",
            selectbackground="#1f538d", selectforeground="white",
            font=("Arial", 12), relief="flat",
            highlightthickness=0, borderwidth=0, activestyle="none",
            height=5,
        )
        self._suggest_lb.pack(fill="both", expand=True, padx=1, pady=1)
        self._suggest_lb.bind("<ButtonRelease-1>", self._on_suggestion_click)

        # Platform info bar
        self._info_bar = ctk.CTkFrame(self, fg_color="transparent")
        self._info_bar.pack(fill="x", padx=14, pady=(0, 2))
        self._platform_label = ctk.CTkLabel(
            self._info_bar, text="", font=font_bold, text_color="#4db8ff"
        )
        self._platform_label.pack(side="left")

        # Shared fields
        self._shared_frame = ctk.CTkFrame(self, fg_color="#1e1e1e", corner_radius=8)
        self._shared_frame.pack(fill="x", padx=14, pady=(0, 6))
        self._shared_vars: dict[str, tk.StringVar] = {}

        # Row section header
        row_header = ctk.CTkFrame(self, fg_color="transparent")
        row_header.pack(fill="x", padx=14, pady=(0, 0))
        ctk.CTkLabel(row_header, text="Supplier Rows",
                     font=font_bold, text_color="#4db8ff").pack(side="left")
        ctk.CTkButton(row_header, text="+ Add Row", width=100, height=28,
                      font=ctk.CTkFont(size=12), fg_color="#2a5040", hover_color="#1e3a2e",
                      command=self._add_new_row).pack(side="right")

        self._rows_scroll = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a", corner_radius=6)
        self._rows_scroll.pack(fill="both", expand=True, padx=14, pady=(4, 8))

        # Bottom buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkButton(btn_row, text="Save All", width=120, height=34,
                      font=ctk.CTkFont(size=13), command=self._on_save).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancel", width=100, height=34,
                      font=ctk.CTkFont(size=13),
                      fg_color="gray35", hover_color="gray25",
                      command=self.destroy).pack(side="left")

    def _all_platforms(self) -> list[str]:
        if not self._store:
            return []
        seen: dict[str, None] = {}
        for r in self._store.get_rows():
            p = str(r.get("Platform") or "").strip()
            if p:
                seen[p] = None
        return list(seen.keys())

    def _on_search_type(self, *_):
        query = self._search_var.get().strip().lower()
        if not query:
            self._suggest_frame.place_forget()
            return
        matches = [p for p in self._all_platforms() if query in p.lower()]
        if not matches:
            self._suggest_frame.place_forget()
            return
        self._suggest_lb.delete(0, "end")
        for m in matches[:10]:
            self._suggest_lb.insert("end", m)
        self._search_entry.update_idletasks()
        x = self._search_entry.winfo_rootx() - self.winfo_rootx()
        y = (self._search_entry.winfo_rooty() - self.winfo_rooty()
             + self._search_entry.winfo_height())
        self._suggest_frame.place(x=x, y=y, width=320)
        self._suggest_frame.lift()

    def _on_suggestion_click(self, _event=None):
        sel = self._suggest_lb.curselection()
        if sel:
            self._search_var.set(self._suggest_lb.get(sel[0]))
        self._suggest_frame.place_forget()
        self._do_search()

    def _do_search(self):
        self._suggest_frame.place_forget()
        platform = self._search_var.get().strip()
        if not platform or not self._store:
            return
        self._current_platform = platform
        all_rows = self._store.get_rows()
        self._shown_rows = [
            (i, r) for i, r in enumerate(all_rows)
            if str(r.get("Platform") or "").strip() == platform
        ]
        self._platform_label.configure(
            text=f"Platform: {platform}  ({len(self._shown_rows)} rows)"
        )
        self._load_shared_fields()
        self._populate_rows()

    def _load_shared_fields(self):
        for w in self._shared_frame.winfo_children():
            w.destroy()
        self._shared_vars = {}

        first = self._shown_rows[0][1] if self._shown_rows else {}
        odm_vals = self._lookups.get("ODM", [])
        gbu_vals = self._lookups.get("GBU", [])
        shared_defs = [("ODM", odm_vals), ("GBU", gbu_vals), ("PL", None)]

        grid = ctk.CTkFrame(self._shared_frame, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=6)

        for i, (field, vals) in enumerate(shared_defs):
            lf = ctk.CTkFrame(grid, fg_color="transparent")
            lf.grid(row=0, column=i, padx=10, pady=4, sticky="w")
            ctk.CTkLabel(lf, text=field, font=ctk.CTkFont(size=13),
                         width=50, anchor="w").pack(side="left", padx=(0, 6))
            var = tk.StringVar(value=str(first.get(field) or ""))
            self._shared_vars[field] = var
            if vals is not None:
                ScrollableDropdown(lf, variable=var, values=vals,
                                   width=160, height=30,
                                   font=("Arial", 12)).pack(side="left")
            else:
                ctk.CTkEntry(lf, textvariable=var, width=160, height=30,
                             font=ctk.CTkFont(size=12)).pack(side="left")

    def _populate_rows(self):
        for f in self._row_frames:
            if f.winfo_exists():
                f.destroy()
        self._row_data = []
        self._row_frames = []
        for store_idx, row in self._shown_rows:
            self._add_row_widget(row, store_idx=store_idx)

    def _add_row_widget(self, prefill: Optional[dict] = None, store_idx: int = -1):
        idx = len(self._row_data)
        prefill = prefill or {}
        font12 = ctk.CTkFont(size=12)

        frame = ctk.CTkFrame(self._rows_scroll, fg_color="#2b2b2b", corner_radius=6)
        frame.pack(fill="x", pady=4, padx=2)

        num_label = ctk.CTkLabel(frame, text=f"#{idx+1}", width=28,
                                  font=ctk.CTkFont(size=12, weight="bold"),
                                  text_color="gray60")
        num_label.grid(row=0, column=0, padx=(6, 2), pady=6)

        subcat_vals   = self._lookups.get("Sub-Category", [])
        supplier_vals = self._lookups.get("GTK Supplier", [])
        status_vals   = self._lookups.get("Status", [])

        vars_: dict = {"_num_label": num_label, "_store_idx": store_idx}
        col = 1

        for field in self._ROW_FIELDS:
            lf = ctk.CTkFrame(frame, fg_color="transparent")
            lf.grid(row=0, column=col, padx=4, pady=6, sticky="w")
            ctk.CTkLabel(lf, text=_label_text(field),
                         font=ctk.CTkFont(size=11), text_color="gray60",
                         anchor="w").pack(anchor="w")

            raw_val = prefill.get(field)

            if field == "DM Issued Date":
                init_date = None
                if raw_val:
                    try:
                        from datetime import datetime as _dt
                        init_date = _dt.strptime(str(raw_val)[:10], "%Y-%m-%d").date()
                    except Exception:
                        pass
                picker = CompactDatePicker(lf)
                if init_date:
                    picker._date = init_date
                    picker._btn.configure(text=init_date.strftime("%Y-%m-%d"))
                picker.pack()
                vars_[field] = picker
            elif field == "Sub-Category":
                var = tk.StringVar(value=str(raw_val or ""))
                w = ScrollableDropdown(lf, variable=var, values=subcat_vals,
                                       width=130, height=30, font=("Arial", 12))
                w.pack()
                vars_[field] = var
                var.trace_add("write", lambda *_, i=idx: self._on_subcat_changed(i))
            elif field == "GTK Supplier":
                var = tk.StringVar(value=str(raw_val or ""))
                w = ScrollableDropdown(lf, variable=var, values=supplier_vals,
                                       width=130, height=30, font=("Arial", 12))
                w.pack()
                vars_[field] = var
            elif field == "Status":
                var = tk.StringVar(value=str(raw_val or ""))
                w = ScrollableDropdown(lf, variable=var, values=status_vals,
                                       width=130, height=30, font=("Arial", 12))
                w.pack()
                vars_[field] = var
            elif field == "Actual Payment":
                var = tk.StringVar(value="" if raw_val is None else str(raw_val))
                entry = ctk.CTkEntry(lf, textvariable=var, width=110, height=30, font=font12)
                entry.pack()
                vars_[field] = var
                vars_["_ap_entry"] = entry
            elif field == "Rebate Initiative %":
                display_val = ""
                if raw_val is not None and raw_val != "":
                    try:
                        fv = float(raw_val)
                        display_val = str(int(fv * 100) if fv <= 1.0 else int(fv))
                    except Exception:
                        display_val = str(raw_val)
                if not display_val:
                    display_val = "10"
                var = tk.StringVar(value=display_val)
                var.trace_add("write", lambda *_, i=idx: self._on_subcat_changed(i))
                ctk.CTkEntry(lf, textvariable=var, width=110, height=30, font=font12).pack()
                vars_[field] = var
            else:
                var = tk.StringVar(value="" if raw_val is None else str(raw_val))
                if field == "Actual GTK \nLiability $":
                    var.trace_add("write", lambda *_, i=idx: self._on_subcat_changed(i))
                ctk.CTkEntry(lf, textvariable=var, width=110, height=30, font=font12).pack()
                vars_[field] = var

            col += 1

        # Trash button
        rm_frame = ctk.CTkFrame(frame, fg_color="transparent")
        rm_frame.grid(row=0, column=col, padx=(4, 6), pady=(20, 6), sticky="s")
        ctk.CTkButton(rm_frame, text="🗑", width=32, height=30,
                      font=ctk.CTkFont(size=14),
                      fg_color="gray35", hover_color="#8b2020",
                      command=lambda f=frame, i=idx: self._remove_row(f, i)).pack()

        self._row_data.append(vars_)
        self._row_frames.append(frame)
        self._on_subcat_changed(idx)

    def _add_new_row(self):
        if not self._current_platform:
            return
        self._add_row_widget(prefill={"Platform": self._current_platform})

    def _remove_row(self, frame: ctk.CTkFrame, idx: int):
        frame.destroy()
        try:
            self._row_data.pop(idx)
            self._row_frames.pop(idx)
        except IndexError:
            pass
        for i, vars_ in enumerate(self._row_data):
            lbl = vars_.get("_num_label")
            if lbl and lbl.winfo_exists():
                lbl.configure(text=f"#{i+1}")

    def _on_subcat_changed(self, idx: int):
        try:
            vars_ = self._row_data[idx]
        except IndexError:
            return
        sub_var = vars_.get("Sub-Category")
        is_keyboard = (
            isinstance(sub_var, tk.StringVar)
            and sub_var.get().strip() in ("Keyboard", "Fingerprint/Touchpad")
        )
        ap_var   = vars_.get("Actual Payment")
        ap_entry = vars_.get("_ap_entry")
        if ap_entry and isinstance(ap_var, tk.StringVar):
            if is_keyboard:
                ap_entry.configure(state="disabled", text_color="gray50")
                try:
                    gtk_val = float((vars_.get("Actual GTK \nLiability $") or tk.StringVar()).get() or 0)
                    reb_raw = (vars_.get("Rebate Initiative %") or tk.StringVar()).get().strip()
                    reb = float(reb_raw) if reb_raw else 0.0
                    reb_pct = reb / 100.0 if reb > 1.0 else reb
                    ap_entry.configure(state="normal")
                    ap_var.set(str(round(gtk_val * (1 - reb_pct), 1)))
                    ap_entry.configure(state="disabled", text_color="gray50")
                except (ValueError, TypeError):
                    pass
            else:
                ap_entry.configure(state="normal", text_color="white")

    def _on_save(self):
        from tkinter import messagebox as _mb
        if not self._store:
            return

        shared = {f: v.get().strip() for f, v in self._shared_vars.items()}
        platform = self._current_platform

        updates: list[tuple[int, dict]] = []
        new_rows: list[dict] = []

        for vars_ in self._row_data:
            store_idx = vars_.get("_store_idx", -1)
            row: dict = {"Platform": platform}
            row.update(shared)
            for field in self._ROW_FIELDS:
                if field == "DM Issued Date":
                    picker = vars_.get(field)
                    row[field] = picker.get_date_str() if isinstance(picker, CompactDatePicker) else ""
                elif field.startswith("_"):
                    continue
                else:
                    v = vars_.get(field)
                    row[field] = v.get().strip() if isinstance(v, tk.StringVar) else ""
            if store_idx >= 0:
                updates.append((store_idx, row))
            else:
                new_rows.append(row)

        if updates:
            self._store.bulk_update_rows(updates)
        if new_rows:
            self._store.bulk_append_rows(new_rows)

        total = len(updates) + len(new_rows)
        _mb.showinfo("Saved", f"Saved {total} row(s).", parent=self)
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
