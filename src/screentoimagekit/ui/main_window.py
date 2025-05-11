"""Main application window for ScreenToImageKit."""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from PIL import Image, ImageTk
from src.screentoimagekit.progress_tracker import ProgressTracker, WorkflowStage
from src.screentoimagekit.config import ConfigManager
from src.screentoimagekit.services.image_handler import ImageHandler
import pyperclip
import win32con
import win32gui
import win32api
from src.screentoimagekit.ui.config_dialog import ConfigDialog
from src.screentoimagekit.ui.preview_window import PreviewWindow
from src.screentoimagekit.ui.selection_window import SelectionWindow

logger = logging.getLogger(__name__)

class MainWindow:
    """Main application window."""
    
    def __init__(self, root, image_handler, imagekit_service):
        """Initialize the window."""
        self.root = root
        self.image_handler = image_handler
        self.imagekit_service = imagekit_service
        self.config_manager = ConfigManager()
        
        # Load icons
        self.icons = {}
        self._load_icons()
        
        # UI elements
        self.info_label = None
        self.status_label = None
        self.success_label = None
        self.screenshot_button = None
        self.fullscreen_button = None
        self.config_button = None
        self.import_env_button = None
        self.direct_upload_var = None
        self.use_gemini_var = None
        
        # Progress tracking
        self.progress_tracker = ProgressTracker(self._show_status)
        
        # Hotkey state
        self.last_capture_time = 0
        self.is_capturing = False
        
        # Initialize
        self._setup_window()
        self._create_ui()
        self._load_credentials()
        self._setup_message_check()

    def _load_icons(self):
        """Load icons for buttons."""
        icon_files = {
            'capture': 'capture.png',
            'fullscreen': 'capture-full-screen.png',
            'settings': 'settings.png',
            'password': 'password.png',
            'tray': 'tray.png'
        }
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'icons')
        
        for name, filename in icon_files.items():
            try:
                image = Image.open(os.path.join(icons_dir, filename))
                # Resize to appropriate button size
                image = image.resize((24, 24), Image.Resampling.LANCZOS)
                self.icons[name] = ImageTk.PhotoImage(image)
            except Exception as e:
                logger.error(f"Error loading icon {filename}: {e}")
                self.icons[name] = None

    def _create_ui(self):
        """Create the user interface."""
        # Info label
        self.info_label = ttk.Label(
            self.root,
            text="Press Ctrl+W for quick capture, or use buttons below:",
            wraplength=350
        )
        self.info_label.pack(pady=10)

        # Screenshot buttons frame
        buttons_frame = ttk.Frame(self.root)
        buttons_frame.pack(pady=5)

        # Area selection button
        self.screenshot_button = ttk.Button(
            buttons_frame,
            image=self.icons['capture'],
            command=lambda: self._handle_area_selection()
        )
        self.screenshot_button.pack(side=tk.LEFT, padx=5)
        _create_tooltip(self.screenshot_button, "Select Area & Capture")

        # Full screen button
        self.fullscreen_button = ttk.Button(
            buttons_frame,
            image=self.icons['fullscreen'],
            command=lambda: self._handle_fullscreen()
        )
        self.fullscreen_button.pack(side=tk.LEFT, padx=5)
        _create_tooltip(self.fullscreen_button, "Capture Full Screen")

        # Config frame
        config_frame = ttk.Frame(self.root)
        config_frame.pack(pady=10)

        # Configure ImageKit button
        self.config_button = ttk.Button(
            config_frame,
            image=self.icons['settings'],
            command=lambda: self._show_config_dialog()
        )
        self.config_button.pack(side=tk.LEFT, padx=5)
        _create_tooltip(self.config_button, "Configure ImageKit")

        # Import from .env button
        self.import_env_button = ttk.Button(
            config_frame,
            image=self.icons['password'],
            command=lambda: self._import_from_env()
        )
        self.import_env_button.pack(side=tk.LEFT, padx=5)
        _create_tooltip(self.import_env_button, "Import from .env")

        # Options frame
        options_frame = ttk.Frame(self.root)
        options_frame.pack(pady=5)

        # Direct upload checkbox
        self.direct_upload_var = tk.BooleanVar(value=True)
        direct_upload_cb = ttk.Checkbutton(
            options_frame,
            text="Direct Upload",
            variable=self.direct_upload_var
        )
        direct_upload_cb.pack(side=tk.LEFT, padx=5)

        # Use Gemini AI checkbox
        self.use_gemini_var = tk.BooleanVar(value=False)
        use_gemini_cb = ttk.Checkbutton(
            options_frame,
            text="Use Gemini AI",
            variable=self.use_gemini_var
        )
        use_gemini_cb.pack(side=tk.LEFT, padx=5)

        # Status label with colors
        self.status_label = ttk.Label(
            self.root,
            text="Ready",
            foreground="green"
        )
        self.status_label.pack(pady=5)

        # Success label
        self.success_label = ttk.Label(
            self.root,
            text="",
            foreground="green",
            wraplength=350
        )
        self.success_label.pack(pady=5)

        # Exit button
        self.exit_button = ttk.Button(
            self.root,
            text="✖",
            width=3,
            command=lambda: self._exit_app()
        )
        self.exit_button.pack(pady=10)
        _create_tooltip(self.exit_button, "Exit Application")

    def _setup_window(self):
        """Setup main window properties."""
        self.root.title("Screenshot to ImageKit")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.root.iconify)
        
        # Set minimum size to prevent window from becoming too small
        self.root.minsize(300, 200)
        
        # Center window
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Bind hotkey
        self.root.bind('<Control-w>', lambda e: self._quick_capture())

    def _load_credentials(self):
        """Load ImageKit credentials."""
        try:
            private_key, public_key, url_endpoint = self.config_manager.load_credentials()
            if all([private_key, public_key, url_endpoint]):
                if self.imagekit_service.initialize(private_key, public_key, url_endpoint):
                    self.status_label.configure(
                        text="ImageKit configured successfully!",
                        foreground="green"
                    )
                    return True
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            self._show_status("Error loading credentials: " + str(e), True)
        return False

    def _setup_message_check(self):
        """Setup Windows message checking."""
        self.root.after(200, self.check_messages)

    def check_messages(self):
        """Check for hotkey combinations."""
        try:
            current_time = time.time()
            # Check if enough time has passed since last capture (1 second cooldown)
            if current_time - self.last_capture_time >= 1.0 and not self.is_capturing:
                # Check if Ctrl+W is pressed
                if win32api.GetAsyncKeyState(win32con.VK_CONTROL) & 0x8000 and \
                   win32api.GetAsyncKeyState(ord('W')) & 0x8000:
                    self.last_capture_time = current_time
                    self._quick_capture()
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
        finally:
            # Schedule next check (reduced frequency)
            self.root.after(200, self.check_messages)

    def _quick_capture(self):
        """Handle quick capture with Ctrl + W."""
        if self.is_capturing:
            return
            
        logger.info("Quick capture triggered with Ctrl + W")
        self.is_capturing = True
        
        try:
            # Create selection window with callback
            self.area = None
            def on_selection(coords):
                self.area = coords
            
            selection = SelectionWindow(self.root, on_selection)
            self.root.wait_window(selection.window)  # Wait for selection window to close
            
            if self.area:
                # Capture the selected area
                temp_path, screenshot = self.image_handler.capture_area(self.area)
                if temp_path:
                    # Upload to ImageKit
                    try:
                        url = self.imagekit_service.upload_file(temp_path)
                        if url:
                            # Show success message at bottom
                            self._show_success("Screenshot uploaded and URL copied to clipboard!")
                        else:
                            self._show_success("Failed to upload screenshot to ImageKit")
                    except ValueError as ve:
                        self._show_status("ImageKit is not configured. Please configure it first.", True)
                    except Exception as e:
                        self._show_status(f"Failed to upload screenshot: {str(e)}", True)
        except Exception as e:
            logger.error(f"Error during quick capture: {e}")
            self._show_status(f"Failed to capture screenshot: {str(e)}", True)
        finally:
            self.is_capturing = False

    def _handle_area_selection(self):
        """Handle area selection button click."""
        try:
            self.progress_tracker.start_workflow()
            logger.info("Starting area selection")
            
            # Create selection window with callback
            selection = SelectionWindow(self.root, self._on_area_selected)
            
        except Exception as e:
            self.progress_tracker.update_progress(str(e), True)
            logger.error(f"Error in area selection: {e}")

    def _on_area_selected(self, coords):
        """Handle area selection completion."""
        try:
            if not coords or len(coords) != 4:
                logger.warning("Invalid coordinates received")
                return

            # Hide main window during capture
            self.root.withdraw()
            self.root.update()
            time.sleep(0.2)  # Give time for window to hide

            logger.info(f"Capturing screenshot with coords: {coords}")
            
            # Capture the screenshot
            temp_path, screenshot = self.image_handler.capture_area(coords)
            if not temp_path or not screenshot:
                raise Exception("Failed to capture screenshot")

            # Get description if Gemini is enabled
            renamed_path = temp_path
            if self.use_gemini_var.get():
                description = self.image_handler.get_image_description(temp_path)
                if description:
                    renamed_path = self.image_handler.rename_with_description(temp_path, description)
            
            # If direct upload is enabled, skip preview
            if self.direct_upload_var.get():
                self._on_upload_confirmed(renamed_path)
            else:
                # Show preview window
                PreviewWindow(
                    self.root,
                    screenshot,
                    lambda path: self._on_upload_confirmed(renamed_path),
                    lambda path: self._on_preview_cancelled(renamed_path),
                    self.direct_upload_var.get(),
                    self.use_gemini_var.get()
                )
            
            # Restore main window state
            self.root.deiconify()
            self.root.lift()
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            self._show_error(f"Error capturing screenshot: {e}")
            self.progress_tracker.reset()
            self.root.deiconify()

    def _handle_fullscreen(self):
        """Handle full screen capture button click."""
        if not self.imagekit_service.is_configured:
            self._show_status("Please configure ImageKit credentials.", True)
            return

        try:
            self.progress_tracker.start_workflow()
            logger.info("Capturing full screen")
            
            # Hide window before capture
            self.root.withdraw()
            self.root.update()
            time.sleep(0.5)  # Give time for window to hide
            
            # Capture full screen
            temp_path, screenshot = self.image_handler.capture_fullscreen()
            if temp_path and screenshot:
                # Get description if Gemini is enabled
                if self.use_gemini_var.get():
                    description = self.image_handler.get_image_description(temp_path)
                    if description:
                        temp_path = self.image_handler.rename_with_description(temp_path, description)

                # If direct upload is enabled, skip preview
                if self.direct_upload_var.get():
                    self._on_upload_confirmed(temp_path)
                else:
                    # Show preview
                    PreviewWindow(
                        self.root,
                        screenshot,
                        self._on_upload_confirmed,
                        self._on_preview_cancelled,
                        self.direct_upload_var.get(),
                        self.use_gemini_var.get()
                    )
                
                # Restore window
                self.root.deiconify()
                self.root.lift()
            else:
                raise Exception("Failed to capture full screen")
                
        except Exception as e:
            self.progress_tracker.update_progress(str(e), True)
            logger.error(f"Error capturing full screen: {e}")
            self.root.deiconify()

    def _on_upload_confirmed(self, temp_path):
        """Handle upload confirmation from preview window."""
        try:
            if not self.imagekit_service.is_configured:
                raise ValueError("ImageKit is not configured")
            
            url = self.imagekit_service.upload_file(temp_path)
            if url:
                pyperclip.copy(url)
                self._show_success("Screenshot uploaded and URL copied to clipboard!")
                self.progress_tracker.complete()
            else:
                raise Exception("Failed to get URL from ImageKit")
                
        except Exception as e:
            self._show_error(f"Error uploading screenshot: {e}")
            logger.error(f"Error uploading screenshot: {e}")
        finally:
            self.image_handler.cleanup_temp_file(temp_path)

    def _on_preview_cancelled(self, temp_path):
        """Handle preview cancellation."""
        self.image_handler.cleanup_temp_file(temp_path)
        self.progress_tracker.reset()

    def _handle_cancel(self, temp_path):
        """Handle preview cancellation."""
        self.image_handler.cleanup_temp_file(temp_path)

    def _show_config_dialog(self):
        """Handle configuration button click."""
        dialog = ConfigDialog(self.root)
        if dialog.result:
            try:
                if self.imagekit_service.initialize(
                    dialog.result['private_key'],
                    dialog.result['public_key'],
                    dialog.result['url_endpoint']
                ):
                    self.config_manager.save_credentials(
                        dialog.result['private_key'],
                        dialog.result['public_key'],
                        dialog.result['url_endpoint']
                    )
                    self._show_status("Configuration saved successfully!")
                else:
                    self._show_status("Error validating ImageKit credentials.", True)
            except Exception as e:
                logger.error(f"Error saving configuration: {e}")
                self._show_status(f"Error saving configuration: {str(e)}", True)

    def _import_from_env(self):
        """Handle importing configuration from .env file."""
        try:
            private_key, public_key, url_endpoint = self.config_manager.load_env_credentials()
            if all([private_key, public_key, url_endpoint]):
                if self.imagekit_service.initialize(private_key, public_key, url_endpoint):
                    # Save to encrypted storage for future use
                    self.config_manager.save_credentials(private_key, public_key, url_endpoint)
                    self._show_status("Configuration imported from .env successfully!")
                else:
                    self._show_status("Error initializing ImageKit with .env credentials.", True)
            else:
                self._show_status("Missing required credentials in .env file.", True)
        except Exception as e:
            logger.error(f"Error importing .env configuration: {e}")
            self._show_status("Error importing .env configuration: " + str(e), True)

    def _exit_app(self):
        """Exit the application."""
        try:
            # Clean up temporary files
            if hasattr(self, 'image_handler'):
                self.image_handler.cleanup()
            
            # Destroy the window and exit
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during exit: {e}")

    def _show_status(self, message, is_error=False):
        """Show status message with color."""
        if is_error:
            self.status_label.configure(foreground="red", text=message)
        else:
            self.status_label.configure(foreground="green", text=message)
        self.root.update()

    def _show_success(self, message):
        """Show success message in green."""
        self.success_label.configure(text=message, foreground="green")
        self.root.update()

    def _show_error(self, message):
        """Show error message in red."""
        self.success_label.configure(text=message, foreground="red")
        self.root.update()

    def run(self):
        """Start the application main loop."""
        try:
            logger.info("Starting application main loop")
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise

    def hide(self):
        """Hide the main window."""
        self.root.withdraw()

    def show(self):
        """Show and focus the main window."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def close(self):
        """Close the application window."""
        self.root.quit()

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind('<Enter>', self.show)
        self.widget.bind('<Leave>', self.hide)

    def show(self, event=None):
        """Display the tooltip."""
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            self.tooltip,
            text=self.text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1
        )
        label.pack()

    def hide(self, event=None):
        """Hide the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def _create_tooltip(widget, text):
    """Create a tooltip for a widget."""
    ToolTip(widget, text)
