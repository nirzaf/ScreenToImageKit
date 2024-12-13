"""Area selection window for capturing screenshots."""

import tkinter as tk
import logging

logger = logging.getLogger(__name__)

class SelectionWindow:
    """Window for selecting screen area to capture."""

    def __init__(self, parent, on_selection):
        self.parent = parent
        self.on_selection = on_selection
        self.window = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self._create_window()

    def _create_window(self):
        """Create the selection window."""
        try:
            self.window = tk.Toplevel(self.parent)
            self.window.attributes('-fullscreen', True, '-alpha', 0.3)
            self.window.configure(background='grey')

            # Bind mouse events
            self.window.bind('<Button-1>', self._begin_rect)
            self.window.bind('<B1-Motion>', self._update_rect)
            self.window.bind('<ButtonRelease-1>', self._end_rect)

            # Create canvas for drawing selection rectangle
            self.canvas = tk.Canvas(
                self.window,
                highlightthickness=0
            )
            self.canvas.pack(fill='both', expand=True)
            
            logger.debug("Selection window created successfully")

        except Exception as e:
            logger.error(f"Error creating selection window: {e}")
            if self.window:
                self.window.destroy()
            raise

    def _begin_rect(self, event):
        """Begin drawing selection rectangle."""
        logger.debug(f"Beginning rectangle selection at ({event.x}, {event.y})")
        self.start_x = event.x
        self.start_y = event.y
        
        if self.current_rect:
            self.canvas.delete(self.current_rect)
            
        self.current_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y,
            self.start_x, self.start_y,
            outline='red',
            width=2
        )

    def _update_rect(self, event):
        """Update selection rectangle as mouse moves."""
        if self.current_rect and self.start_x is not None:
            self.canvas.coords(
                self.current_rect,
                self.start_x, self.start_y,
                event.x, event.y
            )

    def _end_rect(self, event):
        """Complete the selection process."""
        if self.current_rect:
            logger.info("Ending rectangle selection")
            coords = self.canvas.coords(self.current_rect)
            logger.debug(f"Selected coordinates: {coords}")
            self.window.destroy()
            
            if self.on_selection:
                self.on_selection(coords)
