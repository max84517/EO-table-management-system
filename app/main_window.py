"""
Main application window — EO Table Management System.
"""

from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import customtkinter as ctk

from app.data_store import DISPLAY_COLUMNS, ExcelDataStore
from app.entry_form import EntryFormDialog
from app.lookup_editor import LookupEditorDialog
from app.user_selector import UserSelectorDialog

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

# Status indicator colours
COLOR_RED = "#e84646"
COLOR_GREEN = "#3dbb6e"

# Column widths for treeview
COL_WIDTHS = {
    "●": 36,
    "Sub-Category": 140,
    "Platform": 130,
    "GTK Supplier": 155,
    "Actual Payment": 140,
    "Status": 130,
    "Payment Received Date": 170,
    "Payment Received Quarter": 165,
    "Update Date": 175,
}


def _load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)


class MainWindow:
    def __init__(self):
        self._root = ctk.CTk()
        self._root.title("EO Table Management System")
        self._root.geometry("1200x720")
        self._root.minsize(900, 600)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._store: Optional[ExcelDataStore] = None
        self._filepath: Optional[str] = None
        self._current_user: Optional[str] = None
        self._sort_col: str = "Update Date"  # default: newest first
        self._sort_asc: bool = False
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._refresh_table())

        self._build_ui()
        # Set initial sort arrow
        self._tree.heading("Update Date", text="Update Date ▼")

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self):
        # ---- Top bar — buttons packed RIGHT first so they're always visible ----
        top = ctk.CTkFrame(self._root, height=52, corner_radius=0)
        top.pack(side="top", fill="x")
        top.pack_propagate(False)

        # Right-side buttons (packed before path label to guarantee visibility)
        ctk.CTkButton(top, text="+ Add Entry", width=105, height=32,
                      font=ctk.CTkFont(size=12), command=self._add_entry).pack(side="right", padx=(4, 12))
        ctk.CTkButton(top, text="Manage Options", width=128, height=32,
                      font=ctk.CTkFont(size=12), fg_color="gray35", hover_color="gray25",
                      command=self._open_lookup_editor).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Open Excel", width=100, height=32,
                      font=ctk.CTkFont(size=12), command=self._browse_file).pack(side="right", padx=4)

        # Left: title + user badge + file name
        ctk.CTkLabel(top, text="EO Table Management",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=(14, 6))
        self._user_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=12),
                                        text_color="#4db8ff")
        self._user_label.pack(side="left", padx=(0, 8))
        self._path_label = ctk.CTkLabel(top, text="No file loaded",
                                        font=ctk.CTkFont(size=11), text_color="gray60", anchor="w")
        self._path_label.pack(side="left", padx=4, expand=True, fill="x")

        # ---- Filter bar ----
        filter_bar = ctk.CTkFrame(self._root, height=46, corner_radius=0, fg_color="#1e1e1e")
        filter_bar.pack(side="top", fill="x")
        filter_bar.pack_propagate(False)
        ctk.CTkLabel(filter_bar, text="Search:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(14, 4))
        ctk.CTkEntry(filter_bar, textvariable=self._filter_var, width=300, height=32,
                     font=ctk.CTkFont(size=13),
                     placeholder_text="Filter any column...").pack(side="left", padx=4)

        ctk.CTkLabel(filter_bar,
                     text="  ● Red = Tracking (no payment)    ● Green = Complete",
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(side="right", padx=14)

        # ---- Table area ----
        table_frame = tk.Frame(self._root, bg="#1e1e1e")
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Treeview style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=34,
                        fieldbackground="#2b2b2b",
                        font=("Arial", 12))
        style.configure("Custom.Treeview.Heading",
                        background="#1f538d",
                        foreground="white",
                        relief="flat",
                        font=("Arial", 12, "bold"))
        style.map("Custom.Treeview",
                  background=[("selected", "#1f538d")],
                  foreground=[("selected", "white")])
        style.map("Custom.Treeview.Heading",
                  background=[("active", "#174b7a")])

        cols = ["●"] + DISPLAY_COLUMNS
        self._tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="Custom.Treeview", selectmode="browse")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._tree.pack(fill="both", expand=True)

        # Configure columns
        for col in cols:
            w = COL_WIDTHS.get(col, 120)
            self._tree.heading(col, text=col, anchor="center",
                               command=lambda c=col: self._sort_by(c))
            self._tree.column(col, width=w, minwidth=40, stretch=(col != "●"), anchor="center")

        self._col_header_base = {c: c for c in cols}  # track base label for sort arrows

        # Row tags for status indicator colours
        self._tree.tag_configure("red_dot", foreground=COLOR_RED)
        self._tree.tag_configure("green_dot", foreground=COLOR_GREEN)
        self._tree.tag_configure("stripe", background="#313131")
        self._tree.tag_configure("stripe_red", background="#313131", foreground=COLOR_RED)
        self._tree.tag_configure("stripe_green", background="#313131", foreground=COLOR_GREEN)

        # Double-click to edit
        self._tree.bind("<Double-1>", self._on_double_click)

        # ---- Status bar ----
        self._status_var = tk.StringVar(value="Ready")
        status_bar = ctk.CTkLabel(self._root, textvariable=self._status_var,
                                  font=ctk.CTkFont(size=12), text_color="gray60", anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=14, pady=(0, 5))

    # --------------------------------------------------------------- actions --
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls"), ("All files", "*.*")]
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        try:
            self._store = ExcelDataStore(path)
            self._filepath = path
            self._path_label.configure(text=os.path.basename(path))
            cfg = _load_config()
            user_paths = cfg.get("user_paths", {})
            if self._current_user:
                user_paths[self._current_user] = path
                cfg["user_paths"] = user_paths
            _save_config(cfg)
            self._refresh_table()
            n = len(self._store.get_rows())
            self._status_var.set(f"Loaded {n} rows from: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load file:\n{exc}")

    def _refresh_table(self):
        if self._store is None:
            return
        rows = self._store.get_rows()

        # Apply filter
        flt = self._filter_var.get().lower().strip()
        if flt:
            rows = [r for r in rows if any(flt in str(v).lower() for v in r.values())]

        # Apply sort
        if self._sort_col == "●":
            # Sort by payment status: ascending = red (no payment) first
            rows = sorted(rows,
                          key=lambda r: (1 if bool(r.get("Payment Received Date")) else 0),
                          reverse=not self._sort_asc)
        elif self._sort_col:
            def _key(r):
                v = r.get(self._sort_col)
                if v is None:
                    return ("", )
                return (str(v).lower(), )
            rows = sorted(rows, key=_key, reverse=not self._sort_asc)

        # Redraw — use after() to avoid blocking
        self._root.after(0, lambda: self._populate_tree(rows))

    def _populate_tree(self, rows: list[dict]):
        self._tree.delete(*self._tree.get_children())
        for i, row in enumerate(rows):
            prd = row.get("Payment Received Date")
            has_payment = bool(prd)
            dot = "●"
            stripe = (i % 2 == 1)

            values = [dot] + [self._fmt(row.get(c)) for c in DISPLAY_COLUMNS]

            if has_payment:
                tag = "stripe_green" if stripe else "green_dot"
            else:
                tag = "stripe_red" if stripe else "red_dot"

            # Store original index in iid
            self._tree.insert("", "end", iid=str(id(row)) + str(i),
                               values=values, tags=(tag,))

        # Store rows list for edit lookup
        self._current_rows = rows

    def _fmt(self, val) -> str:
        if val is None:
            return ""
        return str(val)

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            # Clear previous sort arrow
            if self._sort_col and hasattr(self, "_col_header_base"):
                base = self._col_header_base.get(self._sort_col, self._sort_col)
                self._tree.heading(self._sort_col, text=base)
            self._sort_col = col
            self._sort_asc = True
        # Update heading with sort arrow
        if hasattr(self, "_col_header_base"):
            base = self._col_header_base.get(col, col)
            arrow = " ▲" if self._sort_asc else " ▼"
            self._tree.heading(col, text=base + arrow)
        self._refresh_table()

    def _add_entry(self):
        if self._store is None:
            messagebox.showwarning("No file", "Please open an Excel file first.")
            return
        dlg = EntryFormDialog(self._root, title="Add Entry")
        self._root.wait_window(dlg)
        result = dlg.get_result()
        if result:
            self._store.append_row(result)
            self._refresh_table()
            self._status_var.set("Entry added.")

    def _on_double_click(self, event):
        item = self._tree.focus()
        if not item:
            return
        idx = self._tree.index(item)
        if not hasattr(self, "_current_rows") or idx >= len(self._current_rows):
            return
        existing = self._current_rows[idx]
        # Find actual index in store
        all_rows = self._store.get_rows()
        try:
            store_idx = all_rows.index(existing)
        except ValueError:
            store_idx = None

        dlg = EntryFormDialog(self._root, existing_row=existing, title="Edit Entry")
        self._root.wait_window(dlg)
        result = dlg.get_result()
        if result is not None and store_idx is not None:
            self._store.update_row(store_idx, result)
            self._refresh_table()
            self._status_var.set("Entry updated.")

    def _open_lookup_editor(self):
        dlg = LookupEditorDialog(self._root)
        self._root.wait_window(dlg)

    def _select_user_at_startup(self):
        """Show user selector and load the user's saved Excel path."""
        cfg = _load_config()
        users = cfg.get("users", [])
        last_user = cfg.get("last_user")

        dlg = UserSelectorDialog(self._root, users=users, last_user=last_user)
        self._root.wait_window(dlg)

        selected = dlg.get_selected()
        if not selected:
            self._root.destroy()
            sys.exit(0)

        all_users = dlg.get_all_users()
        cfg["users"] = all_users
        cfg["last_user"] = selected
        _save_config(cfg)

        self._current_user = selected
        self._user_label.configure(text=f"👤 {selected}")
        self._root.title(f"EO Table Management — {selected}")

        # Load user's remembered Excel path
        user_paths = cfg.get("user_paths", {})
        path = user_paths.get(selected, "")
        if path and os.path.exists(path):
            self._load_file(path)
        else:
            self._status_var.set(f"Welcome, {selected}! Open an Excel file to get started.")

    def _on_close(self):
        self._root.destroy()
        sys.exit(0)

    def run(self):
        self._root.after(80, self._select_user_at_startup)
        self._root.mainloop()
