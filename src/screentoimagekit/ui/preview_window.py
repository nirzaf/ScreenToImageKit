"""Preview window for captured screenshots."""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, ImageFilter, Image, ImageDraw
import math
from .drawing_tools import DrawingToolbar, DrawingCanvas, DrawingTool
import logging

logger = logging.getLogger(__name__)

class PreviewWindow(tk.Toplevel):
    """Window for previewing and managing captured screenshots."""

    def __init__(self, parent, image, on_upload=None, on_cancel=None):
        """Initialize preview window.
        
        Args:
            parent: Parent window
            image: PIL Image object or path to image
            on_upload: Callback for upload action
            on_cancel: Callback for cancel action
        """
        super().__init__(parent)
        self.title("Preview")
        self.on_upload = on_upload
        self.on_cancel = on_cancel
        self.photo_image = None
        self.image = None  # Store the PIL image
        
        # Create top frame for toolbar and upload button
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Create toolbar
        self.toolbar = DrawingToolbar(top_frame, self._on_tool_selected)
        self.toolbar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add upload button
        upload_button = ttk.Button(top_frame, text="Upload", command=self._handle_upload)
        upload_button.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Create scrollable canvas frame with proper weight configuration
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')

        # Process the input image
        if isinstance(image, str):
            self._load_image(image)
        else:
            self._display_image(image)
        
        # Create drawing canvas with the processed image
        self.canvas = DrawingCanvas(self.canvas_frame, self.image)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set,
                            yscrollcommand=self.v_scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        
        # Configure scrollbars
        self.h_scrollbar.configure(command=self.canvas.xview)
        self.v_scrollbar.configure(command=self.canvas.yview)
        
        # Set canvas in toolbar
        self.toolbar.set_canvas(self.canvas)
        
        # Configure window
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.state('zoomed')

    def _handle_upload(self):
        """Handle upload button click."""
        if self.on_upload:
            # Get the annotated image before uploading
            annotated_image = self.canvas.get_annotated_image()
            # Save the annotated image temporarily
            import os
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, "annotated_screenshot.png")
            annotated_image.save(temp_path, "PNG")
            # Call the upload callback with the new temp path
            self.on_upload(temp_path)
        self.destroy()

    def get_image(self):
        """Get the current image (with annotations if any)."""
        return self.image

    def _load_image(self, image_path):
        """Load and display the image from file."""
        try:
            self.image = Image.open(image_path)
            self._scale_image()
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            self.destroy()

    def _display_image(self, image):
        """Display the PIL image on the canvas."""
        try:
            self.image = image
            self._scale_image()
        except Exception as e:
            logger.error(f"Error displaying image: {e}")
            self.destroy()

    def _scale_image(self):
        """Scale the image to fit the window while maintaining aspect ratio."""
        try:
            # Get the screen dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Calculate available space (accounting for window decorations and toolbar)
            available_width = screen_width - 50  # Account for scrollbar and padding
            available_height = screen_height - 100  # Account for toolbar and window decorations
            
            # Calculate scaling factors
            width_ratio = available_width / self.image.width
            height_ratio = available_height / self.image.height
            
            # Use the smaller ratio to maintain aspect ratio while fitting the screen
            scale_factor = min(width_ratio, height_ratio)
            
            # Calculate new dimensions
            new_width = int(self.image.width * scale_factor)
            new_height = int(self.image.height * scale_factor)
            
            # Resize the image
            self.image = self.image.resize((new_width, new_height), Image.LANCZOS)
        except Exception as e:
            logger.error(f"Error scaling image: {e}")
            self.destroy()

    def _on_tool_selected(self, tool):
        """Handle tool selection."""
        if self.canvas:
            self.canvas.current_tool = tool

    def _on_closing(self):
        """Handle window closing."""
        if self.on_cancel:
            self.on_cancel()
        self.destroy()

    def show(self):
        """Display the preview window."""
        self.mainloop()

    def get_annotated_image(self):
        """Get the image with annotations."""
        if self.canvas:
            return self.canvas.get_annotated_image()
        return self.image
