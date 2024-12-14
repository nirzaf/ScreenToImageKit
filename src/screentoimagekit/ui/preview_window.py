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
        
        # Create toolbar and canvas
        self.toolbar = DrawingToolbar(self, self._on_tool_selected)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Create scrollable canvas frame
        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Process the input image
        if isinstance(image, str):
            self._load_image(image)
        else:
            self._display_image(image)
        
        # Create drawing canvas with the processed image
        self.canvas = DrawingCanvas(self.canvas_frame, self.image)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set,
                            yscrollcommand=self.v_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure scrollbars
        self.h_scrollbar.configure(command=self.canvas.xview)
        self.v_scrollbar.configure(command=self.canvas.yview)
        
        # Set canvas in toolbar
        self.toolbar.set_canvas(self.canvas)
        
        # Configure window
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.state('zoomed')

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
            # Scale the image to fit the window while maintaining aspect ratio
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            target_width = int(screen_width * 0.85)
            target_height = int(screen_height * 0.85)
            width_ratio = target_width / self.image.width
            height_ratio = target_height / self.image.height
            scale_factor = min(width_ratio, height_ratio)
            
            if scale_factor < 1:
                new_width = int(self.image.width * scale_factor)
                new_height = int(self.image.height * scale_factor)
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
        return None
