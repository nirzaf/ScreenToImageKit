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
        
        # Set window size to 90% of screen size
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = int(screen_width * 0.9)
        window_height = int(screen_height * 0.9)
        self.window.geometry(f"{window_width}x{window_height}")
        self.window.minsize(800, 600)
        self.window.resizable(True, True)

    def _create_ui(self):
        """Create window UI elements."""
        try:
            # Create toolbar frame with minimal padding
            toolbar_frame = ttk.Frame(self.window)
            toolbar_frame.grid(row=0, column=0, sticky='ew', padx=2, pady=2)
            
            # Create drawing toolbar
            self.toolbar = DrawingToolbar(toolbar_frame, self._on_tool_selected)
            self.toolbar.grid(row=0, column=0, sticky='ew')

            # Create main content frame
            content_frame = ttk.Frame(self.window)
            content_frame.grid(row=1, column=0, sticky='nsew', padx=2, pady=(0, 2))
            content_frame.rowconfigure(0, weight=1)
            content_frame.columnconfigure(0, weight=1)

            # Create canvas frame that will expand to fill space
            canvas_frame = ttk.Frame(content_frame)
            canvas_frame.grid(row=0, column=0, sticky='nsew')
            canvas_frame.rowconfigure(0, weight=1)
            canvas_frame.columnconfigure(0, weight=1)

            # Create scrollable canvas
            self.scrolled_canvas = self._create_scrolled_canvas(canvas_frame)
            
            # Scale image to fit the window while maintaining aspect ratio
            scaled_image = self._scale_image(self.image)
            self.canvas = DrawingCanvas(self.scrolled_canvas, scaled_image)
            self.canvas.grid(row=0, column=0, sticky='nsew')

            # Create button frame with minimal space
            self._create_buttons()

        except Exception as e:
            self.window.destroy()
            raise

    def _create_scrolled_canvas(self, parent):
        """Create a scrollable frame for the canvas."""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky='nsew')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        
        # Create canvas with white background
        canvas = tk.Canvas(frame, xscrollcommand=lambda *args: None, 
                         yscrollcommand=lambda *args: None,
                         highlightthickness=0, bg='white')
        canvas.grid(row=0, column=0, sticky='nsew')
        
        # Add scrollbars
        h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        
        # Configure canvas scrolling
        canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # Grid scrollbars - only show when needed
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Bind mouse wheel
        canvas.bind('<MouseWheel>', lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.bind('<Shift-MouseWheel>', lambda e: canvas.xview_scroll(int(-1*(e.delta/120)), "units"))
        
        return canvas

    def _scale_image(self, image):
        """Scale the image to fit the window while maintaining aspect ratio."""
        # Get window dimensions (accounting for padding and toolbars)
        window_width = self.window.winfo_width() - 20  # Account for padding
        window_height = self.window.winfo_height() - 100  # Account for toolbar and buttons
        
        if window_width <= 1 or window_height <= 1:  # Window not realized yet
            window_width = int(self.window.winfo_screenwidth() * 0.8)
            window_height = int(self.window.winfo_screenheight() * 0.8)
        
        # Calculate scaling factor
        width_ratio = window_width / image.width
        height_ratio = window_height / image.height
        scale_factor = min(width_ratio, height_ratio)
        
        # Scale image
        if scale_factor != 1:
            new_width = int(image.width * scale_factor)
            new_height = int(image.height * scale_factor)
            return image.resize((new_width, new_height), Image.LANCZOS)
        return image

    def _create_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.window)
        button_frame.grid(row=2, column=0, sticky='e', padx=5, pady=2)

        style = ttk.Style()
        style.configure('Preview.TButton', padding=(8, 3))

        ttk.Button(
            button_frame,
            text="Upload",
            style='Preview.TButton',
            command=self._handle_upload
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Cancel",
            style='Preview.TButton',
            command=self._handle_cancel
        ).pack(side=tk.LEFT, padx=2)

    def _handle_upload(self):
        """Handle upload button click."""
        # Save image with annotations before uploading
        annotated_image = self._save_image()
        self.window.destroy()
        if self.on_upload:
            self.on_upload()

    def _handle_cancel(self):
        """Handle cancel button click."""
        self.window.destroy()
        if self.on_cancel:
            self.on_cancel()

    def _on_tool_selected(self, tool: DrawingTool):
        """Handle tool selection from toolbar."""
        self.canvas.current_tool = tool

    def _save_image(self):
        """Save the image with annotations."""
        # Create a new image to draw on
        result = self.image.copy()
        if result.mode != 'RGBA':
            result = result.convert('RGBA')
        draw = ImageDraw.Draw(result)
        
        # Sort elements by layer
        sorted_elements = sorted(self.canvas.elements, key=lambda e: e.layer)
        
        # Draw each element
        for element in sorted_elements:
            if element.tool_type in (DrawingTool.RECTANGLE, DrawingTool.ELLIPSE):
                # Draw shape with transparent fill
                draw.rectangle([element.x1, element.y1, element.x2, element.y2], 
                             outline=element.color, fill=element.fill, width=element.width)
            elif element.tool_type == DrawingTool.LINE:
                draw.line([element.x1, element.y1, element.x2, element.y2],
                         fill=element.color, width=element.width)
            elif element.tool_type == DrawingTool.ARROW:
                # Draw arrow using PIL
                draw.line([element.x1, element.y1, element.x2, element.y2],
                         fill=element.color, width=element.width)
                angle = math.atan2(element.y2 - element.y1, element.x2 - element.x1)
                head_length = min(20, ((element.x2 - element.x1)**2 + (element.y2 - element.y1)**2)**0.5 / 3)
                x3 = element.x2 - head_length * math.cos(angle - math.pi/6)
                y3 = element.y2 - head_length * math.sin(angle - math.pi/6)
                x4 = element.x2 - head_length * math.cos(angle + math.pi/6)
                y4 = element.y2 - head_length * math.sin(angle + math.pi/6)
                draw.polygon([element.x2, element.y2, x3, y3, x4, y4],
                           fill=element.color)
            elif element.tool_type == DrawingTool.FREEHAND:
                if hasattr(element, 'points') and len(element.points) > 1:
                    draw.line(element.points, fill=element.color, width=element.width)
            elif element.tool_type == DrawingTool.TEXT:
                draw.text((element.x1, element.y1), element.text,
                         font=element.font, fill=element.color)
            elif element.tool_type == DrawingTool.PIXELATE:
                # Get the region to pixelate
                region = result.crop((element.x1, element.y1,
                                   element.x2, element.y2))
                # Reduce and resize to create pixelation effect
                size = (region.width // element.effect_strength,
                       region.height // element.effect_strength)
                if all(s > 0 for s in size):
                    region = region.resize(size, Image.NEAREST)
                    region = region.resize((element.x2 - element.x1,
                                        element.y2 - element.y1),
                                       Image.NEAREST)
                    result.paste(region, (element.x1, element.y1))
            elif element.tool_type == DrawingTool.GRAYSCALE:
                # Convert region to grayscale
                region = result.crop((element.x1, element.y1,
                                   element.x2, element.y2))
                region = region.convert('L')
                result.paste(region, (element.x1, element.y1))
                    
        return result

    def show(self):
        """Display the preview window."""
        self.window.mainloop()
