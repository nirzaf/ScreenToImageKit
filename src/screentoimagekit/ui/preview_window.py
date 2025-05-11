"""Preview window for captured screenshots."""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import ImageTk, ImageFilter, Image, ImageDraw
import math
from .drawing_tools import DrawingToolbar, DrawingCanvas, DrawingTool
import logging
import os

logger = logging.getLogger(__name__)

class PreviewWindow(tk.Toplevel):
    """Window for previewing and managing captured screenshots."""

    def __init__(self, parent, image_or_path, on_upload=None, on_cancel=None, direct_upload=True, use_gemini=False):
        """Initialize preview window.
        
        Args:
            parent: Parent window
            image_or_path: PIL Image object or path to image
            on_upload: Callback for upload action
            on_cancel: Callback for cancel action
            direct_upload: Whether to upload immediately
            use_gemini: Whether to use Gemini AI for analysis
        """
        super().__init__(parent)
        self.title("Preview")
        self.on_upload = on_upload
        self.on_cancel = on_cancel
        self.direct_upload = direct_upload
        self.use_gemini = use_gemini
        self.photo_image = None
        self.image = None  # Store the PIL image
        self.temp_path = None  # Store the path if provided
        
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
        
        # Create drawing canvas
        self.canvas = DrawingCanvas(self.canvas_frame, self.image)
        
        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Load and display the image
        self._load_image(image_or_path)
        
        # Bind events
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_image(self, image_or_path):
        """Load and display the image."""
        try:
            if isinstance(image_or_path, str):
                self.image = Image.open(image_or_path)
                self.temp_path = image_or_path
            else:
                self.image = image_or_path
                # Temp path will be set when saving
            
            # Convert image for display
            self.photo_image = ImageTk.PhotoImage(self.image)
            
            # Update canvas size and scrollregion
            self.canvas.config(scrollregion=(0, 0, self.image.width, self.image.height))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.destroy()

    def _handle_upload(self):
        """Handle upload button click."""
        try:
            if self.on_upload:
                # Get the current image with any annotations
                annotated_image = self.get_annotated_image()
                if annotated_image:
                    # Save the annotated image to the temp path
                    if self.temp_path:
                        annotated_image.save(self.temp_path)
                        self.on_upload(self.temp_path)
                    else:
                        # Create a new temp file if we don't have one
                        temp_path = os.path.join(os.getenv('TEMP'), 'screentoimagekit', f"s{os.urandom(4).hex()}.png")
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        annotated_image.save(temp_path)
                        self.on_upload(temp_path)
                self.destroy()
        except Exception as e:
            logger.error(f"Error handling upload: {e}")
            messagebox.showerror("Error", f"Failed to upload image: {e}")

    def _on_close(self):
        """Handle window close."""
        try:
            if self.on_cancel and self.temp_path:
                self.on_cancel(self.temp_path)
            self.destroy()
        except Exception as e:
            logger.error(f"Error during close: {e}")
            self.destroy()

    def _on_tool_selected(self, tool):
        """Handle tool selection."""
        self.canvas.current_tool = tool

    def get_image(self):
        """Get the current image (with annotations if any)."""
        return self.image

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

    def show(self):
        """Display the preview window."""
        self.mainloop()

    def get_annotated_image(self):
        """Get the image with annotations."""
        if self.canvas:
            return self.canvas.get_annotated_image()
        return self.image
