"""Drawing tools and annotation interface for ScreenToImageKit."""

import tkinter as tk
from tkinter import ttk, colorchooser
from PIL import Image, ImageDraw, ImageTk
from enum import Enum, auto
from typing import Optional, Tuple, List
import math

class DrawingTool(Enum):
    """Enumeration of available drawing tools."""
    SELECT = auto()
    RECTANGLE = auto()
    ELLIPSE = auto()
    LINE = auto()
    ARROW = auto()
    FREEHAND = auto()
    TEXT = auto()
    SPEECH_BUBBLE = auto()
    COUNTER = auto()

class DrawingElement:
    """Base class for drawing elements."""
    def __init__(self, tool_type: DrawingTool, x1: int, y1: int, x2: int = None, y2: int = None):
        self.tool_type = tool_type
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2 or x1
        self.y2 = y2 or y1
        self.color = "#000000"
        self.fill = ''  # Empty string for transparent fill
        self.width = 2
        self.font = ("Arial", 12)
        self.text = ""
        self.angle = 0
        self.locked = False
        self.points = []  # For freehand drawing
        self.counter_value = 1  # For counter tool
        self.effect_strength = 10  # For pixelate/blur effects

class DrawingToolbar(ttk.Frame):
    """Toolbar containing drawing tools and options."""
    
    def __init__(self, parent, on_tool_selected=None):
        super().__init__(parent)
        self.current_tool = DrawingTool.SELECT
        self.on_tool_selected = on_tool_selected
        self.canvas = None
        self.current_color = '#000000'  # Default black
        self.current_fill = ''
        
        # Define colors
        self.colors = {
            'Black': '#000000',
            'White': '#FFFFFF',
            'Yellow': '#FFD700',
            'Green': '#32CD32',
            'Blue': '#1E90FF'
        }
        
        # Store reference to current color indicator
        self.current_color_indicator = None
        
        self._create_toolbar()

    def _create_toolbar(self):
        """Create the drawing toolbar interface."""
        # Main toolbar frame
        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Tools frame
        tools_frame = ttk.Frame(toolbar_frame)
        tools_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        # Add tool buttons horizontally
        tools = [
            ("Rectangle", DrawingTool.RECTANGLE),
            ("Ellipse", DrawingTool.ELLIPSE),
            ("Line", DrawingTool.LINE),
            ("Arrow", DrawingTool.ARROW),
            ("Freehand", DrawingTool.FREEHAND),
            ("Text", DrawingTool.TEXT)
        ]

        # Create tool buttons with consistent size and spacing
        for text, tool in tools:
            btn = ttk.Button(tools_frame, text=text, width=10,
                           command=lambda t=tool: self._select_tool(t))
            btn.pack(side=tk.LEFT, padx=2)

        # Color selection frame
        color_frame = ttk.Frame(toolbar_frame)
        color_frame.pack(side=tk.TOP, fill=tk.X, pady=2)

        # Add current color indicator
        current_color_frame = ttk.Frame(color_frame)
        current_color_frame.pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(current_color_frame, text="Current:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Create current color indicator
        self.current_color_indicator = tk.Canvas(current_color_frame, width=20, height=20,
                                               highlightthickness=1, highlightbackground='#666666',
                                               bg=self.current_color)
        self.current_color_indicator.pack(side=tk.LEFT)

        # Add color selection label
        ttk.Label(color_frame, text="Colors:").pack(side=tk.LEFT, padx=(0, 5))

        # Create color selection boxes
        for color_name, color_code in self.colors.items():
            self._create_color_button(color_frame, color_code, color_name)

    def _create_color_button(self, parent, color, name):
        """Create a color selection button."""
        # Create a frame for the color box with white border
        frame = ttk.Frame(parent, style='ColorBox.TFrame')
        frame.pack(side=tk.LEFT, padx=2)
        
        # Create canvas for color box
        canvas = tk.Canvas(frame, width=20, height=20, highlightthickness=1,
                         highlightbackground='#666666', bg=color)
        canvas.pack(padx=1, pady=1)
        
        # Bind click event
        canvas.bind('<Button-1>', lambda e, c=color: self._select_color(c))
        
        # Add tooltip
        self._add_tooltip(canvas, name)

    def _add_tooltip(self, widget, text):
        """Add tooltip to widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, background="#ffffe0", 
                            relief='solid', borderwidth=1)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())
            
        widget.bind('<Enter>', show_tooltip)

    def _select_tool(self, tool):
        """Handle tool selection."""
        self.current_tool = tool
        if self.on_tool_selected:
            self.on_tool_selected(tool)

    def _select_color(self, color):
        """Handle color selection."""
        self.current_color = color
        # Update current color indicator
        if self.current_color_indicator:
            self.current_color_indicator.configure(bg=color)
            
        if self.canvas:
            self.canvas.current_color = color
            # Update selected elements
            for element in self.canvas.selected_elements:
                element.color = color
            self.canvas._update_canvas()

    def set_canvas(self, canvas):
        """Set the associated drawing canvas."""
        self.canvas = canvas
        self.canvas.current_color = self.current_color  # Set initial color

class DrawingCanvas(tk.Canvas):
    """Canvas for drawing and managing annotation elements."""
    
    def __init__(self, parent, image):
        """Initialize drawing canvas.
        
        Args:
            parent: Parent widget
            image: PIL Image object to display
        """
        super().__init__(parent, bg='white', highlightthickness=0)
        self.current_tool = DrawingTool.SELECT
        self.current_color = '#000000'
        self.current_width = 2
        self.elements = []
        self.selected_elements = set()
        self.dragging = False
        self.last_x = None
        self.last_y = None
        self.start_x = None
        self.start_y = None
        self.temp_element = None
        self.original_image = image
        self.freehand_points = []
        
        # Create PhotoImage for display
        self.photo_image = ImageTk.PhotoImage(image)
        self.create_image(0, 0, anchor='nw', image=self.photo_image)
        self.configure(scrollregion=self.bbox('all'))
        
        # Bind mouse events
        self.bind('<Button-1>', self._on_mouse_down)
        self.bind('<B1-Motion>', self._on_mouse_drag)
        self.bind('<ButtonRelease-1>', self._on_mouse_up)
        self.bind('<Button-3>', self._on_right_click)

    def _on_mouse_down(self, event):
        """Handle mouse down event."""
        self.dragging = True
        self.last_x = event.x
        self.last_y = event.y
        self.start_x = event.x
        self.start_y = event.y
        
        if self.current_tool == DrawingTool.FREEHAND:
            self.freehand_points = [(event.x, event.y)]
            self.temp_element = DrawingElement(DrawingTool.FREEHAND, event.x, event.y)
            self.temp_element.points = self.freehand_points
            self.temp_element.color = self.current_color
            self.temp_element.width = self.current_width

    def _on_mouse_drag(self, event):
        """Handle mouse drag event."""
        if not self.dragging:
            return
            
        if self.current_tool == DrawingTool.SELECT:
            self._select_element(event.x, event.y)
        elif self.current_tool == DrawingTool.FREEHAND:
            self.freehand_points.append((event.x, event.y))
            self._update_canvas()
        else:
            if not self.temp_element:
                self.temp_element = DrawingElement(self.current_tool, self.start_x, self.start_y)
                self.temp_element.color = self.current_color
                self.temp_element.width = self.current_width
            self.temp_element.x2 = event.x
            self.temp_element.y2 = event.y
            self._update_canvas()

    def _on_mouse_up(self, event):
        """Handle mouse up event."""
        if not self.dragging:
            return
            
        self.dragging = False
        if self.current_tool != DrawingTool.SELECT:
            if self.temp_element:
                if self.current_tool == DrawingTool.FREEHAND:
                    if len(self.freehand_points) > 1:
                        self.elements.append(self.temp_element)
                    self.freehand_points = []
                else:
                    self.elements.append(self.temp_element)
                self.temp_element = None
                self._update_canvas()

    def _on_right_click(self, event):
        """Handle right click event."""
        self._select_element(event.x, event.y)

    def _select_element(self, x, y):
        """Select element at the given coordinates."""
        for element in reversed(self.elements):
            if self._is_point_in_element(element, x, y):
                self.selected_elements = {element}
                break
        self._update_canvas()

    def _update_canvas(self):
        """Redraw all elements on the canvas."""
        # Clear canvas
        self.delete("all")
        self.create_image(0, 0, anchor='nw', image=self.photo_image)
        
        # Draw all completed elements
        for element in self.elements:
            self._draw_element_on_canvas(element)
        
        # Draw current element being created
        if self.temp_element:
            self._draw_element_on_canvas(self.temp_element)
        
        # Draw selection indicators
        for element in self.selected_elements:
            x1, y1 = element.x1, element.y1
            x2, y2 = getattr(element, 'x2', x1), getattr(element, 'y2', y1)
            self.create_rectangle(
                min(x1, x2) - 2, min(y1, y2) - 2,
                max(x1, x2) + 2, max(y1, y2) + 2,
                outline='#00FF00', width=1, dash=(2, 2)
            )

    def _draw_element_on_canvas(self, element):
        """Draw a single element on the canvas."""
        if element.tool_type in [DrawingTool.LINE, DrawingTool.FREEHAND]:
            kwargs = {
                'fill': element.color,
                'width': element.width
            }
        else:
            kwargs = {
                'fill': '',
                'outline': element.color,
                'width': element.width
            }
        
        if element.tool_type == DrawingTool.RECTANGLE:
            self.create_rectangle(element.x1, element.y1, element.x2, element.y2, **kwargs)
        elif element.tool_type == DrawingTool.ELLIPSE:
            self.create_oval(element.x1, element.y1, element.x2, element.y2, **kwargs)
        elif element.tool_type == DrawingTool.LINE:
            self.create_line(element.x1, element.y1, element.x2, element.y2, **kwargs)
        elif element.tool_type == DrawingTool.ARROW:
            self._draw_arrow(element.x1, element.y1, element.x2, element.y2, element.color, element.width)
        elif element.tool_type == DrawingTool.FREEHAND:
            if hasattr(element, 'points') and len(element.points) > 1:
                self.create_line(*[coord for point in element.points for coord in point], **kwargs)
        elif element.tool_type == DrawingTool.TEXT:
            if hasattr(element, 'text') and element.text:
                self.create_text(element.x1, element.y1, text=element.text,
                               fill=element.color, anchor='nw')

    def _draw_arrow(self, x1, y1, x2, y2, color, width):
        """Draw an arrow line with arrowhead."""
        # Draw the line
        self.create_line(x1, y1, x2, y2, fill=color, width=width)
        
        # Calculate arrowhead
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_size = 10 + width
        
        # Calculate points for arrowhead
        points = [
            x2, y2,
            x2 - arrow_size * math.cos(angle - math.pi/6),
            y2 - arrow_size * math.sin(angle - math.pi/6),
            x2 - arrow_size * math.cos(angle + math.pi/6),
            y2 - arrow_size * math.sin(angle + math.pi/6)
        ]
        
        # Draw arrowhead
        self.create_polygon(points, fill=color, outline=color)

class TextInputDialog(tk.Toplevel):
    """Dialog for entering text."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enter Text")
        self.text = None
        self._create_dialog()
        
    def _create_dialog(self):
        """Create dialog UI."""
        self.text_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.text_var)
        entry.pack(padx=10, pady=5)
        entry.focus_set()
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="OK", command=self._handle_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT)
        
    def _handle_ok(self):
        """Handle OK button click."""
        self.text = self.text_var.get()
        self.destroy()