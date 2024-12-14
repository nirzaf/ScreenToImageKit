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
    HIGHLIGHT = auto()
    PIXELATE = auto()
    GRAYSCALE = auto()

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
        self.layer = 0
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
        # Initialize default colors to black
        self.current_color = '#000000'
        self.current_fill = ''  # Empty string for no fill
        self._create_toolbar()

    def _create_toolbar(self):
        """Create the drawing toolbar interface."""
        # Tool selection buttons
        tools_frame = ttk.LabelFrame(self, text="Drawing Tools")
        tools_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

        self._add_tool_button(tools_frame, "Select", DrawingTool.SELECT)
        self._add_tool_button(tools_frame, "Rectangle", DrawingTool.RECTANGLE)
        self._add_tool_button(tools_frame, "Ellipse", DrawingTool.ELLIPSE)
        self._add_tool_button(tools_frame, "Line", DrawingTool.LINE)
        self._add_tool_button(tools_frame, "Arrow", DrawingTool.ARROW)
        self._add_tool_button(tools_frame, "Freehand", DrawingTool.FREEHAND)

        # Text tools
        text_frame = ttk.LabelFrame(self, text="Text Tools")
        text_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        self._add_tool_button(text_frame, "Text", DrawingTool.TEXT)
        self._add_tool_button(text_frame, "Speech", DrawingTool.SPEECH_BUBBLE)
        self._add_tool_button(text_frame, "Counter", DrawingTool.COUNTER)

        # Effects frame
        effects_frame = ttk.LabelFrame(self, text="Effects")
        effects_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

        self._add_tool_button(effects_frame, "Highlight", DrawingTool.HIGHLIGHT)
        self._add_tool_button(effects_frame, "Pixelate", DrawingTool.PIXELATE)
        self._add_tool_button(effects_frame, "Grayscale", DrawingTool.GRAYSCALE)

        # Properties frame
        props_frame = ttk.LabelFrame(self, text="Properties")
        props_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

        # Color picker
        ttk.Button(props_frame, text="Color...", command=self._pick_color).pack(pady=2)
        
        # Line width
        width_frame = ttk.Frame(props_frame)
        width_frame.pack(pady=2)
        ttk.Label(width_frame, text="Width:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="2")
        width_spin = ttk.Spinbox(width_frame, from_=1, to=20, width=3, 
                                textvariable=self.width_var,
                                command=self._width_changed)
        width_spin.pack(side=tk.LEFT)

        # Fill color
        ttk.Button(props_frame, text="Fill Color...", command=self._pick_fill).pack(pady=2)

        # Shadow toggle
        self.shadow_var = tk.BooleanVar(value=False)
        # Shadow effects disabled
        self.shadow_var.set(False)

        # Layer controls
        layer_frame = ttk.LabelFrame(self, text="Layers")
        layer_frame.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)
        
        ttk.Button(layer_frame, text="Bring Forward",
                  command=lambda: self.canvas and self.canvas.bring_to_front(
                      next(iter(self.canvas.selected_elements), None))).pack(pady=2)
        ttk.Button(layer_frame, text="Send Back",
                  command=lambda: self.canvas and self.canvas.send_to_back(
                      next(iter(self.canvas.selected_elements), None))).pack(pady=2)
        ttk.Button(layer_frame, text="Group",
                  command=lambda: self.canvas and self.canvas.group_selected()).pack(pady=2)
        ttk.Button(layer_frame, text="Ungroup",
                  command=lambda: self.canvas and self.canvas.ungroup_selected()).pack(pady=2)
        ttk.Button(layer_frame, text="Lock",
                  command=lambda: self.canvas and self._toggle_lock()).pack(pady=2)

    def _add_tool_button(self, parent, text, tool):
        """Add a tool selection button to the toolbar."""
        btn = ttk.Button(parent, text=text, 
                        command=lambda t=tool: self._select_tool(t))
        btn.pack(pady=2)

    def _select_tool(self, tool):
        """Handle tool selection."""
        self.current_tool = tool
        if self.on_tool_selected:
            self.on_tool_selected(tool)

    def _pick_color(self):
        """Open color picker dialog."""
        color = colorchooser.askcolor(title="Choose Color")
        if color[1]:  # Use the hex color value
            self.current_color = color[1]
            if self.canvas:
                self.canvas.current_color = color[1]
                for element in self.canvas.selected_elements:
                    element.color = color[1]
                self.canvas._update_canvas()

    def _pick_fill(self):
        """Set transparent fill for selected elements."""
        self.current_fill = None
        if self.canvas:
            self.canvas.current_fill = None
            for element in self.canvas.selected_elements:
                element.fill = None
            self.canvas._update_canvas()

    def _width_changed(self):
        """Handle line width change."""
        if self.canvas:
            width = int(self.width_var.get())
            for element in self.canvas.selected_elements:
                element.width = width
            self.canvas.current_width = width
            self.canvas._update_canvas()

    def _toggle_shadow(self):
        """Toggle drop shadow for selected elements."""
        if self.canvas:
            for element in self.canvas.selected_elements:
                element.shadow_offset = 3 if self.shadow_var.get() else 0
            self.canvas._update_canvas()

    def _toggle_lock(self):
        """Toggle lock state for selected elements."""
        if self.canvas:
            for element in self.canvas.selected_elements:
                element.locked = not element.locked
            self.canvas._update_canvas()

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

class DrawingCanvas(tk.Canvas):
    """Canvas for drawing and managing annotation elements."""
    
    def __init__(self, parent, image):
        super().__init__(parent)
        self.parent = parent
        self.image = image
        self.elements = []
        self.selected_elements = set()
        self.clipboard = []
        self.undo_stack = []
        self.redo_stack = []
        self.current_tool = DrawingTool.SELECT
        self.drawing = False
        self.current_element = None
        self.current_color = "#000000"
        self.current_fill = None
        self.current_width = 2
        self._setup_canvas()
        self._bind_events()

    def _setup_canvas(self):
        """Initialize the canvas with the background image."""
        self.photo_image = ImageTk.PhotoImage(self.image)
        self.create_image(0, 0, image=self.photo_image, anchor=tk.NW)

    def _bind_events(self):
        """Bind mouse events and keyboard shortcuts to canvas."""
        # Mouse events
        self.bind("<Button-1>", self._start_drawing)
        self.bind("<B1-Motion>", self._draw)
        self.bind("<ButtonRelease-1>", self._end_drawing)
        
        # Keyboard shortcuts
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-c>", lambda e: self.copy_selected())
        self.bind("<Control-v>", lambda e: self.paste())
        self.bind("<Delete>", lambda e: self.delete_selected())
        
        # Selection events
        self.bind("<Shift-Button-1>", self._add_to_selection)
        self.bind("<Control-Button-1>", self._toggle_selection)
        
        # Element manipulation
        self.bind("<Left>", lambda e: self.move_selected(-1, 0))
        self.bind("<Right>", lambda e: self.move_selected(1, 0))
        self.bind("<Up>", lambda e: self.move_selected(0, -1))
        self.bind("<Down>", lambda e: self.move_selected(0, 1))
        self.bind("<Control-bracketleft>", lambda e: self.rotate_selected(-5))
        self.bind("<Control-bracketright>", lambda e: self.rotate_selected(5))
        
    def undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            return
        
        action, element = self.undo_stack.pop()
        if action == "add":
            self.elements.remove(element)
            self.redo_stack.append(("add", element))
        elif action == "delete":
            self.elements.append(element)
            self.redo_stack.append(("delete", element))
        elif action == "modify":
            old_state, new_state = element
            self._restore_element_state(old_state)
            self.redo_stack.append(("modify", (new_state, old_state)))
        
        self._update_canvas()
        
    def redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            return
            
        action, element = self.redo_stack.pop()
        if action == "add":
            self.elements.append(element)
            self.undo_stack.append(("add", element))
        elif action == "delete":
            self.elements.remove(element)
            self.undo_stack.append(("delete", element))
        elif action == "modify":
            old_state, new_state = element
            self._restore_element_state(old_state)
            self.undo_stack.append(("modify", (new_state, old_state)))
            
        self._update_canvas()
        
    def copy_selected(self):
        """Copy selected elements to clipboard."""
        self.clipboard = []
        for element in self.selected_elements:
            self.clipboard.append(self._clone_element(element))
            
    def paste(self):
        """Paste elements from clipboard."""
        if not self.clipboard:
            return
            
        offset_x = 10
        offset_y = 10
        new_elements = []
        
        for element in self.clipboard:
            new_element = self._clone_element(element)
            new_element.x1 += offset_x
            new_element.y1 += offset_y
            if hasattr(new_element, 'x2'):
                new_element.x2 += offset_x
                new_element.y2 += offset_y
            new_elements.append(new_element)
            
        self.elements.extend(new_elements)
        self.undo_stack.append(("add", new_elements))
        self._update_canvas()
        
    def move_selected(self, dx, dy):
        """Move selected elements by the specified delta."""
        if not self.selected_elements:
            return
            
        for element in self.selected_elements:
            if element.locked:
                continue
            element.x1 += dx
            element.y1 += dy
            if hasattr(element, 'x2'):
                element.x2 += dx
                element.y2 += dy
                
        self._update_canvas()
        
    def rotate_selected(self, angle_delta):
        """Rotate selected elements by the specified angle."""
        if not self.selected_elements:
            return
            
        for element in self.selected_elements:
            if element.locked:
                continue
            element.angle = (element.angle + angle_delta) % 360
            
        self._update_canvas()
        
    def bring_to_front(self, element):
        """Move an element to the front layer."""
        if element in self.elements:
            max_layer = max((e.layer for e in self.elements), default=0)
            element.layer = max_layer + 1
            self._update_canvas()
            
    def send_to_back(self, element):
        """Move an element to the back layer."""
        if element in self.elements:
            min_layer = min((e.layer for e in self.elements), default=0)
            element.layer = min_layer - 1
            self._update_canvas()
            
    def group_selected(self):
        """Group selected elements together."""
        if len(self.selected_elements) < 2:
            return
            
        group = DrawingElement(DrawingTool.SELECT, 0, 0)
        group.elements = list(self.selected_elements)
        for element in group.elements:
            self.elements.remove(element)
        self.elements.append(group)
        self.selected_elements = {group}
        self._update_canvas()
        
    def ungroup_selected(self):
        """Ungroup selected groups."""
        new_elements = []
        for element in self.selected_elements:
            if hasattr(element, 'elements'):
                self.elements.remove(element)
                new_elements.extend(element.elements)
        self.elements.extend(new_elements)
        self.selected_elements = set(new_elements)
        self._update_canvas()

    def _start_drawing(self, event):
        """Handle start of drawing operation."""
        self.drawing = True
        self.current_element = DrawingElement(self.current_tool, event.x, event.y)
        
    def _draw(self, event):
        """Handle drawing motion."""
        if not self.drawing:
            return
            
        if self.current_tool == DrawingTool.FREEHAND:
            self.current_element.points.append((event.x, event.y))
        else:
            self.current_element.x2 = event.x
            self.current_element.y2 = event.y
            
        self._update_preview()

    def _end_drawing(self, event):
        """Handle end of drawing operation."""
        if not self.drawing:
            return
        self.drawing = False
        if not self.current_element:
            return
            
        # Handle text input for text-based tools
        if self.current_element.tool_type in (DrawingTool.TEXT, DrawingTool.SPEECH_BUBBLE):
            dialog = TextInputDialog(self)
            self.wait_window(dialog)
            if dialog.text:
                self.current_element.text = dialog.text
            else:
                self.current_element = None
                return
        elif self.current_element.tool_type == DrawingTool.COUNTER:
            # Find highest counter value and increment
            max_counter = max((e.counter_value for e in self.elements 
                            if e.tool_type == DrawingTool.COUNTER), default=0)
            self.current_element.counter_value = max_counter + 1
            
        # Apply current style properties
        self.current_element.color = self.current_color
        self.current_element.width = self.current_width
            
        self.elements.append(self.current_element)
        self.undo_stack.append(("add", self.current_element))
        self.redo_stack.clear()
        self.current_element = None
        self._update_canvas()

    def _update_preview(self):
        """Update canvas preview during drawing."""
        self._update_canvas()

    def _draw_shadow(self, element):
        """Draw a shadow effect for the given element."""
        # Shadow effects disabled
        pass
        # Shadow properties
        shadow_color = '#000000'
        shadow_alpha = 0.3
        
        # Get element coordinates and properties
        x1, y1 = element.x1 + element.shadow_offset, element.y1 + element.shadow_offset
        if hasattr(element, 'x2'):
            x2, y2 = element.x2 + element.shadow_offset, element.y2 + element.shadow_offset
        else:
            x2, y2 = x1, y1
            
        # Apply shadow based on element type
        shadow_kwargs = {
            'fill': self._with_alpha(shadow_color, shadow_alpha)
        }
        
        if element.tool_type == DrawingTool.RECTANGLE:
            self.create_rectangle(x1, y1, x2, y2, **shadow_kwargs)
        elif element.tool_type == DrawingTool.ELLIPSE:
            self.create_oval(x1, y1, x2, y2, **shadow_kwargs)
        elif element.tool_type in (DrawingTool.LINE, DrawingTool.ARROW):
            shadow_kwargs['width'] = element.width
            self.create_line(x1, y1, x2, y2, **shadow_kwargs)
        elif element.tool_type == DrawingTool.TEXT:
            self.create_text(x1, y1, text=element.text, fill=self._with_alpha(shadow_color, shadow_alpha),
                           font=element.font, anchor='nw')

    def _with_alpha(self, color: str, alpha: float) -> str:
        """Convert color to semi-transparent version."""
        # For Tkinter, we need to use standard color names or #RRGGBB format
        # Convert hex color to RGB
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Apply alpha by darkening the color (mixing with black)
        r = int(r * (1 - alpha))
        g = int(g * (1 - alpha))
        b = int(b * (1 - alpha))
        
        # Return color in #RRGGBB format
        return f'#{r:02x}{g:02x}{b:02x}'
        
    def _restore_element_state(self, state):
        """Restore element state for undo/redo."""
        for element in self.elements:
            if state.get('id') == id(element):
                for key, value in state.items():
                    if key != 'id':
                        setattr(element, key, value)
                break

    def _clone_element(self, element):
        """Create a copy of a drawing element."""
        clone = DrawingElement(element.tool_type, element.x1, element.y1,
                             element.x2, element.y2)
        # Copy all attributes
        for attr in vars(element):
            if attr not in ('x1', 'y1', 'x2', 'y2', 'tool_type'):
                setattr(clone, attr, getattr(element, attr))
        return clone
        
    def _add_to_selection(self, event):
        """Add element to selection."""
        element = self._find_element_at(event.x, event.y)
        if element:
            self.selected_elements.add(element)
            self._update_canvas()
            
    def _toggle_selection(self, event):
        """Toggle element selection."""
        element = self._find_element_at(event.x, event.y)
        if element:
            if element in self.selected_elements:
                self.selected_elements.remove(element)
            else:
                self.selected_elements.add(element)
            self._update_canvas()
            
    def _find_element_at(self, x, y):
        """Find the topmost element at the given coordinates."""
        for element in reversed(self.elements):
            if self._is_point_in_element(element, x, y):
                return element
        return None
        
    def _is_point_in_element(self, element, x, y):
        """Check if a point is within an element's bounds."""
        x1, y1 = min(element.x1, element.x2), min(element.y1, element.y2)
        x2, y2 = max(element.x1, element.x2), max(element.y1, element.y2)
        
        if element.tool_type in (DrawingTool.RECTANGLE, DrawingTool.ELLIPSE,
                               DrawingTool.HIGHLIGHT, DrawingTool.PIXELATE,
                               DrawingTool.GRAYSCALE):
            return x1 <= x <= x2 and y1 <= y <= y2
        elif element.tool_type in (DrawingTool.LINE, DrawingTool.ARROW):
            # Check if point is near the line
            d = self._point_to_line_distance(x, y, element.x1, element.y1,
                                           element.x2, element.y2)
            return d < 5  # 5 pixels tolerance
        return False
        
    def _point_to_line_distance(self, x, y, x1, y1, x2, y2):
        """Calculate distance from point to line segment."""
        A = x - x1
        B = y - y1
        C = x2 - x1
        D = y2 - y1
        
        dot = A * C + B * D
        len_sq = C * C + D * D
        
        if len_sq == 0:
            return math.sqrt(A * A + B * B)
            
        param = dot / len_sq
        
        if param < 0:
            return math.sqrt((x - x1) * (x - x1) + (y - y1) * (y - y1))
        elif param > 1:
            return math.sqrt((x - x2) * (x - x2) + (y - y2) * (y - y2))
        
        return abs(A * D - C * B) / math.sqrt(len_sq)

    def _update_canvas(self):
        """Redraw all elements on the canvas."""
        # Clear and redraw background
        self.delete("all")
        self.create_image(0, 0, image=self.photo_image, anchor=tk.NW)
        
        # Redraw all elements
        for element in sorted(self.elements, key=lambda e: e.layer):
            self._draw_element(element)

        # Draw current element if any
        if self.current_element:
            self._draw_element(self.current_element)

    def _draw_element(self, element):
        """Draw a single element on the canvas."""
        # Draw drop shadow if enabled
        if hasattr(element, 'shadow_offset') and element.shadow_offset > 0:
            self._draw_shadow(element)
            
        # Draw the main element
        if element.tool_type == DrawingTool.RECTANGLE:
            self.create_rectangle(element.x1, element.y1, element.x2, element.y2,
                                outline=element.color, width=element.width,
                                fill=element.fill)
        elif element.tool_type == DrawingTool.ELLIPSE:
            self.create_oval(element.x1, element.y1, element.x2, element.y2,
                           outline=element.color, width=element.width,
                           fill=element.fill)
        elif element.tool_type == DrawingTool.LINE:
            self.create_line(element.x1, element.y1, element.x2, element.y2,
                           fill=element.color, width=element.width)
        elif element.tool_type == DrawingTool.ARROW:
            # Calculate arrow head points
            angle = math.atan2(element.y2 - element.y1, element.x2 - element.x1)
            head_length = min(20, ((element.x2 - element.x1)**2 + (element.y2 - element.y1)**2)**0.5 / 3)
            head_width = head_length * 0.8
            
            # Arrow shaft
            self.create_line(element.x1, element.y1, element.x2, element.y2,
                           fill=element.color, width=element.width)
            
            # Arrow head
            x3 = element.x2 - head_length * math.cos(angle - math.pi/6)
            y3 = element.y2 - head_length * math.sin(angle - math.pi/6)
            x4 = element.x2 - head_length * math.cos(angle + math.pi/6)
            y4 = element.y2 - head_length * math.sin(angle + math.pi/6)
            self.create_polygon(element.x2, element.y2, x3, y3, x4, y4,
                              fill=element.color)
            
        elif element.tool_type == DrawingTool.FREEHAND:
            if hasattr(element, 'points') and len(element.points) > 1:
                self.create_line(element.points, fill=element.color, width=element.width)
                
        elif element.tool_type == DrawingTool.TEXT:
            self.create_text(element.x1, element.y1, text=element.text,
                           font=element.font, fill=element.color,
                           anchor=tk.NW)
            
        elif element.tool_type == DrawingTool.SPEECH_BUBBLE:
            # Draw rounded rectangle for speech bubble
            rx = 20  # corner radius
            points = [
                element.x1 + rx, element.y1,
                element.x2 - rx, element.y1,
                element.x2, element.y1 + rx,
                element.x2, element.y2 - rx,
                element.x2 - rx, element.y2,
                element.x1 + rx, element.y2,
                element.x1, element.y2 - rx,
                element.x1, element.y1 + rx,
            ]
            self.create_polygon(points, smooth=True,
                              outline=element.color, width=element.width,
                              fill=element.fill or "white")
            
            # Draw tail
            tail_points = [
                element.x1 + (element.x2 - element.x1) * 0.7,
                element.y2,
                element.x1 + (element.x2 - element.x1) * 0.5,
                element.y2 + 20,
                element.x1 + (element.x2 - element.x1) * 0.8,
                element.y2,
            ]
            self.create_polygon(tail_points, fill=element.fill or "white",
                              outline=element.color, width=element.width)
            
            if element.text:
                self.create_text((element.x1 + element.x2) / 2,
                               (element.y1 + element.y2) / 2,
                               text=element.text, font=element.font,
                               fill=element.color)
                
        elif element.tool_type == DrawingTool.COUNTER:
            # Draw circle
            r = 15
            self.create_oval(element.x1 - r, element.y1 - r,
                           element.x1 + r, element.y1 + r,
                           outline=element.color, width=element.width,
                           fill=element.fill or "white")
            # Draw number
            self.create_text(element.x1, element.y1,
                           text=str(element.counter_value),
                           font=element.font, fill=element.color)
                           
        elif element.tool_type == DrawingTool.HIGHLIGHT:
            # Create semi-transparent highlight
            highlight_color = self._with_alpha(element.color, 0.3)
            self.create_rectangle(element.x1, element.y1, element.x2, element.y2,
                                fill=highlight_color, outline="")
                                
        elif element.tool_type == DrawingTool.PIXELATE:
            # Mark region for pixelation effect
            self.create_rectangle(element.x1, element.y1, element.x2, element.y2,
                                outline=element.color, width=1,
                                dash=(4, 4))
            # The actual pixelation is applied during image save
            
        elif element.tool_type == DrawingTool.GRAYSCALE:
            # Mark region for grayscale effect
            self.create_rectangle(element.x1, element.y1, element.x2, element.y2,
                                outline=element.color, width=1,
                                dash=(4, 4))
            # The actual grayscale effect is applied during image save