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
        # Set a larger initial window size
        self.window.geometry("1024x768")
        self.window.resizable(False, False)

    def _create_ui(self):
        """Create window UI elements."""
        try:
            # Create drawing toolbar
            self.toolbar = DrawingToolbar(self.window, self._on_tool_selected)
            self.toolbar.pack(fill=tk.X, padx=10, pady=(10, 0))

            # Create drawing canvas
            self.canvas = DrawingCanvas(self.window, self.image)
            self.canvas.pack(padx=10, pady=10)

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
