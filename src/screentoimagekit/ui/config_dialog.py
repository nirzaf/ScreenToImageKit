"""Configuration dialog for ScreenToImageKit."""

import tkinter as tk
from tkinter import ttk

class ConfigDialog(tk.Toplevel):
    """Dialog for configuring ImageKit credentials."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("ImageKit Configuration")
        self.result = None
        self._init_ui()
        self._center_dialog(parent)

    def _init_ui(self):
        """Initialize dialog UI elements."""
        self.transient(self.master)
        self.grab_set()

        # Create form fields
        self._create_form_fields()
        self._create_buttons()

    def _create_form_fields(self):
        """Create and layout form fields."""
        # Private Key
        tk.Label(self, text="Private Key:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.private_key = ttk.Entry(self, width=50)
        self.private_key.grid(row=0, column=1, padx=5, pady=5)

        # Public Key
        tk.Label(self, text="Public Key:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.public_key = ttk.Entry(self, width=50)
        self.public_key.grid(row=1, column=1, padx=5, pady=5)

        # URL Endpoint
        tk.Label(self, text="URL Endpoint:").grid(
            row=2, column=0, padx=5, pady=5, sticky="e"
        )
        self.url_endpoint = ttk.Entry(self, width=50)
        self.url_endpoint.grid(row=2, column=1, padx=5, pady=5)

    def _create_buttons(self):
        """Create and layout dialog buttons."""
        button_frame = ttk.Frame(self)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame, 
            text="OK", 
            command=self.ok_clicked
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame, 
            text="Cancel", 
            command=self.cancel_clicked
        ).pack(side=tk.LEFT, padx=5)

    def _center_dialog(self, parent):
        """Center dialog relative to parent window."""
        self.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        self.private_key.focus_set()

    def ok_clicked(self):
        """Handle OK button click."""
        self.result = {
            'private_key': self.private_key.get(),
            'public_key': self.public_key.get(),
            'url_endpoint': self.url_endpoint.get()
        }
        self.destroy()

    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.destroy()
