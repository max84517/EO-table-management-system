"""
User selector dialog — shown at startup to identify the current user.
Each user gets their own remembered Excel path stored in config.json.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk


class UserSelectorDialog(ctk.CTkToplevel):
    """Modal dialog to select or create a user at startup."""

    def __init__(self, parent, users: list[str], last_user: Optional[str] = None):
        super().__init__(parent)
        self.title("Who are you?")
        self.resizable(False, False)
        self.grab_set()
        self.lift()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._users: list[str] = sorted(set(users))
        self._selected: Optional[str] = None

        initial = last_user if (last_user and last_user in self._users) else (self._users[0] if self._users else "")
        self._var = tk.StringVar(value=initial)
        self._new_var = tk.StringVar()
        self._radio_buttons: list[ctk.CTkRadioButton] = []

        self._build_ui()
        self._center()

    # ------------------------------------------------------------------ UI ---
    def _build_ui(self):
        fl = ctk.CTkFont(size=13)
        fh = ctk.CTkFont(size=16, weight="bold")

        ctk.CTkLabel(self, text="Who are you?", font=fh).pack(pady=(22, 4))
        ctk.CTkLabel(self, text="Select a user or add a new one",
                     font=ctk.CTkFont(size=12), text_color="gray60").pack(pady=(0, 12))

        # Scrollable user list
        self._list_frame = ctk.CTkScrollableFrame(self, width=240, height=180, fg_color="#2b2b2b")
        self._list_frame.pack(padx=28, pady=(0, 6))
        self._render_users()

        # Divider
        ctk.CTkFrame(self, height=1, fg_color="gray30").pack(fill="x", padx=28, pady=10)

        # Add new user row
        add_frame = ctk.CTkFrame(self, fg_color="transparent")
        add_frame.pack(fill="x", padx=28, pady=(0, 10))
        ctk.CTkLabel(add_frame, text="New user:", font=fl, width=80, anchor="e").pack(side="left", padx=(0, 8))
        ctk.CTkEntry(add_frame, textvariable=self._new_var, width=150, height=32,
                     font=fl, placeholder_text="Enter name...").pack(side="left", padx=(0, 8))
        ctk.CTkButton(add_frame, text="Add", width=64, height=32,
                      font=fl, command=self._add_user).pack(side="left")

        # Confirm button
        ctk.CTkButton(self, text="Confirm", width=160, height=38,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._confirm).pack(pady=(4, 22))

    def _render_users(self):
        for w in self._radio_buttons:
            w.destroy()
        self._radio_buttons.clear()
        for user in sorted(self._users):
            rb = ctk.CTkRadioButton(
                self._list_frame, text=user,
                variable=self._var, value=user,
                font=ctk.CTkFont(size=13),
            )
            rb.pack(anchor="w", padx=12, pady=5)
            self._radio_buttons.append(rb)

    # -------------------------------------------------------------- actions --
    def _add_user(self):
        name = self._new_var.get().strip()
        if not name:
            return
        if name not in self._users:
            self._users.append(name)
            self._users = sorted(self._users)
        self._var.set(name)
        self._new_var.set("")
        self._render_users()

    def _confirm(self):
        # If there's text in the "new user" field, treat it as add + confirm
        pending = self._new_var.get().strip()
        if pending:
            self._add_user()
            # fall through to confirm with newly added user

        selected = self._var.get().strip()
        if not selected:
            messagebox.showwarning("Select User", "Please select or create a user.", parent=self)
            return
        self._selected = selected
        self.destroy()

    def _on_close(self):
        # User closed the dialog → no selection
        self.destroy()

    # ---------------------------------------------------------------- utils --
    def get_selected(self) -> Optional[str]:
        return self._selected

    def get_all_users(self) -> list[str]:
        return list(self._users)

    def _center(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        x = max(0, sw // 2 - w // 2)
        y = max(0, sh // 2 - h // 2)
        self.geometry(f"+{x}+{y}")
