"""Preview window for captured screenshots."""

import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, ImageFilter, Image, ImageDraw
import math
from .drawing_tools import DrawingToolbar, DrawingCanvas, DrawingTool

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
        
        # Make window responsive with proper weights
        self.window.rowconfigure(1, weight=1)  # Maximum weight to canvas row
        self.window.columnconfigure(0, weight=1)
        
        # Set window size to 95% of screen size for maximum space
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = int(screen_width * 0.95)
        window_height = int(screen_height * 0.95)
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.minsize(1024, 768)  # Increased minimum size
        self.window.resizable(True, True)

    def _create_scrolled_canvas(self, parent):
        """Create a scrollable frame for the canvas."""
        # Create container frame
        container = ttk.Frame(parent)
        container.grid(row=0, column=0, sticky='nsew')
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Create canvas with scrollbars
        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        h_scrollbar = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)

        # Configure canvas scrolling
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        # Create frame inside canvas for content
        inner_frame = ttk.Frame(canvas)
        inner_frame.rowconfigure(0, weight=1)
        inner_frame.columnconfigure(0, weight=1)

        # Create window in canvas for the frame
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        # Grid layout
        canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')

        # Update canvas scroll region when frame size changes
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
            # Ensure window fills canvas width
            canvas.itemconfig(canvas_window, width=max(inner_frame.winfo_reqwidth(), canvas.winfo_width()))

        def _on_canvas_configure(event):
            # Update inner frame width when canvas resizes
            canvas.itemconfig(canvas_window, width=max(inner_frame.winfo_reqwidth(), event.width))

        inner_frame.bind('<Configure>', _on_frame_configure)
        canvas.bind('<Configure>', _on_canvas_configure)

        # Bind mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all('<MouseWheel>', _on_mousewheel)
        canvas.bind_all('<Shift-MouseWheel>', _on_shift_mousewheel)

        return inner_frame

    def _scale_image(self, image):
        """Scale the image to fit the window while maintaining aspect ratio."""
        # Get window dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Use 85% of screen size for image area
        target_width = int(screen_width * 0.85)
        target_height = int(screen_height * 0.85)
        
        # Calculate scaling factor
        width_ratio = target_width / image.width
        height_ratio = target_height / image.height
        scale_factor = min(width_ratio, height_ratio)
        
        # Only scale down if image is larger than target size
        if scale_factor < 1:
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            return image.resize((new_width, new_height), Image.LANCZOS)
        
        # Keep original size if image is smaller than target
        return image

    def _create_ui(self):
        """Create window UI elements."""
        try:
            # Create main container
            main_container = ttk.Frame(self.window)
            main_container.grid(row=0, column=0, sticky='nsew')
            main_container.rowconfigure(1, weight=1)
            main_container.columnconfigure(0, weight=1)

            # Create toolbar
            self.toolbar = DrawingToolbar(main_container, self._on_tool_selected)
            self.toolbar.grid(row=0, column=0, sticky='ew', padx=1, pady=1)

            # Create canvas container
            canvas_container = ttk.Frame(main_container)
            canvas_container.grid(row=1, column=0, sticky='nsew', padx=1, pady=1)
            canvas_container.rowconfigure(0, weight=1)
            canvas_container.columnconfigure(0, weight=1)

            # Create scrollable canvas
            self.scrolled_frame = self._create_scrolled_canvas(canvas_container)
            
            # Scale and create drawing canvas
            scaled_image = self._scale_image(self.image)
            self.canvas = DrawingCanvas(self.scrolled_frame, scaled_image)
            self.canvas.grid(row=0, column=0, sticky='nsew')

        except Exception as e:
            self.window.destroy()
            raise

    def _on_tool_selected(self, tool):
        """Handle tool selection."""
        if self.canvas:
            self.canvas.current_tool = tool

    def _save_image(self):
        """Save the image with annotations."""
        annotated_image = self.canvas.get_annotated_image()
        return annotated_image

    def show(self):
        """Display the preview window."""
        self.window.mainloop()
