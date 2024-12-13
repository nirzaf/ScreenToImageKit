"""Preview window for captured screenshots."""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk

class PreviewWindow:
    """Window for previewing and managing captured screenshots."""

    def __init__(self, parent, image, on_upload, on_cancel):
        self.window = tk.Toplevel(parent)
        self.image = image
        self.on_upload = on_upload
        self.on_cancel = on_cancel
        self.photo_image = None
        self._init_window()
        self._create_ui()

    def _init_window(self):
        """Initialize window properties."""
        self.window.title("Screenshot Preview")
        self.window.transient(self.window.master)
        self.window.grab_set()
        self.window.focus_force()
        self.window.resizable(False, False)

    def _create_ui(self):
        """Create window UI elements."""
        try:
            # Create and display image
            self.photo_image = ImageTk.PhotoImage(self.image)
            preview_label = ttk.Label(self.window, image=self.photo_image)
            preview_label.image = self.photo_image  # Keep a reference
            preview_label.pack(padx=10, pady=10)

            # Create buttons
            self._create_buttons()

        except Exception as e:
            self.window.destroy()
            raise

    def _create_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Upload",
            command=self._handle_upload
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._handle_cancel
        ).pack(side=tk.LEFT, padx=5)

    def _handle_upload(self):
        """Handle upload button click."""
        self.window.destroy()
        if self.on_upload:
            self.on_upload()

    def _handle_cancel(self):
        """Handle cancel button click."""
        self.window.destroy()
        if self.on_cancel:
            self.on_cancel()

    def show(self):
        """Display the preview window."""
        self.window.mainloop()
